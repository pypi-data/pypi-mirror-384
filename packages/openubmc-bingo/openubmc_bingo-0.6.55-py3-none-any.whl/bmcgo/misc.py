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
import re
import os
import sys
from enum import Enum
from conan import conan_version


CACHE_DIR = f"{os.path.expanduser('~')}/.bmcgo_log"
CONAN_REPO = "openubmc_dev"
CONAN_USER = 'openUBMC'

STORE_TRUE = "store_true"
STORE_FALSE = "store_false"
SCHEMA_FILE_PATH = "/usr/share/bingo/schema"
GLOBAL_CFG_FILE = "/etc/bmcgo.conf"
CONAN = "conan"
# bmcgo.conf中用于定义路径的选项名
GLOBAL_BMCGO_CONF_FOLDER = "folder"
REF_TAGS = "refs/tags/"
CONAN_DEPDENCIES_KEY = "dependencies"
GIT_REVISION = "revision"
GRP_MISC = "Misc commands"
GRP_CONAN_IDX = "Conan Index commmands"
GRP_IBMC_SDK = "SDK commmands"
GRP_COMP = "Component commands"
GRP_INTE = "Integrated commands"
GRP_STUDIO = "Studio commands"

DESCRIPTION = "description"
PATTERN = "pattern"
ENV_CONST = "env"
JSON_CHECKER = "json_checker"
HTTP_PROXY_CONST = "http_proxy"
HTTPS_PROXY_CONST = "https_proxy"
FTP_PROXY_CONST = "ftp_proxy"
NO_PROXY_CONST = "no_proxy"
TIMESTAMP_SIGN_SERVER = "timestamp_sign_server"
JARSIGNER_HTTP_PROXY = "jarsigner_http_proxy"
CUSTOM_PLUGINS = "plugins_path"
DEFAULT_PLUGINS_PATH = os.path.join(os.environ["HOME"], ".bmcgo", "plugins")

DEPLOY_HOST_CONST = "deploy-host"
PORT_CONST = "port"
USERNAME_CONST = "username"
PASSWORD_CONST = "password"

DEPENDENCY_XML = "dependency.xml"
CODE_XML = "code.xml"
REPO_BASE = "repoBase"
ENV_LOGNAME = "LOGNAME"
NAME = "name"
COLOR_RED = "RED"
CLI = "cli"

BUILD = "build"
ANALYSIS = "analysis"
DEPLOY = "deploy"
TEST = "test"
GEN = "gen"
HELP = "help"

ROOTCA_DER = "rootca.der"
CMS_CRL = "cms.crl"

# hpm签名CA根证书配置
HPM_SIGN_ROOTCA_DER = "rootca_der"

# hpm服务器签名配置
HPM_SERVER_SIGN = "hpm_server_sign"
HPM_SERVER_SIGN_CERT_ID = "cert_id"
HPM_SERVER_SIGN_URL = "url"
HPM_SERVER_SIGN_SSL_VERYFY = "ssl_verify"

# hpm自签名配置
HPM_SELF_SIGN = "hpm_self_sign"
HPM_SELF_SIGN_ROOTCA_CRL = "rootca_crl"
HPM_SELF_SIGN_SIGNER_PEM = "signer_pem"
HPM_SELF_SIGN_TS_PEM = "ts_signer_pem"
HPM_SELF_SIGN_TS_CNF = "ts_signer_cnf"

# eeprom服务器签名配置
E2P_SERVER_SIGN = "eeprom_server_sign"
E2P_SERVER_SIGN_URL = "url"

# eeprom自签名配置
E2P_SELF_SIGN = "eeprom_self_sign"
E2P_SELF_SIGN_PEM = "priv_pem"

# hpm加密配置
HPM_ENCRYPT = "hpm_encrypt"
HPM_ENCRYPT_ENABLE = "enable"
HPM_ENCRYPT_TOOL = "crypto_tool"

# CONAN包每一段的正则表达式
CONAN_NAME_RESTR = "[a-z0-9_][a-z0-9_+.-]{1,100}"

# 工具名称
BINGO_NAME = "bingo"


class StageEnum(Enum):
    STAGE_DEV = "dev"
    STAGE_PRE = "pre"
    STAGE_RC = "rc"
    STAGE_STABLE = "stable"


class BuildTypeEnum(Enum):
    DEBUG = "debug"
    RELEASE = "release"


def conan_v1():
    return conan_version.major == 1


def conan_v2():
    return conan_version.major == 2


def build_type():
    bt = ["debug", "release"]
    if conan_v1():
        bt.append("dt")
    return bt


def build_type_str():
    bt = "debug, release"
    if conan_v1():
        bt += ", dt"
    return bt


class CommandInfo():
    def __init__(self, group, name, description, hidden, help_info=None, module=None):
        # 命令组
        self.group = group
        # 命令对外呈现的名称
        self.name = name
        # 命令描述，字符串数组
        self.description = description
        # 命令帮助，可以为空
        self.help_info = help_info
        # 是否在help中隐藏
        self.hidden = hidden
        # 模块，由cli.py加载
        self.module = module


def get_decleared_schema_file(file) -> str:
    with open(file, "r") as fp:
        lines = fp.readlines()
    for line in lines:
        match = re.match("#[ ]*yaml-language-server[ ]*:[ ]*\\$schema[ ]*=[ ]*(.*)$", line)
        if match is None:
            continue
        schema_file = match.group(1).strip()
        if os.path.isfile(schema_file):
            return str(schema_file)
        if "/bmcgo/" in schema_file and tool_name() == "bingo":
            bing_schema = schema_file.replace("/bmcgo/", "/bingo/")
            if os.path.isfile(bing_schema):
                return str(bing_schema)
        schema_file = os.path.join(os.path.dirname(file), schema_file)
        schema_file = os.path.realpath(schema_file)
        if os.path.isfile(schema_file):
            return str(schema_file)
    return ""


def tool_name() -> str:
    return os.path.basename(sys.argv[0])


def community_name() -> str:
    """
    返回社区名称，默认为openubmc，可以通过环境变量修改
    """
    return os.environ.get("OPENUBMC_COMMUNITY_NAME", "openubmc")


def conan_user() -> str:
    """
    返回正式conan包的user字段
    """
    if conan_v1():
        return os.environ.get("OPENUBMC_DEFAULT_CONAN_USER", "openUBMC.release")
    else:
        return os.environ.get("OPENUBMC_DEFAULT_CONAN_USER", "openubmc")


def conan_user_dev() -> str:
    """
    返回调试conan包的user字段
    """
    if conan_v1():
        return os.environ.get("OPENUBMC_DEFAULT_CONAN_USER", "openUBMC.release")
    else:
        return os.environ.get("OPENUBMC_DEFAULT_CONAN_USER_DEV", "openubmc.dev")


def conan_remote() -> str:
    """
    返回默认远程仓名
    """
    return os.environ.get("OPENUBMC_DEFAULT_CONAN_REMOTE", "openubmc_dev")


def boardname_default() -> str:
    """
    返回默认单板名
    """
    return os.environ.get("OPENUBMC_DEFAULT_BOARD_NAME", "openUBMC")


def logo() -> str:
    """
    返回LOGO
    """
    return os.environ.get("OPENUBMC_DEFAULT_LOGO", "openUBMC")


def boardname_default() -> str:
    """
    返回默认单板名
    """
    return os.environ.get("OPENUBMC_DEFAULT_BOARD_NAME", "openUBMC")


def schema_path() -> str:
    return os.environ.get("OPENUBMC_SCHEMA_PATH", "/usr/share/bingo/schema")


def vendor() -> str:
    """
    默认厂商名，用于制作HPM包时使用，生效时的优先级：
    1. 优先manifest/base/vendor配置
    2. 再次OPENUBMC_DEFAULT_VENDOR环境变量
    3. 最后使用社区名
    """
    return os.environ.get("OPENUBMC_DEFAULT_VENDOR", "openUBMC")


def need_encrypt_hpm() -> str:
    """
    是否需要加密固件
    """
    return os.environ.get("OPENUBMC_ENCRYPTO_HPM_PACKAGE", False)


def conan_package_match(name: str, valid_range=True) -> bool:
    restr = CONAN_NAME_RESTR
    if re.match(f"^{restr}/{restr}@{restr}/{restr}$", name):
        return True
    if valid_range:
        match = re.search('\\[.*\\]', name)
        if match:
            return True
    return False
