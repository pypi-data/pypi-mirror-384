from ..whisper_db import WhisperDB
import requests
from .red_auth_client import RedAuthClient
import logging
from datetime import datetime
import time
import json

class RedStoreClient:
    def __init__(self):
        self.auth = RedAuthClient(app_id="4b8ab3245c704723a6d1", secret="febb545d489bea34eae32879a88e1a55")
        self.COMMAND_URL = "https://ark.xiaohongshu.com/ark/open_api/v3/common_controller"

    def getOrderInfo(
            self, 
            order_id: str
        ) -> dict:
        """
        获取订单信息
        :param order_id: 订单ID
        :return: 订单信息字典
        """
        method = "order.getOrderDetail"
        # API 可能使用 orderId 作为参数名
        method_params = {"orderId": order_id}

        logging.info("Sending request with method=%s orderId=%s", method, order_id)
        # 调用内部 _post_request（内部会获取 access_token、构建 payload 并签名），url 内部使用 self.COMMAND_URL
        body =  self._post_request(method=method, method_params=method_params)
        # 检查小红书返回的 success
        if not body.get("success", False):
            error_msg = f"小红书接口返回错误: errcode={body.get('error_code')}, errmsg={body.get('errmsg')}, body={body}"
            logging.error(error_msg)
            return {"success": False, "message": body.get("errmsg", error_msg)}

        order_info = body.get("data", {})
        created_time = order_info.get("createdTime")
        if created_time:
            # 假设 created_time 是时间戳（毫秒或秒），需转为标准格式
            try:
                # 判断是否为毫秒级时间戳
                if len(str(created_time)) > 10:
                    created_time = int(str(created_time)[:10])
                else:
                    created_time = int(created_time)
                created_time_str = datetime.fromtimestamp(created_time).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                created_time_str = order_info.get("createdTime")
        else:
            created_time_str = None

        status_map = {
            "1": "已下单待付款",
            "2": "已支付处理中",
            "3": "清关中",
            "4": "待发货",
            "5": "部分发货",
            "6": "待收货",
            "7": "已完成",
            "8": "已关闭",
            "9": "已取消",
            "10": "换货申请中"
        }
        status_code = str(order_info.get("orderStatus"))
        status_cn = status_map.get(status_code, status_code)

        # 售后状态映射
        after_sales_status_map = {
            "1": "无售后",
            "2": "售后处理中",
            "3": "售后完成",
            "4": "售后拒绝",
            "5": "售后关闭",
            "6": "平台介入中",
            "7": "售后取消"
        }
        after_sales_status_code = str(order_info.get("orderAfterSalesStatus"))
        after_sales_status_cn = after_sales_status_map.get(after_sales_status_code, after_sales_status_code)

        # 只保留 skuList 中的指定属性
        raw_sku_list = order_info.get("skuList", [])
        filtered_sku_list = []
        for sku in raw_sku_list:
            filtered_sku = {
                "skuId": sku.get("skuId"),
                "skuName": sku.get("skuName"),
                "skuSpec": sku.get("skuSpec"),
                "skuQuantity": sku.get("skuQuantity"),
                #"skuDetailList": sku.get("skuDetailList"),
                "skuAfterSaleStatus": after_sales_status_map.get(str(sku.get("skuAfterSaleStatus")), str(sku.get("skuAfterSaleStatus"))),
                "totalPaidAmount": sku.get("totalPaidAmount")
            }
            filtered_sku_list.append(filtered_sku)

        new_order_info = {
            "order_id": order_info.get("orderId"),
            "status": status_cn,
            "order_after_sales_status": after_sales_status_cn,
            "created_time": created_time_str,
            "receiverCountryName": order_info.get("receiverCountryName"),
            "receiverProvinceName": order_info.get("receiverProvinceName"),
            "receiverCityName": order_info.get("receiverCityName"),
            "receiverDistrictName": order_info.get("receiverDistrictName"),
            "customerRemark": order_info.get("customerRemark"),
            "sellerRemark": order_info.get("sellerRemark"),
            "skuList": filtered_sku_list
        }

        return new_order_info

    def addOrderNote(self, order_id: str, note: str) -> dict:
        """
        添加订单备注
        """
        order_info = self.getOrderInfo(order_id)
        # 检查是否为错误响应
        if not order_info or order_info.get("success") is False:
            return {"success": False, "message": order_info.get("message", "order_not_found") if order_info else "order_not_found"}
        
        order_note = order_info.get("sellerRemark", "")
    
        if order_note:
            order_note += "\n"
        else:
            order_note = ""
        order_note += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {note}"

        method = "order.modifySellerMarkInfo"
        method_params = {
            "orderId": order_id,
            "sellerMarkNote": order_note,
            "operator": "AI客服",
            "sellerMarkPriority": 2
        }

        logging.info("Sending request with method=%s method_params=%s", method, method_params)

        body = self._post_request(method=method, method_params=method_params)
        # 检查小红书返回的 success
        if not body.get("success", False):
            error_msg = f"小红书接口返回错误: errcode={body.get('error_code')}, errmsg={body.get('errmsg')}, body={body}"
            logging.error(error_msg)
            return {"success": False, "message": body.get("errmsg", error_msg)}

        return {"success": True, "message": body.get("errmsg", "备注添加成功")}

    def collectSellingProduct(self, shop_name: str):
        product_list = self._getProductList()
        # 按照 product_id 和 product_name 分组，并区分可售/不可售 sku
        grouped_products = {}
        for product in product_list:
            product_id = product.get("item", {}).get("id")
            product_name = product.get("item", {}).get("name")
            sku_name = product.get("sku", {}).get("name")
            stock = product.get("sku", {}).get("stock", 0)

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
                myDB.query(sql_insert, (product_name, product_name, sell_json, unsell_json, shop_name))
            myDB.commit()

    def _getProductList(self) -> list:
        """
        获取商品列表（针对小红书）
        :return: 商品ID列表
        """
        method = "product.getDetailSkuList"

        method_params = {
            "buyable": True,
            "pageNo": 1,
            "pageSize": 100
        }

        all_products = []
        while True:
            body = self._post_request(method=method, method_params=method_params)
            if not body.get("success", False):
                error_msg = f"小红书接口返回错误: errcode={body.get('error_code')}, errmsg={body.get('errmsg')}, body={body}"
                logging.error(error_msg)
                break
            products = body.get("data", []).get("data", [])
            # logging.info("Fetched products: %s", products)
            all_products.extend(products)
            total = body.get("total", 0)
            page_size = method_params["pageSize"]
            if len(products) < page_size or len(all_products) >= total:
                break
            method_params["pageNO"] += 1

        logging.info("Total products fetched: %d", len(all_products))
        return all_products

    def _post_request(self, method: str = None, method_params: dict = None, access_token: str = None, timeout: int = 10, retries: int = 2) -> dict:
        """
        内部构建网关 payload、获取 access_token（若未传入）、计算 sign 并 POST。
        """
        if method is None:
            raise RuntimeError("_post_request requires 'method' argument")

        # timestamp 使用秒级字符串
        ts = str(int(time.time()))
        # 若未提供 access_token，则内部获取
        if access_token is None:
            access_token = self.auth.get_access_token()

        full_payload = {
            "appId": self.auth.app_id,
            "version": "2.0",
            "method": method,
            "timestamp": ts,
        }
        if access_token:
            full_payload["accessToken"] = access_token
        if method_params:
            full_payload.update(method_params)

        # 计算签名（优先使用 auth 中的签名函数）
        sign_params = {"method": method, "appId": self.auth.app_id, "timestamp": ts, "version": "2.0"}
        full_payload["sign"] = self.auth.generate_sign(sign_params)

        # 发送请求（带重试），内部始终使用 self.COMMAND_URL
        attempt = 0
        backoff = 1
        headers = {"Content-Type": "application/json"}
        while attempt <= retries:
            try:
                attempt += 1
                resp = requests.post(self.COMMAND_URL, json=full_payload, headers=headers, timeout=timeout)
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
