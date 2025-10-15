from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from llm_client_redis import LLMClientRedis
from llm_client_redis.tools import OutputTools

if __name__ == '__main__':
    llm_repeator_redis = LLMClientRedis()

    model: str = "home_qwen3:32b"

    messages: list[BaseMessage] = [SystemMessage("你是一个好助手"), HumanMessage("你好")]

    answer = llm_repeator_redis.request(messages=messages, model=model)

    print(answer)
    result: str = OutputTools.remove_think(answer["answer"]).strip()

    print(result)

    print('done')