# llm_repeator_redis

## 项目简述

## 使用方法

### 01. 环境准备

确保你已经安装了所需的依赖包。你可以使用 `pip` 安装这些依赖包：

```bash
pip install -r requirements.txt
```

### 02. 配置文件 

`llm_worker` 依赖于配置文件来读取 Redis 和 LLM 的配置信息。确保以下配置文件存在并正确配置：

- **config.ini**：包含 Redis 和 LLM 的配置信息。
- **llm_resources.json**：包含 LLM 模型的资源信息。

### 03. 配置文件 

确保设置了 Redis 密码的环境变量。例如：

```bash
export REDIS_PASSWORD=your_redis_password
export REDIS_ARCH_PASSWORD=your_redis_arch_password
```

### 04.启动 llm_workder

`llm_worker` 是一个用于处理 LLM（Large Language Model）请求的 Redis 中继程序。它从 Redis 队列中获取请求，调用相应的 LLM 模型生成响应，并将响应保存回 Redis。以下是启动 `llm_worker` 的步骤：

```bash
python src/llm_services/llm_worker.py
```

### 05.启动 arch_worker

`arch_worker` 是一个用于从 Redis 中读取归档数据并将其保存到本地文件系统的程序。它定期从 Redis 中读取最新的归档记录，并将这些记录保存到指定的目录中。以下是启动 `arch_worker` 的步骤：

在终端中导航到项目目录并运行 `arch_worker.py`：

```bash
python src/arch_services/arch_worker.py
```

### 06. 使用 LLMRepeatorRedis 交互

`LLMRepeatorRedis` 类提供了一个接口，用于将请求消息推送到 Redis 队列中，并获取 LLM（Large Language Model）的响应。以下是使用 `LLMRepeatorRedis` 类进行交互的详细步骤和示例代码。

#### 1. 初始化 LLMRepeatorRedis

首先，你需要初始化 `LLMRepeatorRedis` 类的实例。你可以通过指定配置文件路径和 LLM 资源文件路径来初始化。

```python
from llm_services.llm_repeator_redis import LLMRepeatorRedis

# 初始化 LLMRepeatorRedis 实例
llm_repeater = LLMRepeatorRedis(llm_json_path='../config/llm_resources.json', config_path='../config/config.ini')
```


#### 2. 发送请求并获取响应

`LLMRepeatorRedis` 类提供了多种方法来发送请求并获取响应。以下是每种方法的详细说明和示例代码。

##### 2.1 `request` 方法

`request` 方法是最基本的方法，用于将请求消息推送到 Redis 队列中，并获取响应。

**参数**：
- `messages`: 请求消息列表，类型为 `List[BaseMessage]`。
- `model`: 使用的模型名称，类型为 `str`。
- `block_time`: 阻塞时间，单位为秒，默认为 5 分钟。
- `internal`: 请求答案的时间间隔，单位为秒，默认为 1 秒。

**示例代码**：

```python
from langchain_core.messages import SystemMessage, HumanMessage

# 创建消息列表
messages = [
    SystemMessage("You are a helpful assistant."),
    HumanMessage("What is the capital of France?")
]

# 发送请求并获取响应
response = llm_repeater.request(messages=messages, model='home_deepseek-r1:8b-llama-distill-fp16')

print(response)
```


##### 2.2 `request_messages` 方法

`request_messages` 方法与 `request` 方法类似，但它允许你在获取响应后根据配置文件中的 `response_type` 进行进一步处理。

**参数**：
- `messages`: 请求消息列表，类型为 `List[BaseMessage]`。
- `model`: 使用的模型名称，类型为 `str`。
- `block_time`: 阻塞时间，单位为秒，默认为 5 分钟。
- `internal`: 请求答案的时间间隔，单位为秒，默认为 1 秒。

**示例代码**：

```python
# 创建消息列表
messages = [
    SystemMessage("You are a helpful assistant."),
    HumanMessage("What is the capital of France?")
]

# 发送请求并获取响应
response = llm_repeater.request_messages(messages=messages, model='home_deepseek-r1:8b-llama-distill-fp16')

print(response)
```


##### 2.3 `request_str_human` 方法

`request_str_human` 方法用于快速发送包含系统提示和人类消息的请求。

**参数**：
- `system`: 系统提示词，类型为 `str`。
- `human`: 人类消息，类型为 `str`。
- `model`: 使用的模型名称，类型为 `str`。
- `block_time`: 阻塞时间，单位为秒，默认为 5 分钟。
- `internal`: 请求答案的时间间隔，单位为秒，默认为 1 秒。

**示例代码**：

```python
# 发送请求并获取响应
response = llm_repeater.request_str_human(
    system="You are a helpful assistant.",
    human="What is the capital of France?",
    model='home_deepseek-r1:8b-llama-distill-fp16'
)

print(response)
```


##### 2.4 `request_file_human` 方法

`request_file_human` 方法用于从文件中读取系统提示词，并发送包含系统提示和人类消息的请求。

**参数**：
- `system_file_path`: 系统提示词文件路径，类型为 `str`。
- `human`: 人类消息，类型为 `str`。
- `model`: 使用的模型名称，类型为 `str`。
- `block_time`: 阻塞时间，单位为秒，默认为 5 分钟。
- `internal`: 请求答案的时间间隔，单位为秒，默认为 1 秒。

**示例代码**：

```python
# 发送请求并获取响应
response = llm_repeater.request_file_human(
    system_file_path='../prompts/system_prompt.txt',
    human="What is the capital of France?",
    model='home_deepseek-r1:8b-llama-distill-fp16'
)

print(response)
```


通过以上步骤和示例代码，你可以轻松地使用 `LLMRepeatorRedis` 类与 LLM 进行交互，并处理响应。

## 配置文件说明

### config.ini

### llm_resources.json

## 开发备忘

### 更新 requirements.txt 文件

前提是安装了 pipreqs：
```bash
pip install pipreqs
```

执行命令：
```bash
pipreqs . --force --encoding=utf-8
```

### 打包成 whl 文件

# 成生分包文件
```bash
python -m build
```

文件将在 `dist` 目录下生成。