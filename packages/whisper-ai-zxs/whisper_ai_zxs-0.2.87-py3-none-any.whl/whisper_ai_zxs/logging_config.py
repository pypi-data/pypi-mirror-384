import logging
import logging.config
import logging.handlers
import queue
import socket
import os
import sys
from .whisper_db import WhisperDB

# 创建日志队列
log_queue = queue.Queue(-1)

def get_server_ip():
    try:
        # 获取主机名
        hostname = socket.gethostname()
        # 获取主机的IP地址
        ip_address = socket.gethostbyname(hostname)
        return ip_address
    except socket.error as e:
        print(f"Error getting IP address: {e}")
        return None

# 自定义 MySQL 处理器
class MySQLHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.server_name = get_server_ip()

    def emit(self, record):
        try:
            log_entry = self.format(record)  # 确保格式化日志

            # 短连接模式，避免连接超时
            db = WhisperDB()
            connection = db.connection
            cursor = connection.cursor()

            sql = """INSERT INTO openai_logs 
                     (server_name, level, message, logger_name, filename, line_no) 
                     VALUES (%s, %s, %s, %s, %s, %s)"""
            data = (self.server_name, record.levelname, log_entry, record.name, record.filename, record.lineno)
            
            cursor.execute(sql, data)
            connection.commit()
        except Exception as e:
            print(f"MySQL logging error: {e}", file=sys.stderr)
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'connection' in locals():
                connection.close()

# 判断是否是pytest环境
is_testing = os.getenv("TEST_ENV", "") == "true"  # 或者通过其他方式来判断

# 定义日志配置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(levelname)s - %(message)s [%(name)s - %(filename)s:%(lineno)d]" if is_testing else "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "DEBUG",
        },
        # 如果是测试环境，移除数据库相关的配置
        "queue": {
            "()": logging.handlers.QueueHandler,
            "queue": log_queue
        },
    },
    "loggers": {
        "whisper_ai": {
            "level": "DEBUG" if is_testing else "INFO",
            "handlers": ["console"] if is_testing else ["console", "queue"],
            "propagate": False,
        }
    },
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)

    if not is_testing:
        mysql_handler = MySQLHandler()
        listener = logging.handlers.QueueListener(log_queue, mysql_handler, respect_handler_level=True)
        listener.start()

    print("Logging system initialized")  # 方便调试
