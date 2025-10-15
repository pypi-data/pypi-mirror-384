import json

from pathlib import Path
from typing import Literal

from src.mutsumi.tool_set import ToolSet


def genRetval(status: Literal["ok", "error"], content: str) -> str:
    return json.dumps({"status": status, "content": content})


def readFile(path: str) -> str:
    """以纯文本的形式读取一个文件，并返回文件的内容。
    参数`path`为unix文件路径。
    返回值为状态和文件的内容，格式为{"status":"ok"或"error", "content":s}，
    对应于读取成功和错误。"""
    try:
        f = open(path, "r")
        s = f.read()
        f.close()
        return genRetval("ok", s)
    except Exception as e:
        return genRetval("error", repr(e))


def writeFile(path: str, content: str, cover: bool) -> str:
    """以纯文本的形式写入一个文件，并返回写入内容的长度。
    参数`path`为unix文件路径。
    参数`cover`为是否覆盖现有文件，true表示覆盖。
    返回值为状态和文件的内容，格式为{"status":"ok"或"error", "content":s}，
    对应于成功和错误。"""
    file_path = Path(path)
    if file_path.exists() and not cover:
        return genRetval("error", "File exists.")
    try:
        f = open(path, "w")
        w_size = f.write(content)
        f.close()
        return genRetval("ok", str(w_size))
    except Exception as e:
        return genRetval("error", repr(e))


file_tool_set = ToolSet([readFile, writeFile])
