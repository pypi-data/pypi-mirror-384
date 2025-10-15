from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage

from llm_repeator_redis import LLMRepeaterRedis

if __name__ == '__main__':
    llm_repeator_redis = LLMRepeaterRedis(llm_json_path="config/llm_resources.json",
                                          config_path="config/config.ini")

    model: str = "huawei_deepseek_v3_4k"

    messages: [BaseMessage] = [SystemMessage("你是一个好助手"), HumanMessage("你好")]

    answer = llm_repeator_redis.request(messages=messages, model=model)

    print(answer)

    print('done')