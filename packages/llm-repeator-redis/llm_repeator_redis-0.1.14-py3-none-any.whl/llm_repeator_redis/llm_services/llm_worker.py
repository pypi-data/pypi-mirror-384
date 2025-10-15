import logging
import os
import time
from configparser import ConfigParser
from pathlib import Path

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, BaseMessageChunk, AIMessageChunk
from langchain_core.outputs import LLMResult


from llm_repeator_redis.llm_services import LLMResourcesManager
from redis.exceptions import TimeoutError

from llm_repeator_redis.tools.init_tools import InitConfigTools

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
                 llm_json_path: str = None,
                 config_path: str = None,
                 default_model: str = None):
        """
        初始化 llm worker
        :param llm_json_path: llm 资源文件路径
        :param config_path: 配置文件路径
        :param default_model: 默认使用的 llm 的ID，汪指定的话，则使用 config.ini 中配置 local_llm 下的 local_llm_id
        """
        # 设置默认路径
        home = Path.home()
        default_config_dir = home / ".llm_repeator_redis" / "config"
        default_config_dir.mkdir(parents=True, exist_ok=True)

        if config_path is None:
            config_path = default_config_dir / "config.ini"
        if llm_json_path is None:
            llm_json_path = default_config_dir / "llm_resources.json"

        # 确保路径是字符串
        config_path = str(config_path)
        llm_json_path = str(llm_json_path)

        # 创建 config.ini 模板（如果不存在）
        if not os.path.exists(config_path):
            InitConfigTools.create_config_file(config_path)
            logging.info(f"Programme create a config file, you must set it correctly. path: {config_path}")

        # 创建 llm_resources.json 模板（如果不存在）
        if not os.path.exists(llm_json_path):
            InitConfigTools.create_llm_resources_file(llm_json_path)
            logging.info(
                f"Programme create a llm_resources.json file, you can add other llm to it. path: {llm_json_path}")

        from llm_repeator_redis.redis_services import RedisManager
        configparser: ConfigParser = ConfigParser()
        configparser.read(config_path, encoding="utf-8")

        self.redis_manager = RedisManager(configparser=configparser)
        self.llm_manager = LLMResourcesManager(json_path=llm_json_path)
        self.stream_name: str = configparser['redis_server']['request_stream_name']
        self.answer_map_name: str = configparser['redis_server']['answer_map_name']
        self.chunk_stream_prefix: str = configparser['redis_server']['chunk_stream_prefix']
        self.reasoning_stream_prefix: str = configparser['redis_server']['reasoning_stream_prefix']
        self.request_internal = float(configparser['llm_worker']['request_internal'])

        if default_model is not None:
            self.default_model = default_model
        else:
            self.default_model = configparser['local_llm']['local_llm_id']

    def run(self, internal: float = 3):
        """

        :return:
        """
        while True:
            current_time = time.time()

            request: {} = None

            try:
                request = self.redis_manager.pop_request(self.stream_name)
            except TimeoutError as e:
                # 修正字符串格式化，并确保变量名正确
                logger.warning("Failed to get pending requests: %s, and sleep %.2f seconds", str(e), internal)
                time.sleep(internal)

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

                    # 判断是否是 reason 模型正在工作
                    is_reason_working: bool = False

                    for chunk in self.llm_manager.stream(llm_key=model, base_messages=messages):

                        chunk_text: str

                        if isinstance(chunk, str):
                            chunk_text = chunk
                            answer_text += chunk
                        elif isinstance(chunk, AIMessageChunk):

                            if chunk.additional_kwargs is not None and 'reasoning_content' in chunk.additional_kwargs.keys():

                                # 原因还未开始
                                if is_reason_working == False:

                                    is_reason_working = True
                                    print("<think>" + chunk.additional_kwargs['reasoning_content'], end="", flush=True)
                                else:
                                    print(chunk.additional_kwargs['reasoning_content'], end="", flush=True)

                                # 此处增加了思考过程，在获取的时候可以增加
                                self.redis_manager.stream_chunk(seq=seq,
                                                                chunk_text=chunk.additional_kwargs['reasoning_content'],
                                                                chunk_stream_prefix=self.reasoning_stream_prefix)

                                continue


                            if chunk.content is None or chunk.content == "":
                                continue

                            if chunk.content is not None:

                                if is_reason_working == True:
                                    print("</think>", flush=True)
                                    is_reason_working = False

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

def init():
    LLMWorker()
    logging.info("The init() function has been called")