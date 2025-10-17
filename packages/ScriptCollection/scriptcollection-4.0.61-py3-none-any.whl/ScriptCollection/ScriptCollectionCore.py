import traceback
from datetime import timedelta, datetime
import json
import binascii
import filecmp
import hashlib
import multiprocessing
import time
from io import BytesIO
import itertools
import zipfile
import math
import base64
import os
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
from pathlib import Path
from subprocess import Popen
import re
import shutil
from typing import IO
import fnmatch
import uuid
import tempfile
import io
import requests
import ntplib
import yaml
import qrcode
import pycdlib
import send2trash
from pypdf import PdfReader, PdfWriter
from .GeneralUtilities import GeneralUtilities
from .ProgramRunnerBase import ProgramRunnerBase
from .ProgramRunnerPopen import ProgramRunnerPopen
from .SCLog import SCLog, LogLevel

version = "4.0.61"
__version__ = version


class ScriptCollectionCore:

    # The purpose of this property is to use it when testing your code which uses scriptcollection for external program-calls.
    # Do not change this value for productive environments.
    mock_program_calls: bool = False#TODO remove this variable. When someone want to mock program-calls then the ProgramRunnerMock can be used instead
    # The purpose of this property is to use it when testing your code which uses scriptcollection for external program-calls.
    execute_program_really_if_no_mock_call_is_defined: bool = False
    __mocked_program_calls: list = None
    program_runner: ProgramRunnerBase = None
    call_program_runner_directly: bool = None
    log: SCLog = None

    def __init__(self):
        self.program_runner = ProgramRunnerPopen()
        self.call_program_runner_directly = None
        self.__mocked_program_calls = list[ScriptCollectionCore.__MockProgramCall]()
        self.log = SCLog(None, LogLevel.Warning, False)

    @staticmethod
    @GeneralUtilities.check_arguments
    def get_scriptcollection_version() -> str:
        return __version__

    @GeneralUtilities.check_arguments
    def python_file_has_errors(self, file: str, working_directory: str, treat_warnings_as_errors: bool = True) -> tuple[bool, list[str]]:
        errors = list()
        filename = os.path.relpath(file, working_directory)
        if treat_warnings_as_errors:
            errorsonly_argument = GeneralUtilities.empty_string
        else:
            errorsonly_argument = " --errors-only"
        (exit_code, stdout, stderr, _) = self.run_program("pylint", filename + errorsonly_argument, working_directory, throw_exception_if_exitcode_is_not_zero=False)
        if (exit_code != 0):
            errors.append(f"Linting-issues of {file}:")
            errors.append(f"Pylint-exitcode: {exit_code}")
            for line in GeneralUtilities.string_to_lines(stdout): 
                errors.append(line)
            for line in GeneralUtilities.string_to_lines(stderr):
                errors.append(line)
            return (True, errors)

        return (False, errors)

    @GeneralUtilities.check_arguments
    def replace_version_in_dockerfile_file(self, dockerfile: str, new_version_value: str) -> None:
        GeneralUtilities.write_text_to_file(dockerfile, re.sub("ARG Version=\"\\d+\\.\\d+\\.\\d+\"", f"ARG Version=\"{new_version_value}\"", GeneralUtilities.read_text_from_file(dockerfile)))

    @GeneralUtilities.check_arguments
    def replace_version_in_python_file(self, file: str, new_version_value: str):
        GeneralUtilities.write_text_to_file(file, re.sub("version = \"\\d+\\.\\d+\\.\\d+\"", f"version = \"{new_version_value}\"", GeneralUtilities.read_text_from_file(file)))

    @GeneralUtilities.check_arguments
    def replace_version_in_ini_file(self, file: str, new_version_value: str):
        GeneralUtilities.write_text_to_file(file, re.sub("version = \\d+\\.\\d+\\.\\d+", f"version = {new_version_value}", GeneralUtilities.read_text_from_file(file)))

    @GeneralUtilities.check_arguments
    def replace_version_in_nuspec_file(self, nuspec_file: str, new_version: str) -> None:
        # TODO use XSLT instead
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(new_version):
            GeneralUtilities.write_text_to_file(nuspec_file, re.sub(f"<version>{versionregex}<\\/version>", f"<version>{new_version}</version>", GeneralUtilities.read_text_from_file(nuspec_file)))
        else:
            raise ValueError(f"Version '{new_version}' does not match version-regex '{versiononlyregex}'")

    @GeneralUtilities.check_arguments
    def replace_version_in_csproj_file(self, csproj_file: str, current_version: str):
        versionregex = "\\d+\\.\\d+\\.\\d+"
        versiononlyregex = f"^{versionregex}$"
        pattern = re.compile(versiononlyregex)
        if pattern.match(current_version):
            for tag in ["Version", "AssemblyVersion", "FileVersion"]:
                GeneralUtilities.write_text_to_file(csproj_file, re.sub(f"<{tag}>{versionregex}(.\\d+)?<\\/{tag}>", f"<{tag}>{current_version}</{tag}>", GeneralUtilities.read_text_from_file(csproj_file)))
        else:
            raise ValueError(f"Version '{current_version}' does not match version-regex '{versiononlyregex}'")

    @GeneralUtilities.check_arguments
    def push_nuget_build_artifact(self, nupkg_file: str, registry_address: str, api_key: str = None):
        nupkg_file_name = os.path.basename(nupkg_file)
        nupkg_file_folder = os.path.dirname(nupkg_file)
        argument = f"nuget push {nupkg_file_name} --force-english-output --source {registry_address}"
        if api_key is not None:
            argument = f"{argument} --api-key {api_key}" 
        self.run_program("dotnet", argument, nupkg_file_folder)

    @GeneralUtilities.check_arguments
    def dotnet_build(self, folder: str, projectname: str, configuration: str):
        self.run_program("dotnet", f"clean -c {configuration}", folder)
        self.run_program("dotnet", f"build {projectname}/{projectname}.csproj -c {configuration}", folder)

    @GeneralUtilities.check_arguments
    def find_file_by_extension(self, folder: str, extension_without_dot: str):
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        result = [file for file in self.list_content(folder, True, False, False) if file.endswith(f".{extension_without_dot}")]
        result_length = len(result)
        if result_length == 0:
            raise FileNotFoundError(f"No file available in folder '{folder}' with extension '{extension_without_dot}'.")
        if result_length == 1:
            return result[0]
        else:
            raise ValueError(f"Multiple values available in folder '{folder}' with extension '{extension_without_dot}'.")

    @GeneralUtilities.check_arguments
    def find_last_file_by_extension(self, folder: str, extension_without_dot: str) -> str:
        files: list[str] = GeneralUtilities.get_direct_files_of_folder(folder)
        possible_results: list[str] = []
        for file in files:
            if file.endswith(f".{extension_without_dot}"):
                possible_results.append(file)
        result_length = len(possible_results)
        if result_length == 0:
            raise FileNotFoundError(f"No file available in folder '{folder}' with extension '{extension_without_dot}'.")
        else:
            return possible_results[-1]

    @GeneralUtilities.check_arguments
    def commit_is_signed_by_key(self, repository_folder: str, revision_identifier: str, key: str) -> bool:
        self.is_git_or_bare_git_repository(repository_folder)
        result = self.run_program("git", f"verify-commit {revision_identifier}", repository_folder, throw_exception_if_exitcode_is_not_zero=False)
        if (result[0] != 0):
            return False
        if (not GeneralUtilities.contains_line(result[1].splitlines(), f"gpg\\:\\ using\\ [A-Za-z0-9]+\\ key\\ [A-Za-z0-9]+{key}")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        if (not GeneralUtilities.contains_line(result[1].splitlines(), "gpg\\:\\ Good\\ signature\\ from")):
            # TODO check whether this works on machines where gpg is installed in another langauge than english
            return False
        return True

    @GeneralUtilities.check_arguments
    def get_parent_commit_ids_of_commit(self, repository_folder: str, commit_id: str) -> str:
        self.is_git_or_bare_git_repository(repository_folder)
        return self.run_program("git", f'log --pretty=%P -n 1 "{commit_id}"', repository_folder, throw_exception_if_exitcode_is_not_zero=True)[1].replace("\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string).split(" ")


    @GeneralUtilities.check_arguments
    def get_commit_ids_between_dates(self, repository_folder: str, since: datetime, until: datetime, ignore_commits_which_are_not_in_history_of_head: bool = True) -> None:
        self.is_git_or_bare_git_repository(repository_folder)
        since_as_string = self.__datetime_to_string_for_git(since)
        until_as_string = self.__datetime_to_string_for_git(until)
        result = filter(lambda line: not GeneralUtilities.string_is_none_or_whitespace(line), self.run_program("git", f'log --since "{since_as_string}" --until "{until_as_string}" --pretty=format:"%H" --no-patch', repository_folder, throw_exception_if_exitcode_is_not_zero=True)[1].split("\n").replace("\r", GeneralUtilities.empty_string))
        if ignore_commits_which_are_not_in_history_of_head:
            result = [commit_id for commit_id in result if self.git_commit_is_ancestor(repository_folder, commit_id)]
        return result

    @GeneralUtilities.check_arguments
    def __datetime_to_string_for_git(self, datetime_object: datetime) -> str:
        return datetime_object.strftime('%Y-%m-%d %H:%M:%S')

    @GeneralUtilities.check_arguments
    def git_commit_is_ancestor(self, repository_folder: str,  ancestor: str, descendant: str = "HEAD") -> bool:
        self.is_git_or_bare_git_repository(repository_folder)
        result = self.run_program_argsasarray("git", ["merge-base", "--is-ancestor", ancestor, descendant], repository_folder, throw_exception_if_exitcode_is_not_zero=False)
        exit_code = result[0]
        if exit_code == 0:
            return True
        elif exit_code == 1:
            return False
        else:
            raise ValueError(f'Can not calculate if {ancestor} is an ancestor of {descendant} in repository {repository_folder}. Outout of "{repository_folder}> git merge-base --is-ancestor {ancestor} {descendant}": Exitcode: {exit_code}; StdOut: {result[1]}; StdErr: {result[2]}.')

    @GeneralUtilities.check_arguments
    def __git_changes_helper(self, repository_folder: str, arguments_as_array: list[str]) -> bool:
        self.assert_is_git_repository(repository_folder)
        lines = GeneralUtilities.string_to_lines(self.run_program_argsasarray("git", arguments_as_array, repository_folder, throw_exception_if_exitcode_is_not_zero=True)[1], False)
        for line in lines:
            if GeneralUtilities.string_has_content(line):
                return True
        return False

    @GeneralUtilities.check_arguments
    def git_repository_has_new_untracked_files(self, repository_folder: str):
        self.assert_is_git_repository(repository_folder)
        return self.__git_changes_helper(repository_folder, ["ls-files", "--exclude-standard", "--others"])

    @GeneralUtilities.check_arguments
    def git_repository_has_unstaged_changes_of_tracked_files(self, repository_folder: str):
        self.assert_is_git_repository(repository_folder)
        return self.__git_changes_helper(repository_folder, ["--no-pager", "diff"])

    @GeneralUtilities.check_arguments
    def git_repository_has_staged_changes(self, repository_folder: str):
        self.assert_is_git_repository(repository_folder)
        return self.__git_changes_helper(repository_folder, ["--no-pager", "diff", "--cached"])

    @GeneralUtilities.check_arguments
    def git_repository_has_uncommitted_changes(self, repository_folder: str) -> bool:
        self.assert_is_git_repository(repository_folder)
        if (self.git_repository_has_unstaged_changes(repository_folder)):
            return True
        if (self.git_repository_has_staged_changes(repository_folder)):
            return True
        return False

    @GeneralUtilities.check_arguments
    def git_repository_has_unstaged_changes(self, repository_folder: str) -> bool:
        self.assert_is_git_repository(repository_folder)
        if (self.git_repository_has_unstaged_changes_of_tracked_files(repository_folder)):
            return True
        if (self.git_repository_has_new_untracked_files(repository_folder)):
            return True
        return False

    @GeneralUtilities.check_arguments
    def git_get_commit_id(self, repository_folder: str, commit: str = "HEAD") -> str:
        self.is_git_or_bare_git_repository(repository_folder)
        result: tuple[int, str, str, int] = self.run_program_argsasarray("git", ["rev-parse", "--verify", commit], repository_folder, throw_exception_if_exitcode_is_not_zero=True)
        return result[1].replace('\n', '')

    @GeneralUtilities.check_arguments
    def git_get_commit_date(self, repository_folder: str, commit: str = "HEAD") -> datetime:
        self.is_git_or_bare_git_repository(repository_folder)
        result: tuple[int, str, str, int] = self.run_program_argsasarray("git", ["show", "-s", "--format=%ci", commit], repository_folder, throw_exception_if_exitcode_is_not_zero=True)
        date_as_string = result[1].replace('\n', '')
        result = datetime.strptime(date_as_string, '%Y-%m-%d %H:%M:%S %z')
        return result

    @GeneralUtilities.check_arguments
    def git_fetch_with_retry(self, folder: str, remotename: str = "--all", amount_of_attempts: int = 5) -> None:
        GeneralUtilities.retry_action(lambda: self.git_fetch(folder, remotename), amount_of_attempts)

    @GeneralUtilities.check_arguments
    def git_fetch(self, folder: str, remotename: str = "--all") -> None:
        self.is_git_or_bare_git_repository(folder)
        self.run_program_argsasarray("git", ["fetch", remotename, "--tags", "--prune"], folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_fetch_in_bare_repository(self, folder: str, remotename, localbranch: str, remotebranch: str) -> None:
        self.is_git_or_bare_git_repository(folder)
        self.run_program_argsasarray("git", ["fetch", remotename, f"{remotebranch}:{localbranch}"], folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_remove_branch(self, folder: str, branchname: str) -> None:
        self.is_git_or_bare_git_repository(folder)
        self.run_program("git", f"branch -D {branchname}", folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_push_with_retry(self, folder: str, remotename: str, localbranchname: str, remotebranchname: str, forcepush: bool = False, pushalltags: bool = True, verbosity: LogLevel = LogLevel.Quiet, amount_of_attempts: int = 5) -> None:
        GeneralUtilities.retry_action(lambda: self.git_push(folder, remotename, localbranchname, remotebranchname, forcepush, pushalltags, verbosity), amount_of_attempts)

    @GeneralUtilities.check_arguments
    def git_push(self, folder: str, remotename: str, localbranchname: str, remotebranchname: str, forcepush: bool = False, pushalltags: bool = True, verbosity: LogLevel = LogLevel.Quiet,resurse_submodules:bool=False) -> None:
        self.is_git_or_bare_git_repository(folder)
        argument = ["push"]
        if resurse_submodules:
            argument = argument + ["--recurse-submodules=on-demand"]
        argument = argument + [remotename, f"{localbranchname}:{remotebranchname}"]
        if (forcepush):
            argument.append("--force")
        if (pushalltags):
            argument.append("--tags")
        result: tuple[int, str, str, int] = self.run_program_argsasarray("git", argument, folder, throw_exception_if_exitcode_is_not_zero=True, print_errors_as_information=True)
        return result[1].replace('\r', '').replace('\n', '')

    @GeneralUtilities.check_arguments
    def git_pull_with_retry(self, folder: str, remote: str, localbranchname: str, remotebranchname: str, force: bool = False, amount_of_attempts: int = 5) -> None:
        GeneralUtilities.retry_action(lambda: self.git_pull(folder, remote, localbranchname, remotebranchname), amount_of_attempts)

    @GeneralUtilities.check_arguments
    def git_pull(self, folder: str, remote: str, localbranchname: str, remotebranchname: str, force: bool = False) -> None:
        self.is_git_or_bare_git_repository(folder)
        argument = f"pull {remote} {remotebranchname}:{localbranchname}"
        if force:
            argument = f"{argument} --force"
        self.run_program("git", argument, folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_list_remote_branches(self, folder: str, remote: str, fetch: bool) -> list[str]:
        self.is_git_or_bare_git_repository(folder)
        if fetch:
            self.git_fetch(folder, remote)
        run_program_result = self.run_program("git", f"branch -rl {remote}/*", folder, throw_exception_if_exitcode_is_not_zero=True)
        output = GeneralUtilities.string_to_lines(run_program_result[1])
        result = list[str]()
        for item in output:
            striped_item = item.strip()
            if GeneralUtilities.string_has_content(striped_item):
                branch: str = None
                if " " in striped_item:
                    branch = striped_item.split(" ")[0]
                else:
                    branch = striped_item
                branchname = branch[len(remote)+1:]
                if branchname != "HEAD":
                    result.append(branchname)
        return result

    @GeneralUtilities.check_arguments
    def git_clone(self, clone_target_folder: str, remote_repository_path: str, include_submodules: bool = True, mirror: bool = False) -> None:
        if (os.path.isdir(clone_target_folder)):
            pass  # TODO throw error
        else:
            args = ["clone", remote_repository_path, clone_target_folder]
            if include_submodules:
                args.append("--recurse-submodules")
                args.append("--remote-submodules")
            if mirror:
                args.append("--mirror")
            self.run_program_argsasarray("git", args, os.getcwd(), throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_get_all_remote_names(self, directory: str) -> list[str]:
        self.is_git_or_bare_git_repository(directory)
        result = GeneralUtilities.string_to_lines(self.run_program_argsasarray("git", ["remote"], directory, throw_exception_if_exitcode_is_not_zero=True)[1], False)
        return result

    @GeneralUtilities.check_arguments
    def git_get_remote_url(self, directory: str, remote_name: str) -> str:
        self.is_git_or_bare_git_repository(directory)
        result = GeneralUtilities.string_to_lines(self.run_program_argsasarray("git", ["remote", "get-url", remote_name], directory, throw_exception_if_exitcode_is_not_zero=True)[1], False)
        return result[0].replace('\n', '')

    @GeneralUtilities.check_arguments
    def repository_has_remote_with_specific_name(self, directory: str, remote_name: str) -> bool:
        self.is_git_or_bare_git_repository(directory)
        return remote_name in self.git_get_all_remote_names(directory)

    @GeneralUtilities.check_arguments
    def git_add_or_set_remote_address(self, directory: str, remote_name: str, remote_address: str) -> None:
        self.assert_is_git_repository(directory)
        if (self.repository_has_remote_with_specific_name(directory, remote_name)):
            self.run_program_argsasarray("git", ['remote', 'set-url', 'remote_name', remote_address], directory, throw_exception_if_exitcode_is_not_zero=True)
        else:
            self.run_program_argsasarray("git", ['remote', 'add', remote_name, remote_address], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_stage_all_changes(self, directory: str) -> None:
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ["add", "-A"], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_unstage_all_changes(self, directory: str) -> None:
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ["reset"], directory, throw_exception_if_exitcode_is_not_zero=True)
        # TODO check if this will also be done for submodules

    @GeneralUtilities.check_arguments
    def git_stage_file(self, directory: str, file: str) -> None:
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ['stage', file], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_unstage_file(self, directory: str, file: str) -> None:
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ['reset', file], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_discard_unstaged_changes_of_file(self, directory: str, file: str) -> None:
        """Caution: This method works really only for 'changed' files yet. So this method does not work properly for new or renamed files."""
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ['checkout', file], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_discard_all_unstaged_changes(self, directory: str) -> None:
        """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ['clean', '-df'], directory, throw_exception_if_exitcode_is_not_zero=True)
        self.run_program_argsasarray("git", ['checkout', '.'], directory, throw_exception_if_exitcode_is_not_zero=True)
        # TODO check if this will also be done for submodules

    @GeneralUtilities.check_arguments
    def git_commit(self, directory: str, message: str = "Saved changes.", author_name: str = None, author_email: str = None, stage_all_changes: bool = True, no_changes_behavior: int = 0) -> str:
        """no_changes_behavior=0 => No commit; no_changes_behavior=1 => Commit anyway; no_changes_behavior=2 => Exception"""
        self.assert_is_git_repository(directory)
        author_name = GeneralUtilities.str_none_safe(author_name).strip()
        author_email = GeneralUtilities.str_none_safe(author_email).strip()
        argument = ['commit', '--quiet', '--allow-empty', '--message', message]
        if (GeneralUtilities.string_has_content(author_name)):
            argument.append(f'--author="{author_name} <{author_email}>"')
        git_repository_has_uncommitted_changes = self.git_repository_has_uncommitted_changes(directory)

        if git_repository_has_uncommitted_changes:
            do_commit = True
            if stage_all_changes:
                self.git_stage_all_changes(directory)
        else:
            if no_changes_behavior == 0:
                self.log.log(f"Commit '{message}' will not be done because there are no changes to commit in repository '{directory}'", LogLevel.Debug)
                do_commit = False
            elif no_changes_behavior == 1:
                self.log.log(f"There are no changes to commit in repository '{directory}'. Commit '{message}' will be done anyway.", LogLevel.Debug)
                do_commit = True
            elif no_changes_behavior == 2:
                raise RuntimeError(f"There are no changes to commit in repository '{directory}'. Commit '{message}' will not be done.")
            else:
                raise ValueError(f"Unknown value for no_changes_behavior: {GeneralUtilities.str_none_safe(no_changes_behavior)}")

        if do_commit:
            self.log.log(f"Commit changes in '{directory}'", LogLevel.Information)
            self.run_program_argsasarray("git", argument, directory, throw_exception_if_exitcode_is_not_zero=True)

        return self.git_get_commit_id(directory)
    
    def search_repository_folder(self,some_file_in_repository:str)->str:
        current_path:str=os.path.dirname(some_file_in_repository)
        enabled:bool=True
        while enabled:
            try:
                current_path=GeneralUtilities.resolve_relative_path("..",current_path)
                if self.is_git_repository(current_path):
                    return current_path
            except:
                enabled=False
        raise ValueError(f"Can not find git-repository for folder \"{some_file_in_repository}\".")
    

    @GeneralUtilities.check_arguments
    def git_create_tag(self, directory: str, target_for_tag: str, tag: str, sign: bool = False, message: str = None) -> None:
        self.is_git_or_bare_git_repository(directory)
        argument = ["tag", tag, target_for_tag]
        if sign:
            if message is None:
                message = f"Created {target_for_tag}"
            argument.extend(["-s", '-m', message])
        self.run_program_argsasarray("git", argument, directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_delete_tag(self, directory: str, tag: str) -> None:
        self.is_git_or_bare_git_repository(directory)
        self.run_program_argsasarray("git", ["tag", "--delete", tag], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_checkout(self, directory: str, branch: str, undo_all_changes_after_checkout: bool = True, assert_no_uncommitted_changes: bool = True) -> None:
        self.assert_is_git_repository(directory)
        if assert_no_uncommitted_changes:
            GeneralUtilities.assert_condition(not self.git_repository_has_uncommitted_changes(directory), f"Repository '{directory}' has uncommitted changes.")
        self.run_program_argsasarray("git", ["checkout", branch], directory, throw_exception_if_exitcode_is_not_zero=True)
        self.run_program_argsasarray("git", ["submodule", "update", "--recursive"], directory, throw_exception_if_exitcode_is_not_zero=True)
        if undo_all_changes_after_checkout:
            self.git_undo_all_changes(directory)

    @GeneralUtilities.check_arguments
    def merge_repository(self, repository_folder: str, remote: str, branch: str, pull_first_if_there_are_no_uncommitted_changes: bool = True):
        if pull_first_if_there_are_no_uncommitted_changes:
            uncommitted_changes = self.git_repository_has_uncommitted_changes(repository_folder)
            if not uncommitted_changes:
                is_pullable: bool = self.git_commit_is_ancestor(repository_folder, branch, f"{remote}/{branch}")
                if is_pullable:
                    self.git_pull(repository_folder, remote, branch, branch)
                    uncommitted_changes = self.git_repository_has_uncommitted_changes(repository_folder)
                    GeneralUtilities.assert_condition(not uncommitted_changes, f"Pulling remote \"{remote}\" in \"{repository_folder}\" caused new uncommitted files.")
        self.git_checkout(repository_folder, branch)
        self.git_commit(repository_folder, "Automatic commit due to merge")
        self.git_fetch(repository_folder, remote)
        self.git_merge(repository_folder, f"{remote}/{branch}", branch)
        self.git_push_with_retry(repository_folder, remote, branch, branch)
        self.git_checkout(repository_folder, branch)

    @GeneralUtilities.check_arguments
    def git_merge_abort(self, directory: str) -> None:
        self.assert_is_git_repository(directory)
        self.run_program_argsasarray("git", ["merge", "--abort"], directory, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_merge(self, directory: str, sourcebranch: str, targetbranch: str, fastforward: bool = True, commit: bool = True, commit_message: str = None, undo_all_changes_after_checkout: bool = True, assert_no_uncommitted_changes: bool = True) -> str:
        self.assert_is_git_repository(directory)
        self.git_checkout(directory, targetbranch, undo_all_changes_after_checkout, assert_no_uncommitted_changes)
        args = ["merge"]
        if not commit:
            args.append("--no-commit")
        if not fastforward:
            args.append("--no-ff")
        if commit_message is not None:
            args.append("-m")
            args.append(commit_message)
        args.append(sourcebranch)
        self.run_program_argsasarray("git", args, directory, throw_exception_if_exitcode_is_not_zero=True)
        self.run_program_argsasarray("git", ["submodule", "update"], directory, throw_exception_if_exitcode_is_not_zero=True)
        return self.git_get_commit_id(directory)

    @GeneralUtilities.check_arguments
    def git_undo_all_changes(self, directory: str) -> None:
        """Caution: This function executes 'git clean -df'. This can delete files which maybe should not be deleted. Be aware of that."""
        self.assert_is_git_repository(directory)
        self.git_unstage_all_changes(directory)
        self.git_discard_all_unstaged_changes(directory)

    @GeneralUtilities.check_arguments
    def git_fetch_or_clone_all_in_directory(self, source_directory: str, target_directory: str) -> None:
        for subfolder in GeneralUtilities.get_direct_folders_of_folder(source_directory):
            foldername = os.path.basename(subfolder)
            if self.is_git_repository(subfolder):
                source_repository = subfolder
                target_repository = os.path.join(target_directory, foldername)
                if os.path.isdir(target_directory):
                    # fetch
                    self.git_fetch(target_directory)
                else:
                    # clone
                    self.git_clone(target_repository, source_repository, include_submodules=True, mirror=True)

    def get_git_submodules(self, directory: str) -> list[str]:
        self.is_git_or_bare_git_repository(directory)
        e = self.run_program("git", "submodule status", directory)
        result = []
        for submodule_line in GeneralUtilities.string_to_lines(e[1], False, True):
            result.append(submodule_line.split(' ')[1])
        return result

    @GeneralUtilities.check_arguments
    def file_is_git_ignored(self, file_in_repository: str, repositorybasefolder: str) -> None:
        self.is_git_or_bare_git_repository(repositorybasefolder)
        exit_code = self.run_program_argsasarray("git", ['check-ignore', file_in_repository], repositorybasefolder, throw_exception_if_exitcode_is_not_zero=False)[0]
        if (exit_code == 0):
            return True
        if (exit_code == 1):
            return False
        raise ValueError(f"Unable to calculate whether '{file_in_repository}' in repository '{repositorybasefolder}' is ignored due to git-exitcode {exit_code}.")

    @GeneralUtilities.check_arguments
    def git_discard_all_changes(self, repository: str) -> None:
        self.assert_is_git_repository(repository)
        self.run_program_argsasarray("git", ["reset", "HEAD", "."], repository, throw_exception_if_exitcode_is_not_zero=True)
        self.run_program_argsasarray("git", ["checkout", "."], repository, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def git_get_current_branch_name(self, repository: str) -> str:
        self.assert_is_git_repository(repository)
        result = self.run_program_argsasarray("git", ["rev-parse", "--abbrev-ref", "HEAD"], repository, throw_exception_if_exitcode_is_not_zero=True)
        return result[1].replace("\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string)

    @GeneralUtilities.check_arguments
    def git_get_commitid_of_tag(self, repository: str, tag: str) -> str:
        self.is_git_or_bare_git_repository(repository)
        stdout = self.run_program_argsasarray("git", ["rev-list", "-n", "1", tag], repository)
        result = stdout[1].replace("\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string)
        return result

    @GeneralUtilities.check_arguments
    def git_get_tags(self, repository: str) -> list[str]:
        self.is_git_or_bare_git_repository(repository)
        tags = [line.replace("\r", GeneralUtilities.empty_string) for line in self.run_program_argsasarray(
            "git", ["tag"], repository)[1].split("\n") if len(line) > 0]
        return tags

    @GeneralUtilities.check_arguments
    def git_move_tags_to_another_branch(self, repository: str, tag_source_branch: str, tag_target_branch: str, sign: bool = False, message: str = None) -> None:
        self.is_git_or_bare_git_repository(repository)
        tags = self.git_get_tags(repository)
        tags_count = len(tags)
        counter = 0
        for tag in tags:
            counter = counter+1
            self.log.log(f"Process tag {counter}/{tags_count}.", LogLevel.Information)
            # tag is on source-branch
            if self.git_commit_is_ancestor(repository, tag, tag_source_branch):
                commit_id_old = self.git_get_commitid_of_tag(repository, tag)
                commit_date: datetime = self.git_get_commit_date(repository, commit_id_old)
                date_as_string = self.__datetime_to_string_for_git(commit_date)
                search_commit_result = self.run_program_argsasarray("git", ["log", f'--after="{date_as_string}"', f'--before="{date_as_string}"', "--pretty=format:%H", tag_target_branch], repository, throw_exception_if_exitcode_is_not_zero=False)
                if search_commit_result[0] != 0 or not GeneralUtilities.string_has_nonwhitespace_content(search_commit_result[1]):
                    raise ValueError(f"Can not calculate corresponding commit for tag '{tag}'.")
                commit_id_new = search_commit_result[1]
                self.git_delete_tag(repository, tag)
                self.git_create_tag(repository, commit_id_new, tag, sign, message)

    @GeneralUtilities.check_arguments
    def get_current_git_branch_has_tag(self, repository_folder: str) -> bool:
        self.is_git_or_bare_git_repository(repository_folder)
        result = self.run_program_argsasarray("git", ["describe", "--tags", "--abbrev=0"], repository_folder, throw_exception_if_exitcode_is_not_zero=False)
        return result[0] == 0

    @GeneralUtilities.check_arguments
    def get_latest_git_tag(self, repository_folder: str) -> str:
        self.is_git_or_bare_git_repository(repository_folder)
        result = self.run_program_argsasarray("git", ["describe", "--tags", "--abbrev=0"], repository_folder)
        result = result[1].replace("\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string)
        return result

    @GeneralUtilities.check_arguments
    def get_staged_or_committed_git_ignored_files(self, repository_folder: str) -> list[str]:
        self.assert_is_git_repository(repository_folder)
        temp_result = self.run_program_argsasarray("git", ["ls-files", "-i", "-c", "--exclude-standard"], repository_folder)
        temp_result = temp_result[1].replace("\r", GeneralUtilities.empty_string)
        result = [line for line in temp_result.split("\n") if len(line) > 0]
        return result

    @GeneralUtilities.check_arguments
    def git_repository_has_commits(self, repository_folder: str) -> bool:
        self.assert_is_git_repository(repository_folder)
        return self.run_program_argsasarray("git", ["rev-parse", "--verify", "HEAD"], repository_folder, throw_exception_if_exitcode_is_not_zero=False)[0] == 0

    @GeneralUtilities.check_arguments
    def run_git_command_in_repository_and_submodules(self, repository_folder: str, arguments: list[str]) -> None:
        self.is_git_or_bare_git_repository(repository_folder)
        self.run_program_argsasarray("git", arguments, repository_folder)
        self.run_program_argsasarray("git", ["submodule", "foreach", "--recursive", "git"]+arguments, repository_folder)

    @GeneralUtilities.check_arguments
    def export_filemetadata(self, folder: str, target_file: str, encoding: str = "utf-8", filter_function=None) -> None:
        folder = GeneralUtilities.resolve_relative_path_from_current_working_directory(folder)
        lines = list()
        path_prefix = len(folder)+1
        items = dict()
        for item in GeneralUtilities.get_all_folders_of_folder(folder):
            items[item] = "d"
        for item in GeneralUtilities.get_all_files_of_folder(folder):
            items[item] = "f"
        for file_or_folder, item_type in items.items():
            truncated_file = file_or_folder[path_prefix:]
            if (filter_function is None or filter_function(folder, truncated_file)):
                owner_and_permisssion = self.get_file_owner_and_file_permission(file_or_folder)
                user = owner_and_permisssion[0]
                permissions = owner_and_permisssion[1]
                lines.append(f"{truncated_file};{item_type};{user};{permissions}")
        lines = sorted(lines, key=str.casefold)
        with open(target_file, "w", encoding=encoding) as file_object:
            file_object.write("\n".join(lines))

    @GeneralUtilities.check_arguments
    def escape_git_repositories_in_folder(self, folder: str) -> dict[str, str]:
        return self.__escape_git_repositories_in_folder_internal(folder, dict[str, str]())

    @GeneralUtilities.check_arguments
    def __escape_git_repositories_in_folder_internal(self, folder: str, renamed_items: dict[str, str]) -> dict[str, str]:
        for file in GeneralUtilities.get_direct_files_of_folder(folder):
            filename = os.path.basename(file)
            if ".git" in filename:
                new_name = filename.replace(".git", ".gitx")
                target = os.path.join(folder, new_name)
                os.rename(file, target)
                renamed_items[target] = file
        for subfolder in GeneralUtilities.get_direct_folders_of_folder(folder):
            foldername = os.path.basename(subfolder)
            if ".git" in foldername:
                new_name = foldername.replace(".git", ".gitx")
                subfolder2 = os.path.join(str(Path(subfolder).parent), new_name)
                os.rename(subfolder, subfolder2)
                renamed_items[subfolder2] = subfolder
            else:
                subfolder2 = subfolder
            self.__escape_git_repositories_in_folder_internal(subfolder2, renamed_items)
        return renamed_items

    @GeneralUtilities.check_arguments
    def deescape_git_repositories_in_folder(self, renamed_items: dict[str, str]):
        for renamed_item, original_name in renamed_items.items():
            os.rename(renamed_item, original_name)

    @GeneralUtilities.check_arguments
    def is_git_repository(self, folder: str) -> bool:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        folder=folder.replace("\\","/")
        if folder.endswith("/"):
            folder = folder[:-1]
        if not self.is_folder(folder):
            raise ValueError(f"Folder '{folder}' does not exist.")
        git_folder_path = f"{folder}/.git"
        return self.is_folder(git_folder_path) or self.is_file(git_folder_path)

    @GeneralUtilities.check_arguments
    def is_bare_git_repository(self, folder: str) -> bool:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if folder.endswith("/") or folder.endswith("\\"):
            folder = folder[:-1]
        if not self.is_folder(folder):
            raise ValueError(f"Folder '{folder}' does not exist.")
        return folder.endswith(".git")

    @GeneralUtilities.check_arguments
    def is_git_or_bare_git_repository(self, folder: str) -> bool:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        return self.is_git_repository(folder) or self.is_bare_git_repository(folder)

    @GeneralUtilities.check_arguments
    def assert_is_git_repository(self, folder: str) -> str:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        GeneralUtilities.assert_condition(self.is_git_repository(folder), f"'{folder}' is not a git-repository.")

    @GeneralUtilities.check_arguments
    def convert_git_repository_to_bare_repository(self, repository_folder: str):
        repository_folder = repository_folder.replace("\\", "/")
        self.assert_is_git_repository(repository_folder)
        git_folder = repository_folder + "/.git"
        if not self.is_folder(git_folder):
            raise ValueError(f"Converting '{repository_folder}' to a bare repository not possible. The folder '{git_folder}' does not exist. Converting is currently only supported when the git-folder is a direct folder in a repository and not a reference to another location.")
        target_folder: str = repository_folder + ".git"
        GeneralUtilities.ensure_directory_exists(target_folder)
        GeneralUtilities.move_content_of_folder(git_folder, target_folder)
        GeneralUtilities.ensure_directory_does_not_exist(repository_folder)
        self.run_program_argsasarray("git", ["config", "--bool", "core.bare", "true"], target_folder)

    @GeneralUtilities.check_arguments
    def assert_no_uncommitted_changes(self, repository_folder: str):
        if self.git_repository_has_uncommitted_changes(repository_folder):
            raise ValueError(f"Repository '{repository_folder}' has uncommitted changes.")

    @GeneralUtilities.check_arguments
    def list_content(self, path: str, include_files: bool, include_folder: bool, printonlynamewithoutpath: bool) -> list[str]:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        result: list[str] = []
        if self.program_runner.will_be_executed_locally():
            if include_files:
                result = result + GeneralUtilities.get_direct_files_of_folder(path)
            if include_folder:
                result = result + GeneralUtilities.get_direct_folders_of_folder(path)
        else:
            arguments = ["--path", path]
            if not include_files:
                arguments = arguments+["--excludefiles"]
            if not include_folder:
                arguments = arguments+["--excludedirectories"]
            if printonlynamewithoutpath:
                arguments = arguments+["--printonlynamewithoutpath"]
            exit_code, stdout, stderr, _ = self.run_program_argsasarray("sclistfoldercontent", arguments)
            if exit_code == 0:
                for line in stdout.split("\n"):
                    normalized_line = line.replace("\r", "")
                    result.append(normalized_line)
            else:
                raise ValueError(f"Fatal error occurrs while checking whether file '{path}' exists. StdErr: '{stderr}'")
        result = [item for item in result if GeneralUtilities.string_has_nonwhitespace_content(item)]
        return result

    @GeneralUtilities.check_arguments
    def is_file(self, path: str) -> bool:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():
            return os.path.isfile(path)  # works only locally, but much more performant than always running an external program
        else:
            exit_code, _, stderr, _ = self.run_program_argsasarray("scfileexists", ["--path", path], throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
            if exit_code == 0:
                return True
            elif exit_code == 1:
                raise ValueError(f"Not calculatable whether file '{path}' exists. StdErr: '{stderr}'")
            elif exit_code == 2:
                return False
            raise ValueError(f"Fatal error occurrs while checking whether file '{path}' exists. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def is_folder(self, path: str) -> bool:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():  # works only locally, but much more performant than always running an external program
            return os.path.isdir(path)
        else:
            exit_code, _, stderr, _ = self.run_program_argsasarray("scfolderexists", ["--path", path], throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
            if exit_code == 0:
                return True
            elif exit_code == 1:
                raise ValueError(f"Not calculatable whether folder '{path}' exists. StdErr: '{stderr}'")
            elif exit_code == 2:
                return False
            raise ValueError(f"Fatal error occurrs while checking whether folder '{path}' exists. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def get_file_content(self, path: str, encoding: str = "utf-8") -> str:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():
            return GeneralUtilities.read_text_from_file(path, encoding)
        else:
            result = self.run_program_argsasarray("scprintfilecontent", ["--path", path, "--encofing", encoding])  # works platform-indepent
            return result[1].replace("\\n", "\n")

    @GeneralUtilities.check_arguments
    def set_file_content(self, path: str, content: str, encoding: str = "utf-8") -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():
            GeneralUtilities.write_text_to_file(path, content, encoding)
        else:
            content_bytes = content.encode('utf-8')
            base64_bytes = base64.b64encode(content_bytes)
            base64_string = base64_bytes.decode('utf-8')
            self.run_program_argsasarray("scsetfilecontent", ["--path", path, "--argumentisinbase64", "--content", base64_string])  # works platform-indepent

    @GeneralUtilities.check_arguments
    def remove(self, path: str) -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():  # works only locally, but much more performant than always running an external program
            if os.path.isdir(path):
                GeneralUtilities.ensure_directory_does_not_exist(path)
            if os.path.isfile(path):
                GeneralUtilities.ensure_file_does_not_exist(path)
        else:
            if self.is_file(path):
                exit_code, _, stderr, _ = self.run_program_argsasarray("scremovefile", ["--path", path], throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
                if exit_code != 0:
                    raise ValueError(f"Fatal error occurrs while removing file '{path}'. StdErr: '{stderr}'")
            if self.is_folder(path):
                exit_code, _, stderr, _ = self.run_program_argsasarray("scremovefolder", ["--path", path], throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
                if exit_code != 0:
                    raise ValueError(f"Fatal error occurrs while removing folder '{path}'. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def rename(self,  source: str, target: str) -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():  # works only locally, but much more performant than always running an external program
            os.rename(source, target)
        else:
            exit_code, _, stderr, _ = self.run_program_argsasarray("screname", ["--source", source, "--target", target], throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
            if exit_code != 0:
                raise ValueError(f"Fatal error occurrs while renaming '{source}' to '{target}'. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def copy(self, source: str, target: str) -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():  # works only locally, but much more performant than always running an external program
            if os.path.isfile(target) or os.path.isdir(target):
                raise ValueError(f"Can not copy to '{target}' because the target already exists.")
            if os.path.isfile(source):
                shutil.copyfile(source, target)
            elif os.path.isdir(source):
                GeneralUtilities.ensure_directory_exists(target)
                GeneralUtilities.copy_content_of_folder(source, target)
            else:
                raise ValueError(f"'{source}' can not be copied because the path does not exist.")
        else:
            exit_code, _, stderr, _ = self.run_program_argsasarray("sccopy", ["--source", source, "--target", target], throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
            if exit_code != 0:
                raise ValueError(f"Fatal error occurrs while copying '{source}' to '{target}'. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def create_file(self, path: str, error_if_already_exists: bool, create_necessary_folder: bool) -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)

            if os.path.isfile(path) and error_if_already_exists:
                raise ValueError(f"File '{path}' already exists.")

            # TODO maybe it should be checked if there is a folder with the same path which already exists.

            folder = os.path.dirname(path)

            if not os.path.isdir(folder):
                if create_necessary_folder:
                    GeneralUtilities.ensure_directory_exists(folder)  # TODO check if this also create nested folders if required
                else:
                    raise ValueError(f"Folder '{folder}' does not exist.")

            GeneralUtilities.ensure_file_exists(path)
        else:
            arguments = ["--path", path]

            if error_if_already_exists:
                arguments = arguments+["--errorwhenexists"]

            if create_necessary_folder:
                arguments = arguments+["--createnecessaryfolder"]

            exit_code, _, stderr, _ = self.run_program_argsasarray("sccreatefile", arguments, throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
            if exit_code != 0:
                raise ValueError(f"Fatal error occurrs while create file '{path}'. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def create_folder(self, path: str, error_if_already_exists: bool, create_necessary_folder: bool) -> None:
        """This function works platform-independent also for non-local-executions if the ScriptCollection commandline-commands are available as global command on the target-system."""
        if self.program_runner.will_be_executed_locally():
            if not os.path.isabs(path):
                path = os.path.join(os.getcwd(), path)

            if os.path.isdir(path) and error_if_already_exists:
                raise ValueError(f"Folder '{path}' already exists.")

            # TODO maybe it should be checked if there is a file with the same path which already exists.

            folder = os.path.dirname(path)

            if not os.path.isdir(folder):
                if create_necessary_folder:
                    GeneralUtilities.ensure_directory_exists(folder)  # TODO check if this also create nested folders if required
                else:
                    raise ValueError(f"Folder '{folder}' does not exist.")

            GeneralUtilities.ensure_directory_exists(path)
        else:
            arguments = ["--path", path]

            if error_if_already_exists:
                arguments = arguments+["--errorwhenexists"]

            if create_necessary_folder:
                arguments = arguments+["--createnecessaryfolder"]

            exit_code, _, stderr, _ = self.run_program_argsasarray("sccreatefolder", arguments, throw_exception_if_exitcode_is_not_zero=False)  # works platform-indepent
            if exit_code != 0:
                raise ValueError(f"Fatal error occurrs while create folder '{path}'. StdErr: '{stderr}'")

    @GeneralUtilities.check_arguments
    def __sort_fmd(self, line: str):
        splitted: list = line.split(";")
        filetype: str = splitted[1]
        if filetype == "d":
            return -1
        if filetype == "f":
            return 1
        return 0

    @GeneralUtilities.check_arguments
    def restore_filemetadata(self, folder: str, source_file: str, strict=False, encoding: str = "utf-8", create_folder_is_not_exist: bool = True) -> None:
        lines = GeneralUtilities.read_lines_from_file(source_file, encoding)
        lines.sort(key=self.__sort_fmd)
        for line in lines:
            splitted: list = line.split(";")
            full_path_of_file_or_folder: str = os.path.join(folder, splitted[0])
            filetype: str = splitted[1]
            user: str = splitted[2]
            permissions: str = splitted[3]
            if filetype == "d" and create_folder_is_not_exist and not os.path.isdir(full_path_of_file_or_folder):
                GeneralUtilities.ensure_directory_exists(full_path_of_file_or_folder)
            if (filetype == "f" and os.path.isfile(full_path_of_file_or_folder)) or (filetype == "d" and os.path.isdir(full_path_of_file_or_folder)):
                self.set_owner(full_path_of_file_or_folder, user, os.name != 'nt')
                self.set_permission(full_path_of_file_or_folder, permissions)
            else:
                if strict:
                    if filetype == "f":
                        filetype_full = "File"
                    elif filetype == "d":
                        filetype_full = "Directory"
                    else:
                        raise ValueError(f"Unknown filetype: {GeneralUtilities.str_none_safe(filetype)}")
                    raise ValueError(f"{filetype_full} '{full_path_of_file_or_folder}' does not exist")

    @GeneralUtilities.check_arguments
    def __calculate_lengh_in_seconds(self, filename: str, folder: str) -> float:
        argument = ['-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', filename]
        result = self.run_program_argsasarray("ffprobe", argument, folder, throw_exception_if_exitcode_is_not_zero=True)
        return float(result[1].replace('\n', ''))

    @GeneralUtilities.check_arguments
    def __create_thumbnails(self, filename: str, fps: str, folder: str, tempname_for_thumbnails: str) -> list[str]:
        argument = ['-i', filename, '-r', fps, '-vf', 'scale=-1:120', '-vcodec', 'png', f'{tempname_for_thumbnails}-%002d.png']
        self.run_program_argsasarray("ffmpeg", argument, folder, throw_exception_if_exitcode_is_not_zero=True)
        files = GeneralUtilities.get_direct_files_of_folder(folder)
        result: list[str] = []
        regex = "^"+re.escape(tempname_for_thumbnails)+"\\-\\d+\\.png$"
        regex_for_files = re.compile(regex)
        for file in files:
            filename = os.path.basename(file)
            if regex_for_files.match(filename):
                result.append(file)
        GeneralUtilities.assert_condition(0 < len(result), "No thumbnail-files found.")
        return result

    @GeneralUtilities.check_arguments
    def __create_thumbnail(self, outputfilename: str, folder: str, length_in_seconds: float, tempname_for_thumbnails: str, amount_of_images: int) -> None:
        duration = timedelta(seconds=length_in_seconds)
        info = GeneralUtilities.timedelta_to_simple_string(duration)
        next_square_number = GeneralUtilities.get_next_square_number(amount_of_images)
        root = math.sqrt(next_square_number)
        rows: int = root  # 5
        columns: int = root  # math.ceil(amount_of_images/rows)
        argument = ['-title', f'"{outputfilename} ({info})"', '-tile', f'{rows}x{columns}', f'{tempname_for_thumbnails}*.png', f'{outputfilename}.png']
        self.run_program_argsasarray("montage", argument, folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def __create_thumbnail2(self, outputfilename: str, folder: str, length_in_seconds: float, rows: int, columns: int, tempname_for_thumbnails: str, amount_of_images: int) -> None:
        duration = timedelta(seconds=length_in_seconds)
        info = GeneralUtilities.timedelta_to_simple_string(duration)
        argument = ['-title', f'"{outputfilename} ({info})"', '-tile', f'{rows}x{columns}', f'{tempname_for_thumbnails}*.png', f'{outputfilename}.png']
        self.run_program_argsasarray("montage", argument, folder, throw_exception_if_exitcode_is_not_zero=True)

    @GeneralUtilities.check_arguments
    def __roundup(self, x: float, places: int) -> int:
        d = 10 ** places
        if x < 0:
            return math.floor(x * d) / d
        else:
            return math.ceil(x * d) / d

    @GeneralUtilities.check_arguments
    def generate_thumbnail(self, file: str, frames_per_second: float, tempname_for_thumbnails: str = None, hook=None) -> None:
        if tempname_for_thumbnails is None:
            tempname_for_thumbnails = "t_"+str(uuid.uuid4())

        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        filename = os.path.basename(file)
        folder = os.path.dirname(file)
        filename_without_extension = Path(file).stem
        preview_files: list[str] = []
        try:
            length_in_seconds = self.__calculate_lengh_in_seconds(filename, folder)
            # frames per second, example: frames_per_second="20fps" => 20 frames per second
            frames_per_second = self.__roundup(float(frames_per_second[:-3]), 2)
            frames_per_second_as_string = str(frames_per_second)
            preview_files = self.__create_thumbnails(filename, frames_per_second_as_string, folder, tempname_for_thumbnails)
            if hook is not None:
                hook(file, preview_files)
            actual_amounf_of_previewframes = len(preview_files)
            self.__create_thumbnail(filename_without_extension, folder, length_in_seconds, tempname_for_thumbnails, actual_amounf_of_previewframes)
        finally:
            for thumbnail_to_delete in preview_files:
                os.remove(thumbnail_to_delete)

    @GeneralUtilities.check_arguments
    def generate_thumbnail_by_amount_of_pictures(self, file: str, amount_of_columns: int, amount_of_rows: int, tempname_for_thumbnails: str = None, hook=None) -> None:
        if tempname_for_thumbnails is None:
            tempname_for_thumbnails = "t_"+str(uuid.uuid4())

        file = GeneralUtilities.resolve_relative_path_from_current_working_directory(file)
        filename = os.path.basename(file)
        folder = os.path.dirname(file)
        filename_without_extension = Path(file).stem
        preview_files: list[str] = []
        try:
            length_in_seconds = self.__calculate_lengh_in_seconds(filename, folder)
            amounf_of_previewframes = int(amount_of_columns*amount_of_rows)
            frames_per_second_as_string = f"{amounf_of_previewframes-2}/{length_in_seconds}"
            preview_files = self.__create_thumbnails(filename, frames_per_second_as_string, folder, tempname_for_thumbnails)
            if hook is not None:
                hook(file, preview_files)
            actual_amounf_of_previewframes = len(preview_files)
            self.__create_thumbnail2(filename_without_extension, folder, length_in_seconds, amount_of_rows, amount_of_columns, tempname_for_thumbnails, actual_amounf_of_previewframes)
        finally:
            for thumbnail_to_delete in preview_files:
                os.remove(thumbnail_to_delete)

    @GeneralUtilities.check_arguments
    def extract_pdf_pages(self, file: str, from_page: int, to_page: int, outputfile: str) -> None:
        pdf_reader: PdfReader = PdfReader(file)
        pdf_writer: PdfWriter = PdfWriter()
        start = from_page
        end = to_page
        while start <= end:
            pdf_writer.add_page(pdf_reader.pages[start-1])
            start += 1
        with open(outputfile, 'wb') as out:
            pdf_writer.write(out)

    @GeneralUtilities.check_arguments
    def merge_pdf_files(self, files: list[str], outputfile: str) -> None:
        # TODO add wildcard-option
        pdfFileMerger: PdfWriter = PdfWriter()
        for file in files:
            with open(file, "rb") as f:
                pdfFileMerger.append(f)
        with open(outputfile, "wb") as output:
            pdfFileMerger.write(output)
            pdfFileMerger.close()

    @GeneralUtilities.check_arguments
    def pdf_to_image(self, file: str, outputfilename_without_extension: str) -> None:
        raise ValueError("Function currently not available")
        # PyMuPDF can be used for that but sometimes it throws
        # "ImportError: DLL load failed while importing _fitz: Das angegebene Modul wurde nicht gefunden."

        # doc = None  # fitz.open(file)
        # for i, page in enumerate(doc):
        #     pix = page.get_pixmap()
        #     img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        #     img.save(f"{outputfilename_without_extension}_{i}.png", "PNG")

    @GeneralUtilities.check_arguments
    def show_missing_files(self, folderA: str, folderB: str):
        for file in GeneralUtilities.get_missing_files(folderA, folderB):
            GeneralUtilities.write_message_to_stdout(file)

    @GeneralUtilities.check_arguments
    def SCCreateEmptyFileWithSpecificSize(self, name: str, size_string: str) -> int:
        if size_string.isdigit():
            size = int(size_string)
        else:
            if len(size_string) >= 3:
                if (size_string.endswith("kb")):
                    size = int(size_string[:-2]) * pow(10, 3)
                elif (size_string.endswith("mb")):
                    size = int(size_string[:-2]) * pow(10, 6)
                elif (size_string.endswith("gb")):
                    size = int(size_string[:-2]) * pow(10, 9)
                elif (size_string.endswith("kib")):
                    size = int(size_string[:-3]) * pow(2, 10)
                elif (size_string.endswith("mib")):
                    size = int(size_string[:-3]) * pow(2, 20)
                elif (size_string.endswith("gib")):
                    size = int(size_string[:-3]) * pow(2, 30)
                else:
                    self.log.log("Wrong format", LogLevel.Error)
                    return 1
            else:
                self.log.log("Wrong format", LogLevel.Error)
                return 1
        with open(name, "wb") as f:
            f.seek(size-1)
            f.write(b"\0")
        return 0

    @GeneralUtilities.check_arguments
    def SCCreateHashOfAllFiles(self, folder: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            with open(file+".sha256", "w+", encoding="utf-8") as f:
                f.write(GeneralUtilities.get_sha256_of_file(file))

    @GeneralUtilities.check_arguments
    def SCCreateSimpleMergeWithoutRelease(self, repository: str, sourcebranch: str, targetbranch: str, remotename: str, remove_source_branch: bool) -> None:
        commitid = self.git_merge(repository, sourcebranch, targetbranch, False, True)
        self.git_merge(repository, targetbranch, sourcebranch, True, True)
        created_version = self.get_semver_version_from_gitversion(repository)
        self.git_create_tag(repository, commitid, f"v{created_version}", True)
        self.git_push(repository, remotename, targetbranch, targetbranch, False, True)
        if (GeneralUtilities.string_has_nonwhitespace_content(remotename)):
            self.git_push(repository, remotename, sourcebranch, sourcebranch, False, True)
        if (remove_source_branch):
            self.git_remove_branch(repository, sourcebranch)

    @GeneralUtilities.check_arguments
    def sc_organize_lines_in_file(self, file: str, encoding: str, sort: bool = False, remove_duplicated_lines: bool = False, ignore_first_line: bool = False, remove_empty_lines: bool = True, ignored_start_character: list = list()) -> int:
        if os.path.isfile(file):

            # read file
            lines = GeneralUtilities.read_lines_from_file(file, encoding)
            if (len(lines) == 0):
                return 0

            # store first line if desiredpopd

            if (ignore_first_line):
                first_line = lines.pop(0)

            # remove empty lines if desired
            if remove_empty_lines:
                temp = lines
                lines = []
                for line in temp:
                    if (not (GeneralUtilities.string_is_none_or_whitespace(line))):
                        lines.append(line)

            # remove duplicated lines if desired
            if remove_duplicated_lines:
                lines = GeneralUtilities.remove_duplicates(lines)

            # sort lines if desired
            if sort:
                lines = sorted(lines, key=lambda singleline: self.__adapt_line_for_sorting(singleline, ignored_start_character))

            # reinsert first line
            if ignore_first_line:
                lines.insert(0, first_line)

            # write result to file
            GeneralUtilities.write_lines_to_file(file, lines, encoding)

            return 0
        else:
            self.log.log(f"File '{file}' does not exist.", LogLevel.Error)
            return 1

    @GeneralUtilities.check_arguments
    def __adapt_line_for_sorting(self, line: str, ignored_start_characters: list):
        result = line.lower()
        while len(result) > 0 and result[0] in ignored_start_characters:
            result = result[1:]
        return result

    @GeneralUtilities.check_arguments
    def SCGenerateSnkFiles(self, outputfolder, keysize=4096, amountofkeys=10) -> int:
        GeneralUtilities.ensure_directory_exists(outputfolder)
        for _ in range(amountofkeys):
            file = os.path.join(outputfolder, str(uuid.uuid4())+".snk")
            argument = f"-k {keysize} {file}"
            self.run_program("sn", argument, outputfolder)

    @GeneralUtilities.check_arguments
    def __merge_files(self, sourcefile: str, targetfile: str) -> None:
        with open(sourcefile, "rb") as f:
            source_data = f.read()
        with open(targetfile, "ab") as fout:
            merge_separator = [0x0A]
            fout.write(bytes(merge_separator))
            fout.write(source_data)

    @GeneralUtilities.check_arguments
    def __process_file(self, file: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
        new_filename = os.path.join(os.path.dirname(file), os.path.basename(file).replace(substringInFilename, newSubstringInFilename))
        if file != new_filename:
            if os.path.isfile(new_filename):
                if filecmp.cmp(file, new_filename):
                    send2trash.send2trash(file)
                else:
                    if conflictResolveMode == "ignore":
                        pass
                    elif conflictResolveMode == "preservenewest":
                        if (os.path.getmtime(file) - os.path.getmtime(new_filename) > 0):
                            send2trash.send2trash(file)
                        else:
                            send2trash.send2trash(new_filename)
                            os.rename(file, new_filename)
                    elif (conflictResolveMode == "merge"):
                        self.__merge_files(file, new_filename)
                        send2trash.send2trash(file)
                    else:
                        raise ValueError('Unknown conflict resolve mode')
            else:
                os.rename(file, new_filename)

    @GeneralUtilities.check_arguments
    def SCReplaceSubstringsInFilenames(self, folder: str, substringInFilename: str, newSubstringInFilename: str, conflictResolveMode: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            self.__process_file(file, substringInFilename, newSubstringInFilename, conflictResolveMode)

    @GeneralUtilities.check_arguments
    def __check_file(self, file: str, searchstring: str) -> None:
        bytes_ascii = bytes(searchstring, "ascii")
        # often called "unicode-encoding"
        bytes_utf16 = bytes(searchstring, "utf-16")
        bytes_utf8 = bytes(searchstring, "utf-8")
        with open(file, mode='rb') as file_object:
            content = file_object.read()
            if bytes_ascii in content:
                GeneralUtilities.write_message_to_stdout(file)
            elif bytes_utf16 in content:
                GeneralUtilities.write_message_to_stdout(file)
            elif bytes_utf8 in content:
                GeneralUtilities.write_message_to_stdout(file)

    @GeneralUtilities.check_arguments
    def SCSearchInFiles(self, folder: str, searchstring: str) -> None:
        for file in GeneralUtilities.absolute_file_paths(folder):
            self.__check_file(file, searchstring)

    @GeneralUtilities.check_arguments
    def __print_qr_code_by_csv_line(self, displayname: str, website: str, emailaddress: str, key: str, period: str) -> None:
        qrcode_content = f"otpauth://totp/{website}:{emailaddress}?secret={key}&issuer={displayname}&period={period}"
        GeneralUtilities.write_message_to_stdout(f"{displayname} ({emailaddress}):")
        GeneralUtilities.write_message_to_stdout(qrcode_content)
        qr = qrcode.QRCode()
        qr.add_data(qrcode_content)
        f = io.StringIO()
        qr.print_ascii(out=f)
        f.seek(0)
        GeneralUtilities.write_message_to_stdout(f.read())

    @GeneralUtilities.check_arguments
    def SCShow2FAAsQRCode(self, csvfile: str) -> None:
        lines = GeneralUtilities.read_csv_file(csvfile, True)
        lines.sort(key=lambda items: ''.join(items).lower())
        for line in lines:
            self.__print_qr_code_by_csv_line(line[0], line[1], line[2], line[3], line[4])
            GeneralUtilities.write_message_to_stdout(GeneralUtilities.get_longline())

    @GeneralUtilities.check_arguments
    def SCCalculateBitcoinBlockHash(self, block_version_number: str, previousblockhash: str, transactionsmerkleroot: str, timestamp: str, target: str, nonce: str) -> str:
        # Example-values:
        # block_version_number: "00000020"
        # previousblockhash: "66720b99e07d284bd4fe67ff8c49a5db1dd8514fcdab61000000000000000000"
        # transactionsmerkleroot: "7829844f4c3a41a537b3131ca992643eaa9d093b2383e4cdc060ad7dc5481187"
        # timestamp: "51eb505a"
        # target: "c1910018"
        # nonce: "de19b302"
        header = str(block_version_number + previousblockhash + transactionsmerkleroot + timestamp + target + nonce)
        return binascii.hexlify(hashlib.sha256(hashlib.sha256(binascii.unhexlify(header)).digest()).digest()[::-1]).decode('utf-8')

    @GeneralUtilities.check_arguments
    def SCChangeHashOfProgram(self, inputfile: str) -> None:
        valuetoappend = str(uuid.uuid4())

        outputfile = inputfile + '.modified'

        shutil.copy2(inputfile, outputfile)
        with open(outputfile, 'a', encoding="utf-8") as file:
            # TODO use rcedit for .exe-files instead of appending valuetoappend ( https://github.com/electron/rcedit/ )
            # background: you can retrieve the "original-filename" from the .exe-file like discussed here:
            # https://security.stackexchange.com/questions/210843/ is-it-possible-to-change-original-filename-of-an-exe
            # so removing the original filename with rcedit is probably a better way to make it more difficult to detect the programname.
            # this would obviously also change the hashvalue of the program so appending a whitespace is not required anymore.
            file.write(valuetoappend)

    @GeneralUtilities.check_arguments
    def __adjust_folder_name(self, folder: str) -> str:
        result = os.path.dirname(folder).replace("\\", "/")
        if result == "/":
            return GeneralUtilities.empty_string
        else:
            return result

    @GeneralUtilities.check_arguments
    def __create_iso(self, folder, iso_file) -> None:
        created_directories = []
        files_directory = "FILES"
        iso = pycdlib.PyCdlib()
        iso.new()
        files_directory = files_directory.upper()
        iso.add_directory("/" + files_directory)
        created_directories.append("/" + files_directory)
        for root, _, files in os.walk(folder):
            for file in files:
                full_path = os.path.join(root, file)
                with (open(full_path, "rb").read()) as text_io_wrapper:
                    content = text_io_wrapper
                    path_in_iso = '/' + files_directory + \
                        self.__adjust_folder_name(full_path[len(folder)::1]).upper()
                    if path_in_iso not in created_directories:
                        iso.add_directory(path_in_iso)
                        created_directories.append(path_in_iso)
                    iso.add_fp(BytesIO(content), len(content), path_in_iso + '/' + file.upper() + ';1')
        iso.write(iso_file)
        iso.close()

    @GeneralUtilities.check_arguments
    def SCCreateISOFileWithObfuscatedFiles(self, inputfolder: str, outputfile: str, printtableheadline, createisofile, extensions) -> None:
        if (os.path.isdir(inputfolder)):
            namemappingfile = "name_map.csv"
            files_directory = inputfolder
            files_directory_obf = f"{files_directory}_Obfuscated"
            self.SCObfuscateFilesFolder(
                inputfolder, printtableheadline, namemappingfile, extensions)
            os.rename(namemappingfile, os.path.join(
                files_directory_obf, namemappingfile))
            if createisofile:
                self.__create_iso(files_directory_obf, outputfile)
                shutil.rmtree(files_directory_obf)
        else:
            raise ValueError(f"Directory not found: '{inputfolder}'")

    @GeneralUtilities.check_arguments
    def SCFilenameObfuscator(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if (obfuscate_all_files):
            obfuscate_file_extensions = None
        else:
            obfuscate_file_extensions = extensions.split(",")
        if (os.path.isdir(inputfolder)):
            printtableheadline = GeneralUtilities.string_to_boolean(
                printtableheadline)
            files = []
            if not os.path.isfile(namemappingfile):
                with open(namemappingfile, "a", encoding="utf-8"):
                    pass
            if printtableheadline:
                GeneralUtilities.append_line_to_file(
                    namemappingfile, "Original filename;new filename;SHA2-hash of file")
            for file in GeneralUtilities.absolute_file_paths(inputfolder):
                if os.path.isfile(os.path.join(inputfolder, file)):
                    if obfuscate_all_files or self.__extension_matchs(file, obfuscate_file_extensions):
                        files.append(file)
            for file in files:
                hash_value = GeneralUtilities.get_sha256_of_file(file)
                extension = Path(file).suffix
                new_file_name_without_path = str(uuid.uuid4())[0:8] + extension
                new_file_name = os.path.join(
                    os.path.dirname(file), new_file_name_without_path)
                os.rename(file, new_file_name)
                GeneralUtilities.append_line_to_file(namemappingfile, os.path.basename(file) + ";" + new_file_name_without_path + ";" + hash_value)
        else:
            raise ValueError(f"Directory not found: '{inputfolder}'")

    @GeneralUtilities.check_arguments
    def __extension_matchs(self, file: str, obfuscate_file_extensions) -> bool:
        for extension in obfuscate_file_extensions:
            if file.lower().endswith("."+extension.lower()):
                return True
        return False

    @GeneralUtilities.check_arguments
    def SCHealthcheck(self, file: str) -> int:
        lines = GeneralUtilities.read_lines_from_file(file)
        for line in reversed(lines):
            if not GeneralUtilities.string_is_none_or_whitespace(line):
                if "RunningHealthy (" in line:  # TODO use regex
                    GeneralUtilities.write_message_to_stderr(f"Healthy running due to line '{line}' in file '{file}'.")
                    return 0
                else:
                    GeneralUtilities.write_message_to_stderr(f"Not healthy running due to line '{line}' in file '{file}'.")
                    return 1
        GeneralUtilities.write_message_to_stderr(f"No valid line found for healthycheck in file '{file}'.")
        return 2

    @GeneralUtilities.check_arguments
    def SCObfuscateFilesFolder(self, inputfolder: str, printtableheadline, namemappingfile: str, extensions: str) -> None:
        obfuscate_all_files = extensions == "*"
        if (obfuscate_all_files):
            obfuscate_file_extensions = None
        else:
            if "," in extensions:
                obfuscate_file_extensions = extensions.split(",")
            else:
                obfuscate_file_extensions = [extensions]
        newd = inputfolder+"_Obfuscated"
        shutil.copytree(inputfolder, newd)
        inputfolder = newd
        if (os.path.isdir(inputfolder)):
            for file in GeneralUtilities.absolute_file_paths(inputfolder):
                if obfuscate_all_files or self.__extension_matchs(file, obfuscate_file_extensions):
                    self.SCChangeHashOfProgram(file)
                    os.remove(file)
                    os.rename(file + ".modified", file)
            self.SCFilenameObfuscator(inputfolder, printtableheadline, namemappingfile, extensions)
        else:
            raise ValueError(f"Directory not found: '{inputfolder}'")

    @GeneralUtilities.check_arguments
    def get_services_from_yaml_file(self, yaml_file: str) -> list[str]:
        with open(yaml_file, encoding="utf-8") as stream:
            loaded = yaml.safe_load(stream)
            services = loaded["services"]
            result = list(services.keys())
            return result

    @GeneralUtilities.check_arguments
    def kill_docker_container(self, container_name: str) -> None:
        self.run_program("docker", f"container rm -f {container_name}")

    @GeneralUtilities.check_arguments
    def get_docker_debian_version(self, image_tag: str) -> str:
        result = ScriptCollectionCore().run_program_argsasarray("docker", ['run', f'debian:{image_tag}', 'bash', '-c', 'apt-get -y update && apt-get -y install lsb-release && lsb_release -cs'])
        result_line = GeneralUtilities.string_to_lines(result[1])[-1]
        return result_line

    @GeneralUtilities.check_arguments
    def get_latest_tor_version_of_debian_repository(self, debian_version: str) -> str:
        package_url: str = f"https://deb.torproject.org/torproject.org/dists/{debian_version}/main/binary-amd64/Packages"
        headers = {'Cache-Control': 'no-cache'}
        r = requests.get(package_url, timeout=5, headers=headers)
        if r.status_code != 200:
            raise ValueError(f"Checking for latest tor package resulted in HTTP-response-code {r.status_code}.")
        lines = GeneralUtilities.string_to_lines(GeneralUtilities.bytes_to_string(r.content))
        version_line_prefix = "Version: "
        version_content_line = [line for line in lines if line.startswith(version_line_prefix)][1]
        version_with_overhead = version_content_line[len(version_line_prefix):]
        tor_version = version_with_overhead.split("~")[0]
        return tor_version

    def run_testcases_for_python_project(self, repository_folder: str):
        self.assert_is_git_repository(repository_folder)
        self.run_program("coverage", "run -m pytest", repository_folder)
        self.run_program("coverage", "xml", repository_folder)
        GeneralUtilities.ensure_directory_exists(os.path.join(repository_folder, "Other/TestCoverage"))
        coveragefile = os.path.join(repository_folder, "Other/TestCoverage/TestCoverage.xml")
        GeneralUtilities.ensure_file_does_not_exist(coveragefile)
        os.rename(os.path.join(repository_folder, "coverage.xml"), coveragefile)

    @GeneralUtilities.check_arguments
    def get_file_permission(self, file: str) -> str:
        """This function returns an usual octet-triple, for example "700"."""
        ls_output: str = self.run_ls_for_folder(file)
        return self.__get_file_permission_helper(ls_output)

    @GeneralUtilities.check_arguments
    def __get_file_permission_helper(self, permissions: str) -> str:
        return str(self.__to_octet(permissions[0:3])) + str(self.__to_octet(permissions[3:6]))+str(self.__to_octet(permissions[6:9]))

    @GeneralUtilities.check_arguments
    def __to_octet(self, string: str) -> int:
        return int(self.__to_octet_helper(string[0]) + self.__to_octet_helper(string[1])+self.__to_octet_helper(string[2]), 2)

    @GeneralUtilities.check_arguments
    def __to_octet_helper(self, string: str) -> str:
        if (string == "-"):
            return "0"
        else:
            return "1"

    @GeneralUtilities.check_arguments
    def get_file_owner(self, file: str) -> str:
        """This function returns the user and the group in the format "user:group"."""
        ls_output: str = self.run_ls_for_folder(file)
        return self.__get_file_owner_helper(ls_output)

    @GeneralUtilities.check_arguments
    def __get_file_owner_helper(self, ls_output: str) -> str:
        splitted = ls_output.split()
        return f"{splitted[2]}:{splitted[3]}"

    @GeneralUtilities.check_arguments
    def get_file_owner_and_file_permission(self, file: str) -> str:
        ls_output: str = self.run_ls_for_folder(file)
        return [self.__get_file_owner_helper(ls_output), self.__get_file_permission_helper(ls_output)]

    @GeneralUtilities.check_arguments
    def run_ls_for_folder(self, file_or_folder: str) -> str:
        file_or_folder = file_or_folder.replace("\\", "/")
        GeneralUtilities.assert_condition(os.path.isfile(file_or_folder) or os.path.isdir(file_or_folder), f"Can not execute 'ls -ld' because '{file_or_folder}' does not exist.")
        ls_result = self.run_program_argsasarray("ls", ["-ld", file_or_folder])
        GeneralUtilities.assert_condition(ls_result[0] == 0, f"'ls -ld {file_or_folder}' resulted in exitcode {str(ls_result[0])}. StdErr: {ls_result[2]}")
        GeneralUtilities.assert_condition(not GeneralUtilities.string_is_none_or_whitespace(ls_result[1]), f"'ls -ld' of '{file_or_folder}' had an empty output. StdErr: '{ls_result[2]}'")
        output = ls_result[1]
        result = output.replace("\n", GeneralUtilities.empty_string)
        result = ' '.join(result.split())   # reduce multiple whitespaces to one
        return result

    @GeneralUtilities.check_arguments
    def run_ls_for_folder_content(self, file_or_folder: str) -> list[str]:
        file_or_folder = file_or_folder.replace("\\", "/")
        GeneralUtilities.assert_condition(os.path.isfile(file_or_folder) or os.path.isdir(file_or_folder), f"Can not execute 'ls -la' because '{file_or_folder}' does not exist.")
        ls_result = self.run_program_argsasarray("ls", ["-la", file_or_folder])
        GeneralUtilities.assert_condition(ls_result[0] == 0, f"'ls -la {file_or_folder}' resulted in exitcode {str(ls_result[0])}. StdErr: {ls_result[2]}")
        GeneralUtilities.assert_condition(not GeneralUtilities.string_is_none_or_whitespace(ls_result[1]), f"'ls -la' of '{file_or_folder}' had an empty output. StdErr: '{ls_result[2]}'")
        output = ls_result[1]
        result = output.split("\n")[3:]  # skip the lines with "Total", "." and ".."
        result = [' '.join(line.split()) for line in result]  # reduce multiple whitespaces to one
        return result

    @GeneralUtilities.check_arguments
    def set_permission(self, file_or_folder: str, permissions: str, recursive: bool = False) -> None:
        """This function expects an usual octet-triple, for example "700"."""
        args = []
        if recursive:
            args.append("--recursive")
        args.append(permissions)
        args.append(file_or_folder)
        self.run_program_argsasarray("chmod", args)

    @GeneralUtilities.check_arguments
    def set_owner(self, file_or_folder: str, owner: str, recursive: bool = False, follow_symlinks: bool = False) -> None:
        """This function expects the user and the group in the format "user:group"."""
        args = []
        if recursive:
            args.append("--recursive")
        if follow_symlinks:
            args.append("--no-dereference")
        args.append(owner)
        args.append(file_or_folder)
        self.run_program_argsasarray("chown", args)

    # <run programs>

    @GeneralUtilities.check_arguments
    def __run_program_argsasarray_async_helper(self, program: str, arguments_as_array: list[str] = [], working_directory: str = None, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, custom_argument: object = None, interactive: bool = False) -> Popen:
        popen: Popen = self.program_runner.run_program_argsasarray_async_helper(program, arguments_as_array, working_directory, custom_argument, interactive)
        return popen

    @staticmethod
    def __enqueue_output(file: IO, queue: Queue):
        for line in iter(file.readline, ''):
            queue.put(line)
        file.close()

    @staticmethod
    def __continue_process_reading(pid: int, p: Popen, q_stdout: Queue, q_stderr: Queue, reading_stdout_last_time_resulted_in_exception: bool, reading_stderr_last_time_resulted_in_exception: bool):
        if p.poll() is None:
            return True

        # if reading_stdout_last_time_resulted_in_exception and reading_stderr_last_time_resulted_in_exception:
        #    return False

        if not q_stdout.empty():
            return True

        if not q_stderr.empty():
            return True

        return False

    @staticmethod
    def __read_popen_pipes(p: Popen, print_live_output: bool, print_errors_as_information: bool, log: SCLog) -> tuple[list[str], list[str]]:
        p_id = p.pid
        with ThreadPoolExecutor(2) as pool:
            q_stdout = Queue()
            q_stderr = Queue()

            pool.submit(ScriptCollectionCore.__enqueue_output, p.stdout, q_stdout)
            pool.submit(ScriptCollectionCore.__enqueue_output, p.stderr, q_stderr)
            reading_stdout_last_time_resulted_in_exception: bool = False
            reading_stderr_last_time_resulted_in_exception: bool = False

            stdout_result: list[str] = []
            stderr_result: list[str] = []

            while (ScriptCollectionCore.__continue_process_reading(p_id, p, q_stdout, q_stderr, reading_stdout_last_time_resulted_in_exception, reading_stderr_last_time_resulted_in_exception)):
                try:
                    while not q_stdout.empty():
                        out_line: str = q_stdout.get_nowait()
                        out_line = out_line.replace("\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string)
                        if GeneralUtilities.string_has_content(out_line):
                            stdout_result.append(out_line)
                            reading_stdout_last_time_resulted_in_exception = False
                            if print_live_output:
                                loglevel = LogLevel.Information
                                if out_line.startswith("Debug: "):
                                    loglevel = LogLevel.Debug
                                    out_line = out_line[len("Debug: "):]
                                if out_line.startswith("Diagnostic: "):
                                    loglevel = LogLevel.Diagnostic
                                    out_line = out_line[len("Diagnostic: "):]
                                log.log(out_line, loglevel)
                except Empty:
                    reading_stdout_last_time_resulted_in_exception = True

                try:
                    while not q_stderr.empty():
                        err_line: str = q_stderr.get_nowait()
                        err_line = err_line.replace("\r", GeneralUtilities.empty_string).replace("\n", GeneralUtilities.empty_string)
                        if GeneralUtilities.string_has_content(err_line):
                            stderr_result.append(err_line)
                            reading_stderr_last_time_resulted_in_exception = False
                            if print_live_output:
                                loglevel = LogLevel.Error
                                if err_line.startswith("Warning: "):
                                    loglevel = LogLevel.Warning
                                    err_line = err_line[len("Warning: "):]
                                if print_errors_as_information:  # "errors" in "print_errors_as_information" means: all what is written to std-err
                                    loglevel = LogLevel.Information
                                log.log(err_line, loglevel)
                except Empty:
                    reading_stderr_last_time_resulted_in_exception = True

                time.sleep(0.01)  # this is required to not finish too early

            return (stdout_result, stderr_result)

    @GeneralUtilities.check_arguments
    def run_program_argsasarray(self, program: str, arguments_as_array: list[str] = [], working_directory: str = None, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, throw_exception_if_exitcode_is_not_zero: bool = True, custom_argument: object = None, interactive: bool = False, print_live_output: bool = False) -> tuple[int, str, str, int]:
        if self.call_program_runner_directly:
            return self.program_runner.run_program_argsasarray(program, arguments_as_array, working_directory, custom_argument, interactive)
        try:
            arguments_as_str = ' '.join(arguments_as_array)
            mock_loader_result = self.__try_load_mock(program, arguments_as_str, working_directory)
            if mock_loader_result[0]:
                return mock_loader_result[1]

            working_directory = self.__adapt_workingdirectory(working_directory)

            if arguments_for_log is None:
                arguments_for_log = arguments_as_array

            cmd = f'{working_directory}>{program}'
            if 0 < len(arguments_for_log):
                arguments_for_log_as_string: str = ' '.join([f'"{argument_for_log}"' for argument_for_log in arguments_for_log])
                cmd = f'{cmd} {arguments_for_log_as_string}'

            if GeneralUtilities.string_is_none_or_whitespace(title):
                info_for_log = cmd
            else:
                info_for_log = title

            self.log.log(f"Run '{info_for_log}'.", LogLevel.Debug)

            exit_code: int = None
            stdout: str = GeneralUtilities.empty_string
            stderr: str = GeneralUtilities.empty_string
            pid: int = None

            with self.__run_program_argsasarray_async_helper(program, arguments_as_array, working_directory,  print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, custom_argument, interactive) as process:

                if log_file is not None:
                    GeneralUtilities.ensure_file_exists(log_file)
                pid = process.pid

                outputs: tuple[list[str], list[str]] = ScriptCollectionCore.__read_popen_pipes(process, print_live_output, print_errors_as_information, self.log)

                for out_line_plain in outputs[0]:
                    if out_line_plain is not None:
                        out_line: str = None
                        if isinstance(out_line_plain, str):
                            out_line = out_line_plain
                        elif isinstance(out_line_plain, bytes):
                            out_line = GeneralUtilities.bytes_to_string(out_line_plain)
                        else:
                            raise ValueError(f"Unknown type of output: {str(type(out_line_plain))}")

                        if out_line is not None and GeneralUtilities.string_has_content(out_line):
                            if out_line.endswith("\n"):
                                out_line = out_line[:-1]
                            if 0 < len(stdout):
                                stdout = stdout+"\n"
                            stdout = stdout+out_line
                            if log_file is not None:
                                GeneralUtilities.append_line_to_file(log_file, out_line)

                for err_line_plain in outputs[1]:
                    if err_line_plain is not None:
                        err_line: str = None
                        if isinstance(err_line_plain, str):
                            err_line = err_line_plain
                        elif isinstance(err_line_plain, bytes):
                            err_line = GeneralUtilities.bytes_to_string(err_line_plain)
                        else:
                            raise ValueError(f"Unknown type of output: {str(type(err_line_plain))}")
                        if err_line is not None and GeneralUtilities.string_has_content(err_line):
                            if err_line.endswith("\n"):
                                err_line = err_line[:-1]
                            if 0 < len(stderr):
                                stderr = stderr+"\n"
                            stderr = stderr+err_line
                            if log_file is not None:
                                GeneralUtilities.append_line_to_file(log_file, err_line)

            exit_code = process.returncode
            GeneralUtilities.assert_condition(exit_code is not None, f"Exitcode of program-run of '{info_for_log}' is None.")

            result_message = f"Program '{info_for_log}' resulted in exitcode {exit_code}."

            self.log.log(result_message, LogLevel.Debug)

            if throw_exception_if_exitcode_is_not_zero and exit_code != 0:
                raise ValueError(f"{result_message} (StdOut: '{stdout}', StdErr: '{stderr}')")

            result = (exit_code, stdout, stderr, pid)
            return result
        except Exception as e:#pylint:disable=unused-variable, try-except-raise
            raise

    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @GeneralUtilities.check_arguments
    def run_program_with_retry(self, program: str, arguments:  str = "", working_directory: str = None,  print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, throw_exception_if_exitcode_is_not_zero: bool = True, custom_argument: object = None, interactive: bool = False, print_live_output: bool = False, amount_of_attempts: int = 5) -> tuple[int, str, str, int]:
        return GeneralUtilities.retry_action(lambda: self.run_program(program, arguments, working_directory,  print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, throw_exception_if_exitcode_is_not_zero, custom_argument, interactive, print_live_output), amount_of_attempts)

    # Return-values program_runner: Exitcode, StdOut, StdErr, Pid
    @GeneralUtilities.check_arguments
    def run_program(self, program: str, arguments:  str = "", working_directory: str = None,  print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, throw_exception_if_exitcode_is_not_zero: bool = True, custom_argument: object = None, interactive: bool = False, print_live_output: bool = False) -> tuple[int, str, str, int]:
        if self.call_program_runner_directly:
            return self.program_runner.run_program(program, arguments, working_directory, custom_argument, interactive)
        return self.run_program_argsasarray(program, GeneralUtilities.arguments_to_array(arguments), working_directory,  print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, throw_exception_if_exitcode_is_not_zero, custom_argument, interactive, print_live_output)

    # Return-values program_runner: Pid
    @GeneralUtilities.check_arguments
    def run_program_argsasarray_async(self, program: str, arguments_as_array: list[str] = [], working_directory: str = None,  print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, custom_argument: object = None, interactive: bool = False) -> int:
        if self.call_program_runner_directly:
            return self.program_runner.run_program_argsasarray_async(program, arguments_as_array, working_directory, custom_argument, interactive)
        mock_loader_result = self.__try_load_mock(program, ' '.join(arguments_as_array), working_directory)
        if mock_loader_result[0]:
            return mock_loader_result[1]
        process: Popen = self.__run_program_argsasarray_async_helper(program, arguments_as_array, working_directory,  print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, custom_argument, interactive)
        return process.pid

    # Return-values program_runner: Pid
    @GeneralUtilities.check_arguments
    def run_program_async(self, program: str, arguments: str = "",  working_directory: str = None,print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, custom_argument: object = None, interactive: bool = False) -> int:
        if self.call_program_runner_directly:
            return self.program_runner.run_program_argsasarray_async(program, arguments, working_directory, custom_argument, interactive)
        return self.run_program_argsasarray_async(program, GeneralUtilities.arguments_to_array(arguments), working_directory,  print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, custom_argument, interactive)

    @GeneralUtilities.check_arguments
    def __try_load_mock(self, program: str, arguments: str, working_directory: str) -> tuple[bool, tuple[int, str, str, int]]:
        if self.mock_program_calls:
            try:
                return [True, self.__get_mock_program_call(program, arguments, working_directory)]
            except LookupError:
                if not self.execute_program_really_if_no_mock_call_is_defined:
                    raise
        return [False, None]

    @GeneralUtilities.check_arguments
    def __adapt_workingdirectory(self, workingdirectory: str) -> str:
        result: str = None
        if workingdirectory is None:
            result = os.getcwd()
        else:
            if os.path.isabs(workingdirectory):
                result = workingdirectory
            else:
                result = GeneralUtilities.resolve_relative_path_from_current_working_directory(workingdirectory)
        if not os.path.isdir(result):
            raise ValueError(f"Working-directory '{workingdirectory}' does not exist.")
        return result

    @GeneralUtilities.check_arguments
    def verify_no_pending_mock_program_calls(self):
        if (len(self.__mocked_program_calls) > 0):
            raise AssertionError("The following mock-calls were not called:\n"+",\n    ".join([self.__format_mock_program_call(r) for r in self.__mocked_program_calls]))

    @GeneralUtilities.check_arguments
    def __format_mock_program_call(self, r) -> str:
        r: ScriptCollectionCore.__MockProgramCall = r
        return f"'{r.workingdirectory}>{r.program} {r.argument}' (" \
            f"exitcode: {GeneralUtilities.str_none_safe(str(r.exit_code))}, " \
            f"pid: {GeneralUtilities.str_none_safe(str(r.pid))}, "\
            f"stdout: {GeneralUtilities.str_none_safe(str(r.stdout))}, " \
            f"stderr: {GeneralUtilities.str_none_safe(str(r.stderr))})"

    @GeneralUtilities.check_arguments
    def register_mock_program_call(self, program: str, argument: str, workingdirectory: str, result_exit_code: int, result_stdout: str, result_stderr: str, result_pid: int, amount_of_expected_calls=1):
        "This function is for test-purposes only"
        for _ in itertools.repeat(None, amount_of_expected_calls):
            mock_call = ScriptCollectionCore.__MockProgramCall()
            mock_call.program = program
            mock_call.argument = argument
            mock_call.workingdirectory = workingdirectory
            mock_call.exit_code = result_exit_code
            mock_call.stdout = result_stdout
            mock_call.stderr = result_stderr
            mock_call.pid = result_pid
            self.__mocked_program_calls.append(mock_call)

    @GeneralUtilities.check_arguments
    def __get_mock_program_call(self, program: str, argument: str, workingdirectory: str):
        result: ScriptCollectionCore.__MockProgramCall = None
        for mock_call in self.__mocked_program_calls:
            if ((re.match(mock_call.program, program) is not None)
               and (re.match(mock_call.argument, argument) is not None)
               and (re.match(mock_call.workingdirectory, workingdirectory) is not None)):
                result = mock_call
                break
        if result is None:
            raise LookupError(f"Tried to execute mock-call '{workingdirectory}>{program} {argument}' but no mock-call was defined for that execution")
        else:
            self.__mocked_program_calls.remove(result)
            return (result.exit_code, result.stdout, result.stderr, result.pid)

    @GeneralUtilities.check_arguments
    class __MockProgramCall:
        program: str
        argument: str
        workingdirectory: str
        exit_code: int
        stdout: str
        stderr: str
        pid: int

    @GeneralUtilities.check_arguments
    def run_with_epew(self, program: str, argument: str = "", working_directory: str = None, print_errors_as_information: bool = False, log_file: str = None, timeoutInSeconds: int = 600, addLogOverhead: bool = False, title: str = None, log_namespace: str = "", arguments_for_log:  list[str] = None, throw_exception_if_exitcode_is_not_zero: bool = True, custom_argument: object = None, interactive: bool = False,print_live_output:bool=False,encode_argument_in_base64:bool=False) -> tuple[int, str, str, int]:
        epew_argument=["-p",program ,"-w", working_directory]
        if encode_argument_in_base64:
            if arguments_for_log is None:
                arguments_for_log=epew_argument+["-a",f"\"{argument}\""]
            base64_string = base64.b64encode(argument.encode("utf-8")).decode("utf-8")
            epew_argument=epew_argument+["-a",base64_string,"-b"]
        else:
            epew_argument=epew_argument+["-a",argument]
            if arguments_for_log is None:
                arguments_for_log=epew_argument
        return self.run_program_argsasarray("epew", epew_argument, working_directory, print_errors_as_information, log_file, timeoutInSeconds, addLogOverhead, title, log_namespace, arguments_for_log, throw_exception_if_exitcode_is_not_zero, custom_argument, interactive,print_live_output=print_live_output)


    # </run programs>

    @GeneralUtilities.check_arguments
    def extract_archive_with_7z(self, unzip_program_file: str, zip_file: str, password: str, output_directory: str) -> None:
        password_set = not password is None
        file_name = Path(zip_file).name
        file_folder = os.path.dirname(zip_file)
        argument = "x"
        if password_set:
            argument = f"{argument} -p\"{password}\""
        argument = f"{argument} -o {output_directory}"
        argument = f"{argument} {file_name}"
        return self.run_program(unzip_program_file, argument, file_folder)

    @GeneralUtilities.check_arguments
    def get_internet_time(self) -> datetime:
        response = ntplib.NTPClient().request('pool.ntp.org')
        return datetime.fromtimestamp(response.tx_time)

    @GeneralUtilities.check_arguments
    def system_time_equals_internet_time(self, maximal_tolerance_difference: timedelta) -> bool:
        return abs(GeneralUtilities.get_now() - self.get_internet_time()) < maximal_tolerance_difference

    @GeneralUtilities.check_arguments
    def system_time_equals_internet_time_with_default_tolerance(self) -> bool:
        return self.system_time_equals_internet_time(self.__get_default_tolerance_for_system_time_equals_internet_time())

    @GeneralUtilities.check_arguments
    def check_system_time(self, maximal_tolerance_difference: timedelta):
        if not self.system_time_equals_internet_time(maximal_tolerance_difference):
            raise ValueError("System time may be wrong")

    @GeneralUtilities.check_arguments
    def check_system_time_with_default_tolerance(self) -> None:
        self.check_system_time(self.__get_default_tolerance_for_system_time_equals_internet_time())

    @GeneralUtilities.check_arguments
    def __get_default_tolerance_for_system_time_equals_internet_time(self) -> timedelta:
        return timedelta(hours=0, minutes=0, seconds=3)

    @GeneralUtilities.check_arguments
    def increment_version(self, input_version: str, increment_major: bool, increment_minor: bool, increment_patch: bool) -> str:
        splitted = input_version.split(".")
        GeneralUtilities.assert_condition(len(splitted) == 3, f"Version '{input_version}' does not have the 'major.minor.patch'-pattern.")
        major = int(splitted[0])
        minor = int(splitted[1])
        patch = int(splitted[2])
        if increment_major:
            major = major+1
        if increment_minor:
            minor = minor+1
        if increment_patch:
            patch = patch+1
        return f"{major}.{minor}.{patch}"

    @GeneralUtilities.check_arguments
    def get_semver_version_from_gitversion(self, repository_folder: str) -> str:
        self.assert_is_git_repository(repository_folder)
        if (self.git_repository_has_commits(repository_folder)):
            result = self.get_version_from_gitversion(repository_folder, "MajorMinorPatch")
            if self.git_repository_has_uncommitted_changes(repository_folder):
                if self.get_current_git_branch_has_tag(repository_folder):
                    id_of_latest_tag = self.git_get_commitid_of_tag(repository_folder, self.get_latest_git_tag(repository_folder))
                    current_commit = self.git_get_commit_id(repository_folder)
                    current_commit_is_on_latest_tag = id_of_latest_tag == current_commit
                    if current_commit_is_on_latest_tag:
                        result = self.increment_version(result, False, False, True)
        else:
            result = "0.1.0"
        return result

    @staticmethod
    @GeneralUtilities.check_arguments
    def is_patch_version(version_string: str) -> bool:
        return not version_string.endswith(".0")

    @GeneralUtilities.check_arguments
    def get_version_from_gitversion(self, folder: str, variable: str) -> str:
        # called twice as workaround for issue 1877 in gitversion ( https://github.com/GitTools/GitVersion/issues/1877 )
        result = self.run_program_argsasarray("gitversion", ["/showVariable", variable], folder)
        result = self.run_program_argsasarray("gitversion", ["/showVariable", variable], folder)
        result = GeneralUtilities.strip_new_line_character(result[1])

        return result

    @GeneralUtilities.check_arguments
    def generate_certificate_authority(self, folder: str, name: str, subj_c: str, subj_st: str, subj_l: str, subj_o: str, subj_ou: str, days_until_expire: int = None, password: str = None) -> None:
        if days_until_expire is None:
            days_until_expire = 1825
        if password is None:
            password = GeneralUtilities.generate_password()
        GeneralUtilities.ensure_directory_exists(folder)
        self.run_program_argsasarray("openssl", ['req', '-new', '-newkey', 'ec', '-pkeyopt', 'ec_paramgen_curve:prime256v1', '-days', str(days_until_expire), '-nodes', '-x509', '-subj', f'/C={subj_c}/ST={subj_st}/L={subj_l}/O={subj_o}/CN={name}/OU={subj_ou}', '-passout', f'pass:{password}', '-keyout', f'{name}.key', '-out', f'{name}.crt'], folder)

    @GeneralUtilities.check_arguments
    def generate_certificate(self, folder: str,  domain: str, filename: str, subj_c: str, subj_st: str, subj_l: str, subj_o: str, subj_ou: str, days_until_expire: int = None, password: str = None) -> None:
        if days_until_expire is None:
            days_until_expire = 397
        if password is None:
            password = GeneralUtilities.generate_password()
        rsa_key_length = 4096
        self.run_program_argsasarray("openssl", ['genrsa', '-out', f'{filename}.key', f'{rsa_key_length}'], folder)
        self.run_program_argsasarray("openssl", ['req', '-new', '-subj', f'/C={subj_c}/ST={subj_st}/L={subj_l}/O={subj_o}/CN={domain}/OU={subj_ou}', '-x509', '-key', f'{filename}.key', '-out', f'{filename}.unsigned.crt', '-days', f'{days_until_expire}'], folder)
        self.run_program_argsasarray("openssl", ['pkcs12', '-export', '-out', f'{filename}.selfsigned.pfx', '-password', f'pass:{password}', '-inkey', f'{filename}.key', '-in', f'{filename}.unsigned.crt'], folder)
        GeneralUtilities.write_text_to_file(os.path.join(folder, f"{filename}.password"), password)
        GeneralUtilities.write_text_to_file(os.path.join(folder, f"{filename}.san.conf"), f"""[ req ]
default_bits        = {rsa_key_length}
distinguished_name  = req_distinguished_name
req_extensions      = v3_req
default_md          = sha256
dirstring_type      = nombstr
prompt              = no

[ req_distinguished_name ]
countryName         = {subj_c}
stateOrProvinceName = {subj_st}
localityName        = {subj_l}
organizationName    = {subj_o}
organizationUnit    = {subj_ou}
commonName          = {domain}

[v3_req]
subjectAltName      = @subject_alt_name

[ subject_alt_name ]
DNS                 = {domain}
""")

    @GeneralUtilities.check_arguments
    def generate_certificate_sign_request(self, folder: str, domain: str, filename: str, subj_c: str, subj_st: str, subj_l: str, subj_o: str, subj_ou: str) -> None:
        self.run_program_argsasarray("openssl", ['req', '-new', '-subj', f'/C={subj_c}/ST={subj_st}/L={subj_l}/O={subj_o}/CN={domain}/OU={subj_ou}', '-key', f'{filename}.key', f'-out', f'{filename}.csr', f'-config', f'{filename}.san.conf'], folder)

    @GeneralUtilities.check_arguments
    def sign_certificate(self, folder: str, ca_folder: str, ca_name: str, domain: str, filename: str, days_until_expire: int = None) -> None:
        if days_until_expire is None:
            days_until_expire = 397
        ca = os.path.join(ca_folder, ca_name)
        password_file = os.path.join(folder, f"{filename}.password")
        password = GeneralUtilities.read_text_from_file(password_file)
        self.run_program_argsasarray("openssl", ['x509', '-req', '-in', f'{filename}.csr', '-CA', f'{ca}.crt', '-CAkey', f'{ca}.key', '-CAcreateserial', '-CAserial', f'{ca}.srl', '-out', f'{filename}.crt', '-days', str(days_until_expire),  '-sha256', '-extensions', 'v3_req', '-extfile', f'{filename}.san.conf'], folder)
        self.run_program_argsasarray("openssl", ['pkcs12', '-export', '-out', f'{filename}.pfx', f'-inkey', f'{filename}.key', '-in', f'{filename}.crt', '-password', f'pass:{password}'], folder)

    @GeneralUtilities.check_arguments
    def update_dependencies_of_python_in_requirementstxt_file(self, file: str, ignored_dependencies: list[str]):
        # TODO consider ignored_dependencies
        lines = GeneralUtilities.read_lines_from_file(file)
        new_lines = []
        for line in lines:
            if GeneralUtilities.string_has_content(line):
                new_lines.append(self.__get_updated_line_for_python_requirements(line.strip()))
        GeneralUtilities.write_lines_to_file(file, new_lines)

    @GeneralUtilities.check_arguments
    def __get_updated_line_for_python_requirements(self, line: str) -> str:
        if "==" in line or "<" in line:
            return line
        elif ">" in line:
            try:
                # line is something like "cyclonedx-bom>=2.0.2" and the function must return with the updated version
                # (something like "cyclonedx-bom>=2.11.0" for example)
                package = line.split(">")[0]
                operator = ">=" if ">=" in line else ">"
                headers = {'Cache-Control': 'no-cache'}
                response = requests.get(f'https://pypi.org/pypi/{package}/json', timeout=5, headers=headers)
                latest_version = response.json()['info']['version']
                # TODO update only minor- and patch-version
                # TODO print info if there is a new major-version
                return package+operator+latest_version
            except:
                return line
        else:
            raise ValueError(f'Unexpected line in requirements-file: "{line}"')

    @GeneralUtilities.check_arguments
    def update_dependencies_of_python_in_setupcfg_file(self, setup_cfg_file: str, ignored_dependencies: list[str]):
        # TODO consider ignored_dependencies
        lines = GeneralUtilities.read_lines_from_file(setup_cfg_file)
        new_lines = []
        requirement_parsing_mode = False
        for line in lines:
            new_line = line
            if (requirement_parsing_mode):
                if ("<" in line or "=" in line or ">" in line):
                    updated_line = f"    {self.__get_updated_line_for_python_requirements(line.strip())}"
                    new_line = updated_line
                else:
                    requirement_parsing_mode = False
            else:
                if line.startswith("install_requires ="):
                    requirement_parsing_mode = True
            new_lines.append(new_line)
        GeneralUtilities.write_lines_to_file(setup_cfg_file, new_lines)

    @GeneralUtilities.check_arguments
    def update_dependencies_of_dotnet_project(self, csproj_file: str,  ignored_dependencies: list[str]):
        folder = os.path.dirname(csproj_file)
        csproj_filename = os.path.basename(csproj_file)
        self.log.log(f"Check for updates in {csproj_filename}", LogLevel.Information)
        result = self.run_program_with_retry("dotnet", f"list {csproj_filename} package --outdated", folder, print_errors_as_information=True)
        for line in result[1].replace("\r", GeneralUtilities.empty_string).split("\n"):
            # Relevant output-lines are something like "    > NJsonSchema             10.7.0        10.7.0      10.9.0"
            if ">" in line:
                package_name = line.replace(">", GeneralUtilities.empty_string).strip().split(" ")[0]
                if not (package_name in ignored_dependencies):
                    self.log.log(f"Update package {package_name}...", LogLevel.Debug)
                    time.sleep(1.1)  # attempt to prevent rate-limit
                    self.run_program_with_retry("dotnet", f"add {csproj_filename} package {package_name}", folder, print_errors_as_information=True)

    @GeneralUtilities.check_arguments
    def create_deb_package(self, toolname: str, binary_folder: str, control_file_content: str, deb_output_folder: str, permission_of_executable_file_as_octet_triple: int) -> None:

        # prepare
        GeneralUtilities.ensure_directory_exists(deb_output_folder)
        temp_folder = os.path.join(tempfile.gettempdir(), str(uuid.uuid4()))
        GeneralUtilities.ensure_directory_exists(temp_folder)
        bin_folder = binary_folder
        tool_content_folder_name = toolname+"Content"

        # create folder
        GeneralUtilities.ensure_directory_exists(temp_folder)
        control_content_folder_name = "controlcontent"
        packagecontent_control_folder = os.path.join(temp_folder, control_content_folder_name)
        GeneralUtilities.ensure_directory_exists(packagecontent_control_folder)
        data_content_folder_name = "datacontent"
        packagecontent_data_folder = os.path.join(temp_folder, data_content_folder_name)
        GeneralUtilities.ensure_directory_exists(packagecontent_data_folder)
        entireresult_content_folder_name = "entireresultcontent"
        packagecontent_entireresult_folder = os.path.join(temp_folder, entireresult_content_folder_name)
        GeneralUtilities.ensure_directory_exists(packagecontent_entireresult_folder)

        # create "debian-binary"-file
        debianbinary_file = os.path.join(packagecontent_entireresult_folder, "debian-binary")
        GeneralUtilities.ensure_file_exists(debianbinary_file)
        GeneralUtilities.write_text_to_file(debianbinary_file, "2.0\n")

        # create control-content

        #  conffiles
        conffiles_file = os.path.join(packagecontent_control_folder, "conffiles")
        GeneralUtilities.ensure_file_exists(conffiles_file)

        #  postinst-script
        postinst_file = os.path.join(packagecontent_control_folder, "postinst")
        GeneralUtilities.ensure_file_exists(postinst_file)
        exe_file = f"/usr/bin/{tool_content_folder_name}/{toolname}"
        link_file = f"/usr/bin/{toolname.lower()}"
        permission = str(permission_of_executable_file_as_octet_triple)
        GeneralUtilities.write_text_to_file(postinst_file, f"""#!/bin/sh
ln -s {exe_file} {link_file}
chmod {permission} {exe_file}
chmod {permission} {link_file}
""")

        #  control
        control_file = os.path.join(packagecontent_control_folder, "control")
        GeneralUtilities.ensure_file_exists(control_file)
        GeneralUtilities.write_text_to_file(control_file, control_file_content)

        #  md5sums
        md5sums_file = os.path.join(packagecontent_control_folder, "md5sums")
        GeneralUtilities.ensure_file_exists(md5sums_file)

        # create data-content

        #  copy binaries
        usr_bin_folder = os.path.join(packagecontent_data_folder, "usr/bin")
        GeneralUtilities.ensure_directory_exists(usr_bin_folder)
        usr_bin_content_folder = os.path.join(usr_bin_folder, tool_content_folder_name)
        GeneralUtilities.copy_content_of_folder(bin_folder, usr_bin_content_folder)

        # create debfile
        deb_filename = f"{toolname}.deb"
        self.run_program_argsasarray("tar", ["czf", f"../{entireresult_content_folder_name}/control.tar.gz", "*"], packagecontent_control_folder)
        self.run_program_argsasarray("tar", ["czf", f"../{entireresult_content_folder_name}/data.tar.gz", "*"], packagecontent_data_folder)
        self.run_program_argsasarray("ar", ["r", deb_filename, "debian-binary", "control.tar.gz", "data.tar.gz"], packagecontent_entireresult_folder)
        result_file = os.path.join(packagecontent_entireresult_folder, deb_filename)
        shutil.copy(result_file, os.path.join(deb_output_folder, deb_filename))

        # cleanup
        GeneralUtilities.ensure_directory_does_not_exist(temp_folder)

    @GeneralUtilities.check_arguments
    def update_year_in_copyright_tags(self, file: str) -> None:
        current_year = str(GeneralUtilities.get_now().year)
        lines = GeneralUtilities.read_lines_from_file(file)
        lines_result = []
        for line in lines:
            if match := re.search("(.*<[Cc]opyright>.*)\\d\\d\\d\\d(.*<\\/[Cc]opyright>.*)", line):
                part1 = match.group(1)
                part2 = match.group(2)
                adapted = part1+current_year+part2
            else:
                adapted = line
            lines_result.append(adapted)
        GeneralUtilities.write_lines_to_file(file, lines_result)

    @GeneralUtilities.check_arguments
    def update_year_in_first_line_of_file(self, file: str) -> None:
        current_year = str(GeneralUtilities.get_now().year)
        lines = GeneralUtilities.read_lines_from_file(file)
        lines[0] = re.sub("\\d\\d\\d\\d", current_year, lines[0])
        GeneralUtilities.write_lines_to_file(file, lines)

    @GeneralUtilities.check_arguments
    def get_external_ip(self) -> str:
        information = self.get_externalnetworkinformation_as_json_string()
        parsed = json.loads(information)
        return parsed.IPAddress

    @GeneralUtilities.check_arguments
    def get_country_of_external_ip(self) -> str:
        information = self.get_externalnetworkinformation_as_json_string()
        parsed = json.loads(information)
        return parsed.Country

    @GeneralUtilities.check_arguments
    def get_externalnetworkinformation_as_json_string(self) -> str:
        headers = {'Cache-Control': 'no-cache'}
        response = requests.get('https://clientinformation.anion327.de/API/v1/ClientInformationBackendController/Information',  timeout=5, headers=headers)
        network_information_as_json_string = GeneralUtilities.bytes_to_string(response.content)
        return network_information_as_json_string

    @GeneralUtilities.check_arguments
    def change_file_extensions(self, folder: str, from_extension: str, to_extension: str, recursive: bool, ignore_case: bool) -> None:
        extension_to_compare: str = None
        if ignore_case:
            extension_to_compare = from_extension.lower()
        else:
            extension_to_compare = from_extension
        for file in GeneralUtilities.get_direct_files_of_folder(folder):
            if (ignore_case and file.lower().endswith(f".{extension_to_compare}") or not ignore_case and file.endswith(f".{extension_to_compare}")):
                p = Path(file)
                p.rename(p.with_suffix('.'+to_extension))
        if recursive:
            for subfolder in GeneralUtilities.get_direct_folders_of_folder(folder):
                self.change_file_extensions(subfolder, from_extension, to_extension, recursive, ignore_case)

    @GeneralUtilities.check_arguments
    def __add_chapter(self, main_reference_file, reference_content_folder, number: int, chaptertitle: str, content: str = None):
        if content is None:
            content = "TXDX add content here"
        filename = str(number).zfill(2)+"_"+chaptertitle.replace(' ', '-')
        file = f"{reference_content_folder}/{filename}.md"
        full_title = f"{number}. {chaptertitle}"

        GeneralUtilities.append_line_to_file(main_reference_file, f"- [{full_title}](./{filename}.md)")

        GeneralUtilities.ensure_file_exists(file)
        GeneralUtilities.write_text_to_file(file, f"""# {full_title}

{content}
""".replace("XDX", "ODO"))

    @GeneralUtilities.check_arguments
    def generate_arc42_reference_template(self, repository: str, productname: str = None, subfolder: str = None):
        productname: str
        if productname is None:
            productname = os.path.basename(repository)
        if subfolder is None:
            subfolder = "Other/Reference"
        reference_root_folder = f"{repository}/{subfolder}"
        reference_content_folder = reference_root_folder + "/Technical"
        if os.path.isdir(reference_root_folder):
            raise ValueError(f"The folder '{reference_root_folder}' does already exist.")
        GeneralUtilities.ensure_directory_exists(reference_root_folder)
        GeneralUtilities.ensure_directory_exists(reference_content_folder)
        main_reference_file = f"{reference_root_folder}/Reference.md"
        GeneralUtilities.ensure_file_exists(main_reference_file)
        GeneralUtilities.write_text_to_file(main_reference_file, f"""# {productname}

TXDX add minimal service-description here.

## Technical documentation

""".replace("XDX", "ODO"))
        self.__add_chapter(main_reference_file, reference_content_folder, 1, 'Introduction and Goals', """## Overview

TXDX

## Quality goals

TXDX

## Stakeholder

| Name | How to contact | Reason |
| ---- | -------------- | ------ |""")
        self.__add_chapter(main_reference_file, reference_content_folder, 2, 'Constraints', """## Technical constraints

| Constraint-identifier | Constraint | Reason |
| --------------------- | ---------- | ------ |

## Organizational constraints

| Constraint-identifier | Constraint | Reason |
| --------------------- | ---------- | ------ |""")
        self.__add_chapter(main_reference_file, reference_content_folder, 3, 'Context and Scope', """## Context

TXDX

## Scope

TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 4, 'Solution Strategy', """TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 5, 'Building Block View', """TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 6, 'Runtime View', """TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 7, 'Deployment View', """## Infrastructure-overview

TXDX

## Infrastructure-requirements

TXDX

## Deployment-proecsses

TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 8, 'Crosscutting Concepts', """TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 9, 'Architectural Decisions', """## Decision-board

| Decision-identifier | Date | Decision | Reason and notes |
| ------------------- | ---- | -------- | ---------------- |""")  # empty because there are no decsions yet
        self.__add_chapter(main_reference_file, reference_content_folder, 10, 'Quality Requirements', """TXDX""")
        self.__add_chapter(main_reference_file, reference_content_folder, 11, 'Risks and Technical Debt', """## Risks

Currently there are no known risks.

## Technical debts

Currently there are no technical depts.""")
        self.__add_chapter(main_reference_file, reference_content_folder, 12, 'Glossary', """## Terms

| Term | Meaning |
| ---- | ------- |

## Abbreviations

| Abbreviation | Meaning |
| ------------ | ------- |""")

        GeneralUtilities.append_to_file(main_reference_file, """

## Responsibilities

| Responsibility  | Name and contact-information |
| --------------- | ---------------------------- |
| Pdocut-owner    | TXDX                         |
| Product-manager | TXDX                         |
| Support         | TXDX                         |

## License & Pricing

TXDX

## External resources

- [Repository](TXDX)
- [Productive-System](TXDX)
- [QualityCheck-system](TXDX)
""".replace("XDX", "ODO"))

    @GeneralUtilities.check_arguments
    def run_with_timeout(self, method, timeout_in_seconds: float) -> bool:
        # Returns true if the method was terminated due to a timeout
        # Returns false if the method terminates in the given time
        p = multiprocessing.Process(target=method)
        p.start()
        p.join(timeout_in_seconds)
        if p.is_alive():
            p.kill()
            p.join()
            return True
        else:
            return False

    @GeneralUtilities.check_arguments
    def ensure_local_docker_network_exists(self, network_name: str) -> None:
        if not self.local_docker_network_exists(network_name):
            self.create_local_docker_network(network_name)

    @GeneralUtilities.check_arguments
    def ensure_local_docker_network_does_not_exist(self, network_name: str) -> None:
        if self.local_docker_network_exists(network_name):
            self.remove_local_docker_network(network_name)

    @GeneralUtilities.check_arguments
    def local_docker_network_exists(self, network_name: str) -> bool:
        return network_name in self.get_all_local_existing_docker_networks()

    @GeneralUtilities.check_arguments
    def get_all_local_existing_docker_networks(self) -> list[str]:
        program_call_result = self.run_program("docker", "network list")
        std_out = program_call_result[1]
        std_out_lines = std_out.split("\n")[1:]
        result: list[str] = []
        for std_out_line in std_out_lines:
            normalized_line = ';'.join(std_out_line.split())
            splitted = normalized_line.split(";")
            result.append(splitted[1])
        return result

    @GeneralUtilities.check_arguments
    def remove_local_docker_network(self, network_name: str) -> None:
        self.run_program("docker", f"network remove {network_name}")

    @GeneralUtilities.check_arguments
    def create_local_docker_network(self, network_name: str) -> None:
        self.run_program("docker", f"network create {network_name}")

    @GeneralUtilities.check_arguments
    def format_xml_file(self, file: str) -> None:
        encoding = "utf-8"
        element = ET.XML(GeneralUtilities.read_text_from_file(file, encoding))
        ET.indent(element)
        GeneralUtilities.write_text_to_file(file, ET.tostring(element, encoding="unicode"), encoding)

    @GeneralUtilities.check_arguments
    def install_requirementstxt_file(self, requirements_txt_file: str):
        folder: str = os.path.dirname(requirements_txt_file)
        filename: str = os.path.basename(requirements_txt_file)
        self.run_program_argsasarray("pip", ["install", "-r", filename], folder)

    @GeneralUtilities.check_arguments
    def ocr_analysis_of_folder(self, folder: str, serviceaddress: str, extensions: list[str], languages: list[str]) -> list[str]:  # Returns a list of changed files due to ocr-analysis.
        GeneralUtilities.write_message_to_stdout("Starting OCR analysis of folder " + folder)
        supported_extensions = ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif', 'pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt']
        changes_files: list[str] = []
        if extensions is None:
            extensions = supported_extensions
        for file in GeneralUtilities.get_direct_files_of_folder(folder):
            file_lower = file.lower()
            for extension in extensions:
                if file_lower.endswith("."+extension):
                    if self.ocr_analysis_of_file(file, serviceaddress, languages):
                        changes_files.append(file)
                    break
        for subfolder in GeneralUtilities.get_direct_folders_of_folder(folder):
            for file in self.ocr_analysis_of_folder(subfolder, serviceaddress, extensions, languages):
                changes_files.append(file)
        return changes_files

    @GeneralUtilities.check_arguments
    def ocr_analysis_of_file(self, file: str, serviceaddress: str, languages: list[str]) -> bool:  # Returns true if the ocr-file was generated or updated. Returns false if the existing ocr-file was not changed.
        GeneralUtilities.write_message_to_stdout("Do OCR analysis of file " + file)
        supported_extensions = ['png', 'jpg', 'jpeg', 'tiff', 'bmp', 'webp', 'gif', 'pdf', 'rtf', 'docx', 'doc', 'odt', 'xlsx', 'xls', 'ods', 'pptx', 'ppt', 'odp']
        for extension in supported_extensions:
            if file.lower().endswith("."+extension):
                raise ValueError(f"Extension '{extension}' is not supported. Supported extensions are: {', '.join(supported_extensions)}")
        target_file = file+".ocr.txt"
        hash_of_current_file: str = GeneralUtilities. get_sha256_of_file(file)
        if os.path.isfile(target_file):
            lines = GeneralUtilities.read_lines_from_file(target_file)
            previous_hash_of_current_file: str = lines[1].split(":")[1].strip()
            if hash_of_current_file == previous_hash_of_current_file:
                return False
        ocr_content = self.get_ocr_content_of_file(file, serviceaddress, languages)
        GeneralUtilities.ensure_file_exists(target_file)
        GeneralUtilities.write_text_to_file(file, f"""Name of file: \"{os.path.basename(file)}\""
Hash of file: {hash_of_current_file}
OCR-content:
\"{ocr_content}\"""")
        return True

    @GeneralUtilities.check_arguments
    def get_ocr_content_of_file(self, file: str, serviceaddress: str, languages: list[str]) -> str:  # serviceaddress = None means local executable
        result: str = None
        extension = Path(file).suffix
        if serviceaddress is None:
            program_result = self.run_program_argsasarray("simpleocr", ["--File", file, "--Languages", "+".join(languages)] + languages)
            result = program_result[1]
        else:
            languages_for_url = '%2B'.join(languages)
            package_url: str = f"https://{serviceaddress}/GetOCRContent?languages={languages_for_url}&fileType={extension}"
            headers = {'Cache-Control': 'no-cache'}
            r = requests.put(package_url, timeout=5, headers=headers, data=GeneralUtilities.read_binary_from_file(file))
            if r.status_code != 200:
                raise ValueError(f"Checking for latest tor package resulted in HTTP-response-code {r.status_code}.")
            result = GeneralUtilities.bytes_to_string(r.content)
        return result

    @GeneralUtilities.check_arguments
    def ocr_analysis_of_repository(self, folder: str, serviceaddress: str, extensions: list[str], languages: list[str]) -> None:
        self.assert_is_git_repository(folder)
        changed_files = self.ocr_analysis_of_folder(folder, serviceaddress, extensions, languages)
        for changed_ocr_file in changed_files:
            GeneralUtilities.assert_condition(changed_ocr_file.endswith(".ocr.txt"), f"File '{changed_ocr_file}' is not an OCR-file. It should end with '.ocr.txt'.")
            base_file = changed_ocr_file[:-len(".ocr.txt")]
            GeneralUtilities.assert_condition(os.path.isfile(base_file), f"Base file '{base_file}' does not exist. The OCR-file '{changed_ocr_file}' is not valid.")
            base_file_relative_path = os.path.relpath(base_file, folder)
            base_file_diff_program_result = self.run_program("git", f"diff --quiet -- \"{base_file_relative_path}\"", folder, throw_exception_if_exitcode_is_not_zero=False)
            has_staged_changes: bool = None
            if base_file_diff_program_result[0] == 0:
                has_staged_changes = False
            elif base_file_diff_program_result[0] == 1:
                has_staged_changes = True
            else:
                raise RuntimeError(f"Unexpected exit code {base_file_diff_program_result[0]} when checking for staged changes of file '{base_file_relative_path}'.")
            if has_staged_changes:
                changed_ocr_file_relative_path = os.path.relpath(changed_ocr_file, folder)
                self.run_program_argsasarray("git", ["add", changed_ocr_file_relative_path], folder)

    @GeneralUtilities.check_arguments
    def update_timestamp_in_file(self, target_file: str) -> None:
        lines = GeneralUtilities.read_lines_from_file(target_file)
        new_lines = []
        prefix: str = "# last update: "
        for line in lines:
            if line.startswith(prefix):
                new_lines.append(prefix+GeneralUtilities.datetime_to_string_with_timezone(GeneralUtilities.get_now()))
            else:
                new_lines.append(line)
        GeneralUtilities.write_lines_to_file(target_file, new_lines)

    def do_and_log_task(self, name_of_task: str, task):
        try:
            self.log.log(f"Start action \"{name_of_task}\".", LogLevel.Information)
            result = task()
            if result is None:
                result = 0
            return result
        except Exception as e:
            self.log.log_exception(f"Error while running action \"{name_of_task}\".", e, traceback)
            return 1
        finally:
            self.log.log(f"Finished action \"{name_of_task}\".", LogLevel.Information)

    def get_lines_of_code_with_default_excluded_patterns(self, repository: str) -> int:
        return self.get_lines_of_code(repository, self.default_excluded_patterns_for_loc)

    default_excluded_patterns_for_loc: list[str] = [".txt", ".md", ".vscode", "Resources", "Reference", ".gitignore", ".gitattributes", "Other/Metrics"]

    def get_lines_of_code(self, repository: str, excluded_pattern: list[str]) -> int:
        self.assert_is_git_repository(repository)
        result: int = 0
        self.log.log(f"Calculate lines of code in repository '{repository}' with excluded patterns: {', '.join(excluded_pattern)}",LogLevel.Debug)
        git_response = self.run_program("git", "ls-files", repository)
        files: list[str] = GeneralUtilities.string_to_lines(git_response[1])
        for file in files:
            if os.path.isfile(os.path.join(repository, file)):
                if self.__is_excluded_by_glob_pattern(file, excluded_pattern):
                    self.log.log(f"File '{file}' is ignored because it matches an excluded pattern.",LogLevel.Diagnostic)
                else:
                    full_file: str = os.path.join(repository, file)
                    if GeneralUtilities.is_binary_file(full_file):
                        self.log.log(f"File '{file}' is ignored because it is a binary-file.",LogLevel.Diagnostic)
                    else:
                        self.log.log(f"Count lines of file '{file}'.",LogLevel.Diagnostic)
                        length = len(GeneralUtilities.read_nonempty_lines_from_file(full_file))
                        result = result+length
            else:
                self.log.log(f"File '{file}' is ignored because it does not exist.",LogLevel.Diagnostic)
        return result

    def __is_excluded_by_glob_pattern(self, file: str, excluded_patterns: list[str]) -> bool:
        for pattern in excluded_patterns:
            if fnmatch.fnmatch(file, f"*{pattern}*"):
                return True
        return False
    
    @GeneralUtilities.check_arguments
    def create_zip_archive(self, folder:str,zip_file:str) -> None:
        GeneralUtilities.assert_folder_exists(folder)
        GeneralUtilities.assert_file_does_not_exist(zip_file)
        folder = os.path.abspath(folder)
        with zipfile.ZipFile(zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=folder)
                    zipf.write(file_path, arcname)

    @GeneralUtilities.check_arguments
    def start_local_test_service(self, file: str):
        example_folder = os.path.dirname(file)
        docker_compose_file = os.path.join(example_folder, "docker-compose.yml")
        for service in self.get_services_from_yaml_file(docker_compose_file):
            self.kill_docker_container(service)
        example_name = os.path.basename(example_folder)
        title = f"Test{example_name}"
        self.run_program("docker", f"compose -p {title.lower()} up --detach", example_folder, title=title)

    @GeneralUtilities.check_arguments
    def stop_local_test_service(self, file: str):
        example_folder = os.path.dirname(file)
        example_name = os.path.basename(example_folder)
        title = f"Test{example_name}"
        self.run_program("docker", f"compose -p {title.lower()} down", example_folder, title=title)
