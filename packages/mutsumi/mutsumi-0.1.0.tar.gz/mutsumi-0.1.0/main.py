from src.mutsumi.deepseek import DeepSeek
from src.mutsumi.tool_set import ToolSet

import readline

NumberBook = {
    "1": "张三",
    "2": "李四",
    "3": "王五",
}


def getName(id: str) -> str:
    """根据 id 号从本地数据库获取人员的姓名。
    参数 `id` 为人员的识别代码，类型为字符串。
    返回值类型为字符串，为人员的姓名，如果不存在则返回空字符串。"""
    return NumberBook.get(id, "")


test_tool_set = ToolSet([getName])


if __name__ == "__main__":
    with open("cfg/key") as f:
        key = f.read()

    client = DeepSeek(key)
    ctx = client.create(
        log_name="main",
        tool_set=test_tool_set,
    )

    client.interact(ctx)
