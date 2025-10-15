import json
import os
from typing import List

from langchain_core.messages import HumanMessage

from ..command_def import Command, AbstractChatSession


class SendTemplateCommand(Command):
    """
    实现模板 + 数据 JSON 的组合发送功能
    """

    def __init__(self):
        super().__init__("send", [], "发送模版文件，如果指定第二个参数，则从第二个参数指向的文件或文件夹中，加载 JSON 数据用于合成模板，再发送llm")

    def match(self, input_str: str, session: AbstractChatSession) -> bool:
        """ 判断是否匹配 """
        return input_str.lower().startswith(self.name)

    def execute(self, session: AbstractChatSession, args: List[str] = None):

        # 如果只有一个参数，加载文件的内容，直接发送
        if len(args) == 1:
            with open(args[0], "r", encoding="utf-8") as f:
                content = f.read()

                print(f"(1/1)发送内容：{content}")

                msg: HumanMessage = HumanMessage(content)
                session._get_response(msg)
        # 如果两个参数，且第二个参数是文件
        elif len(args) == 2 and os.path.isfile(args[1]):
            with open(args[0], "r", encoding="utf-8") as f:
                content = f.read()
                # 读取文件内容，作为模板
                # 读取第二个参数，作为文件路径
                with open(args[1], "r", encoding="utf-8") as f:
                    data = f.read()
                    json_data = json.loads(data)
                    # 读取文件内容，作为数据
                    # 合成模板和数据
                    for key in json_data:
                        content = content.replace("${" + key +"}", json_data[key])

                    print(f"发送内容：{content}")

                    msg: HumanMessage = HumanMessage(content)
                    session._get_response(msg)
        # 如果两个参数，且第二个参数文件夹，则加载里面所有的 json 文件，并分别访问
        elif len(args) == 2 and os.path.isdir(args[1]):

            content: str
            with open(args[0], "r", encoding="utf-8") as f:
                content = f.read()

            for file in os.listdir(args[1]):
                if str.lower(file).endswith(".json"):
                    with open(os.path.join(args[1], file), "r", encoding="utf-8") as f:
                        data = f.read()
                        json_data = json.loads(data)
                        # 读取文件内容，作为数据
                        # 合成模板和数据

                        # 需要保留content 不变，克隆 content 的值到 this_content
                        this_content = content

                        for key in json_data:
                            this_content = this_content.replace("${" + key +"}", json_data[key])
                        print(f"{file} 发送内容：{this_content}")
                        msg: HumanMessage = HumanMessage(this_content)
                        session._get_response(msg)
        else:
            print("参数错误，请输入正确的参数")
            print("第一个参数为模板文件，第二个参数可以是文件夹，则加载其中所有 .json，可以是文件被直接加载成json")
            return
