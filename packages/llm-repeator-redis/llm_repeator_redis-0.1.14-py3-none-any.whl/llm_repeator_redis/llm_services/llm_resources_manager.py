import json
import logging
import os
import time
from pathlib import Path

from langchain_core.messages import BaseMessage,  BaseMessageChunk
from langchain_core.outputs import LLMResult
from langchain_deepseek import ChatDeepSeek
from langchain_ollama import OllamaLLM
from openai import APITimeoutError
from typing_extensions import Iterator

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

    def __init__(self, json_path: str = None):

        if json_path is None:
            home_path: Path = Path.home()
            json_path = str(home_path / ".llm_repeator" / "config" / "llm_resources.json")

        with open(json_path, 'r', encoding='utf-8') as f:
            self.llm_dic: dict = json.load(f)

        logger.info(f'Loaded {len(self.llm_dic)} LLM resources from {json_path}')
        logger.info(logger.info(f'Available LLM resources: {self.llm_dic.keys()}'))

    @staticmethod
    def format_messages_to_text(base_messages: list[BaseMessage]) -> str:
        """
        自定义消息转文本函数（按模型需求调整格式）
        :return:
        """
        return "\n".join([f"'{msg.type}': '{msg.content}'" for msg in base_messages]).strip()

    def stream(self,
               llm_key: str,
               base_messages: list[BaseMessage],
               retry: int = 6,
               retry_internal: int = 20) -> Iterator[BaseMessageChunk] | None:
        """
        向 LLM 资源发出信息请求，将生成结果的 redis list 的名称进行反馈
        :param llm_key: LLM 资源 key
        :param base_messages: 消息列表
        :param retry: 重试次数, 默认 6 次
        :param retry_internal: 重试间隔, 默认 20 秒
        :return: redis list 的名称
        """
        if llm_key not in self.llm_dic:
            raise ValueError(f'LLM key {llm_key} not found in llm_resources.json')

        llm_def = self.llm_dic[llm_key]

        api_key = None

        if llm_def["env_api_key_name"]:
            api_key = os.getenv(llm_def["env_api_key_name"])

        if llm_def["type"] == "BaseChatOpenAI":
            llm: ChatDeepSeek
        elif llm_def["type"] == "BaseLLM":
            llm: OllamaLLM

        if api_key is None:
            llm = self.__providers[llm_def["provider"]](api_base=llm_def["base_url"], model=llm_def["model"])
        else:
            llm = self.__providers[llm_def["provider"]](api_base=llm_def["base_url"], model=llm_def["model"], api_key=api_key)

        retry_count: int = 0

        while retry_count < retry:
            try:
                if llm_def["type"] == "BaseChatOpenAI":
                    return llm.stream(base_messages)
                elif llm_def["type"] == "BaseLLM":
                    # 原实现很多时候反回英语
                    # return llm.generate([self.format_messages_to_text(base_messages=base_messages)])

                    text: str = ""

                    for msg in base_messages:
                        text += msg.content
                        text += "\n\n"

                    return llm.stream([text])
            except APITimeoutError as e:
                logger.error(f"API timeout error: {e}")
                logger.warning(f"Retry {retry_count} times, waiting {retry_internal} seconds")
                retry_count += 1
                time.sleep(retry_internal)
            except Exception as e:
                logger.error(f"Error: {e}")
                logger.warning(f"Retry {retry_count} times, waiting {retry_internal} seconds")
                retry_count += 1
                time.sleep(retry_internal)
            finally:
                if retry_count == retry:
                    logger.error(f"Retry {retry_count} times, still failed")
                    return None


    def generate(self, llm_key: str,
                 base_messages:list[BaseMessage],
                 retry: int = 6,
                 retry_internal: int = 20) -> LLMResult | None:

        """
        向 LLM 资源发出信息请求，将生成结果反馈
        :param llm_key: LLM 资源 key
        :param base_messages: 消息列表
        :param retry: 重试次数, 默认 6 次
        :param retry_internal: 重试间隔, 默认 20 秒
        :return: BaseMessage
        """
        if llm_key not in self.llm_dic:
            raise ValueError(f'LLM key {llm_key} not found in llm_resources.json')

        llm_def = self.llm_dic[llm_key]

        api_key = None

        if llm_def["env_api_key_name"]:
            api_key = os.getenv(llm_def["env_api_key_name"])

        if llm_def["type"] == "BaseChatOpenAI":
            llm: ChatDeepSeek
        elif llm_def["type"] == "BaseLLM":
            llm: OllamaLLM

        if api_key is None:
            llm = self.__providers[llm_def["provider"]](api_base=llm_def["base_url"], model=llm_def["model"])
        else:
            llm = self.__providers[llm_def["provider"]](api_base=llm_def["base_url"], model=llm_def["model"], api_key=api_key)

        retry_count: int = 0

        while retry_count < retry:
            try:
                if llm_def["type"] == "BaseChatOpenAI":
                    return llm.generate([base_messages])
                elif llm_def["type"] == "BaseLLM":
                    # 原实现很多时候反回英语
                    # return llm.generate([self.format_messages_to_text(base_messages=base_messages)])

                    text: str = ""

                    for msg in base_messages:
                        text += msg.content
                        text += "\n\n"

                    return llm.generate([text])
            except APITimeoutError as e:
                logger.error(f"API timeout error: {e}")
                logger.warning(f"Retry {retry_count} times, waiting {retry_internal} seconds")
                retry_count += 1
                time.sleep(retry_internal)
            except Exception as e:
                logger.error(f"Error: {e}")
                logger.warning(f"Retry {retry_count} times, waiting {retry_internal} seconds")
                retry_count += 1
                time.sleep(retry_internal)
            finally:
                if retry_count == retry:
                    logger.error(f"Retry {retry_count} times, still failed")
                    return None

    def list_llm_def(self):
        """
        列出所有 LLM 资源
        :return: LLM 资源 key 列表
        """
        return [key for key in self.llm_dic.keys()]

    def is_model_available(self, llm_key: str) -> bool:
        """
        判断是否存在指定 LLM 资源
        :param llm_key: LLM 资源 key
        :return: True or False
        """
        return llm_key in self.llm_dic
