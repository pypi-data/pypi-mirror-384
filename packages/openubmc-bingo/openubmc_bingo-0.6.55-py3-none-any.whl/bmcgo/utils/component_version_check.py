#!/usr/bin/env python
# coding=utf-8
# Copyright (c) 2024 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.

"""
文件名: work_component_version_check.py
功能: 对比manifest.yml生成的组件清单和自动生成的清单是否一致
注意: 这个文件名为work, 但不继承 Task 类 !!!!!!
"""
import os
import json
from pathlib import Path
import yaml
from bmcgo.logger import Logger
from bmcgo import misc
from bmcgo.utils.tools import Tools

log = Logger("component_version_check")
tools = Tools()


class ComponentVersionCheck:
    """类方法中的 manifest.yml 是有两个含义, conan 目录和单板目录, 均已注明
       conan 目录的 manifest.yml 文件是由单板目录下的 manifest.yml 自动生成的
    """

    def __init__(self, manifest_yml: str, ibmc_lock: str, community_name: str, openubmcsdk: str):
        """读取 manifest.yml(conan目录) 文件与 openubmc.lock 文件

        Args:
            manifest_yml (str): manifest.yml文件路径
            ibmc_lock (str): openubmc.lock文件路径
        """
        self.manifest = ""
        self.manifest_yml = manifest_yml
        self.ibmc_lock = ibmc_lock
        self.manifest_dict = {}
        self.ibmc_lock_dict = {}
        self.openubmcsdk_comp = openubmcsdk
        self.openubmcsdk_dict = self.generate_openubmcsdk_dict(self.openubmcsdk_comp)
        self.community_name = community_name

    @staticmethod
    def get_cache_path(component):
        """根据openubmcsdk的包名获取export文件夹路径

        Returns:
            str: 返回 openubmcsdk 的export路径
        """
        if misc.conan_v1():
            conan_home = Path(os.environ.get("CONAN_HOME", Path.home() / ".conan/data"))
            openubmcsdk_file = os.path.join(conan_home, component.replace("@", "/"), "export", "requirements.yml")
        else:
            conan_home = f"conan cache path {component}"
            openubmcsdk_file = os.path.join(
                Tools().run_command(conan_home, capture_output=True).stdout(),
                "requirements.yml"
                )
        return openubmcsdk_file

    def openubmc_folder(self):
        with open(self.manifest_yml, "r") as manifest_fp:
            self.manifest = yaml.safe_load(manifest_fp)
        with open(self.ibmc_lock, "r") as ibmc_lock_fp:
            self.ibmc_lock = json.load(ibmc_lock_fp)

    def generate_openubmcsdk_dict(self, component) -> dict:
        """根据 requirement.yml(conan目录) 配置生成 组件名: 组件配置 的字典

        Returns:
            dict: 返回 组件名: 组件配置 的字典
        """
        # component == ""表示manifest.yml未定义"base/sdk"
        if component == "":
            return {}
        openubmcsdk_file = self.get_cache_path(component)
        if not os.path.isfile(openubmcsdk_file):
            tools.download_conan_recipes(component, [misc.CONAN_REPO])
            openubmcsdk_file = self.get_cache_path(component)
        with open(openubmcsdk_file, "r") as openubmcsdk_fp:
            self.openubmcsdk = yaml.safe_load(openubmcsdk_fp)
        dependency_list = self.openubmcsdk[misc.CONAN_DEPDENCIES_KEY]
        openubmc_dict = {x[misc.CONAN].split('/')[0]: x[misc.CONAN].split('@')[0] for x in dependency_list}
        return openubmc_dict
    
    def get_dict(self):
        self.openubmc_folder()
        self.manifest_dict = self.generate_manifest_dict()
        self.ibmc_lock_dict = self.generate_bmc_lock_dict()

    def generate_manifest_dict(self) -> dict:
        """根据 manifest.yml(conan目录) 配置生成 组件名: 组件配置 的字典

        Returns:
            dict: 返回 组件名: 组件配置 的字典
        """
        dependency_list = self.manifest[misc.CONAN_DEPDENCIES_KEY]
        manifest_dict = {x[misc.CONAN].split('/')[0]: x[misc.CONAN].split('@')[0] for x in dependency_list}
        return manifest_dict

    def generate_bmc_lock_dict(self) -> dict:
        """根据 bmc.lock 配置生成 组件名: 组件配置 的字典

        Returns:
            dict: 返回 组件名: 组件配置 的字典
        """
        if misc.conan_v1():
            component_list = self.ibmc_lock["graph_lock"]["nodes"]
            ibmc_lock_dict = {x["ref"].split('/')[0]: x["ref"].split('@')[0]
                            for x in [component_conf for _, component_conf in component_list.items()]}
            ibmc_lock_dict.pop(misc.community_name())
        else:
            component_list = self.ibmc_lock["requires"]
            ibmc_lock_dict = {x.split('/')[0]: x.split('@')[0] for x in component_list}
        return ibmc_lock_dict

    def run(self):
        """检查所有组件是否都在 manifest.yml(单板目录下) 中配置了
        """
        # 这里使用报错退出, 为防止有多个组件未配置, 报错在方法结束后触发
        self.get_dict()
        report_error = False
        for key, version in self.ibmc_lock_dict.items():
            if key not in self.manifest_dict.keys() and key not in self.openubmcsdk_dict.keys():
                log.error(f"{version} 组件没有在manifest中配置!!!!!!")
                report_error = True
            elif key in self.openubmcsdk_dict.keys() and version != self.openubmcsdk_dict.get(key, ""):
                log.error(f"{version} 组件版本与openubmcsdk中配置{self.openubmcsdk_dict[key]}不匹配!!!!!!")
                report_error = True
            elif key in self.manifest_dict.keys() and version != self.manifest_dict.get(key, ""):
                log.error(f"{version} 组件版本与manifest中配置{self.manifest_dict[key]}不匹配!!!!!!")
                report_error = True

        if report_error is True:
            raise AttributeError
        else:
            log.info("所有组件均已在manifest中配置")
