import json
from src.mutsumi.tool_set import ToolSet

from emailtools import Email, EmailServer

EMAIL_CONFIG_FILE = "cfg/email.json"
EMAIL_BOOK_FILE = "cfg/email_book.json"

with open(EMAIL_BOOK_FILE) as f:
    email_book: dict[str, str] = json.load(f)


def getAvaliableEmailAddresses() -> str:
    """输出所有可用的邮件地址。
    格式为JSON，一个键值对为一条信息，
    其中键为邮箱的使用者，值为对应的邮箱地址。"""
    return json.dumps(email_book)


def sendEmail(receivers: dict[str, str] | str, subject: str, content: str) -> str:  # type: ignore
    """给接收者发邮件。
    `receivers`接收一个字典，保存了接收者的名字和地址。
    每一个键值对为一条数据，键为地址，值为名字。
    `subject`是邮件的主题。
    `content`是邮件的内容。内容格式可以是markdown格式。
    返回值恒为字符串'ok'。"""
    if isinstance(receivers, str):
        try:
            receivers: dict[str, str] = json.loads(receivers)
        except:
            return "参数 'receivers' 格式错误"

    with open(EMAIL_CONFIG_FILE) as f:
        cfg: dict[str, str] = json.load(f)

    email = Email.sequence(subject, *content.split("\n"))
    server = EmailServer(
        host=cfg["host"],
        userName=cfg["name"],
        userAddr=cfg["addr"],
        key=cfg["key"],
    )
    server.send(email, receivers)
    return "ok"


email_tool_set = ToolSet([getAvaliableEmailAddresses, sendEmail])
