#!/usr/bin/env python3
"""
Собственно проверялка.

Позволяет запустить один комплект собственных и удалённых тестов на одном
решении и генерировать отчёт о прохождении этих тестов. Проверялка должна
работать в двух вариантах: дома у любого пользователя (в этом случае придётся
пользоваться доставкой как минимум удалённых тестов) и в составе системы
массовой проверки под управлением подсистемы изолированного запуска.
"""

from os.path import isdir, isfile, realpath, join, basename, dirname, getsize
from glob import glob
from tempfile import mkdtemp, NamedTemporaryFile as mkftmp
from shutil import rmtree
from subprocess import run, PIPE, TimeoutExpired, CompletedProcess
from typing import Union
from difflib import unified_diff
from atexit import register
import sys


PROGRAM_TYPES: dict = {"Python": ".py",  "Other": ".*"}
PROGRAM_NAMES: list = ["prog", "main", "program", "*"]
TEST_PATTERNS: list = ["[0-9]*.E", "test*[0-9].E"]
TEST_EXTENSIONS: list = [("in", "out"), ("dat", "res")]
MAX_TEST_SIZE: int = 80

_test_tmp_dir: str = mkdtemp()


def _clean():
    """Cleans temporary directories and files at the end of program"""
    if _test_tmp_dir:
        rmtree(_test_tmp_dir)


register(_clean)


def find_program(prog_prompt: str = "") -> (str, str):
    """Finds a program to test

    :param prog_prompt: Program directory, file pattern or empty string
    :return: Program realpath and program type
    """
    prog_prompt = prog_prompt or "."
    if isdir(prog_prompt):
        prog_dir = realpath(prog_prompt)
        for prog_type, ext in PROGRAM_TYPES.items():
            for name in PROGRAM_NAMES:
                prog_list = list(filter(isfile, glob(join(prog_dir, name + ext))))
                if len(prog_list) > 0:
                    return prog_list[0], prog_type
    else:
        prog_list = list(filter(isfile, glob(prog_prompt)))
        if len(prog_list) > 0:
            for prog_type, ext in PROGRAM_TYPES:
                if prog_list[0].endswith(ext):
                    return realpath(prog_list[0]), prog_type
    return "", ""


def ext_replace(path: str, extension: str) -> str:
    """Replaces extension of a given path file to desired

    :param path: File path
    :param extension: Extension to replace
    :return: Converted path
    """
    file_dir, file_name = dirname(path), basename(path).rsplit(sep=".", maxsplit=1)[0] + "." + extension
    return join(file_dir, file_name)


def find_local_tests(test_prompt: str = "") -> list[tuple[str, str]]:
    """Finds local test pairs

    :param test_prompt: Tests directory or empty string
    :return: List of test realpath pairs
    """
    test_pairs = []
    test_dir = realpath(test_prompt or ".")
    for in_ext, out_ext in TEST_EXTENSIONS:
        for test_pattern in TEST_PATTERNS:
            in_pattern = join(test_dir, test_pattern.replace("E", in_ext))
            for in_test in glob(in_pattern):
                if isfile(in_test) and isfile(out_test := ext_replace(in_test, out_ext)):
                    test_pairs.append((in_test, out_test))
    return sorted(test_pairs, key=lambda x: x[0])


def unprotected_python_runner(prog_path: str, prog_input: str, time_limit: float = 1, ) -> tuple[str, str, int]:
    """Runs program with a given input (until protected runner is implemented)

    :param prog_path: Program realpath
    :param prog_input: Input file real path
    :param time_limit: Time limit for a program
    :return: Program output file realpath or Exception, stderr and return code of proccess
    """
    with open(prog_input) as f_in, mkftmp(prefix=basename(prog_input) + "_", dir=_test_tmp_dir, delete=False) as f_out:
        try:
            result = run([sys.executable, prog_path], stdin=f_in, stdout=f_out, stderr=PIPE, timeout=time_limit)
        except TimeoutExpired as time_error:
            result = CompletedProcess(time_error.args, -1, stderr=str(time_error).encode(errors='replace'))

    return f_out.name or "-", result.stderr.decode(errors='replace'), result.returncode


def choose_runner(prog: str, prog_type: str, prog_input: str):
    # TODO
    return unprotected_python_runner


def test_check(actual: str, initial: str) -> Union[unified_diff, None]:
    """Compares two test file without insignificant whitespaces

    :param actual: Output from program
    :param initial: Supposed output
    :return: unified_diff of files or None if outputs are the same
    """
    with open(actual) as act, open(initial) as init:
        act_lines = [line.strip() + "\n" for line in act.readlines()]
        init_lines = [line.strip() + "\n" for line in init.readlines()]
    if act_lines == init_lines:
        return None
    act_size, init_size = getsize(actual), getsize(initial)
    if act_size > MAX_TEST_SIZE or init_size > MAX_TEST_SIZE:
        init_lines, act_lines = [f"Size differs: {init_size}\n"], [f"Size differs: <output>\n"]
    return unified_diff(init_lines, act_lines, basename(initial), "<output>")


def group_result(prog: str, prog_type: str, tests: list[tuple[str, str]]) -> dict:
    """Generates results for one group of tests

    :param prog: Realpath of program to test
    :param prog_type: Program type
    :param tests: List of tests pairs
    :return: Dictionary with score, output and testing information
    """
    info_result = {"Score": None, }
    test_amount = len(tests)
    success = 0
    for f_in, f_out in tests:
        runner = choose_runner(prog, prog_type, f_in)
        output, stderr, status = runner(prog, f_in)
        if status == 0:
            test_comparison = test_check(output, f_out)
            if test_comparison is None:
                success += 1
        else:
            test_comparison = "Error occurred"
        info_result[basename(f_in)] = {"Tests Comparison": test_comparison, "Stderr": stderr, "Status": status}
    if test_amount:
        info_result["Score"] = float(success) / test_amount * 100
    return info_result


def local_remote_result(prog: str, prog_type: str, local_tests: list, remote_tests: list) -> dict:
    """Generates results for both local and remote tests
    :param prog: Program realpath
    :param prog_type: Program type
    :param local_tests: list of local tests pairs
    :param remote_tests: list of remote tests pairs
    :return: Dictionary with score, output and testing information for two tests groups
    """
    all_results = dict()
    all_results["Local"] = group_result(prog, prog_type, local_tests)
    all_results["Remote"] = group_result(prog, prog_type, remote_tests)
    return all_results


def download_remote_tests(remote_dir: str) -> str:
    # TODO
    return remote_dir


def check(prog_path: str, local_dir: str, remote_dirs: list) -> dict:
    """Gives all information about program testing

    :param prog_path: Program path
    :param local_dir: Local tests directory
    :param remote_dirs: Remote tests directory
    :return:
    """
    # TODO
    prog, prog_type = find_program(prog_path)
    local_tests = find_local_tests(local_dir)
    remote_tests = []
    if remote_dirs:
        for remote_dir in remote_dirs:
            download_dir = download_remote_tests(remote_dir)
            remote_tests.append(find_local_tests(download_dir))
    return local_remote_result(prog, prog_type, local_tests, remote_tests)


def beautiful_check_output(check_info: dict):
    """Gives all information about program testing for user

    :param check_info: info dictionary
    """
    for group_name, group in check_info.items():
        print(group_name + ":")
        for info_name, info in group.items():
            print("\t", end="")
            print(info_name + ": ", end="")
            if isinstance(info, dict):
                if not (info["Status"] or info["Tests Comparison"]):
                    print("OK")
                elif info["Status"]:
                    print(info["Stderr"], end="" if info["Stderr"][-1] == "\n" else "\n")
                else:
                    for line in info["Tests Comparison"]:
                        print(line, end="")
                        print("\t\t", end="")
            else:
                print('%.2f' % info + "%" if info else "-")
            print()


def main():
    prog_path, local_dir, remote_dirs = "", "", []
    if len(sys.argv) > 1:
        prog_path, local_dir = sys.argv[1], sys.argv[2]
        remote_dirs = [var for var in sys.argv[3:]]
    test_info = check(prog_path, local_dir, remote_dirs)
    beautiful_check_output(test_info)


if __name__ == "__main__":
    main()
