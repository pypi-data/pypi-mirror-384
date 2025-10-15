import logging
import time
from configparser import ConfigParser

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, BaseMessageChunk, AIMessageChunk
from langchain_core.outputs import LLMResult
from llm_repeator_redis.redis_services.redis_read_manager import RedisManager

from llm_repeator_redis.llm_services.llm_resources_manager import LLMResourcesManager

# 模块级别的日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class LLMWorker:
    """

    """
    def __init__(self,
                 llm_json_path: str = './config/llm_resources.json',
                 config_path: str = './config/config.ini',
                 default_model: str = 'home_deepseek-r1:8b-llama-distill-fp16'):
        """

        :param llm_json_path:
        :param config_path:
        :param default_model:
        """
        configparser: ConfigParser = ConfigParser()

        configparser.read(config_path, encoding="utf-8")

        self.redis_manager = RedisManager(configparser=configparser)

        self.llm_manager = LLMResourcesManager(json_path=llm_json_path)

        self.stream_name: str = configparser['redis_server']['request_stream_name']

        self.answer_map_name: str = configparser['redis_server']['answer_map_name']

        self.chunk_stream_prefix: str = configparser['redis_server']['chunk_stream_prefix']

        self.request_internal = float(configparser['llm_worker']['request_internal'])

        self.default_model = default_model

    def run(self):
        """

        :return:
        """
        while True:
            current_time = time.time()

            request: {} = self.redis_manager.pop_request(self.stream_name)
            if request:
                seq = request['seq']
                text_messages = request['messages']

                if "model" not in request:
                    model = None
                else:
                    model = request['model']

                action_type = request['action_type']

                if not model:
                    model = self.default_model

                messages: [BaseMessage] = []

                for msg in text_messages:
                    if msg['type'] == "system":
                        messages.append(SystemMessage(msg['content']))
                    elif msg['type'] == "human":
                        messages.append(HumanMessage(msg['content']))
                    else:
                        raise ValueError(f"Unknown message type: {msg['type']}")

                # 当 action_type 是 generate 时
                if str.lower(action_type) == "generate":
                    logger.info(f"begin the llm model: {model} to generate answer, seq: {seq}")

                    answer: LLMResult = self.llm_manager.generate(llm_key=model, base_messages=messages)

                    # print(answer.generations[0][0])

                    answer_text: str = answer.generations[0][0].text

                    self.redis_manager.save_response(seq=seq, model=model, response=answer_text)

                    logger.info(f"end the llm model: {model} to generate answer, seq: {seq}")

                # 当 action_type 是 stream 时
                elif str.lower(action_type) == "stream":
                    logger.info(f"begin the llm model: {model} to stream answer, seq: {seq}")

                    answer_text: str = ""

                    for chunk in self.llm_manager.stream(llm_key=model, base_messages=messages):

                        chunk_text: str

                        if isinstance(chunk, str):
                            chunk_text = chunk
                            answer_text += chunk
                        elif isinstance(chunk, AIMessageChunk):
                            chunk_text = chunk.content
                            answer_text += chunk_text

                        self.redis_manager.stream_chunk(seq=seq,
                                                        chunk_text=chunk_text,
                                                        chunk_stream_prefix=self.chunk_stream_prefix)

                        # time.sleep(0.3)

                    # 设置 对话的完成状态
                    self.redis_manager.finish_stream(seq=seq, chunk_stream_prefix=self.chunk_stream_prefix)

                    logger.info(f"end the llm model: {model} to stream answer, seq: {seq}")

                else:
                    raise ValueError(f"Unknown action type: {action_type}")

                # 在请求中，是否开启了归档 （让请求也可以确定是否归档）
                request_enable_arch: bool = request['enable_arch']

                logger.debug(f"the request enable_arch: {request_enable_arch}")

                if request_enable_arch:
                    # 进行对话归档到 redis 的操作
                    logger.info(f"begin to archive the request: {seq}")
                    self.redis_manager.save_to_arch_redis(seq=seq,
                                                          model=model,
                                                          request_json=request,
                                                          answer_text=answer_text,
                                                          llm_manager=self.llm_manager)

            else:
                logger.debug(f"no request, sleep {self.request_internal} seconds")
                time.sleep(self.request_internal)

            now = time.time()

            if now - current_time > 60*2:
                current_time = time.time()
                logger.info(f"the llm worker is running, but no request")