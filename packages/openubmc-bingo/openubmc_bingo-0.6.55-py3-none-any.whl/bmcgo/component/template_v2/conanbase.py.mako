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
import os
import concurrent.futures
import urllib3
% if not pkg.is_maintain:
import time
% endif
% if pkg.is_maintain:
import stat
import shutil
% endif
from conan import ConanFile
from conan.tools.scm import Git
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import copy, update_conandata, chdir, rm, mkdir
% if language == "c":
from bmcgo.component.gen import GenComp
% endif
% if pkg.is_maintain:
from conan.tools.files import patch as apply_patch
from conan.errors import ConanException
% endif

urllib3.disable_warnings()

# 构建时由工具自动生成到业务仓，做为conanfile.py的基类参与组件构建
# 如需要调试，请修改模板文件（目录中存在python版本号、bingo集成开发环境应用名称，请适配）：
#   ~/.local/lib/python3.8/site-packages/bingo/component/template/conanbase.py.mako


class ConanBase(ConanFile):
    name = "${pkg.name}"
% if not pkg.is_maintain:
    version = "${pkg.version}"
% endif
    settings = "os", "compiler", "build_type", "arch"
    license = "Mulan PSL v2"
    generators = "CMakeDeps", "VirtualBuildEnv", "PkgConfigDeps"
    language = "${language}"
    _cmake = None
    _codegen_version = ${codegen_version}
    options = {
        "asan": [True, False],
        "gcov": [True, False],
        "test": [True, False],
        "manufacture": [True, False],
    % if language == "lua":
        "enable_luajit": [True, False],
    % endif
    % for op, ctx in pkg.design_options.items():
        "${op}": [${", ".join(("\"" + i + "\"") if isinstance(i, str) else str(i) for i in ctx["option"])}],
    % endfor
    }
    default_options = {
        "asan": False,
        "gcov": False,
        "test": False,
        "manufacture": False,
    % if language == "lua":
        "enable_luajit": False,
    % endif
    % for op, ctx in pkg.design_options.items():
        "${op}": ${("\"" + ctx["default"] + "\"") if isinstance(ctx["default"], str) else str(ctx["default"])},
    % endfor
    }

    def layout(self):
        cmake_layout(self, build_folder=".build")

    def requirements(self):
    % if len(pkg.build_dependencies) > 0:
        # 编译依赖
        % for build_dep in pkg.build_dependencies:
        self.requires("${build_dep}")
        % endfor
    % endif
    %if language == "lua":
        skynet = self.conf.get("user.tools:skynet")
        if skynet:
            self.tool_requires(skynet, options={"tools_only": True})
        luajit = self.conf.get("user.tools:luajit")
        if luajit:
            self.tool_requires(luajit, options={"tools_only": True})
    % endif
        pass

    def export(self):
        copy(self, "conanbase.py", self.recipe_folder, self.export_folder)
        % if not pkg.is_maintain:
        git = Git(self, self.recipe_folder)
        if git.is_dirty():
            update_conandata(self, {"sources": {self.version: {"branch": None, "url": None, "pwd": os.getcwd(), "timestamp": int(time.time())}}})
            return
        url = None
        url_remote = None
        commit = git.get_commit()
        branches = git.run("branch -r --contains {}".format(commit))
        remotes = git.run("remote")
        for remote in remotes.splitlines():
            if "{}/".format(remote) in branches:
                url = git.get_remote_url(remote)
                url_remote = remote
                break
        if not url:
            update_conandata(self, {"sources": {self.version: {"branch": None, "url": None, "pwd": os.getcwd(), "timestamp": int(time.time())}}})
            return
        try:
            self.run(f"git fetch --prune --prune-tags {url_remote}")
            tag = git.run(f"tag --points-at HEAD | grep -m 1 {self.version}")
        except:
            tag = ""
        update_conandata(self, {"sources": {self.version: {"branch": f"refs/tags/{tag}" if tag else commit, "url": url}}})
        % endif

    % if pkg.is_maintain:
    def export_sources(self):
        patches = self.conan_data.get("patches", {}).get(self.version, [])
        for patch in patches:
            patch_file = patch.get("patch_file")
            if patch_file is None:
                continue
            # 与export_conandata_patches方法不同点：所有patches将从recipes_folder/../pacthes读取
            src = os.path.join(self.recipe_folder, "..", patch_file)
            dst = os.path.join(self.export_sources_folder, patch_file)
            mkdir(self, os.path.dirname(dst))
            shutil.copy2(src, dst)

    % endif
    def source(self):
        git = Git(self)
        sources = self.conan_data["sources"][self.version]
    % if not pkg.is_maintain:
        if sources["url"] and sources["branch"]:
            git.fetch_commit(url=sources["url"], commit=sources["branch"].split("/")[-1])
        else:
            copy(self, "*", src=sources["pwd"], dst=".")
    % else:
        git.fetch_commit(url=sources["url"], commit=sources["branch"].split("/")[-1])
    % endif
        % if language == "c":
        self._codegen()
        % endif
    % if pkg.is_maintain:
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            patch_file = patch.get("patch_file")
            if not patch_file:
                continue
            real_path = os.path.join(self.folders.base_source, patch_file)
            print(f"Start patch file {patch_file}")
            changed_files = self._get_patch_changed_files(real_path)
            try:
                apply_patch(self, patch_file=real_path)
                self._revise_renamed_files(changed_files)
                cmd = f"git commit -m \"{patch_file}\""
                self.run(cmd)
            except ConanException:
                # 尝试还原文件修改
                for a_file, b_file in changed_files.items():
                    cmd = f"git checkout -- {a_file}"
                    self.run(cmd, ignore_errors=True)
                    cmd = f"git checkout -- {b_file}"
                    self.run(cmd, ignore_errors=True)
                cmd = "git am " + real_path
                self.run(cmd)
    % endif

    def generate(self):
        tc = self._pre_generate()
        tc.generate()

% if pkg.is_maintain:
    @staticmethod
    def _get_patch_changed_files(patch_file):
        files = {}
        for line in open(patch_file):
            if not line.startswith("diff --git"):
                continue
            line = line.strip()
            chunk = line.split()
            a_file = chunk[-2][2:]
            b_file = chunk[-1][2:]
            files[a_file] = b_file
        return files

%endif
    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        cmake = self._configure_cmake()
        cmake.install()
        files_to_copy = [
            ("permissions.ini", self.source_folder, self.package_folder),
            ("model.json", os.path.join(self.source_folder, "mds"),
                os.path.join(self.package_folder, "include/mds")),
            ("service.json", os.path.join(self.source_folder, "mds"),
                os.path.join(self.package_folder, "include/mds")),
            ("*", os.path.join(self.source_folder, "customization"),
                os.path.join(self.package_folder, "include")),
            ("*", os.path.join(self.source_folder, "mds"),
                os.path.join(self.package_folder, "usr/share/doc/openubmc/${pkg.name}/mds")),
            ("*", os.path.join(self.source_folder, "docs"),
                os.path.join(self.package_folder, "usr/share/doc/openubmc/${pkg.name}/docs")),
            ("*", os.path.join(self.source_folder, "build"),
                os.path.join(self.package_folder, "include")),
            ("permissions.ini", os.path.join(self.source_folder, "dist"), self.package_folder),
            ("*.md", self.source_folder, os.path.join(self.package_folder,
                "usr/share/doc/openubmc/${pkg.name}/docs")),
            ("*.MD", self.source_folder, os.path.join(self.package_folder,
                "usr/share/doc/openubmc/${pkg.name}/docs"))
        ]
        for pattern, src, dst in files_to_copy:
            copy(self, pattern, src=src, dst=dst, keep_path=True)

        # 只有当需要统计覆盖率且TRANSTOBIN环境变量未设置时才不处理lua文件
        if self.options.gcov and os.getenv("TRANSTOBIN") is None:
            return

        os.chdir(self.package_folder)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            for root, _, files in os.walk("."):
                self.compile_files(root, files, executor)
        rm(self, "luac.out", self.package_folder)

    def compile_files(self, root, files, executor):
        for file in files:
            if file.endswith(".lua") and not os.path.islink(os.path.join(root, file)):
                file_path = os.path.join(root, file)
                if self.options.enable_luajit:
                    executor.submit(self.compile_file, file_path, True)
                else:
                    executor.submit(self.compile_file, file_path, False)

    def compile_file(self, file_path, enable_luajit):
        if enable_luajit:
            self.run(f"luajit -b -g {file_path} {file_path}")
        else:
            self.run(f"luac -o {file_path} {file_path}")
            self.run(f"luac -s {file_path}")

    def package_info(self):
        app_dir = os.path.join(self.package_folder, "opt/bmc/apps/${pkg.name}")
        if os.path.isdir(app_dir):
            self.runenv_info.append("PATH", ':' + app_dir)
            self.buildenv_info.append("PATH", ':' + app_dir)
    % if "application" in pkg.package_type and pkg.package_info is not None:
        % if len(pkg.package_info.get("bindirs", [])) > 0:
        self.cpp_info.bindirs = [${", ".join("\"" + i + "\"" for i in pkg.package_info["bindirs"])}]
            % for dir in pkg.package_info["bindirs"]:
        self.env_info.PATH.append(os.path.join(self.package_folder, "${dir}"))
            % endfor
        % endif
    % endif
        libs = []
        dirs = []
        for root, _, files in os.walk("."):
            for file in files:
                dirname, libname = self.find_libraries(root, file)
                if dirname and dirname not in dirs:
                    dirs.append(dirname)
                if libname:
                    libs.append(libname)

        if dirs:
            dirs.sort()
            libs.sort()
            self.cpp_info.components["${pkg.name}"].set_property("cmake_target_name", "${pkg.name}::${pkg.name}")
            self.cpp_info.components["${pkg.name}"].set_property("cmake_target_aliass", ["${pkg.name}::${pkg.name}"])
            self.cpp_info.components["${pkg.name}"].set_property("pkg_config_name", "${pkg.name}")
            self.cpp_info.components["${pkg.name}"].libs = libs
            self.cpp_info.components["${pkg.name}"].libdirs = dirs
            for dir in dirs:
                self.runenv_info.append("LD_LIBRARY_PATH", os.path.join(self.package_folder, dir))
                self.buildenv_info.append("LD_LIBRARY_PATH", os.path.join(self.package_folder, dir))

    def find_libraries(self, root, file):
        if file.endswith(".so") and file.startswith("lib"):
            if root.startswith("./"):
                dirname = root[2:]
            else:
                dirname = root
            libname = file[3:-3]
            return (dirname, libname)
        if file.endswith(".a") and file.startswith("lib"):
            if root.startswith("./"):
                dirname = root[2:]
            else:
                dirname = root
            return (dirname, file)
        return (None, None)

% if pkg.is_maintain:
    def _revise_renamed_files(self, changed_files):
        for a_file, b_file in changed_files.items():
            if a_file != b_file:
                if a_file != "/dev/null" and b_file != "/dev/null":
                    os.rename(a_file, b_file)
                    cmd = f"git rm -f {a_file}"
                    self.run(cmd)
                elif a_file != "/dev/null":
                    cmd = f"git rm -f {a_file}"
                    self.run(cmd)
                    continue
            cmd = f"git add {b_file}"
            self.run(cmd)

%endif
    def _configure_cmake(self):
        if self._cmake is not None:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.configure()
        return self._cmake

% if language == "c":
    def _codegen(self):
        args = ["-s", "mds/service.json"]
        gen = GenComp(args)
        gen.run(self._codegen_version)

% endif
    def _pre_generate(self):
        tc = CMakeToolchain(self)
        tc.preprocessor_definitions["_FORTIFY_SOURCE"] = "2"

        tc.variables["BUILD_MANUFACTURE"] = self.options.manufacture
        % if len(pkg.design_options) > 0:
            % for op, _ in pkg.design_options.items():
        tc.variables["CONAN_DEFS_${op.upper()}"] = self.options.${op}
            % endfor
        % endif
    % if language == "lua":
        if self.options.enable_luajit:
            tc.variables["CONAN_DEFS_ENABLE_LUAJIT"] = True
    % endif
        if self.options.test:
            tc.variables["ENABLE_TEST"] = True
            tc.preprocessor_definitions["ENABLE_TEST"] = True
        # 向CMAKE传递版本号信息
        version = self.version.split(".")
        if len(version) >= 1:
            tc.variables["PACKAGE_VERSION_MAJOR"] = version[0]
        if len(version) >= 2:
            tc.variables["PACKAGE_VERSION_MINOR"] = version[1]
        if len(version) >= 3:
            tc.variables["PACKAGE_VERSION_REVISION"] = version[2]
        # 设置额外编译选项或者重定义CFLAGS CXXFLAGS,也可以设置其他开关
        # 示例: os.environ['CFLAGS'] = f"{os.getenv('CFLAGS')} -fPIE"

        if self.settings.arch in ["armv8", "x86_64"]:
            tc.variables["CMAKE_INSTALL_LIBDIR"] = "usr/lib64"
        else:
            tc.variables["CMAKE_INSTALL_LIBDIR"] = "usr/lib"

        if self.options.get_safe("asan", False):
            print("Enable asan flags")
            asan_flags = "-fsanitize=address -fsanitize-recover=address,all -fno-omit-frame-pointer -fno-stack-protector -O0"
            tc.extra_cflags.append(asan_flags)
            tc.extra_cxxflags.append(asan_flags)
            tc.extra_sharedlinkflags.append("-fsanitize=address")
            tc.extra_exelinkflags.append("-fsanitize=address")

        # GCOV 标志设置
        if self.options.get_safe("gcov", False):
            print("Enable gcov flags")
            gcov_flags = "-ftest-coverage -fprofile-arcs -fprofile-update=atomic"
            tc.extra_cflags.append(gcov_flags)
            tc.extra_cxxflags.append(gcov_flags)
        # 配合generate添加宏定义
        tc.variables["CMAKE_TOOLCHAIN_FILE"] = "conan_toolchain.cmake"
        # rpath配置
        tc.variables["CMAKE_SKIP_BUILD_RPATH"] = True
        tc.variables["CMAKE_SKIP_RPATH"] = True
        tc.variables["CMAKE_SKIP_INSTALL_RPATH"] = True
        tc.variables["CMAKE_BUILD_WITH_INSTALL_RPATH"] = False
        tc.variables["CMAKE_INSTALL_RPATH_USE_LINK_PATH"] = False
        return tc
