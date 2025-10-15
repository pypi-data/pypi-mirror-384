import json
import logging
import os.path
import time
from configparser import ConfigParser

from llm_repeator_redis.redis_services.redis_read_manager import RedisManager

# 模块级别的日志配置
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

if not logger.handlers:
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

class ArchFromRedisWorker:
    def __init__(self, config_path: str = './config/config.ini'):
        """

        :param config_path:
        """
        logger.info(f'ArchFromRedisWorker init start')

        configparser: ConfigParser = ConfigParser()

        configparser.read(config_path, encoding="utf-8")

        self.redis_manager = RedisManager(configparser=configparser)

        self.archive_interval: int = configparser.getint('archive', 'archive_interval')
        logger.info(f'archive_interval: {self.archive_interval}')

        self.archive_dir_path: str = configparser.get('archive', 'archive_dir_path')
        logger.info(f'archive_dir_path: {self.archive_dir_path}')

        logger.info(f'ArchFromRedisWorker init success')

    def run(self):
        while True:

            if not os.path.exists(self.archive_dir_path):
                logger.error(f'Archive directory {self.archive_dir_path} does not exist, sleeping for {self.archive_interval} seconds')
                time.sleep(self.archive_interval)
                continue

            logs:[] = self.redis_manager.read_latest_from_arch_redis(count=2)

            if logs is None or len(logs) == 0:
                logger.debug(f'No logs to archive, sleeping for {self.archive_interval} seconds')
                time.sleep(self.archive_interval)
                continue

            for log in logs:

                model: str = log['request']['model']

                model = (model.replace('/', '_').replace('\\', '_')
                         .replace(':', '_').replace('*', '_').replace('?', '_')
                         .replace('"', '_').replace('<', '_').replace('>', '_')
                         .replace('|', '_'))

                model_dir = os.path.join(self.archive_dir_path, model)

                if not os.path.exists(model_dir):
                    os.makedirs(model_dir)
                    logger.info(f'Created directory {model_dir}')

                # 获取当天日期
                today: str = time.strftime("%Y-%m-%d", time.localtime())

                date_dir = os.path.join(model_dir, today)

                if not os.path.exists(date_dir):
                    os.makedirs(date_dir)
                    logger.info(f'Created directory {date_dir}')

                # 生成文件名
                # 获取当前时间的毫秒数
                current_time = time.strftime("%Y%m%d%H%M%S", time.localtime())

                file_name = f"{current_time}_{model}_{log['seq']}.json"

                file_path = os.path.join(date_dir, file_name)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(json.dumps(log, ensure_ascii=False, indent=4))
                    logger.info(f'Archived log to {file_path}')

            time.sleep(self.archive_interval)


if __name__ == '__main__':
    arch_worker = ArchFromRedisWorker()
    arch_worker.run()
