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
import os
import shutil
import stat
import json
import yaml

from mako.lookup import TemplateLookup

from bmcgo.component.package_info import InfoComp
from bmcgo.component.component_helper import ComponentHelper
from bmcgo.codegen.c.helper import Helper
from bmcgo.logger import Logger
from bmcgo.bmcgo_config import BmcgoConfig
from bmcgo import misc

log = Logger("deploy")

cwd_script = os.path.split(os.path.realpath(__file__))[0]


class GraphNode:
    def __init__(self, node):
        if not node:
            self.name = None
            self.package_folder = None
            self.recipe_folder = None
            self.package_id = None
            self.ref = None
            self.node = node
            return
        self.name = node.get("name")
        self.package_folder = node.get("package_folder")
        self.recipe_folder = node.get("recipe_folder")
        self.package_id = node.get("package_id")
        self.ref = node.get("ref")
        self.node = node


class DeployComp():
    def __init__(self, bconfig: BmcgoConfig, info: InfoComp = None):
        self.info: InfoComp = info
        self.bconfig = bconfig
        self.folder = bconfig.component.folder
        os.chdir(self.folder)
        self.temp_path = os.path.join(self.folder, "temp")
        self.graph_nodes: dict[str, GraphNode] = {}

    @staticmethod
    def copy_packages_v1(install_path, rootfs_path):
        for sub_dir in os.listdir(install_path):
            dir_path = os.path.join(install_path, sub_dir)
            if os.path.isfile(dir_path):
                os.unlink(dir_path)
                continue
            for file in os.listdir(dir_path):
                source = os.path.join(dir_path, file)
                cmd = ["/usr/bin/cp", "-arf", source, rootfs_path]
                Helper.run(cmd)

    def get_dt_dependencies(self):
        user_channel = ComponentHelper.get_user_channel(self.info.stage)
        # DT专用的依赖，只在部署时添加
        dependencies = []
        with open(self.bconfig.conf_path, "r") as fp:
            config = yaml.safe_load(fp)
        dt_dependencies = config.get("dt_dependencies", {})
        lua_run_deps = [dt_dependencies.get("luaunit")]
        # 只有lua需要添加依赖
        if not os.path.isdir("test_package") and self.info.coverage:
            lua_run_deps.append(dt_dependencies.get("luacov"))
            lua_run_deps.append(dt_dependencies.get("luafilesystem"))
        for dep in lua_run_deps:
            for build_dep in self.info.build_dependencies:
                if build_dep.startswith(dep.split("/", -1)[0]):
                    dep = build_dep
                    break
            if "@" not in dep:
                dep += user_channel
            dependencies.append(dep)
        
        dependencies += self.info.test_dependencies
        return dependencies

    def gen_conanfile(self):
        dependencies = [self.info.package]
        if self.info.test:
            dependencies += self.get_dt_dependencies()

        # 构建虚拟deploy组件，生成conanfile.py文件
        if misc.conan_v1():
            lookup = TemplateLookup(directories=os.path.join(cwd_script, "template"))
        else:
            lookup = TemplateLookup(directories=os.path.join(cwd_script, "template_v2"))
        template = lookup.get_template("conanfile.deploy.py.mako")
        conanfile = template.render(lookup=lookup, pkg=self.info, dependencies=dependencies)
        file_handler = os.fdopen(os.open("conanfile.py", os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                                         stat.S_IWUSR | stat.S_IRUSR), 'w')
        file_handler.write(conanfile)
        file_handler.close()

    def copy_packages_v2(self, graph_file, rootfs_path=None):
        if not rootfs_path:
            rootfs_path = self.temp_path
        with open(graph_file, "r") as file_handler:
            package_info = json.load(file_handler)
        nodes: dict[str, dict] = package_info.get("graph", {}).get("nodes", {})
        self.graph_nodes = {}
        for _, node in nodes.items():
            if node.get("context") != "host":
                continue
            gn = GraphNode(node)
            self.graph_nodes[gn.name] = gn
            if not gn.package_folder:
                continue
            for file in os.listdir(gn.package_folder):
                source = os.path.join(gn.package_folder, file)
                cmd = ["/usr/bin/cp", "-arf", source, rootfs_path]
                Helper.run(cmd)

    def run(self):
        # 生成虚拟deploy组件，仅用于安装
        deploy_conan = os.path.join(self.temp_path, ".deploy")
        os.makedirs(deploy_conan, exist_ok=True)
        os.chdir(deploy_conan)
        self.gen_conanfile()

        # 安装依赖制品到install目录
        install_path = os.path.join(self.temp_path, ".deploy", ".install")
        log.info("安装所有依赖到目录 %s", install_path)
        shutil.rmtree(install_path, ignore_errors=True)
        cmd = [misc.CONAN, "install"]
        graph_file = "package.info.json"
        if misc.conan_v2():
            append_cmd = ("%s -of=%s -d=full_deploy -f json --out-file=%s" %
                          (self.info.cmd_base, install_path, graph_file))
        else:
            append_cmd = ("%s -if=%s -g deploy" % (self.info.cmd_base, install_path))
            append_cmd = append_cmd.replace(self.info.package, self.info.channel)
        cmd += append_cmd.split()
        cmd.append("--build=missing")
        log.success("运行部署命令: %s", " ".join(cmd))
        Helper.run(cmd)
        # 复制制品到rootfs目录
        rootfs_path = self.temp_path
        log.info("复制所有依赖到目录 %s", rootfs_path)
        os.makedirs(rootfs_path, exist_ok=True)
        if misc.conan_v2():
            self.copy_packages_v2(graph_file, rootfs_path)
        else:
            self.copy_packages_v1(install_path, rootfs_path)
        shutil.rmtree(install_path, ignore_errors=True)
