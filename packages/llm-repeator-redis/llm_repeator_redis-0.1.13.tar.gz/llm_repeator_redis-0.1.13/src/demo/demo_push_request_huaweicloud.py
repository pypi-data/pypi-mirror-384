from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from llm_client_redis import LLMClientRedis

if __name__ == '__main__':
    llm_repeator_redis = LLMClientRedis()

    model: str = "huawei_deepseek_v3_32k"

    messages: list[BaseMessage] = [SystemMessage("你是一个好助手"), HumanMessage("你好")]

    answer = llm_repeator_redis.request(messages=messages, model=model)

    print(answer)

    print('done')