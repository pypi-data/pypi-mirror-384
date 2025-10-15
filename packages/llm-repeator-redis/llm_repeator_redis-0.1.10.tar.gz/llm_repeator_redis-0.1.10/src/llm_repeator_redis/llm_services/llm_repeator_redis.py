import logging
import time
from configparser import ConfigParser
from typing import Iterator

import redis
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, BaseMessageChunk
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

        self.chunk_stream_prefix = configparser['redis_server']['chunk_stream_prefix']

        self.reasoning_stream_prefix = configparser['redis_server']['reasoning_stream_prefix']


    def request(self, messages: [BaseMessage],
                model: str,
                block_time =20 * 60,
                internal: int = 1,
                enable_arch: bool = True) -> {}:
        """
        将请求消息推送到 Redis 队列中，原样返回答复
        :param messages: 请求消息列表
        :param model: 使用的模型
        :param block_time: 阻塞时间，单位为秒,默认为5分钟
        :param internal: 请求答案的时间间隔，单位为秒，默认为1秒
        :param enable_arch: 是否启用归档，默认为 True
        :return: 请求序列号，请求序号是用于获取响应的
        """
        action_type: str = "generate"

        # 获取当前时间
        current_time = time.time()

        if not self.llm_manager.is_model_available(model):
            logger.error(f"model {model} is not available")
            raise Exception(f"model {model} is not available")

        seq: int = self.redis_manager.push_request(stream_name=self.stream_name,
                                                   messages=messages,
                                                   model=model,
                                                   action_type=action_type,
                                                   enable_arch=enable_arch)

        logger.info(f"push request to redis using model: {model} with action_type: {action_type}, get answer seq: {seq}")

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

    def request_stream(self, messages: [BaseMessage],
                       model: str,
                       block_time=20 * 60,
                       internal: float = 0.02,
                       enable_arch: bool = True) -> Iterator[str] | None:

        action_type: str = "stream"
        current_time = time.time()

        if not self.llm_manager.is_model_available(model):
            logger.error(f"model {model} is not available")
            raise Exception(f"model {model} is not available")

        seq: int = self.redis_manager.push_request(
            stream_name=self.stream_name,
            messages=messages,
            model=model,
            action_type=action_type,
            enable_arch=enable_arch
        )

        logger.info(f"Pushed request to Redis using model: {model}, action_type: {action_type}, seq: {seq}")

        # 是否进行思考过程
        is_reasoning: bool = True

        # 是否首次思考
        is_first_reasoning: bool = False

        while time.time() - current_time < block_time:
            try:

                if is_reasoning:
                    # 尝试获取原因分析
                    chunk_data = self.redis_manager.pop_stream_chunk(seq=seq, chunk_stream_prefix=self.reasoning_stream_prefix)

                    # 原因是直接打印，而不是返回结果
                    if chunk_data and is_first_reasoning == False:
                        is_first_reasoning = True
                        print("<think>")
                        print(chunk_data.decode('utf-8'), end="", flush=True)
                        continue
                    elif chunk_data:
                        print(chunk_data.decode('utf-8'), end="", flush=True)
                        continue

                logger.debug(f"Fetching chunk data from Redis with seq: {seq}, prefix: {self.chunk_stream_prefix}")
                chunk_data = self.redis_manager.pop_stream_chunk(seq=seq, chunk_stream_prefix=self.chunk_stream_prefix)

                if not chunk_data:

                    # 如果数据工作已经结束
                    if self.redis_manager.is_finished_stream(seq=seq, chunk_stream_prefix=self.chunk_stream_prefix):

                        logger.info(f"seq: {seq} stream is finished")

                        self.redis_manager.rem_finish_stream(seq=seq, chunk_stream_prefix=self.chunk_stream_prefix)
                        return None

                    else:
                        logger.debug(f"seq: {seq} no chunk data received, retrying in {internal} seconds")
                        time.sleep(internal)
                        continue

                # 原因为空，且
                if is_reasoning and is_first_reasoning:
                    is_reasoning = False
                    print("\n</think>")

                logger.debug(f"seq: {seq} received chunk data: {chunk_data}")

                yield chunk_data.decode('utf-8')

            except redis.exceptions.RedisError as e:
                logger.error(f"Redis error occurred while processing chunk data for seq {seq}: {e}")
                break
            except Exception as e:
                logger.error(f"Unexpected error occurred while processing chunk data for seq {seq}: {e}")
                break

        logger.info(f"Finished processing request stream for seq: {seq}")

    def request_messages(self, messages: [BaseMessage],
                         model: str,
                         block_time =20 * 60,
                         internal: int = 1,
                         enable_arch: bool = True) -> {}:
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

        return answer

    def request_str_human(self, system: str,
                          human: str,
                          model: str,
                          block_time =20 * 60,
                          internal: int = 1,
                          enable_arch: bool = True) -> {}:
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
