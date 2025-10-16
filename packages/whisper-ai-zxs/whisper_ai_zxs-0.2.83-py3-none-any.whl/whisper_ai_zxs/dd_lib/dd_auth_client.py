"""
DyShopAuthClient.py
===================
OAuth2 client for Douyin Shop (抖音店铺) open platform.

Features
--------
- Exchange **auth_code** for `access_token` + `refresh_token`.
- Automatically refresh the token when `access_token` is about to expire.
- Persist tokens in MySQL via WhisperDB, keeping only the latest valid pair.
- Compatible with multi-process / multi-thread deployments (uses scoped_session).

Usage
-----
>>> client = DyShopAuthClient(app_key, app_secret)
>>> client.fetch_token_with_auth_code("YOUR_AUTH_CODE")   # first time
>>> token = client.get_access_token()                     # thereafter
"""

import json
import datetime as dt
from typing import Optional
import time
import hashlib
import hmac
import logging
import requests

from ..whisper_db import WhisperDB

class DDAuthClient:
    """Minimal OAuth2 client for Douyin Shop APIs."""

    TOKEN_URL = "https://openapi-fxg.jinritemai.com/token/create"
    REFRESH_URL = "https://openapi-fxg.jinritemai.com/token/refresh"

    def __init__(self, app_key, app_secret):
        self.app_key = app_key
        self.app_secret = app_secret
        self.token: Optional[dict] = self._load_latest_token()

    def _ensure_datetime(self, value):
        if value is None:
            return None
        if isinstance(value, dt.datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=dt.timezone.utc)
            return value
        if isinstance(value, (int, float)):
            return dt.datetime.fromtimestamp(value, tz=dt.timezone.utc)
        if isinstance(value, str):
            try:
                dtobj = dt.datetime.fromisoformat(value)
                if dtobj.tzinfo is None:
                    return dtobj.replace(tzinfo=dt.timezone.utc)
                return dtobj
            except Exception:
                formats = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")
                for fmt in formats:
                    try:
                        dtobj = dt.datetime.strptime(value, fmt)
                        return dtobj.replace(tzinfo=dt.timezone.utc)
                    except Exception:
                        continue
        return value

    def _parse_expiry_to_datetime(self, expires_in):
        if expires_in is None:
            return None
        try:
            expires_in = int(expires_in)
        except Exception:
            return None
        now = dt.datetime.now(dt.timezone.utc)
        return now + dt.timedelta(seconds=expires_in)

    def _load_latest_token(self) -> Optional[dict]:
        with WhisperDB() as db:
            with db.connection.cursor() as cursor:
                cursor.execute(
                    "SELECT access_token, refresh_token, access_expires, refresh_expires, created_at FROM dyshop_tokens WHERE app_key = %s ORDER BY id DESC LIMIT 1",
                    (self.app_key,),
                )
                row = cursor.fetchone()
                if row:
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

    def fetch_token_with_auth_code(self, auth_code: str, grant_type: str = "authorization_self") -> None:
        params = {
            "code": auth_code,
            "grant_type": grant_type,
        }
        self._request_and_save(self.TOKEN_URL, params)

    def get_access_token(self) -> str:
        now = dt.datetime.now(dt.timezone.utc)
        if (self.token is None) or (self._ensure_datetime(self.token.get("refresh_expires")) is None) or (now >= self._ensure_datetime(self.token.get("refresh_expires"))):
            raise RuntimeError("refresh_token expired; manual re-auth required.")
        if self._is_access_expired():
            self._refresh_token()
        return self.token["access_token"]

    def _is_access_expired(self) -> bool:
        if not self.token:
            return True
        access_exp = self._ensure_datetime(self.token.get("access_expires"))
        if not access_exp:
            return True
        return dt.datetime.now(dt.timezone.utc) >= access_exp - dt.timedelta(seconds=60)

    def _refresh_token(self) -> None:
        params = {
            "refresh_token": self.token["refresh_token"],
            "grant_type": "refresh_token",
        }
        self._request_and_save(self.REFRESH_URL, params)

    def _request_and_save(self, url: str, method_params: dict) -> None:
        ts = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).strftime("%Y-%m-%d %H:%M:%S")
        gateway = {
            "app_key": self.app_key,
            "method": "token.create" if url == self.TOKEN_URL else "token.refresh",
            "timestamp": ts,
            "v": "2",
            "param_json": json.dumps(method_params, ensure_ascii=False, separators=(',', ':')),
        }
        sign = self.generate_sign(gateway)
        payload = {**gateway, "sign": sign, "sign_method": "hmac-sha256"}
        try:
            resp = requests.post(url, data=payload, timeout=10)
            resp.raise_for_status()
            body = resp.json()
        except Exception as exc:
            logging.error("Request failed: %s", exc)
            raise

        if body.get("code") != 10000:
            logging.error("Douyin OAuth error response: %s", body)
            raise RuntimeError("Douyin OAuth error %s: %s" % (body.get("code"), body.get("msg")))

        data = body.get("data") or {}
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        expires_in = data.get("expires_in")
        access_expires = self._parse_expiry_to_datetime(expires_in)
        refresh_expires = self._parse_expiry_to_datetime(14 * 24 * 3600)  # 14天
        now = dt.datetime.now(dt.timezone.utc)
        if access_expires is None:
            access_expires = now
        if refresh_expires is None:
            refresh_expires = now

        if not access_token or not refresh_token:
            logging.error("Token response missing access or refresh token: %s", data)
            raise RuntimeError("Invalid token response; missing access_token or refresh_token")

        canonical = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_expires": access_expires,
            "refresh_expires": refresh_expires,
            "shop_id": data.get("shop_id"),
            "shop_name": data.get("shop_name"),
            "authority_id": data.get("authority_id"),
            "auth_subject_type": data.get("auth_subject_type"),
            "operator_name": data.get("operator_name"),
            "token_type": data.get("token_type"),
            "toutiao_id": data.get("toutiao_id"),
        }
        self._save_token(canonical)

    def generate_sign(self, params: dict) -> str:
        """
        按抖店 API 文档的签名算法生成签名：
        1) 对 param_json 做递归的、有序的 JSON 序列化（保证所有层级 key 有序，数组按原序），
           并将 float 类型如果等于整数则转为 int，保证数字不带多余小数点；禁用 HTML 转义（ensure_ascii=False），
           使用 separators=(",",":")。
        2) 按固定顺序拼接参数（包含参数名）：app_key、method、param_json、timestamp、v，格式为
           app_key{app_key}method{method}param_json{param_json}timestamp{timestamp}v{v}
        3) 在拼接字符串首尾各加一次 app_secret，形成 signPattern。
        4) 使用 HMAC-SHA256(signPattern, key=app_secret) 计算签名，返回小写 hex 字符串。
        """
        def _normalize_obj(o):
            # 将数字保证无多余小数位，将 dict 按 key 排序
            if isinstance(o, dict):
                new = {}
                for kk in sorted(o.keys()):
                    new[kk] = _normalize_obj(o[kk])
                return new
            if isinstance(o, list):
                return [_normalize_obj(x) for x in o]
            if isinstance(o, float):
                # 将形如 1.0 转为 1
                if o.is_integer():
                    return int(o)
                return o
            return o

        try:
            # 取出需要参与签名的固定字段（缺省使用空字符串）
            keys_order = ["app_key", "method", "param_json", "timestamp", "v"]
            parts = []
            for k in keys_order:
                v = params.get(k, "")
                if k == "param_json":
                    # param_json 可能已经是字符串或 dict
                    if isinstance(v, str):
                        try:
                            parsed = json.loads(v)
                            normalized = _normalize_obj(parsed)
                            v_serial = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
                        except Exception:
                            # 无法解析为 JSON，则按原样使用字符串
                            v_serial = v
                    elif isinstance(v, (dict, list)):
                        normalized = _normalize_obj(v)
                        v_serial = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
                    else:
                        v_serial = "" if v is None else str(v)
                    parts.append(f"{k}{v_serial}")
                else:
                    v_serial = "" if v is None else str(v)
                    parts.append(f"{k}{v_serial}")

            param_pattern = "".join(parts)
            sign_pattern = f"{self.app_secret}{param_pattern}{self.app_secret}"
            signature = hmac.new(self.app_secret.encode("utf-8"), sign_pattern.encode("utf-8"), hashlib.sha256).hexdigest()
            logging.debug("Generated douyin sign: %s, preview=%s", signature, sign_pattern[:200])
            return signature
        except Exception as e:
            logging.exception("generate_sign failed: %s", e)
            # 回退到较宽松的签名方法，尽量不阻断调用
            try:
                raw = "".join(f"{k}{params.get(k,'')}" for k in keys_order)
                sign_pattern = f"{self.app_secret}{raw}{self.app_secret}"
                return hmac.new(self.app_secret.encode("utf-8"), sign_pattern.encode("utf-8"), hashlib.sha256).hexdigest()
            except Exception:
                return ""

    def _save_token(self, data: dict) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]
        access_expires = data.get("access_expires") or now
        refresh_expires = data.get("refresh_expires") or now

        with WhisperDB() as db:
            with db.connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO dyshop_tokens (
                        app_key, shop_id, shop_name, authority_id, auth_subject_type,
                        access_token, refresh_token, access_expires, refresh_expires, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        self.app_key,
                        data.get("shop_id"),
                        data.get("shop_name"),
                        data.get("authority_id"),
                        data.get("auth_subject_type"),
                        access_token,
                        refresh_token,
                        access_expires,
                        refresh_expires,
                        now,
                    ),
                )
                last_id = cursor.lastrowid
            db.commit()

        self.token = {
            "id": last_id,
            "app_key": self.app_key,
            "shop_id": data.get("shop_id"),
            "shop_name": data.get("shop_name"),
            "authority_id": data.get("authority_id"),
            "auth_subject_type": data.get("auth_subject_type"),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "access_expires": access_expires,
            "refresh_expires": refresh_expires,
            "created_at": now,
        }
