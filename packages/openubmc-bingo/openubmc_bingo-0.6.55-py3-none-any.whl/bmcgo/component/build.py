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
import json
import os
import shutil
import subprocess
import stat
from tempfile import NamedTemporaryFile
import yaml

from mako.lookup import TemplateLookup

from bmcgo.codegen.c.helper import Helper
from bmcgo.logger import Logger
from bmcgo.utils.tools import Tools
from bmcgo.bmcgo_config import BmcgoConfig
from bmcgo.errors import BmcGoException
from bmcgo.component.package_info import InfoComp
from bmcgo.component.component_helper import ComponentHelper
from bmcgo import misc
from bmcgo import errors
from bmcgo.utils.json_validator import JSONValidator
from bmcgo.component.gen import GenComp

log = Logger()
tool = Tools()

cwd_script = os.path.split(os.path.realpath(__file__))[0]


class BuildComp():
    def __init__(self, bconfig: BmcgoConfig, args=None, gen_conanbase=True,
                 service_json="mds/service.json", enable_upload=True):
        self.init_common_params(bconfig)
        self.info: InfoComp = InfoComp(args, service_json, self.bconfig.partner_mode, enable_upload)
        self.set_remote_url()
        self.gen_conanbase(gen_conanbase, service_json)
        self.gen_log()
        self.graph_file = NamedTemporaryFile(suffix=".graph.json")

    @staticmethod
    def get_remote_urls():
        """ Get remote url regardless of the cloned directory """
        git_cmd = Helper.get_git_path()
        cmd = [git_cmd, "remote", "-v"]
        process = subprocess.run(cmd, check=True, capture_output=True)
        return process.stdout.decode("UTF-8").strip().split("\n")

    @staticmethod
    def check_luac():
        conan_bin = os.path.join(os.path.expanduser('~'), ".conan", "bin")
        # 设置PLD_LIBRARY_PATH环境变量，luajit运行时需要加载so动态库
        ld_library_path = conan_bin + ":" + os.environ.get("LD_LIBRARY_PATH", "")
        os.environ["LD_LIBRARY_PATH"] = ld_library_path
        # 设置PATH环境变量，luajit无需指定全路径
        path = conan_bin + ":" + os.environ.get("PATH", "")
        os.environ["PATH"] = path
        os.environ["LUA_PATH"] = f"{conan_bin}/?.lua"
    
    def install_luac(self):
        self.check_luac()
        if self.bconfig.partner_mode:
            return
        conan_bin = os.path.join(os.path.expanduser('~'), ".conan", "bin")
        luac_path = os.path.join(conan_bin, "luac")
        skynet_pkg = "skynet/1.7.0.B002@hw.ibmc.release/stable"
        skynet_flag = skynet_pkg.split("@")[0].replace("/", "_")
        skynet_flag = os.path.join(conan_bin, skynet_flag)

        options = ""
        if self.info.enable_luajit:
            luac_path = os.path.join(conan_bin, "luajit")
            options = "-o skynet:enable_luajit=True"
            skynet_flag += "_luajit"
        else:
            skynet_flag += "luac"
        if os.path.isfile(skynet_flag) and os.path.exists(luac_path):
            os.chmod(luac_path, stat.S_IRWXU)
            return
        if os.path.isdir(conan_bin):
            shutil.rmtree(conan_bin)
        os.makedirs(conan_bin)
        cmd = [misc.CONAN, "install", skynet_pkg, "-pr", "profile.dt.ini", "--build", "-u"]
        cmd += options.split()
        if self.info.remote:
            cmd += ["-r", self.info.remote]
        Helper.run(cmd)
        os.chmod(luac_path, stat.S_IRWXU)
        if self.info.enable_luajit:
            luajit2luac = shutil.which("luajit2luac.sh")
            cmd = ["cp", luajit2luac, f"{conan_bin}/luac"]
            Helper.run(cmd)
        import pathlib
        pathlib.Path(skynet_flag).touch(exist_ok=True)
        

    def gen_conanbase(self, gen_conanbase, service_json):
        if misc.conan_v1():
            lookup = TemplateLookup(directories=os.path.join(cwd_script, "template"))
        else:
            lookup = TemplateLookup(directories=os.path.join(cwd_script, "template_v2"))
        if gen_conanbase:
            template = lookup.get_template("conanbase.py.mako")
            language = self.info.language
            if language == "c" and misc.conan_v2():
                args = ["-s", service_json]
                gen = GenComp(args)
                gen.run(self.info.codegen_base_version)
            conanbase = template.render(lookup=lookup, pkg=self.info, remote_url=self.remote_url,
                                        codegen_version=self.info.codegen_base_version,
                                        language=language)
            file_handler = os.fdopen(os.open("conanbase.py", os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                                            stat.S_IWUSR | stat.S_IRUSR), 'w')
            file_handler.write(conanbase)
            file_handler.close()

    def gen_log(self):
        self.log_file = os.path.join(misc.CACHE_DIR, self.info.name + ".log")
        file_handler = os.fdopen(os.open(self.log_file, os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                                         stat.S_IWUSR | stat.S_IRUSR), 'w')
        file_handler.close()

    def init_common_params(self, bconfig: BmcgoConfig):
        self.bconfig = bconfig
        self.folder = bconfig.component.folder
        os.chdir(self.folder)

    def set_remote_url(self):
        # 上传模式必须有一个地址
        if self.info.upload:
            self.remote_url = self.get_remote_url(False)
        else:
            self.remote_url = self.get_remote_url(True)
        log.info("仓库地址为: %s", self.remote_url)

    def get_remote_url(self, get_first=True):
        """ Get remote url regardless of the cloned directory """
        output_lines = self.get_remote_urls()
        repos = []
        for line in output_lines:
            if line.find("(push)") > 0:
                repos.append(line)
        log.debug("获取仓库列表:")
        log.debug(repos)
        if len(repos) == 0:
            return ""
        repo_id = 0
        if len(repos) > 1 and not get_first:
            log.info("仓库列表:")
            for repo in repos:
                chunk = repo.split(maxsplit=1)
                log.info("仓库基本信息: %s %s %s", repo_id, chunk[0], chunk[1])
                repo_id += 1
            message = input("请选择要使用的仓库地址:")
            repo_id = int(message, 10)
            if repo_id > len(repos):
                raise OSError("未知的仓库, 退出, 请确认仓库!")

        http_proto = "https://"
        repo = repos[repo_id]
        url = repo.split()[1]
        # 如果以https://开头，直接返回
        if url.startswith(http_proto):
            return url
        # 去掉URL的协议部分，转换为https
        url = url.split("@", 1)[1]
        # 无端口的，直接转为https://
        if not url.find(":") > 0:
            return http_proto + url
        chunk = url.split(":", 1)
        # 如果以端口启始的，删除2222端口号
        if chunk[1].startswith("2222/"):
            return http_proto + chunk[0] + "/" + chunk[1].split("/", 1)[1]
        if chunk[1].startswith("/"):
            return http_proto + chunk[0] + chunk[1]
        return http_proto + chunk[0] + "/" + chunk[1]

    def check_conan_profile(self):
        profile = os.path.join(tool.conan_profiles_dir, self.info.profile)
        if not os.path.isfile(profile):
            raise BmcGoException(f"Profile文件{profile} 不存在，系统可能未初始化，" +
                                 f"请在manifest仓执行{misc.tool_name()} build安装产品配套构建工具")
        if misc.conan_v1():
            luajit_profile = os.path.join(tool.conan_profiles_dir, "profile.luajit.ini")
            if self.info.enable_luajit and not os.path.isfile(luajit_profile):
                raise BmcGoException(f"Profile文件{luajit_profile} 不存在，系统可能未初始化，" +
                                    "请在manifest仓(2024.07.04之后的版本)执行bingo build安装产品配套构建工具")

    def upload_conan_v2(self):
        cmd = f"conan cache path {self.info.package}"
        ret = tool.run_command(cmd, capture_output=True)
        recipe_path = ret.stdout.strip()
        conandata = os.path.join(recipe_path, "conandata.yml")
        with open(conandata, mode="r") as fp:
            config_data = yaml.safe_load(fp)
            cfg = config_data.get("sources", {}).get(self.info.version, {})
            if not cfg:
                raise errors.BmcGoException(f"conandata.yml不存在sources/{self.info.version}配置或配置为空")
            if cfg.get("pwd"):
                log.error("检查到错误的conandata.yml配置")
                fp.seek(0, os.SEEK_SET)
                log.error(fp.read())
                raise errors.BmcGoException(f"组件目录存在脏数据或未推送到远程仓，禁止上传")

        cmd = [misc.CONAN, "upload"]
        cmd += ("%s -r %s --force" % (self.info.package, self.info.remote)).split()
        tool.run_command(cmd, show_log=True)

    def upload_conanv1(self):
        if not self.info.upload:
            return
        pkg = "%s/%s%s" % (self.info.name, self.info.version, self.info.channel)
        cmd = [misc.CONAN, "info"]
        cmd += ("%s %s -s build_type=%s -j" % (pkg, self.info.full_profile, self.info.build_type.capitalize())).split()
        lines = subprocess.run(cmd, capture_output=True, check=True).stdout.decode("utf-8").split("\n")
        conan_info = None
        for line in lines:
            if line.startswith("[{"):
                conan_info = json.loads(line)
                break
        pkg_id = None
        for item in conan_info:
            if item["reference"] == pkg:
                pkg_id = item["id"]
                break
        if pkg_id is None:
            raise OSError(f"获取包版本配置无效, 包名: {pkg}")
        cmd = [misc.CONAN, "upload"]
        cmd += ("%s:%s -r %s --all" % (pkg, pkg_id, self.info.remote)).split()
        tool.run_command(cmd, show_log=True)

    def run_conan_v1(self):
        tool.clean_locks()
        self.check_conan_profile()
        self.install_luac()
        from_source = "--build=missing"
        if self.info.from_source:
            from_source = "--build"
        cache_dir = os.path.join(os.path.expanduser("~/.conan/data"), self.info.package.replace("@", "/"))
        if self.info.no_cache:
            shutil.rmtree(cache_dir, ignore_errors=True)
        # 构建当前组件
        append = "%s %s -tf None" % (self.info.cmd_base, from_source)
        if self.info.no_cache:
            append += " -u"
        cmd = [misc.CONAN, "create"]
        cmd += append.split()
        tool.run_command(cmd, show_log=True)
        self._check_sr_validation(os.path.join(cache_dir, "package"))
        if self.info.upload:
            self.upload_conanv1()

    def run_conan_v2(self):
        self.check_conan_profile()
        from_source = ""
        if not self.info.without_build:
            from_source = f"--build={self.info.name}/*"
        if self.info.from_source:
            from_source = "--build=*"
        else:
            from_source += " --build=missing"
        # # 构建当前组件
        args = "%s %s" % (self.info.cmd_base, from_source)
        if self.info.no_cache:
            args += " -u"
        cmd = [misc.CONAN, "create", "--name", self.info.name, "--version", self.info.version]
        args += f" -f json --out-file={self.graph_file.name} -tf="
        cmd += args.split()
        tool.run_command(cmd, show_log=True)
        package_folder = tool.get_package_folder_from_graph_file(self.graph_file.name, self.info.package)
        self._check_sr_validation(package_folder)
        if self.info.upload:
            self.upload_conan_v2()

    def run(self):
        if misc.conan_v1():
            self.run_conan_v1()
        else:
            self.run_conan_v2()

    def test(self):
        if os.path.isdir("test_package"):
            cmd = [misc.CONAN, "create"]
            cmd += self.info.cmd_base.split()
            cmd += ["--build=missing"]
            cmd += ["-tf", "test_package"]
            Helper.run(cmd)

    def _check_sr_validation(self, dir_path):
        # 检查所有 sr 文件是否合法
        log.info("========== sr 文件检查开始 ==========")
        jc = self.bconfig.bmcgo_config_list.get(misc.ENV_CONST, {}).get(misc.JSON_CHECKER, None)
        JSONValidator().validate_files(dir_path, ['sr'], jc)
        log.info("========== sr 文件检查结束 ==========")
