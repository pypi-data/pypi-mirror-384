import json
import logging
import os
from configparser import ConfigParser
from datetime import datetime, timezone

import redis
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.outputs import LLMResult
from redis import RedisError

from llm_repeator_redis.llm_services.llm_resources_manager import LLMResourcesManager

# 模块级别的日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

# 读取配置文件中的日志级别
_config_file_path = os.path.join(os.path.dirname(__file__), './config', 'config.ini')
if os.path.exists(_config_file_path):
    _configparser = ConfigParser()
    _configparser.read(_config_file_path, encoding='utf-8')
    log_level = _configparser['logging'].get('level', 'INFO').upper()
    logger.setLevel(log_level)

class RedisManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(RedisManager, cls).__new__(cls)
            cls._instance.__initialized = False
        return cls._instance

    def __init__(self, configparser: ConfigParser = None):
        """
        从 config.ini 文件中读取 Redis 服务器的配置信息
        """
        if self.__initialized:
            return
        self.__initialized = True

        if configparser is None:
            configparser = ConfigParser()

            config_file_path: str = os.path.join(os.path.dirname(__file__), './config', 'config.ini')

            if not os.path.exists(config_file_path) or not configparser.read(config_file_path, encoding='utf-8'):
                raise FileNotFoundError(f'配置文件不存在或无法读取 {config_file_path}')

        # 读取 Redis 服务器配置
        self.host = configparser['redis_server']['host']
        self.port = int(configparser['redis_server']['port'])
        self.password_env_var_name = configparser['redis_server']['password_env_var_name']

        if self.password_env_var_name not in os.environ:
            raise ValueError(f'环境变量 {self.password_env_var_name} 未设置，请确保已正确配置环境变量')

        self.db = int(configparser['redis_server']['db'])

        self.request_stream_name = configparser['redis_server']['request_stream_name']

        self.answer_map_name = configparser['redis_server']['answer_map_name']

        logger.info('RedisManager initialized with host: %s, '
                    'port: %s, '
                    'password_env_var_name: %s, '
                    'db: %s, '
                    'request_stream_name: %s',
                    self.host, self.port, self.password_env_var_name, self.db, self.request_stream_name)

        self._connection_pool = redis.ConnectionPool(
            host=self.host,
            port=self.port,
            password=os.getenv(self.password_env_var_name),
            db=self.db
        )

        # 读取 Redis 存档配置
        self.redis_arch_enable: bool = str.lower(configparser['redis_arch'].get('redis_arch_enable', "true")) == "true"

        logger.info('RedisManager initialized with redis_arch_enable: %s', self.redis_arch_enable)

        if self.redis_arch_enable:
            self.redis_arch_host: str = configparser['redis_arch']['redis_arch_host']
            self.redis_arch_port: int = int(configparser['redis_arch']['redis_arch_port'])
            self.redis_arch_password_env_var_name: str = configparser['redis_arch']['redis_arch_password_env_var_name']
            self.redis_arch_db: int = int(configparser['redis_arch']['redis_arch_db'])
            self.redis_arch_data_stream_name: str = configparser['redis_arch']['redis_arch_data_stream_name']

            logger.info('RedisManager initialized with redis_arch_host: %s, redis_arch_port: %s, '
                        'redis_arch_password_env_var_name: %s, redis_arch_db: %s, redis_arch_data_stream_name: %s',
                        self.redis_arch_host,
                        self.redis_arch_port,
                        self.redis_arch_password_env_var_name,
                        self.redis_arch_db,
                        self.redis_arch_data_stream_name)

            self._arch_connection_pool = redis.ConnectionPool(
                host=self.redis_arch_host,
                port=self.redis_arch_port,
                password=os.getenv(self.redis_arch_password_env_var_name),
                db=self.redis_arch_db
            )

            self.enable_local_llm_describe_request = str.lower(configparser['redis_arch'].get('enable_local_llm_describe_request', "true")) == "true"
            logger.info('RedisManager initialized with enable_local_llm_describe_request: %s', self.enable_local_llm_describe_request)

            if not self.enable_local_llm_describe_request:
                self.describe_request_llm_id = configparser['redis_arch']['describe_request_llm_id']

        # 读取本地 LLM 配置
        self.local_llm_id = configparser['local_llm']['local_llm_id']
        logger.info('RedisManager initialized with local_llm_id: %s', self.local_llm_id)

        # 如果 enable_local_llm_describe_request 为 true，则使用 local_llm_id 作为 describe_request_llm_id
        if self.enable_local_llm_describe_request:
            self.describe_request_llm_id = self.local_llm_id
            logger.info('enable_local_llm_describe_request=true describe_request_llm_id will be set: %s', self.local_llm_id)
        elif self.describe_request_llm_id != "" and self.describe_request_llm_id is not None:
            logger.info('RedisManager initialized with describe_request_llm_id: %s', self.describe_request_llm_id)
        else:
            self.describe_request_llm_id = None
            logger.warning('RedisManager initialized with describe_request_llm_id: None')

    def get_redis_connection(self) -> redis.Redis:
        """
        获取 Redis 连接
        :return: redis.Redis
        """
        try:
            return redis.Redis(connection_pool=self._connection_pool)
        except redis.RedisError as e:
            logger.error("Failed to get Redis connection: %s", e)
            raise

    def get_redis_arch_connection(self) -> redis.Redis:
        """
        获取 Redis 存档连接
        :return:
        """
        try:
            return redis.Redis(connection_pool=self._arch_connection_pool)
        except redis.RedisError as e:
            logger.error("Failed to get Redis arch connection: %s", e)
            raise

    def push_request(self, stream_name: str, messages: [BaseMessage], model: str, enable_arch: bool = False) -> int:
        """
        添加请求
        :param stream_name: 流名称
        :param messages: 请求消息列表
        :param model: 模型名称
        :param enable_arch: 是否启用存档，默认：False
        :return: 请求序列号，请求序号是用于获取响应的
        """
        try:
            with self.get_redis_connection() as conn:

                seq: int = conn.incrby(f"request:{stream_name}:count")

                request: {} = {'seq': seq,
                               'model': model,
                               'messages': [msg.model_dump() for msg in messages],
                               'enable_arch': enable_arch}

                data: str = json.dumps(request)

                conn.rpush(stream_name, data)

                return seq
        except Exception as e:
            logger.error("Failed to add request: %s", e)
            raise

    def pop_request(self,
                    stream_name: str) -> {}:
        """
        获取待处理请求
        :param stream_name: 流名称
        :return: 待处理请求数据
        """
        try:
            with self.get_redis_connection() as conn:
                data: str = conn.lpop(name=stream_name)

                if data:
                    return json.loads(data)
                else:
                    return None
        except Exception as e:
            logger.error("Failed to get pending requests: %s", e)
            raise

    def pop_response(self, seq: int) -> {}:
        """
        获取响应结果

        :param seq:
        :return:
        """
        try:
            with self.get_redis_connection() as conn:
                data: str = conn.hget(name=self.answer_map_name, key=str(seq))
                if data:
                    return json.loads(data)
                else:
                    return None
        except Exception as e:
            logger.error("Failed to get response for seq %s: %s", seq, e)
            raise
        finally:
            conn.hdel(self.answer_map_name, str(seq))


    def save_response(self, seq: int, model: str, response: []):
        """
        保存响应结果
        :param seq: 请求序列号
        :param model: 模型名称
        :param response: 响应内容
        """
        try:
            with self.get_redis_connection() as conn:
                conn.hset(name=f"{self.answer_map_name}", key=str(seq), value=json.dumps({
                    "seq": seq,
                    "model": model,
                    "timestamp": str(datetime.now(timezone.utc)),
                    "answer": response
                }))

        except Exception as e:
            logger.error("Failed to save response for serial %s: %s", seq, e)
            raise

    def save_to_arch_redis(self,
                           seq: int,
                           model: str,
                           request_json: {},
                           answer_json: {},
                           llm_manager: LLMResourcesManager):
        """
        将输入消息和输出结果以 JSON 的形式保存到 redis 服务器中，为归档做准备。如果在 config.ini 配置 redis_arch_enable = false时，
        则不进行任何操作
        :param seq: 请求序列号
        :param model: 模型名称
        :param request_json: 请求内容
        :param answer_json: 响应内容
        :param llm_manager: LLM 资源管理器
        """

        if not self.redis_arch_enable:
            logger.debug(f"redis_arch_enable is false, no need to save to arch redis")
            return

        description:str = ""

        # 如果 describe_request_llm_id 为空，则不进行请求描述，否则就需要，可以查看 __init__ 函数中，关于
        # enable_local_llm_describe_request 之后的逻辑及说明
        if self.describe_request_llm_id is not None:

            with open('./prompts/describe_request.txt', 'r', encoding='utf-8') as f:
                prompt = f.read()

            messages: [BaseMessage] = []

            text: str = f"{prompt}\n\n以下是我需要帮我需要你帮我总结的内容：\n\n\n\n"

            for message in request_json['messages']:
                text += message['content']
                text += "\n"

            messages.append(HumanMessage(text))

            llm_result: LLMResult = llm_manager.generate(llm_key=self.describe_request_llm_id, base_messages=messages)

            if llm_result is not None:
                description = llm_result.generations[0][0].text

        try:
            # 构建完整的归档记录（添加 UTC 时间戳）
            record = {
                "seq": seq,
                "model": model,
                "description": description,
                "describe_model": self.describe_request_llm_id,
                "request": request_json,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "answer": answer_json
            }

            with self.get_redis_arch_connection() as conn:
                # 将记录写入 Redis
                conn.rpush(self.redis_arch_data_stream_name, json.dumps(record))
                logger.info(f"Record for serial {seq} saved to Redis")

        except RedisError as e:
            logger.error("Redis 操作失败: %s", e)
            raise RedisError(f"Failed to save to Redis: {e}") from e
        except Exception as e:
            logger.error("保存到 Redis 失败: %s", e)
            raise RuntimeError(f"Failed to save to Redis: {e}") from e

    def read_latest_from_arch_redis(self, count: int = -1) -> list:
        """
        从 Redis 流中读取最新数据
        :param count: 获取数量
        :return: 读取到的数据
        """
        try:
            with self.get_redis_arch_connection() as conn:
                # 获取 Redis 中最新的数据 '>'
                data: list = conn.lrange(name=self.redis_arch_data_stream_name, start=0, end=count)

                if data is None or len(data) == 0:
                    return []

                conn.ltrim(name=self.redis_arch_data_stream_name, start=len(data), end=-1)

                return [json.loads(item) for item in data]
        except Exception as e:
            logger.error("Failed to read latest data from Redis: %s", e)
            raise

