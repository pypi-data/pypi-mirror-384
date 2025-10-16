from ..whisper_db import WhisperDB
import requests
import logging
from datetime import datetime
import time
import json
import logging

from .dd_auth_client import DDAuthClient

class DDStoreClient:
    def __init__(self):
        # API 根地址，实际请求路径会根据 method 动态拼接为 /{module}/{action}
        self.COMMAND_URL = "https://openapi-fxg.jinritemai.com"
        self.auth = DDAuthClient("7542374655928108554", "3fcb520f-4365-47ec-81d0-cfe485b16494")
        self.token = self.auth.get_access_token()
        if not self.token:
            raise RuntimeError("Failed to obtain access token")
        logging.info("Initialized DDStoreClient with access token.")

    def getOrderInfo(
            self, 
            order_id: str
        ) -> dict:
        """
        获取订单详情
        """
        method = "order.orderDetail"
        method_params = {
            "shop_order_id": order_id
        }
        response = self._post_request(method=method, method_params=method_params)

        if response.get("code") != 10000:
            logging.error("Error fetching order info: %s", response)
            return {"success": False, "message": response.get("message", "unknown_error"), "raw": response}

        detail = response.get("data", {}).get("shop_order_detail", {})
        post_addr = detail.get("post_addr", {})
        sku_order_list = detail.get("sku_order_list", [])
        filtered_sku_order_list = [
            {
            "spec": sku.get("spec"),
            "product_name": sku.get("product_name"),
            "item_num": sku.get("item_num"),
            }
            for sku in sku_order_list
        ]

        # 将 create_time 时间戳转换为字符串格式
        create_time_ts = detail.get("create_time")
        if create_time_ts:
            create_time_str = datetime.fromtimestamp(int(create_time_ts)).strftime("%Y-%m-%d %H:%M:%S")
        else:
            create_time_str = ""

        result = {
            "order_id": detail.get("order_id"),
            "order_status_desc": detail.get("order_status_desc"),
            "create_time": create_time_str,
            "buyer_words": detail.get("buyer_words"),
            "seller_words": detail.get("seller_words"),
            #"post_addr": {
            #    "province": post_addr.get("province"),
            #    "city": post_addr.get("city"),
            #    "town": post_addr.get("town"),
            #    "street": post_addr.get("street"),
            #},
            "sku_order_list": filtered_sku_order_list,
            "post_receiver": detail.get("mask_post_receiver"),
            "post_tel": detail.get("mask_post_tel"),
            "post_addr": detail.get("mask_post_addr"),
        }
        return result
    
    def addOrderNote(self, order_id: str, note: str) -> dict:

        order_detail = self.getOrderInfo(order_id)
        if "success" in order_detail and not order_detail["success"]:
            return {"success": False, "message": order_detail.get("message", "unknown_error"), "raw": order_detail.get("raw", {})}

        old_remark = order_detail.get("seller_words", "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_remark = f"{old_remark}\n[{timestamp}] {note}" if old_remark else f"[{timestamp}] {note}"

        if len(new_remark) > 500:
            new_remark = new_remark[-500:]
        """
        添加订单备注
        """
        method = "order.addOrderRemark"
        method_params = {
            "order_id": order_id,
            "remark": new_remark,
            "is_add_star": "true",
            "star": 5,
        }
        response = self._post_request(method=method, method_params=method_params)

        if response.get("code") != 10000:
            logging.error("Error fetching order info: %s", response)
            return {"success": False, "message": response.get("message", "unknown_error"), "raw": response}

        result = {"success": True, "message": "Remark added successfully"}

        return result

    def collectSellingProduct(self, shop_name: str):
        product_list = self._getProductList()
        # 按照 product_id 和 product_name 分组，并区分可售/不可售 sku
        grouped_products = {}
        for product in product_list:
            product_id = product.get("product_id", "")
            product_name = product.get("name", "")

            sku_list = self._getSKUList(product_id)
            for sku in sku_list:
                sku_name = sku.get("sku_name", "")
                stock = sku.get("stock_num", 0)
                sku_status = sku.get("sku_status", 0)
                if not sku_status:
                    continue

                key = (product_id, product_name)
                if key not in grouped_products:
                    grouped_products[key] = {"product_id": product_id, "product_name": product_name, "sell": [], "unsell": []}
                if stock > 0:
                    grouped_products[key]["sell"].append(sku_name)
                else:
                    grouped_products[key]["unsell"].append(sku_name)

        new_product_list = list(grouped_products.values())

        # 直接将 new_product_list 写入数据库

        sql_use = "USE zxs_order;"
        sql_del = f"DELETE FROM `tm_selling_product` WHERE `shop_name` ='{shop_name}'"

        with WhisperDB() as myDB:
            myDB.query(sql_use)
            myDB.query(sql_del)
            for product in new_product_list:
                product_id = product["product_id"]
                product_name = product["product_name"]
                sell_json = json.dumps(product["sell"], ensure_ascii=False)
                unsell_json = json.dumps(product["unsell"], ensure_ascii=False)
                sql_insert = (
                    "INSERT INTO tm_selling_product "
                    "(product_code, product_name, on_sale_sku, off_sale_sku, shop_name, discount_plan, purchase_link) "
                    "VALUES (%s, %s, %s, %s, %s, '', '')"
                )
                myDB.query(sql_insert, (product_id, product_name, sell_json, unsell_json, shop_name))
            myDB.commit()

    def _getProductList(self) -> list:
        """
        获取商品列表（全量，翻页遍历）
        """
        method = "product.listV2"
        page_size = 100  # 最大支持100
        page = 1
        all_products = []

        while True:
            method_params = {
                "status": 0,  # 0表示全部商品，1表示上架商品，2表示下架商品
                "size": page_size,
                "page": page
            }

            response = self._post_request(method=method, method_params=method_params)

            if response.get("code") != 10000:
                logging.error("Error fetching product list: %s", response)
                break

            products = response.get("data", {}).get("data", [])
            if not products:
                break



            all_products.extend(products)

            total = response.get("data", {}).get("total", 0)
            if len(all_products) >= total:
                break

            page += 1

        return all_products

    def _getSKUList(self, product_id: str) -> list:
        """
        获取所有 SKU 列表（全量，翻页遍历）
        """
        method = "sku.list"
        all_skus = []
        method_params = {
            "product_id": product_id
        }
        response = self._post_request(method=method, method_params=method_params)

        if response.get("code") != 10000:
            logging.error("Error fetching SKU list: %s", response)
            return all_skus

        all_skus = [
            {
            "sku_status": sku.get("sku_status"),
            "sku_name": sku.get("spec_detail_name1"),
            "stock_num": sku.get("stock_num"),
            }
            for sku in response.get("data", [])
        ]


        return all_skus

    def _post_request(self, method: str = None, method_params: dict = None, access_token: str = None, timeout: int = 10, retries: int = 2) -> dict:
        """
        构建抖店网关 payload、获取 access_token（若未传入）、计算 sign 并 POST。
        """
        if method is None:
            raise RuntimeError("_post_request requires 'method' argument")

        # 使用 Unix 时间戳（秒）作为 timestamp，按抖店文档：param_json 放 body，其它公共参数放到 URL query
        ts = str(int(time.time()))
        # 若未提供 access_token，则内部获取
        if access_token is None:
            access_token = self.auth.get_access_token()

        # param_json 需为字符串，且业务参数需按参数名字符串大小排序
        param_json = json.dumps(method_params or {}, ensure_ascii=False, separators=(',', ':'))

        # 签名参数只包含 app_key, method, param_json, timestamp, v（不包含 access_token）
        sign_params = {
            "app_key": self.auth.app_key,
            "method": method,
            "param_json": param_json,
            "timestamp": ts,
            "v": "2"
        }
        sign = self.auth.generate_sign(sign_params)

        # 构建请求 URL：根地址 + method 对应的路径（将 '.' 替换为 '/'）
        endpoint = f"{self.COMMAND_URL}/{method.replace('.', '/')}"

        # 公共参数放到 query string，param_json 放到 JSON body
        query_params = {
            "method": method,
            "app_key": self.auth.app_key,
            "timestamp": ts,
            "v": "2",
            "access_token": access_token,
            "sign": sign,
            "sign_method": "hmac-sha256",
        }

        # 发送请求（带重试），始终使用 self.COMMAND_URL
        attempt = 0
        backoff = 1
        headers = {"Content-Type": "application/json"}
        while attempt <= retries:
            try:
                attempt += 1
                resp = requests.post(endpoint, params=query_params, json=method_params or {}, headers=headers, timeout=timeout)
                resp.raise_for_status()
                try:
                    body = resp.json()
                except ValueError:
                    logging.error("Invalid JSON response: %s", resp.text)
                    return {"error": "invalid_json", "raw": resp.text}
                return body
            except requests.exceptions.RequestException as exc:
                logging.warning("POST attempt %d failed: %s", attempt, exc)
                if attempt <= retries:
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logging.error("All POST attempts failed: %s", exc)
                return {"error": "request_failed", "detail": str(exc)}
        return {"error": "unknown_error"}
