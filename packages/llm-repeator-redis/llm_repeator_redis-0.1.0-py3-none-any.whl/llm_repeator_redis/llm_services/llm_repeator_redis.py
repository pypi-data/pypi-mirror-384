import logging
import time
from configparser import ConfigParser

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from llm_repeator_redis.llm_services.llm_resources_manager import LLMResourcesManager

from llm_repeator_redis.redis_services.redis_read_manager import RedisManager

# 模块级别的日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class LLMRepeaterRedis:
    """
    使用 Redis 实现的 LLM 请求器
    """
    def __init__(self, llm_json_path: str = '../config/llm_resources.json', config_path: str = '../config/config.ini'):

        configparser: ConfigParser = ConfigParser()

        configparser.read(config_path, encoding="utf-8")

        self.redis_manager = RedisManager(configparser=configparser)

        self.llm_manager = LLMResourcesManager(json_path=llm_json_path)

        self.stream_name = configparser['redis_server']['request_stream_name']

        self.answer_map_name = configparser['redis_server']['answer_map_name']


    def request(self, messages: [BaseMessage], model: str, block_time =20 * 60, internal: int = 1, enable_arch: bool = True) -> {}:
        """
        将请求消息推送到 Redis 队列中，原样返回答复
        :param messages: 请求消息列表
        :param model: 使用的模型
        :param block_time: 阻塞时间，单位为秒,默认为5分钟
        :param internal: 请求答案的时间间隔，单位为秒，默认为1秒
        :param enable_arch: 是否启用归档，默认为 True
        :return: 请求序列号，请求序号是用于获取响应的
        """

        # 获取当前时间
        current_time = time.time()

        if not self.llm_manager.is_model_available(model):
            logger.error(f"model {model} is not available")
            raise Exception(f"model {model} is not available")

        seq: int = self.redis_manager.push_request(stream_name=self.stream_name, messages=messages, model=model, enable_arch=enable_arch)

        logger.info(f"push request to redis using model: {model}, get answer seq: {seq}")

        # 当总时间超过 block_time 跳出循环
        while time.time() - current_time < block_time:

            # 获取请求的答案
            answer = self.redis_manager.pop_response(seq=seq)
            if answer is not None:
                logger.debug(f"seq: {seq} get answer: {answer}")
                return answer
            else:
                time.sleep(internal)
                logger.debug(f"seq: {seq} get answer is None, sleep {internal} seconds")
        logger.error(f"seq: {seq} get answer timeout")

    def request_messages(self, messages: [BaseMessage], model: str, block_time =20 * 60, internal: int = 1, enable_arch: bool = True) -> {}:
        """
        将请求消息推送到 Redis 队列中，使用 config.ini 中配置的 response_type 来处理响应，再返回结果
        :param messages: 请求消息列表
        :param model: 使用的模型
        :param block_time: 阻塞时间，单位为秒,默认为5分钟
        :param internal: 请求答案的时间间隔，单位为秒，默认为1秒
        :param enable_arch: 是否启用归档，默认为 True
        :return: 请求序列号，请求序号是用于获取响应的
        """
        answer = self.request(messages=messages, model=model, block_time=block_time, internal=internal, enable_arch=enable_arch)

        # TODO 需要根据不同的响应类型进行处理

        return answer

    def request_str_human(self, system: str, human: str, model: str, block_time =20 * 60, internal: int = 1, enable_arch: bool = True) -> {}:
        """
        将请求消息推送到 Redis 队列中，使用 config.ini 中配置的 response_type 来处理响应，再返回结果
        :param system: 提示词
        :param human: 问题
        :param model: 使用的模型
        :param block_time: 阻塞时间，单位为秒,默认为5分钟
        :param internal: 请求答案的时间间隔，单位为秒，默认为1秒
        :param enable_arch: 是否启用归档，默认为 True
        :return:
        """
        messages: [BaseMessage] = [SystemMessage(system), HumanMessage(human)]

        return self.request_messages(messages=messages, model=model, block_time=block_time, internal=internal, enable_arch=enable_arch)

    def request_file_human(self, system_file_path: str, human: str, model: str, block_time =20 * 60, internal: int = 1, enable_arch: bool = True) -> {}:
        """
        将请求消息推送到 Redis 队列中，使用 config.ini 中配置的 response_type 来处理响应，再返回结果
        :param system_file_path: 提示词文件路径
        :param human: 问题
        :param model: 使用的模型
        :param block_time: 阻塞时间，单位为秒,默认为5分钟
        :param internal: 请求答案的时间间隔，单位为秒，默认为1秒
        :param enable_arch: 是否启用归档，默认为 True
        :return: 请求序列号，请求序号是用于获取响应的
        """
        with open(system_file_path, 'r', encoding='utf-8') as f:
            prompt: str = f.read()

        messages: [BaseMessage] = [SystemMessage(prompt), HumanMessage(human)]

        return self.request_messages(messages=messages, model=model, block_time=block_time, internal=internal, enable_arch=enable_arch)
