import json
import logging
import os

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.outputs import LLMResult
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import OllamaLLM

# 模块级别的日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class LLMResourcesManager:

    __providers = {
        "langchain-deepseek": ChatDeepSeek,
        "langchain-ollama": OllamaLLM
    }

    def __init__(self, json_path: str):

        with open(json_path, 'r', encoding='utf-8') as f:
            self.llm_dic = json.load(f)

        logger.info(f'Loaded {len(self.llm_dic)} LLM resources from {json_path}')
        logger.info(logger.info(f'Available LLM resources: {self.llm_dic.keys()}'))

    @staticmethod
    def format_messages_to_text(base_messages: list[BaseMessage]) -> str:
        """
        自定义消息转文本函数（按模型需求调整格式）
        :return:
        """
        return "\n".join([f"'{msg.type}': '{msg.content}'" for msg in base_messages]).strip()

    def generate(self, llm_key: str, base_messages:list[BaseMessage]) -> LLMResult | None:

        """
        向 LLM 资源发出信息请求，将生成结果反馈
        :param llm_key: LLM 资源 key
        :param base_messages: 消息列表
        :return: BaseMessage
        """
        if llm_key not in self.llm_dic:
            raise ValueError(f'LLM key {llm_key} not found in llm_resources.json')

        llm_def = self.llm_dic[llm_key]

        api_key = None

        if llm_def["env_api_key_name"]:

            api_key = os.getenv(llm_def["env_api_key_name"])

        if api_key is None:
            llm = self.__providers[llm_def["provider"]](api_base=llm_def["base_url"], model=llm_def["model"])
        else:
            llm = self.__providers[llm_def["provider"]](api_base=llm_def["base_url"], model=llm_def["model"], api_key=api_key)

        if llm_def["type"] == "BaseChatOpenAI":
            return llm.generate([base_messages])
        elif llm_def["type"] == "BaseLLM":
            # 原实现很多时候反回英语
            # return llm.generate([self.format_messages_to_text(base_messages=base_messages)])

            # TODO 观察效果
            text: str = ""

            for msg in base_messages:
                text += msg.content
                text += "\n\n"

            return llm.generate([text])

    def list_llm_def(self):
        """
        列出所有 LLM 资源
        :return: LLM 资源 key 列表
        """
        return self.llm_dic.keys()

    def is_model_available(self, llm_key: str) -> bool:
        """
        判断是否存在指定 LLM 资源
        :param llm_key: LLM 资源 key
        :return: True or False
        """
        return llm_key in self.llm_dic







if __name__ == '__main__':
    llm_manager = LLMResourcesManager('../config/llm_resources.json')

    messages = [
        SystemMessage("请你使用中文回答我的问候"),
        HumanMessage("How are you?")
    ]

    for llm_id in llm_manager.list_llm_def():
        print(llm_id)
        print(llm_manager.generate(llm_key=llm_id, base_messages=messages))

    # print(llm_manager.generate(llm_key="home_deepseek-r1:8b-llama-distill-fp16", base_messages=messages))

    print("Finished!")
