"""
RedOAuthClient.py
=================
OAuth2 client for Xiaohongshu (RED) advertising open platform.

Features
--------
- Exchange **auth_code** for `access_token` + `refresh_token`.
- Automatically refresh the token when `access_token` is about to expire.
- Persist tokens in MySQL via WhisperDB, keeping only the latest valid pair.
- Compatible with multi-process / multi-thread deployments (uses scoped_session).

Usage
-----
>>> client = RedOAuthClient()
>>> client.fetch_token_with_auth_code("YOUR_AUTH_CODE")   # first time
>>> token = client.get_access_token()                     # thereafter
"""

import json
import datetime as dt
from typing import Optional
import time
import hashlib

import logging

import requests
from ..whisper_db import WhisperDB

# ----------------------------- OAuth2 client class --------------------------- #
class RedAuthClient:
    """Minimal OAuth2 client for Xiaohongshu advertising APIs."""

    TOKEN_URL = "https://ark.xiaohongshu.com/ark/open_api/v3/common_controller"
    REFRESH_URL = "https://ark.xiaohongshu.com/ark/open_api/v3/common_controller"

    def __init__(self, app_id, secret):
        self.app_id = app_id
        self.secret = secret

        # Load latest token if present
        self.token: Optional[dict] = self._load_latest_token()

    def _ensure_datetime(self, value):
        """Normalize value to a timezone-aware datetime (UTC). Accepts datetime/str/int."""
        if value is None:
            return None
        if isinstance(value, dt.datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=dt.timezone.utc)
            return value
        # unix timestamp (int/float)
        if isinstance(value, (int, float)):
            return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
        # try ISO format string
        if isinstance(value, str):
            try:
                # fromisoformat supports timezone if present; fallback to parsing naive then set UTC
                dtobj = dt.datetime.fromisoformat(value)
                if dtobj.tzinfo is None:
                    return dtobj.replace(tzinfo=dt.timezone.utc)
                return dtobj
            # if string not ISO, try common formats
            except Exception:
                formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")
                for fmt in formats:
                    try:
                        dtobj = dt.datetime.strptime(value, fmt)
                        return dtobj.replace(tzinfo=dt.timezone.utc)
                    except Exception:
                        continue
        # unknown type: return as-is (caller should handle)
        return value

    def _parse_expiry_to_datetime(self, val):
        """
        把各种形式的 expires 值转换为带时区的 datetime：
        - 若为 datetime，确保带 UTC tzinfo 并返回
        - 若为字符串且可转 int，按下列规则处理
        - 若为数值：
            * > 1e12: 视作毫秒级 epoch -> 转为 datetime
            * > 1e9 : 视作秒级 epoch -> 转为 datetime
            * 否则   : 视作相对秒数（expires_in） -> now + seconds
        """
        if val is None:
            return None
        # 若已是 datetime：标准化时区
        if isinstance(val, dt.datetime):
            return val if val.tzinfo else val.replace(tzinfo=dt.timezone.utc)
        # 若是字符串，尝试转 int/float
        if isinstance(val, str):
            try:
                num = int(val)
            except Exception:
                try:
                    num = int(float(val))
                except Exception:
                    # 尝试解析 ISO 字符串
                    parsed = self._ensure_datetime(val)
                    if isinstance(parsed, dt.datetime):
                        return parsed
                    return None
        elif isinstance(val, (int, float)):
            num = int(val)
        else:
            return None

        now = dt.datetime.now(dt.timezone.utc)
        # 毫秒级 epoch
        if num > 10**12:
            return dt.datetime.fromtimestamp(num / 1000.0, tz=dt.timezone.utc)
        # 秒级 epoch
        if num > 10**9:
            return dt.datetime.fromtimestamp(num, tz=dt.timezone.utc)
        # 小数值视为相对秒数
        return now + dt.timedelta(seconds=num)

    # ------------------------- Internal DB helpers --------------------------- #
    def _load_latest_token(self) -> Optional[dict]:
        """Return the newest token row as a dict, or None. 使用下标处理 DB 返回。"""
        with WhisperDB() as db:
            with db.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT access_token, refresh_token, access_expires, refresh_expires, created_at FROM red_tokens WHERE app_id = %s ORDER BY id DESC LIMIT 1",
                    (self.app_id,),
                )
                row = cursor.fetchone()
                if row:
                    # 使用下标构建统一的 dict 存入内存
                    token = {
                        "access_token": row[0],
                        "refresh_token": row[1],
                        "access_expires": self._ensure_datetime(row[2]),
                        "refresh_expires": self._ensure_datetime(row[3]),
                        "created_at": self._ensure_datetime(row[4]),
                    }
                    self.token = token
                    return token
                return None

    # ------------------------- Public API ------------------------------------ #
    def fetch_token_with_auth_code(self, auth_code: str) -> None:
        """Exchange a short-lived auth_code for access/refresh tokens."""
        # 使用网关方法 oauth.getAccessToken，方法参数为 code
        self._request_and_save(self.TOKEN_URL, method="oauth.getAccessToken", method_params={"code": auth_code})

    def get_access_token(self) -> str:
        """Return a valid access_token, refreshing it if necessary."""
        now = dt.datetime.now(dt.timezone.utc)

        # 1️⃣ refresh_token 已过期
        if (self.token is None) or (self._ensure_datetime(self.token.get("refresh_expires")) is None) or (now >= self._ensure_datetime(self.token.get("refresh_expires"))):
            recent_code = None
            try:
                with WhisperDB() as db:
                    with db.connection.cursor() as cursor:
                        cursor.execute(
                            """
                            SELECT auth_code
                            FROM red_auth_codes
                            WHERE app_id = %s and created_at > NOW() - INTERVAL 10 MINUTE
                            ORDER BY created_at DESC
                            LIMIT 1
                            """,
                            (self.app_id,),
                        )
                        row = cursor.fetchone()
                        if row:
                            recent_code = row[0]
            except Exception as exc:
                logging.error("Unable to query auth_code table: %s", exc)

            if recent_code:  # 尝试用新 auth_code
                logging.info("Using recent auth_code to obtain new tokens...")
                self.fetch_token_with_auth_code(recent_code)
            else:
                logging.warning("refresh_token & auth_code both expired; manual re-auth required.")
                #发送如下授权链接
                #https://ark.xiaohongshu.com/ark/authorization?appId=4b8ab3245c704723a6d1&redirectUri=https%3A%2F%2Fzxslife.com%2FredServer%2Findex_for_store.php&state=4b8ab3245c704723a6d1
                #raise RuntimeError("需要重新授权.")
                raise RuntimeError("需要重新授权.")

        # 2️⃣ access_token 即将过期
        if self._is_access_expired():
            self._refresh_token()

        return self.token["access_token"]

    # -------------------- Token refresh / storage --------------------------- #
    def _is_access_expired(self) -> bool:
        """Check if access_token is within 60 s of expiry; handle missing token safely."""
        if not self.token:
            return True
        access_exp = self._ensure_datetime(self.token.get("access_expires"))
        if not access_exp:
            # 若没有到期时间，视为过期以触发刷新流程
            return True
        return dt.datetime.now(dt.timezone.utc) >= access_exp - dt.timedelta(seconds=60)

    def _refresh_token(self) -> None:
        # 使用网关方法 oauth.refreshToken（按文档可能不同，如需调整请替换 method 名）
        self._request_and_save(self.REFRESH_URL, method="oauth.refreshToken", method_params={"refresh_token": self.token["refresh_token"]})

    def _request_and_save(self, url: str, method: str, method_params: dict) -> None:
        """Send POST request to Xiaohongshu gateway with required gateway fields and persist token set."""
        # 网关基础参数
        # 文档示例中 timestamp 使用秒级整数
        ts = str(int(time.time()))
        gateway = {
            "appId": self.app_id,
            "version": "2.0",
            "method": method,
            "timestamp": ts,
        }
        # 将 method 参数合并进请求体（注意不覆盖 gateway 字段）
        payload = {**gateway, **(method_params or {})}
        # 计算 sign 并加入
        payload["sign"] = self.generate_sign(payload)

        max_attempts = 3
        backoff = 1
        for attempt in range(1, max_attempts + 1):
            try:
                logging.debug("Request payload: %s", json.dumps(payload, ensure_ascii=False))
                resp = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=10)
                resp.raise_for_status()
                body = resp.json()
                break
            except requests.exceptions.RequestException as exc:
                logging.warning("Request attempt %d failed: %s", attempt, exc)
                if attempt < max_attempts:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                else:
                    logging.error("All request attempts failed.")
                    raise
            except ValueError as exc:
                logging.error("Failed to decode JSON response: %s", exc)
                raise

        logging.debug("Response body: %s", json.dumps(body, ensure_ascii=False))
        if not body.get("success"):
            logging.error("OAuth error response: %s", body)
            raise RuntimeError("Xiaohongshu OAuth error %s: %s" % (body.get("code"), body.get("msg")))

        data = body.get("data") or {}

        access_token = data.get("accessToken")
        refresh_token = data.get("refreshToken")
        access_raw = data.get("accessTokenExpiresAt")
        refresh_raw = data.get("refreshTokenExpiresAt")

        access_expires = self._parse_expiry_to_datetime(access_raw)
        refresh_expires = self._parse_expiry_to_datetime(refresh_raw)
        now = dt.datetime.now(dt.timezone.utc)
        if access_expires is None:
            logging.warning("access_expires parse failed, fallback to now")
            access_expires = now
        if refresh_expires is None:
            logging.warning("refresh_expires parse failed, fallback to now")
            refresh_expires = now

        if not access_token or not refresh_token:
            logging.error("Token response missing access or refresh token: %s", data)
            raise RuntimeError("Invalid token response; missing access_token or refresh_token")

        canonical = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_expires": access_expires,
            "refresh_expires": refresh_expires,
            "user_id": data.get("user_id") or data.get("sellerId"),
            "advertiser_id": data.get("sellerId"),
        }

        # 将已规范化的数据保存
        self._save_token(canonical)

    def generate_sign(self, params: dict) -> str:
        """
        按开放平台新版 sign 算法生成签名（MD5）：
        拼接规则：method + "?" + "appId={appId}&timestamp={timestamp}&version={version}" + appSecret
        对拼接后的字符串做 MD5，返回小写 hex 字符串。
        注意：method-specific 的参数（例如 code、refresh_token）不参与签名计算。
        """
        method = params.get("method", "")
        appId = params.get("appId", "")
        timestamp = params.get("timestamp", "")
        version = params.get("version", "")
        # 构造待签名字符串（严格按文档顺序：appId, timestamp, version）
        raw = f"{method}?appId={appId}&timestamp={timestamp}&version={version}{self.secret or ''}"
        md5 = hashlib.md5()
        md5.update(raw.encode("utf-8"))
        return md5.hexdigest()

    def _save_token(self, data: dict) -> None:
        """Persist the newest token pair to DB and update in-memory copy.
        输入已是规范化字段：access_token, refresh_token, access_expires(datetime), refresh_expires(datetime), user_id, advertiser_id
        """
        now = dt.datetime.now(dt.timezone.utc)
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        access_expires = data.get("access_expires") or now
        refresh_expires = data.get("refresh_expires") or now

        with WhisperDB() as db:
            with db.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO red_tokens (
                        app_id, user_id, advertiser_id, access_token,
                        refresh_token, access_expires, refresh_expires, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.app_id,
                        data.get("user_id"),
                        data.get("advertiser_id"),
                        access_token,
                        refresh_token,
                        access_expires,
                        refresh_expires,
                        now,
                    ),
                )
                last_id = cursor.lastrowid
            db.commit()

        # Update in-memory token (统一使用 access_expires / refresh_expires datetime)
        self.token = {
            "id": last_id,
            "app_id": self.app_id,
            "user_id": data.get("user_id"),
            "advertiser_id": data.get("advertiser_id"),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_expires": access_expires,
            "refresh_expires": refresh_expires,
            "created_at": now,
        }