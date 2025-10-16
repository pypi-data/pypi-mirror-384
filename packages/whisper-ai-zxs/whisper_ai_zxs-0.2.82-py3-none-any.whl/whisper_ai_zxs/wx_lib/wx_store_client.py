from ..whisper_db import WhisperDB
import requests
from .wx_auth_client import WXAuthClient
import logging
from datetime import datetime
import json

class WXStoreClient:
    def __init__(self):
        self.auth = WXAuthClient(appid="wx99c7fd9e318b8575", secret="39de4d2977a6caf6763433bfd2a3b3b2")

    def getOrderInfo(
            self, 
            order_id: str
        ) -> dict:
        """
        获取订单信息
        :param order_id: 订单ID
        :return: 订单信息字典
        """

        access_token = self.auth.get_access_token()
        url = f"https://api.weixin.qq.com/channels/ec/order/get?access_token={access_token}"

        payload = {
            "order_id": order_id,
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logging.exception("请求微信订单信息接口失败: %s", e)
            raise

        body = resp.json()
        # 检查企业微信返回的 errcode
        if int(body.get("errcode", -1)) != 0:
            raise RuntimeError(f"微信接口返回错误: errcode={body.get('errcode')}, errmsg={body.get('errmsg')}, body={body}")

        order_info = body.get("order", {})
        if not order_info:
            raise ValueError(f"未找到 order_id={order_id} 的订单信息")
        
        # 处理订单信息，确保返回的字典格式正确
        if isinstance(order_info, dict):
            status_map = {
                10: "待付款",
                12: "礼物待收下",
                13: "凑单买凑团中",
                20: "待发货",
                21: "部分发货",
                30: "待收货",
                100: "完成",
                200: "全部商品售后之后，订单取消",
                250: "未付款用户主动取消或超时未付款订单自动取消"
            }
            ext_info = order_info.get("order_detail", {}).get("ext_info", {})
            filtered_ext_info = {
                "customer_notes": ext_info.get("customer_notes", ""),
                "merchant_notes": ext_info.get("merchant_notes", "")
            }
            delivery_info = order_info.get("order_detail", {}).get("delivery_info", {})
            filtered_delivery_info = {
                "address_info": delivery_info.get("address_info", {}),
                "delivery_product_info": delivery_info.get("delivery_product_info", [])
            }
            # 转换 create_time 为 YYYY-mm-dd hh:mm:ss 格式
            create_time = order_info.get("create_time", "")
            if create_time:
                try:
                    # 假设 create_time 是时间戳（秒级）
                    create_time = datetime.fromtimestamp(int(create_time)).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    # 如果不是时间戳则保持原样
                    pass

            new_order_info = {
                "order_id": order_info.get("order_id", ""),
                "create_time": create_time,
                "status": status_map.get(order_info.get("status", ""), "未知状态"),
                "order_detail": {
                    "product_infos": [
                        {
                            "product_id": p.get("product_id", ""),
                            "sale_price": p.get("sale_price", ""),
                            "sku_cnt": p.get("sku_cnt", ""),
                            "title": p.get("title", ""),
                            "on_aftersale_sku_cnt": p.get("on_aftersale_sku_cnt", ""),
                            "finish_aftersale_sku_cnt": p.get("finish_aftersale_sku_cnt", ""),
                            "market_price": p.get("market_price", ""),
                            "sku_attrs": p.get("sku_attrs", [])
                        }
                        for p in order_info.get("order_detail", {}).get("product_infos", [])
                        if isinstance(p, dict)
                    ],
                    "delivery_info": filtered_delivery_info,
                    "ext_info": filtered_ext_info
                }
            }
        elif not isinstance(order_info, dict):
            raise TypeError("订单信息格式错误，应该是字典或列表")

        return new_order_info
    
    def addOrderNote(
            self, 
            order_id: str,
            note: str
        ) -> dict:
        """
        添加订单备注信息（追加备注）
        :param order_id: 订单ID
        :param note: 新备注内容
        :return: {'success': bool, 'message': str}
        """

        # 先查询原有备注
        try:
            order_info = self.getOrderInfo(order_id)
            old_note = order_info.get("order_detail", {}).get("ext_info", {}).get("merchant_notes", "")
        except Exception as e:
            logging.exception("查询订单原有备注失败: %s", e)
            return {"success": False, "message": f"查询订单原有备注失败: {e}"}

        # 追加新备注
        if old_note:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_note = f"{old_note}\n[{timestamp}] {note}"
        else:
            new_note = note

        access_token = self.auth.get_access_token()
        url = f"https://api.weixin.qq.com/channels/ec/order/merchantnotes/update?access_token={access_token}"

        payload = {
            "order_id": order_id,
            "merchant_notes": new_note
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logging.exception("请求微信修改订单备注接口失败: %s", e)
            return {"success": False, "message": str(e)}

        body = resp.json()
        # 检查微信返回的 errcode
        if int(body.get("errcode", -1)) != 0:
            error_msg = f"微信接口返回错误: errcode={body.get('errcode')}, errmsg={body.get('errmsg')}, body={body}"
            logging.error(error_msg)
            return {"success": False, "message": body.get("errmsg", error_msg)}

        return {"success": True, "message": body.get("errmsg", "备注添加成功")}

    def collectSellingProduct(self, shop_name: str):
        product_ids = self._getProductList()
        #logging.info(f"获取到的商品ID列表: {product_ids}")
        # 处理商品ID列表，进行销售统计等操作
        new_product_list = []
        for pid in product_ids:
            product_info = self._getProductInfo(pid)
            # 这里可以将 product_info 存储到数据库，或者进行其他处理
            # 示例：打印商品信息
            skus = product_info.get("skus", [])
            on_sale_skus = [
                ",".join(
                    f"{attr.get('attr_key', '')}:{attr.get('attr_value', '')}" 
                    for attr in sku.get("sku_attrs", [])
                ) if sku.get("sku_attrs") else "默认规格"
                for sku in skus if sku.get("stock_num", 0) > 0
            ]
            off_sale_skus = [sku.get("sku_attrs","默认规格") for sku in skus if sku.get("stock_num", 0) <= 0]

            new_product_info = {
                "product_id": product_info.get("product_id", ""),
                "title": product_info.get("title", ""),
                "on_sale_skus": on_sale_skus,
                "off_sale_skus": off_sale_skus,
            }

            new_product_list.append(new_product_info)

        # 直接将 new_product_list 写入数据库

        sql_use = "USE zxs_order;"
        sql_del = f"DELETE FROM `tm_selling_product` WHERE `shop_name` ='{shop_name}'"

        with WhisperDB() as myDB:
            myDB.query(sql_use)
            myDB.query(sql_del)
            for product in new_product_list:
                product_id = product["product_id"]
                product_name = product["title"]
                sell_json = json.dumps(product["on_sale_skus"], ensure_ascii=False)
                unsell_json = json.dumps(product["off_sale_skus"], ensure_ascii=False)
                sql_insert = (
                    "INSERT INTO tm_selling_product "
                    "(product_code, product_name, on_sale_sku, off_sale_sku, shop_name, discount_plan, purchase_link) "
                    "VALUES (%s, %s, %s, %s, %s, '', '')"
                )
                myDB.query(sql_insert, (product_id, product_name, sell_json, unsell_json, shop_name))
            myDB.commit()
        return


    def _getProductList(self) -> list:
        """
        获取商品列表
        :return: 商品信息列表
        """
        access_token = self.auth.get_access_token()
        url = f"https://api.weixin.qq.com/channels/ec/product/list/get?access_token={access_token}"

        all_product_ids = []

        next_key = ""
        while True:
            payload = {
                "status": 5,
                "page_size": 30,
                "next_key": next_key
            }
            try:
                resp = requests.post(url, json=payload, timeout=10)
                resp.raise_for_status()
            except Exception as e:
                logging.exception("请求微信商品列表接口失败: %s", e)
                raise

            body = resp.json()
            # 检查企业微信返回的 errcode
            if int(body.get("errcode", -1)) != 0:
                raise RuntimeError(f"微信接口返回错误: errcode={body.get('errcode')}, errmsg={body.get('errmsg')}, body={body}")

            product_ids = body.get("product_ids", [])
            if not isinstance(product_ids, list):
                raise ValueError("商品列表格式错误，应该是列表")

            all_product_ids.extend(product_ids)
            next_key = body.get("next_key", "")
            total_num = body.get("total_num", 0)
            if len(all_product_ids) >= total_num:
                break

        return all_product_ids

    def _getProductInfo(self, product_id: str) -> dict:
        """
        获取单个商品信息
        :param product_id: 商品ID
        :return: 商品信息字典
        """
        access_token = self.auth.get_access_token()
        url = f"https://api.weixin.qq.com/channels/ec/product/get?access_token={access_token}"

        payload = {
            "product_id": product_id
        }
        try:
            resp = requests.post(url, json=payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            logging.exception("请求微信商品信息接口失败: %s", e)
            return {"success": False, "message": str(e)}

        body = resp.json()
        # 检查企业微信返回的 errcode
        if int(body.get("errcode", -1)) != 0:
            raise RuntimeError(f"微信接口返回错误: errcode={body.get('errcode')}, errmsg={body.get('errmsg')}, body={body}")

        return body.get("product", {})