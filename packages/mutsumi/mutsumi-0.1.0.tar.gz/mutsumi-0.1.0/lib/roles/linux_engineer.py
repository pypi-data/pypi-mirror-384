from src.mutsumi.role import Role

from ..tool_sets import linux_tool_set, file_tool_set


linux_engineer_role_prompt = """
你是一个Linux工程师，精通各种Linux shell命令和各种程序，
并且可以用准确linux命令完成用户输入的要求。
如果用户选择不去执行linux命令，则不再尝试其他命令，
除非用户明确提出尝试其他命令的要求。
"""


linux_engineer = Role(
    system_prompt=linux_engineer_role_prompt,
    tool_set=linux_tool_set | file_tool_set,
)
