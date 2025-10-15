import json
import logging


class InitConfigTools:
    @staticmethod
    def create_llm_resources_file(path: str):
        """

        :param path:
        :return:
        """
        template: dict = {
          "deepseek_r1": {
            "model": "deepseek-reasoner",
            "version": "R1",
            "base_url": "https://api.deepseek.com",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "DEEPSEEK_API_KEY",
            "response_type": "deepseek-reasoner",
            "description": "DeepSeek R1 模型 LangChain 接口"
          },
          "deepseek_v3": {
            "model": "deepseek-chat",
            "version": "V3",
            "base_url": "https://api.deepseek.com",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "DEEPSEEK_API_KEY",
            "response_type": "deepseek-chat",
            "description": "DeepSeek V3 模型 LangChain 接口"
          },
          "huawei_deepseek_r1_32k": {
            "model": "DeepSeek-R1",
            "version": "R1",
            "base_url": "https://maas-cn-southwest-2.modelarts-maas.com/deepseek-r1/v1",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "HUAWEI_MODEL_ART_API_KEY",
            "response_type": "deepseek-reasoner",
            "description": "华为云的 DeepSeek R1 32K 模型 LangChain DeepSeek 接口"
          },
          "huawei_deepseek_v3_32k": {
            "model": "DeepSeek-V3",
            "version": "V1",
            "base_url": "https://maas-cn-southwest-2.modelarts-maas.com/deepseek-v3/v1",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "HUAWEI_MODEL_ART_API_KEY",
            "response_type": "deepseek-chat",
            "description": "华为云的 DeepSeek V3 32K 模型 LangChain DeepSeek 接口"
          },
          "huawei_DeepSeek-R1-32K-0528": {
            "model": "deepseek-r1-250528",
            "version": "R1",
            "base_url": "https://api.modelarts-maas.com/v1",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "HUAWEI_MODEL_ART_API_KEY",
            "response_type": "deepseek-reasoner",
            "description": "华为云的 DeepSeek-R1-32K-0528 模型 LangChain DeepSeek 接口"
          },
          "huawei_qwen3-32b": {
            "model": "qwen3-32b",
            "version": "V1",
            "base_url": "https://api.modelarts-maas.com/v1",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "HUAWEI_MODEL_ART_API_KEY",
            "response_type": "deepseek-chat",
            "description": "华为云的 qwen3-32b 模型 LangChain DeepSeek 接口"
          },
          "huawei_qwen3-235b-a22b": {
            "model": "qwen3-235b-a22b",
            "version": "V1",
            "base_url": "https://api.modelarts-maas.com/v1",
            "type": "BaseChatOpenAI",
            "provider": "langchain-deepseek",
            "env_api_key_name": "HUAWEI_MODEL_ART_API_KEY",
            "response_type": "deepseek-chat",
            "description": "华为云的 qwen3-235b-a22b 模型 LangChain DeepSeek 接口"
          },
          "home_deepseek-r1:32b": {
            "model": "deepseek-r1:32b",
            "version": "32b",
            "base_url": "https://localhost:11434",
            "type": "BaseLLM",
            "provider": "langchain-ollama",
            "env_api_key_name": None,
            "response_type": "deepseek-reasoner",
            "description": "本地 DeepSeek R1 32b 模型 LangChain 接口"
          },
          "home_qwen3:32b": {
            "model": "qwen3:32b",
            "version": "32b",
            "base_url": "https://localhost:11434",
            "type": "BaseLLM",
            "provider": "langchain-ollama",
            "env_api_key_name": None,
            "response_type": "deepseek-reasoner",
            "description": "本地 qwen3:32b 模型 LangChain 接口"
          }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(template, f, indent=4)
        logging.info(f"Created default llm_resources.json at {path}")

    @staticmethod
    def create_config_file(path: str):
        """
        """
        template: str = """# config.ini

[redis_server]
# Redis 服务器的主机地址
host = localhost

# Redis 服务器的端口号
port = 6379

# Redis 密码的环境变量名称（通过环境变量读取密码）
password_env_var_name = REDIS_AUTHENTICATION

# Redis 数据库编号
db = 1

# 用于请求的 Redis 数据流名称
request_stream_name = request_stream

# 用于响应的 Redis 数据配对名称
answer_map_name = answer_map

# 用于响应的 Redis 数据流名称前辍，前辍包含:号，加上序号则表示响应流 list 的名称
chunk_stream_prefix = chunk_stream:

# 用于深入分析的 Redis 数据流名称前辍，前辍包含:号，加上序号则表示响应流 list 的名称
reasoning_stream_prefix = reasoning_stream:

[logging]
# 日志级别，可选值有 DEBUG, INFO, WARNING, ERROR, CRITICAL
level = INFO


[redis_arch]
# 是否启用 Redis 归档功能，true 表示启用，false 表示禁用
redis_arch_enable = true

# Redis 归档服务器的主机地址
redis_arch_host = localhost

# Redis 归档服务器的端口号
redis_arch_port = 6379

# Redis 归档服务器密码的环境变量名称（通过环境变量读取密码）
redis_arch_password_env_var_name = REDIS_AUTHENTICATION

# Redis 归档服务器使用的数据库编号
redis_arch_db = 2

# Redis 归档数据流名称
redis_arch_data_stream_name = arch_stream

# 开启本地llm 描述请求，并保存到归档内容，此时将使用 [local_llm] local_llm_id 来进行请求的描述，同时 describe_request_llm_id 不生效。
# 但如果 local_llm_id 为 false，同时 describe_request_llm_id 指定了有效的llm编号，则 使用指定llm来进行请求的描述。
enable_local_llm_describe_request = false

# 描述请求的llm编号，如果为空，则不描述请求，只有在 enable_local_llm_describe_request 为 false 时生效。
# 请注意，如果 enable_local_llm_describe_request 为 false 且 describe_request_llm_id 为空，则不会描述请求。
describe_request_llm_id=


[llm_worker]
# 获取请求的时间间隔
request_internal=0.3


[local_llm]
local_llm_id = home_qwen3:32b


[archive]
# 归档的文件路径
archive_dir_path = d:/llm_logs_archive/
# 归档的时间间隔（单位：秒）
archive_interval = 60
"""
        with open(path, "w", encoding="utf-8") as _f:
            _f.write(template)
        logging.info(f"Created default config.ini at {path}")