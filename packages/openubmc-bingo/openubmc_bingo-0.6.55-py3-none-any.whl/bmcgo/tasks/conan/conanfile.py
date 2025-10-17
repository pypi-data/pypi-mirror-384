#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2024 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
from conan import ConanFile
import yaml


class OpenubmcConan(ConanFile):
    name = "openubmc"
    url = "https://www.huawei.com"
    settings = "os", "compiler", "build_type", "arch"
    requires = []
    license = "Mulan PSL v2"
    exports_sources = ["manifest.yml"]
    _manifest = None

    def init(self):
        with open("manifest.yml", "r") as fp:
            self._manifest = yaml.safe_load(fp)

    def set_version(self):
        self.version = self._manifest["base"]["version"].lower()

    def requirements(self):
        for dep in self._manifest.get("dependencies", {}):
            require = dep["conan"] + ""
            self.requires(require)

    def build(self):
        pass

    def package(self):
        pass

    def package_info(self):
        pass

