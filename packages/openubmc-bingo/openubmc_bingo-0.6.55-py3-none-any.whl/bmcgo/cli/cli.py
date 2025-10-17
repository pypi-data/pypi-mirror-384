#!/usr/bin/python3
# coding: utf-8
# Copyright (c) 2024 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import argparse
import inspect
import os
import signal
import sys
import textwrap
import importlib
import stat
import json
import re
import traceback
from tempfile import NamedTemporaryFile
from importlib.util import spec_from_file_location, module_from_spec

import yaml
from colorama import Fore, Style
from conan import conan_version

from bmcgo import __version__ as client_version
from bmcgo.component.build import BuildComp
from bmcgo.component.test import TestComp
from bmcgo.component.deploy import DeployComp
from bmcgo.component.gen import GenComp
from bmcgo import errors
from bmcgo import misc
from bmcgo.logger import Logger
from bmcgo.frame import Frame
from bmcgo.bmcgo_config import BmcgoConfig
from bmcgo.utils.tools import Tools
from bmcgo.utils.config import Config


cwd = os.getcwd()
tools = Tools()
log = tools.log

SKIP_CONFIG_COMMANDS = ("config")


class Command(object):
    """A single command of the bmcgo application, with all the first level commands. Manages the
    parsing of parameters and delegates functionality in collaborators. It can also show the
    help of the tool.
    """
    def __init__(self, config: BmcgoConfig = None):
        if not config:
            self.bconfig = BmcgoConfig()
        else:
            self.bconfig = config
        # 请使用_get_command_group获取命令组
        self._command_group = None
        self.comp_cmds = {
            misc.BUILD: misc.BUILD,
            misc.DEPLOY: misc.DEPLOY,
            misc.TEST: misc.TEST,
            misc.GEN: misc.GEN
        }

        self.inte_cmds = {
            misc.BUILD: misc.BUILD,
            "publish": "inte_publish",
        }
        self.misc_cmds = {
            misc.HELP: misc.HELP
        }

        self.studio_cmds = {
        }

        self.conan_idx_cmds = {
        }

        self.ibmc_sdk_cmds = {
        }

        self.cmd_info_dict = {
            misc.GRP_MISC: self.misc_cmds,
            misc.GRP_COMP: self.comp_cmds,
            misc.GRP_INTE: self.inte_cmds,
            misc.GRP_STUDIO: self.studio_cmds,
            misc.GRP_CONAN_IDX: self.conan_idx_cmds,
            misc.GRP_IBMC_SDK: self.ibmc_sdk_cmds
        }
        # 扩展targets文件存储路径，由子类定义
        self.ext_targets_dir = ""

    @property
    def __is_valid_component(self):
        return self.bconfig.component is not None

    @staticmethod
    def _match_command(comm_key: str, command, is_full_match: bool):
        if is_full_match and comm_key == command:
            return True
        elif not is_full_match and comm_key.startswith(command):
            return True
        return False

    @staticmethod
    def _import_from_path(module_name, file_path):
        """"从指定路径动态导入模块"""
        # 创建模块规范
        spec = spec_from_file_location(module_name, file_path)
        if not spec:
            raise ImportError(f"无法从路径{file_path}导入模块{module_name}")
        # 创建新模块
        module = module_from_spec(spec)
        # 添加到sys.modules缓存
        sys.modules[module_name] = module
        # 执行模块代码
        spec.loader.exec_module(module)
        return module

    def frame_build(self, args=None):
        _, work_dir = self._is_integrated_project()
        os.chdir(work_dir)
        config = Config(self.bconfig)
        frame = Frame(self.bconfig, config)
        frame.parse(args, self.ext_targets_dir)
        return frame.run()

    def help(self, *args):
        """
        获取命令帮助
        """

        parser = argparse.ArgumentParser(description=self.help.__doc__,
                                         prog=misc.tool_name() + " help")
        parser.add_argument("command", help='command', nargs="?")
        args = parser.parse_args(*args)
        if not args.command:
            self._show_help()
            return
        try:
            commands = self._commands(False)
            method = commands[args.command]
            self._warn_dependencies_version()
            method(["--help"])
        except KeyError as exp:
            log.debug("Exception: %s", str(exp))
            raise errors.BmcGoException("未知命令 '%s'" % args.command) from exp

    def gen(self, *args):
        """
        代码自动生成，支持Lua和C语言，C组件需要在service.json中添加`"language": "c",`配置.

        支持自动生成服务端和客户端C代码
        """
        argv = args[0]
        # 未指定参数时，使用mds/service.json的配置
        if "-i" not in argv and "-s" not in argv:
            if os.path.isfile("mds/service.json"):
                argv.append("-s")
                argv.append("mds/service.json")
        gen = GenComp(argv)
        gen.run()

    # build package
    def build(self, *args):
        """
        构建出包

            组件需要支持多种跨平台构建场景，典型的包括DT（X86-64）、交叉编译（arm64）
        """
        argv = args[0]
        is_integrated, _ = self._is_integrated_project()
        if is_integrated:
            return self.frame_build(argv)
        is_valid_component = self.__is_valid_component
        if is_valid_component:
            os.chdir(self.bconfig.component.folder)
            build = BuildComp(self.bconfig, argv)
            build.run()
            os.chdir(cwd)
            log.success("构建成功")
        else:
            log.error('注意：检测到当前目录即不是合法的组件(Component)目录也不是合法的产品(Manifest)目录')
            return -1
        return 0

    def inte_publish(self, *args):
        """
        构建版本发布包，-sc参数指定ToSupportE编码

            版本构建
        """
        is_integrated, _ = self._is_integrated_project()
        if not is_integrated:
            raise errors.NotIntegrateException("检测到当前环境中缺少frame.py，可能不是一个合法的manniest仓")
        args = args[0]
        args.append("-t")
        args.append("publish")
        return self.frame_build(args)

    # test package
    def test(self, *args):
        """
        构建DT.

        组件DT用例执行
        """
        argv = args[0]
        if self.__is_valid_component:
            test = TestComp(self.bconfig, argv)
            test.run()
        else:
            log.error(f"这可能是一个无效的 {misc.tool_name()} 组件, 因为 mds/service.json 文件不存在, 构建终止")

    # deploy package
    def deploy(self, *args):
        """
        将组件及其依赖部署至temp/rootfs目录
        """
        if not self.__is_valid_component:
            log.error(f"这可能是一个无效的 {misc.tool_name()} 组件, 因为 mds/service.json 文件不存在, 构建终止")
            return -1
        log.info("安装 package 目录到 ./temp, 开始!")
        argv = args[0]

        # 构建组件
        build = BuildComp(self.bconfig, argv)
        build.run()
        os.chdir(cwd)
        log.success("构建成功")
        # 部署组件
        deploy = DeployComp(self.bconfig, build.info)
        deploy.run()
        os.chdir(cwd)
        log.success("部署 package 目录到 ./temp 成功!")
        return 0

    def run(self, *args):
        """HIDDEN: entry point for executing commands, dispatcher to class
        methods
        """
        force_conan2 = False
        if "--conan2" in args[0]:
            force_conan2 = True
        if not self._check_conan(force_conan2):
            return 1
        self._check_conan_profile()

        try:
            command = args[0][0]
        except IndexError:  # No parameters
            self._show_help()
            return 0
        try:
            if command in ["-v", "--version"]:
                self.show_version()
                return 0

            self._warn_dependencies_version()

            if command in ["-h", "--help"]:
                self._show_help()
                return 0
            #检查是否需要升级
            if self.bconfig.bingo_version_range:
                result_code = self.bingo_upgrade()
                if result_code == 0:
                    log.info("自动升级完成，请重新运行命令")
                return result_code
            valid_command = self._find_real_command(command)
            # 命令参数
            command_args = args[0][1:]
            if isinstance(valid_command, misc.CommandInfo):
                if ("-h" in command_args or "--help" in command_args) and valid_command.help_info is not None:
                    self._show_help_data("", valid_command.help_info)
                    return 0

                module = valid_command.module(self.bconfig, command_args)
                self._init_bmcgo_environ(valid_command.name)
                return module.run()
            elif isinstance(valid_command, str):
                commands = self._commands(True)
                method = commands.get(valid_command)
                if method:
                    self._init_bmcgo_environ(valid_command)
                    return method(command_args)

        except SystemExit as exc:
            if os.environ.get("LOG"):
                log.error(traceback.format_exc())
            if exc.code != 0:
                log.error("构建已退出, 退出码为: %d", exc.code)
            return exc.code
        except errors.ExitOk as exc:
            if os.environ.get("LOG"):
                log.error(traceback.format_exc())
            log.info(str(exc))
            return 0
        except (errors.BmcGoException, errors.EnvironmentException, KeyboardInterrupt) as exc:
            if os.environ.get("LOG"):
                log.error(traceback.format_exc())
            log.error(str(exc))
            log.error("请查看日志信息")
            return -1
        except Exception as exc:
            if os.environ.get("LOG"):
                log.error(traceback.format_exc())
            msg = str(exc)
            log.error(msg)
            log.error("请查看日志信息")
            return -1
        log.error("'%s' 不是 %s 命令. 使用 '%s -h' 查看帮助文档", command, misc.tool_name(), misc.tool_name())
        return -1

    def show_version(self):
        log.info("bingo 版本为: %s", client_version)
        studio_version = self._bmc_studio_version()
        if studio_version:
            log.info("bmc-studio 版本为: %s", studio_version)
    
    def bingo_upgrade(self):
        version_range = self.bconfig.bingo_version_range.replace(",", " ")
        log.info(f"检测到当前版本：{client_version}与约束版本{version_range}不匹配，将自动升级，完成后请重新运行")
        from bmcgo.functional.upgrade import BmcgoCommand as upcommand
        cmd = upcommand(self.bconfig, (["-v", f"bingo{self.bconfig.bingo_version_range}", "-f"]))
        return cmd.run()

    def conan_init(self):
        if misc.conan_v2():
            tools.run_command("conan profile detect --force")
        else:
            tools.run_command("conan config init")
            tools.run_command("conan config set general.revisions_enabled=1")

    def _check_conan_profile(self):
        profile_dir = os.path.join(tools.conan_home, "profiles")
        if not os.path.isdir(profile_dir):
            self.conan_init()

        if misc.conan_v2():
            bingo_profiles = "/usr/share/bingo/profiles_for_conan2"
        else:
            bingo_profiles = "/usr/share/bingo/profiles_for_conan1"
        if not os.path.isdir("/opt/RTOS"):
            log.info(f"未检测到/opt/RTOS目录，可能未安装构建工具，请正确安装构建工具（可以manifest仓执行init.py或{misc.tool_name()} build）")
            return
        rtos_version = ""
        for ver in os.listdir("/opt/RTOS"):
            if re.match("^208\\.[0-9]+\\.[0-9]+$", ver):
                if rtos_version:
                    log.warning(f"/opt/RTOS安装了多个RTOS工具版本，版本不匹配将导致编译失败，建议只保留其中一个，本次将使用{rtos_version}构建。")
                    break
                rtos_version = ver
        if not rtos_version:
            log.info(f"未检测到/opt/RTOS目录下的构建工具，可能未安装构建工具，请正确安装构建工具（可以manifest仓执行init.py或{misc.tool_name()} build）")
            return
        if not os.path.isdir(bingo_profiles):
            return
        for file in os.listdir(bingo_profiles):
            os.makedirs(profile_dir, exist_ok=True)
            src_file = os.path.join(bingo_profiles, file)
            dst_file = os.path.join(profile_dir, file)
            if not os.path.isfile(dst_file):
                log.info(f"复制 {src_file} 到 {dst_file}")
                tools.run_command(f"cp {src_file} {dst_file}")
            tools.run_command(f"sed -i 's/208\\.[0-9]\\+\\.[0-9]\\+/{rtos_version}/g' {dst_file}", command_echo=False)

    def _check_conan(self, force_conan2):
        need_conan_v2 = force_conan2
        conf = None
        if self.bconfig.component and not force_conan2:
            conanfile = os.path.join(self.bconfig.component.folder, "conanfile.py")
            conf = self.bconfig.component.config
            if not os.path.isfile(conanfile):
                log.info("未检测到组件的conanfile.py, 构建可能失败")
                return True
            with open(conanfile, "r") as fp:
                lines = fp.readlines()
            for line in lines:
                if not line.startswith("required_conan_version"):
                    continue
                match = re.search("\"(.*)\"", line)
                if not match:
                    continue
                import semver
                if semver.satisfies("2.13.0", match[1]):
                    need_conan_v2 = True
                    break
        elif not force_conan2:
            if self.bconfig.ibmc_sdk:
                conf = self.bconfig.ibmc_sdk.config
            elif self.bconfig.manifest:
                conf = self.bconfig.manifest.config
            if conf:
                conan_require = conf.get(misc.CONAN, "version", fallback="")
                if conan_require.startswith("2"):
                    need_conan_v2 = True
            else:
                return True
        if need_conan_v2 and misc.conan_v1():
            log.warning("检测到依赖conan2.0但仅安装了conan1.0，尝试重新安装conan2.0")
            log.info("1. 组件仓支持conan2.0的依据：conanfile.py中未申明`required_conan_version`或依赖conan 2.x.x，\
                     如`quired_conan_version = '>=2.13.0'`")
            log.info("2. manifest或ibmc_sdk仓等支持conan2.0的依据：.bmcgo/config或.bingo/config文件记录的conan.version配置版本以2开头，如配置为:")
            log.info("    [conan]")
            log.info("    version = 2.x.x")
            log.info("3. conan_index仓使用参数`--conan2`控制是否构建conan2.0包（conan2.0包配方存储在recipes2目录）")
            tools.run_command("pip3 install conan==2.13.0 --break-system-packages")
            log.warning("检测到依赖conan2.0但仅安装了conan1.0，已安装conan2.0，任务退出，请重新执行")
            return False
        if not need_conan_v2 and misc.conan_v2():
            log.warning("检测到依赖conan1.0但仅安装了conan2.0，尝试重新安装conan1.0")
            log.info("1. 组件仓支持conan1.0的依据：conanfile.py中未申明`required_conan_version`或依赖conan 1.x.x")
            log.info("2. manifest或ibmc_sdk仓支持conan1.0的依据：.bmcgo/config或.bingo/config文件未记录的conan.version配置")
            log.info("3. conan_index仓默认（不指定`--conan2`时）构建conan1.0包（conan1.0包配方存储在recipes目录）")
            tools.run_command("pip3 install conan==1.62.0 --break-system-packages")
            log.warning("检测到依赖conan1.0但仅安装了conan2.0，已安装conan1.0，任务退出，请重新执行")
            return False
        return True

    def _init_bmcgo_environ(self, command):
        if command not in SKIP_CONFIG_COMMANDS and misc.ENV_CONST in self.bconfig.bmcgo_config_list:
            log.info("检测到配置项环境变量，开始使用")
            for env, value in self.bconfig.bmcgo_config_list[misc.ENV_CONST].items():
                log.info("环境变量%s配置为: %s", env, value)
                if os.environ.get(env.upper()):
                    os.environ[env.upper()] = value
                os.environ[env.lower()] = value

    def _find_real_command(self, command):
        if command == misc.HELP:
            return misc.HELP
        # 全词匹配
        full_match_command = self._match_real_command(command)
        if full_match_command:
            return full_match_command
        # 前缀匹配
        start_match_command = self._match_real_command(command, False)
        if start_match_command:
            return start_match_command
        raise errors.CommandNotFoundException(f"未找到命令: {command}, 请执行{misc.tool_name()} -h检查支持的命令")

    def _match_real_command(self, command, is_full_match=True):
        is_integrated, _ = self._is_integrated_project()
        for group_name, comm_names in self._get_command_group():
            is_component_valid = group_name.startswith("Component") and self.__is_valid_component
            is_integrated_valid = group_name.startswith("Integrated") and is_integrated
            is_conan_idx_valid = group_name.startswith("Conan Index") and self.bconfig.conan_index
            is_ibmc_sdk_valid = group_name.startswith("SDK") and self.bconfig.ibmc_sdk
            is_misc_valid = group_name.startswith("Misc")
            is_studio_valid = group_name.startswith("Studio")
            is_group_valid = is_component_valid or is_integrated_valid or is_misc_valid \
                            or is_studio_valid or is_conan_idx_valid or is_ibmc_sdk_valid
            for name, real_method in comm_names.items():
                if (is_group_valid and self._match_command(name, command, is_full_match)):
                    return real_method
        return None

    def _bmc_studio_version(self):
        """检查当前环境中正在使用的bmc studio版本，
        优先通过pip获取，获取不到通过bmc_studio/mds/server获取
        """
        studio_path = tools.get_studio_path()
        bmc_studio_conf = os.path.join(f"{studio_path}/mds/service.json")
        if not os.path.isfile(bmc_studio_conf):
            return ""

        with open(bmc_studio_conf, "r") as conf_fp:
            conf_data = json.load(conf_fp)
            if "version" not in conf_data:
                return ""

        return conf_data["version"]

    def _gen_command_group(self):
        self._command_group = []
        self._command_group.append((misc.GRP_INTE, self.inte_cmds))
        self._command_group.append((misc.GRP_COMP, self.comp_cmds))
        self._command_group.append((misc.GRP_CONAN_IDX, self.conan_idx_cmds))
        self._command_group.append((misc.GRP_IBMC_SDK, self.ibmc_sdk_cmds))
        self._command_group.append((misc.GRP_MISC, self.misc_cmds))
        self._command_group.append((misc.GRP_STUDIO, self.studio_cmds))
        return self._command_group

    def _load_functional(self, functional_path):
        for file in os.listdir(functional_path):
            if file.startswith("_"):
                continue

            file = os.path.join(functional_path, file)
            if not os.path.isfile(file) or not file.endswith(".py"):
                log.debug(f"{file} 不是一个目录或者不是以 .py 结尾的文件, 继续")
                continue

            module_name = os.path.basename(file)[:-3]
            try:
                # 先尝试卸载旧模块
                if module_name in sys.modules:
                    del sys.modules[module_name]
                # 使导入缓存失效
                importlib.invalidate_caches()
                module = self._import_from_path(module_name, file)
                availabile_check = getattr(module, "if_available", None)
                if availabile_check is None:
                    log.debug(f"方法 if_available 没有找到, 跳过 {module_name}")
                    continue
                if not availabile_check(self.bconfig):
                    log.debug(f"方法 if_available 返回 false, 跳过 {module_name}")
                    continue
                cmd_info: misc.CommandInfo = getattr(module, "command_info", None)
                if cmd_info is None:
                    log.debug(f"属性 command_info 没找到, 跳过 {module_name}")
                    continue
                cmd_info.module = getattr(module, "BmcgoCommand", None)
                if cmd_info.module is None:
                    log.debug(f"类 BmcgoCommand 没找到, 跳过 {module_name}")
                    continue

                if cmd_info.group in self.cmd_info_dict:
                    cmds = self.cmd_info_dict.get(cmd_info.group)
                    cmds[cmd_info.name] = cmd_info
                else:
                    raise errors.ConfigException(f"未支持的组 {cmd_info.group}, 无法获取")
            except ModuleNotFoundError:
                log.info(f"导入模块 {module_name} 失败")

    def _gen_command_group_base(self):
        self._load_functional(self.bconfig.functional_path)

    def _get_command_group(self):
        if self._command_group:
            return self._command_group
        self._gen_command_group_base()
        return self._gen_command_group()

    def _show_command_help(self, commands, name, real_method):
        # future-proof way to ensure tabular formatting
        fmt = '    %s'
        if len(name) > 16:
            cmd_name = (fmt % (Fore.GREEN + name[:16] + Style.RESET_ALL))
        else:
            cmd_name = (fmt % (Fore.GREEN + name + Style.RESET_ALL))

        if len(cmd_name) < 32:
            space = " " * (32 - len(cmd_name))
            cmd_name += space

        if isinstance(real_method, str):
            command = commands.get(real_method)
            if command is None:
                return
            # Help will be all the lines up to the first empty one
            docstring_lines = command.__doc__.split('\n')
        elif isinstance(real_method, misc.CommandInfo):
            if not log.is_debug and real_method.hidden:
                return
            docstring_lines = real_method.description
        else:
            return
        data = self._doc_append(docstring_lines)
        if len(name) > 16:
            data.insert(0, name)
        self._show_help_data(cmd_name, data)

    def _show_help(self):
        """
        Prints a summary of all commands.
        """

        commands = self._commands()
        for group_name, comm_names in self._get_command_group():
            if not comm_names:
                continue
            if group_name == misc.GRP_INTE and not self.bconfig.manifest:
                continue
            if group_name == misc.GRP_COMP and not self.bconfig.component:
                continue
            log.info(group_name)
            for name, real_method in comm_names.items():
                self._show_command_help(commands, name, real_method)

        log.info("")
        if self.bconfig.manifest is None and self.bconfig.component is None:
            log.warning(f"未找到 .bmcgo/config或mds/service.json 配置文件, 当前路径可能未包含 {misc.tool_name()} 项目")
            return
        log.info(f'输入 "{misc.tool_name()} <command> -h" 获取子命令帮助')

    def _doc_append(self, lines):
        start = False
        data = []
        for line in lines:
            line = line.strip()
            if not line:
                if start:
                    break
                start = True
                continue
            data.append(line)
        return data

    def _commands(self, show_hidden=False):
        """ Returns a list of available commands.
        """
        result = {}
        for member in inspect.getmembers(self, predicate=inspect.ismethod):
            method_name = member[0]
            if not method_name.startswith('_'):
                method = member[1]
                if method.__doc__ and (show_hidden or not method.__doc__.startswith('HIDDEN')):
                    result[method_name] = method
        return result

    def _warn_dependencies_version(self):
        width = 70
        version = sys.version_info
        if version.major < 3:
            log.info("%s\n 不在提供 Python 2支持. 强烈推荐使用 Python >= 3.0\n", "*" * width)

        log.info("conan版本: " + str(conan_version))

    def _show_help_data(self, cmd_name, help_lines):
        log.info("%s%s", cmd_name, help_lines[0])
        for help_line in help_lines[1:]:
            split_lines = textwrap.wrap(help_line, 80)
            for split_line in split_lines:
                log.info("                       %s", split_line)

    def _is_integrated_project(self):
        if os.path.isfile("build/frame.py"):
            return True, os.getcwd()
        if os.path.isfile("frame.py"):
            return True, os.path.realpath(os.path.join(os.getcwd(), ".."))
        if self.bconfig.manifest is not None:
            return True, self.bconfig.manifest.folder
        return False, None


def prepare_conan():
    if misc.conan_v2():
        return
    home = os.environ["HOME"]
    settings_yml = os.path.join(home, ".conan", "settings.yml")
    if not os.path.isfile(settings_yml):
        return
    with open(settings_yml, mode="r") as fp:
        config_data = yaml.safe_load(fp)
    gcc = config_data["compiler"].get("gcc")
    if gcc.get("luajit") is None:
        config_data["compiler"]["gcc"]["luajit"] = [
            None, "1.7.x"
        ]
    if "Dt" not in config_data["build_type"]:
        config_data["build_type"].append("Dt")
    hm_os = "HongMeng"
    if hm_os not in config_data["os_target"]:
        config_data["os_target"].append(hm_os)
    if config_data["os"].get(hm_os) is None:
        config_data["os"][hm_os] = None
    with os.fdopen(os.open(settings_yml, os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                            stat.S_IWUSR | stat.S_IRUSR), 'w+') as file_handler:
        file_handler.write(yaml.safe_dump(config_data, indent=2, sort_keys=False))


def run(args, command: Command = None):
    """
    main entry point of the bmcgo application, using a Command to
    parse parameters
    """
    os.makedirs(misc.CACHE_DIR, exist_ok=True)

    try:
        tools.run_command("whoami", show_log=True)
        prepare_conan()
        if not command:
            command = Command()
        error = command.run(args)
    except errors.ExitOk as exc:
        log.info(str(exc))
        error = 0
    except Exception as exc:
        if os.environ.get("LOG"):
            log.error(traceback.format_exc())
        msg = str(exc)
        log.error(msg)
        error = -1
    return error


def main(args):
    return run(args)
