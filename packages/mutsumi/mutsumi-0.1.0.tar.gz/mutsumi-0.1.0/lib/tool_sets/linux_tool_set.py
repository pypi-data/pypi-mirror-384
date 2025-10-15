import json
import subprocess
from pathlib import Path

from src.mutsumi.tool_set import ToolSet


def confirmExecCmd(cmd: str) -> str:
    """执行任意shell命令前，必须调用此函数向用户确认，
    以防止错误命令损害计算机。
    参数`cmd`为即将执行的命令。
    返回值为用户的决定。"""
    print("是否执行命令:")
    print("\t" + cmd)
    confrim = input("[Y/n]? ")
    if confrim in ("", "y", "Y"):
        return "确定执行"
    else:
        return "取消执行"


def shellExec(cmd: str) -> str:
    """执行任意shell命令，将运行结果直接显示在终端。
    大语言模型仅需要执行而不需要知道执行结果时调用这个函数。
    参数`cmd`为需要执行的shell命令，
    返回值为执行的返回代码。"""
    sp = subprocess.run(
        cmd,
        text=True,
        shell=True,
    )
    return str(sp.returncode)


def shellExecRetText(cmd: str) -> str:
    """执行任意shell命令，将输出结果作为返回值返回。
    当大语言模型需要命令执行的结果时调用这个函数。
    命令执行的结果不会显示在终端。
    参数`cmd`为需要执行的shell命令，
    返回值为命令运行的结果。"""
    sp = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        shell=True,
    )
    return str(sp.stdout)


linux_tool_set = ToolSet([confirmExecCmd, shellExec, shellExecRetText])
