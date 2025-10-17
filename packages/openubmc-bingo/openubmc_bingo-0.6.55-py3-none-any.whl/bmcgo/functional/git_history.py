#!/usr/bin/env python3
# coding: utf-8
# Copyright (c) 2025 Huawei Technologies Co., Ltd.
# openUBMC is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#         http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import argparse
import datetime
import json
import os
import re
import sys
from datetime import timezone, timedelta
from typing import List, Tuple, Dict, Optional, Any
from git import Repo, Commit, Diff
from git.exc import InvalidGitRepositoryError, GitCommandError
from bmcgo import misc
from bmcgo.utils.tools import Tools
from bmcgo.bmcgo_config import BmcgoConfig
from bmcgo import errors


tools = Tools()
log = tools.log
beijing_timezone = timezone(timedelta(hours=8))


command_info: misc.CommandInfo = misc.CommandInfo(
    group=misc.GRP_COMP,
    name="git_history",
    description=["获取指定开始时间与结束时间之间提交信息，并生成release note"],
    hidden=False
)


def if_available(bconfig: BmcgoConfig):
    if bconfig.component is None:
        return False
    return True


class BmcgoCommand:
    def __init__(self, bconfig: BmcgoConfig, *args):
        self.bconfig = bconfig
        parser = argparse.ArgumentParser(prog="bmcgo git_history", description="生成Git仓库的Release Note", add_help=True,
            formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("--start_date", "-s", help="起始日期YYYY-MM-DD", required=True)
        parser.add_argument("--end_date", "-e", help="结束日期YYYY-MM-DD，默认为当前日期", default=None)
        args, kwargs = parser.parse_known_args(*args)
        self.start_date = args.start_date
        self.end_date = args.end_date
        self.output_file = f"./{self.start_date}_{self.end_date}_releaseNote.log"
        self.service_json_path = "mds/service.json"
        self.repo = Repo(".")

    @staticmethod
    def validate_date(date_str: str) -> datetime.datetime:
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError as e:
            raise errors.BmcGoException(f"日期格式不正确: {date_str}，请使用YYYY-MM-DD格式，错误信息{e}")
        current_date = datetime.datetime.now(beijing_timezone)
        if date.date() > current_date.date():
            raise errors.BmcGoException(f"日期 {date_str} 超过当前日期")
        return date

    @staticmethod
    def extract_version_from_diff(self, diff: Diff) -> Optional[str]:
        try:
            diff_text = diff.diff.decode('utf-8') if diff.diff else str(diff)
            version_pattern = r'[-+]\s*"version"\s*:\s*"([^"]+)"'
            matches = re.findall(version_pattern, diff_text)
            if matches:
                return matches[-1]
        except (UnicodeDecodeError, AttributeError):
            pass
        return None

    @staticmethod
    def is_merge_into_main(s):
        pattern = r'^merge .+ into main$'
        # 使用re.match进行匹配，忽略大小写
        match = re.match(pattern, s, re.IGNORECASE)
        return match is not None

    def get_current_version(self) -> str:
        try:
            with open(self.service_json_path, 'r') as f:
                service_data = json.load(f)
                return service_data.get('version', 'unknown')
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise errors.BmcGoException(f"无法读取或解析 {self.service_json_path}: {e}")

    def get_commits_in_range(self, start_date: str, end_date: str) -> List[Commit]:
        start_dt = self.validate_date(start_date)
        if end_date is None:
            end_dt = datetime.datetime.now(beijing_timezone)
        else:
            try:
                end_dt = self.validate_date(end_date)
            except errors.BmcGoException as e:
                if "超过当前日期" in str(e):
                    log.warning(f"警告: {e}，将使用当前日期作为结束日期")
                    end_dt = datetime.datetime.now(beijing_timezone).replace(tzinfo=None)
                else:
                    raise
        if end_dt < start_dt:
            raise errors.BmcGoException("结束日期不能早于起始日期")
        since_str = start_dt.strftime("%Y-%m-%d")
        until_str = end_dt.strftime("%Y-%m-%d")
        try:
            commits = list(self.repo.iter_commits(
                since=since_str,
                until=until_str
            ))
        except GitCommandError as e:
            raise errors.BmcGoException(f"获取commit记录时出错: {e}")
        return commits

    def get_version_from_commit(self, commit_hash: str) -> Optional[str]:
        try:
            commit = self.repo.commit(commit_hash)
            try:
                file_content = (commit.tree / self.service_json_path).data_stream.read().decode('utf-8')
                data = json.loads(file_content)
                version = data.get('version')
                return version
            except (KeyError, AttributeError):
                log.error(f"在commit {commit_hash} 中找不到文件: {self.service_json_path}")
                return None
            except json.JSONDecodeError:
                log.error(f"在commit {commit_hash} 中的 {self.service_json_path} 文件不是有效的JSON格式")
                return None
        except Exception as e:
            log.error(f"获取commit {commit_hash} 的版本信息时出错: {e}")
            return None

    def get_version_info_for_commits(self, commits: List[Commit]) -> Dict[str, Any]:
        version_info = {
            'current_version': self.get_current_version(),
            'commit_versions': {}
        }
        # 按时间顺序处理commit（从旧到新）
        for commit in reversed(commits):
            try:
                if not self.is_merge_into_main(str(commit.summary)):
                    continue
                modified_version = self.get_version_from_commit(commit.hexsha)
                message = commit.message.strip()
                lines = message.splitlines()
                if len(lines) >= 3:
                    message = lines[2]
                version_info['commit_versions'][commit.hexsha] = {
                        'date': commit.committed_datetime.strftime("%Y-%m-%d"),
                        'message': message,
                        'version': modified_version if modified_version else version_info['current_version']
                    }
                if modified_version:
                    version_info['current_version'] = modified_version
            except Exception as e:
                log.error(f"处理commit {commit.hexsha} 时出错: {e}")
                message = commit.message.strip()
                lines = message.splitlines()
                if len(lines) >= 3:
                    message = lines[2]
                version_info['commit_versions'][commit.hexsha] = {
                    'date': commit.committed_datetime.strftime("%Y-%m-%d"),
                    'message': message,
                    'version': version_info['current_version']
                }
        return version_info

    def generate_release_note(self,
                             start_date: str,
                             end_date: str,
                             output_file: str) -> str:
        release_note = f"从{start_date}至{end_date}特性提交如下：\n"
        commits = self.get_commits_in_range(start_date, end_date)
        if not commits:
            try:
                release_note += f"无更新\n"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(release_note)
                log.info(f"Release Note已保存到: {output_file}")
            except IOError as e:
                log.error(f"保存文件时出错: {e}")
        version_info = self.get_version_info_for_commits(commits)

        for commit in commits:
            commit_info = version_info['commit_versions'].get(commit.hexsha, {})
            if len(commit_info) == 0:
                continue
            release_note += f"-commit ID： {commit.hexsha}\n"
            release_note += f"-修改描述： {commit_info.get('message')}\n"
            release_note += f"-版本号： {commit_info.get('version')}\n"
            release_note += f"-发布日期：{commit_info.get('date')}\n\n"
        if output_file:
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(release_note)
                log.info(release_note)
                log.info(f"Release Note已保存到: {output_file}")
            except IOError as e:
                log.error(f"保存文件时出错: {e}")
        return release_note

    def run(self):
        try:
            _ = self.generate_release_note(
                start_date=self.start_date,
                end_date=self.end_date,
                output_file=self.output_file
            )
        except (ValueError, RuntimeError) as e:
            log.error(f"错误: {e}")
