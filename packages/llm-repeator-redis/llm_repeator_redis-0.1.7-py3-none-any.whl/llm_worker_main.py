from llm_repeator_redis.llm_services.llm_worker import LLMWorker

def main():
    llm_worker = LLMWorker()
    llm_worker.run()

if __name__ == '__main__':
    main()