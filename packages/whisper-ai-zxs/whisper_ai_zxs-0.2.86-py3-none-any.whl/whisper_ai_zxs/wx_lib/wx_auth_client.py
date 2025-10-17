# ...existing code...
import time
import requests
import logging

from ..whisper_db import WhisperDB  # 假设项目中有 WhisperDB 类

class WXAuthClient:
    def __init__(self, appid: str, secret: str):
        self.appid = appid
        self.secret = secret

    def get_appid(self) -> str:
        return self.appid

    def get_secret(self) -> str:
        return self.secret

    def get_access_token(self) -> str:
        access_token = ""
        try:
            with WhisperDB() as db:
                with db.connection.cursor() as cursor:
                    sql = "SELECT `access_token`, `expires_time` FROM `wx_info` WHERE `token_type` = %s"
                    cursor.execute(sql, (self.secret,))
                    row = cursor.fetchone()

                    # 将可能为 tuple/列表的 row 转换为 dict，便于后续使用 row.get(...)
                    if row and not isinstance(row, dict):
                        desc = None
                        try:
                            desc = getattr(cursor, "description", None)
                        except Exception:
                            desc = None

                        if desc:
                            # cursor.description -> sequence of sequences, first item is column name
                            col_names = [d[0] for d in desc]
                            row = {k: v for k, v in zip(col_names, row)}
                        else:
                            # 兜底：按 SQL 查询的列顺序映射
                            row = {
                                "access_token": row[0] if len(row) > 0 else "",
                                "expires_time": row[1] if len(row) > 1 else 0
                            }

                    if row:
                        access_token = row.get("access_token", "") or ""
                        expires_time = int(row.get("expires_time", 0) or 0)
                        # 如果过期（比当前时间早10秒或更早），则尝试刷新
                        if expires_time <= int(time.time()) - 10:
                            token_dict = self._get_token()
                            new_token = token_dict.get("access_token", "") if token_dict else ""
                            if new_token:
                                access_token = new_token
                                new_expires = int(time.time()) + token_dict.get("expires_in", 0)
                                update_sql = "UPDATE `wx_info` SET `access_token`=%s, `expires_time`=%s WHERE `token_type` = %s"
                                cursor.execute(update_sql, (access_token, new_expires, self.secret))
                                db.connection.commit()
                            else:
                                # 刷新失败：保留旧 token（如果有），并记录警告
                                logging.warning("刷新微信 token 失败，保留旧 token（如果存在）。")
                    else:
                        # DB 中无记录，尝试获取一次 token；仅在获取到有效 token 时插入
                        token_dict = self._get_token()
                        new_token = token_dict.get("access_token", "") if token_dict else ""
                        if new_token:
                            access_token = new_token
                            new_expires = int(time.time()) + token_dict.get("expires_in", 0)
                            insert_sql = "INSERT INTO `wx_info` (`access_token`, `expires_time`, `token_type`) VALUES (%s, %s, %s)"
                            cursor.execute(insert_sql, (access_token, new_expires, self.secret))
                            db.connection.commit()
                        else:
                            # 无可用 token，抛出异常以便上层重试或处理
                            raise RuntimeError("无法获取微信 access_token（初次获取失败）")

        except Exception as e:
            logging.exception("获取微信 token 失败: %s", e)
            # 如果数据库操作失败，仍尝试直接获取一次 token（但仅在获取到有效 token 时返回）
            if not access_token:
                token_dict = self._get_token()
                if token_dict and token_dict.get("access_token"):
                    access_token = token_dict.get("access_token", "")
                else:
                    # 无有效 token，抛出异常，避免写入空 token 到 DB，呼叫方可重试
                    raise RuntimeError(f"获取微信 access_token 失败: {e}")

        return access_token

    def _get_token(self) -> dict:
        try:
            url = "https://api.weixin.qq.com/cgi-bin/stable_token"
            payload = {
                "grant_type": "client_credential",
                "appid": self.appid,
                "secret": self.secret
            }
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("access_token") and data.get("expires_in"):
                return {
                    "access_token": data.get("access_token", ""),
                    "expires_in": data.get("expires_in", 0)
                }
            logging.warning("微信获取 token 返回为空 errcode: %s", data)
        except Exception as e:
            logging.exception("请求微信 gettoken 接口失败: %s", e)
        return {}