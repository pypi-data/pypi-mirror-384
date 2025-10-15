from llm_repeator_redis import ChatSession
from llm_repeator_redis.cmd_chat.cmd_templates.send_template_cmd import SendTemplateCommand


def main():
    chat = ChatSession(model="home_qwq:32b",
                       llm_json_path="./llm_repeator_redis/config/llm_resources.json",
                       config_path="./llm_repeator_redis/config/config.ini",
                       max_history=8)  # 保存最近4轮对话

    chat.command_registry.register(SendTemplateCommand())

    chat.start()
    pass

if __name__ == '__main__':
    main()