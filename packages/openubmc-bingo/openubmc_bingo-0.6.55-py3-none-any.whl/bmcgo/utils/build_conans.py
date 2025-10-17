#!/usr/bin/env python
# coding=utf-8
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import os
import stat
import subprocess
import shlex
import time
import json
import math
import tempfile
from queue import Queue
from threading import Thread
from bmcgo.logger import Logger
from bmcgo import errors
from bmcgo.utils.tools import Tools

tools = Tools("build_parallel")
log = tools.log


class GraphNode():
    def __init__(self, node):
        self.node = node
        self.host_packages: dict[str, GraphNode] = {}
        self.build_packages: dict[str, GraphNode] = {}
        self.ref = node.get("ref")
        self.name = self.ref.split("/")[0]
        self.context = node.get("context")
        self.pkg = self.ref.split("#")[0] + "-" + self.context
        self.is_host = self.context == "host"
        self.building = False
        self.builded = False

    @property
    def package_options(self):
        return self.node.get("options", {})

    @property
    def package_setting(self):
        return self.node.get("settings", {})

    @property
    def default_options(self):
        return self.node.get("default_options", {})

    def append_host_package(self, dep):
        self.host_packages[dep.pkg] = dep

    def append_build_package(self, dep):
        self.build_packages[dep.pkg] = dep


class BuildConans(object):
    def __init__(self, graphinfo, lockfile, conan_args, force_build, log_dir):
        self.tools = Tools()
        self.queue = Queue()
        self.graphinfo = os.path.realpath(graphinfo)
        if not os.path.isfile(graphinfo):
            raise errors.BmcGoException(f"graph file {graphinfo} not exist")
        self.lockfile = os.path.realpath(lockfile)
        self.cmd = ""
        args = conan_args.split()
        skip = False
        for arg in args:
            if skip:
                skip = False
                continue
            if arg in ["--user", "--channel", "--version", "--name"]:
                skip = True
                continue
            self.cmd += f"{arg} "
        self.force_build = force_build
        self.log_dir = log_dir
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

    def build_task(self, node: GraphNode, options):
        for name, value in node.package_setting.items():
            options += f" -s {name}={value}"

        cmd = f"conan install --requires={node.ref} {self.cmd} {options}"
        cmd += f" --build=missing -f json --lockfile={self.lockfile}"
        if self.force_build:
            cmd += f" --build=\"{node.name}/*\""
        logfile = f"{self.log_dir}/conan_build_{node.name}.log"
        logfd = os.fdopen(os.open(logfile, os.O_RDWR | os.O_CREAT, stat.S_IWUSR | stat.S_IRUSR), "a+")
        # 最多重试3次
        max_cnt = 3
        for i in range(0, max_cnt):
            log.debug(f">>>> {cmd}")
            log.info(f">>>> build {node.ref} start, logfile: {logfile}")
            real_cmd = shlex.split(cmd)
            pipe = subprocess.Popen(real_cmd, stdout=logfd, stderr=logfd)
            start_time = time.time()
            while True:
                if pipe.poll() is not None:
                    break
                # 1800秒超时
                if time.time() - start_time > 1800:
                    pipe.kill()
                    log.info(f"================== {node.name} 构建超时 ==================")
                    self.queue.put(node)
                    return
                time.sleep(1)
            if pipe.returncode != 0:
                log.info(f"<<<< build {node.ref} not ok")
                # 首次增量构建失败时切换到源码构建模式
                if i == 0 and not self.force_build:
                    cmd += f" --build=\"{node.name}/*\""
                    continue
            else:
                break
        log.success(f"<<<< build {node.ref} finished")
        self.queue.put(node)

    def build(self):
        cwd = os.getcwd()
        tmp = tempfile.TemporaryDirectory()
        os.chdir(tmp.name)
        self._build()
        os.chdir(cwd)

    def _build(self):
        with open(self.graphinfo, "r") as fp:
            grapth = json.load(fp)
        nodes = grapth.get("graph", {}).get("nodes", {})
        dependencies: dict[str, GraphNode] = {}

        build_tasks = {}
        for refid, node in nodes.items():
            if refid == "0":
                continue
            cp = GraphNode(node)
            dependencies[cp.pkg] = cp
            build_tasks[cp.name] = False
        for refid, node in nodes.items():
            if refid == "0":
                continue
            ref = node.get("ref")
            context = node.get("context")
            cp = dependencies[ref.split("#")[0] + "-" + context]
            host_packages = node.get("dependencies", {})
            for _, dep in host_packages.items():
                dep_ref = dep.get("ref")
                build = dep.get("build")
                if build:
                    build_dep = dependencies[dep_ref + "-build"]
                    cp.append_build_package(build_dep)
                    # 存在同名host组件时，将build组件作为host的依赖，避免并发构建
                    host_dep = dependencies.get(dep_ref + "-host")
                    if host_dep:
                        host_dep.append_build_package(build_dep)
                else:
                    host_dep = dependencies[dep_ref + "-host"]
                    cp.append_host_package(host_dep)
        options = ""
        for _, cp in dependencies.items():
            # 跳过build包
            if not cp.is_host:
                continue
            for name, value in cp.package_options.items():
                if value is None:
                    continue
                def_val = cp.default_options.get(name)
                if name == "enable_luajit":
                    conan_name = "*"
                else:
                    conan_name = cp.pkg.split("@")[0]
                option = ""
                if isinstance(def_val, bool):
                    if def_val and "False" == value:
                        option = f" -o {conan_name}:{name}={value}"
                    elif not def_val and "True" == value:
                        option = f" -o {conan_name}:{name}={value}"
                elif def_val != value:
                    option = f" -o {conan_name}:{name}={value}"
                if option not in options:
                    options += option
        tasks_cnt = 0
        max_proc = max(int(math.sqrt(os.cpu_count())), 4)
        while True:
            for _, dep in dependencies.items():
                if tasks_cnt >= max_proc:
                    break
                # 如果是构建工具，不参与构建
                if not dep.is_host:
                    continue
                # 如果还有依赖未构建完成，不参与构建
                if len(dep.host_packages) != 0:
                    continue
                # 相同名称的组件正在构建时不启动新的构建
                if build_tasks.get(dep.name):
                    continue
                if dep.builded:
                    continue
                # 当依赖的构建工具存在正在构建的组件时不能构建
                skip_build = False
                for _, build_dep in dep.build_packages.items():
                    # 正在构建且未构建出制品时
                    if build_dep.building and not build_dep.builded:
                        skip_build = True
                        break
                if skip_build:
                    continue
                # 启动构建前将其依赖的构建工具置为正在构建
                for _, build_dep in dep.build_packages.items():
                    build_dep.building = True
                tasks_cnt += 1
                thread = Thread(target=self.build_task, args=(dep, options,))
                thread.start()
                build_tasks[dep.name] = True
            if not tasks_cnt:
                return
            dep = self.queue.get()
            dep.builded = True
            build_tasks[dep.name] = False
            tasks_cnt -= 1
            for _, sub_cp in dependencies.items():
                if sub_cp.host_packages.get(dep.pkg):
                    sub_cp.host_packages.pop(dep.pkg)
            # 构建完成后，组件的构建依赖工具一定构建完成且制品存在
            for _, build_dep in dep.build_packages.items():
                build_dep.builded = True
