import os
import pymysql
from contextlib import contextmanager

class WhisperDB:
    def __init__(self):
        host = os.getenv("WHISPER_SERVER_HOST", "172.27.0.4")  # 默认用172.27.0.4，pytest环境可以修改DB_HOST
        self.connection = pymysql.connect(host=host,
                                          user='RPA',
                                          password='Zxs123',
                                          database='zxs_order')

    @contextmanager
    def cursor(self):
        cur = self.connection.cursor()
        try:
            yield cur
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def query(self, sql, params=None):
        with self.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

    def commit(self):
        self.connection.commit()

    def get_cursor(self):
        # 保留向后兼容，但建议使用 cursor() 上下文管理器
        return self.connection.cursor()

    def close(self):
        self.connection.close()

    # 实现上下文管理协议
    def __enter__(self):
        # 返回数据库连接对象本身（或其他资源）
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # 有异常时回滚，正常退出时提交
        if exc_type:
            try:
                self.connection.rollback()
            except Exception:
                pass
        else:
            try:
                self.connection.commit()
            except Exception:
                pass
        self.close()
        if exc_type:
            print(f"Error: {exc_value}")