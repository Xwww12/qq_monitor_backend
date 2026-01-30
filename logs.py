import logging
from logging.handlers import RotatingFileHandler
import os
import sys

def setup_logging(name="MyDashboard", log_file="dashboard.log"):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # 如果已经有处理器了，直接返回，不再重复添加
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 文件处理器
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, log_file),
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger