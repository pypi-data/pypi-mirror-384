import time
import hashlib
import json
import requests
from urllib.parse import urlencode
import pandas as pd
import re

class APIWangDianTong:
    def __init__(self):
        """
        :param sid: 卖家账号
        :param appkey: 接口账号
        :param appsecret: 接口密钥
        :param env: 'prod' 正式环境, 'sandbox' 测试环境
        """
        self.sid = "szzxs2"
        self.appkey = "szzxs2-gwa"
        self.appsecret = "2e1191428410c12ea69ad068268ffe8f"
        self.env = 'prod'
        self.base_url = {
            'prod': 'https://api.wangdian.cn/openapi2/',
            'sandbox': 'https://sandbox.wangdian.cn/openapi2/'
        }[self.env]

    def _get_timestamp(self):
        # 旺店通要求北京时间1970-01-01 08:00:00起的总秒数
        return int(time.time())

    def _sign(self, params):
        """
        旺店通标准API签名算法
        """
        items = sorted(params.items())
        sign_str = ""
        for idx, (k, v) in enumerate(items):
            k_utf8_len = len(k.encode('utf-8'))
            v_utf8_len = len(str(v).encode('utf-8'))
            k_len_str = f"{k_utf8_len:02d}"
            v_len_str = f"{v_utf8_len:0>4d}" if v_utf8_len < 10000 else str(v_utf8_len)
            part = f"{k_len_str}-{k}:{v_len_str}-{v}"
            if idx != len(items) - 1:
                part += ";"
            sign_str += part
        sign_str += self.appsecret
        return hashlib.md5(sign_str.encode('utf-8')).hexdigest()

    def _post(self, service_name, biz_params):
        """
        :param service_name: 接口服务名
        :param biz_params: 业务参数(dict)
        :return: 响应json
        """
        url = self.base_url + service_name
        timestamp = self._get_timestamp()
        params = {
            'sid': self.sid,
            'appkey': self.appkey,
            'timestamp': timestamp,
        }
        # 业务参数需json序列化
        for k, v in biz_params.items():
            if isinstance(v, (dict, list)):
                # 使用ensure_ascii=True确保所有字符为ASCII，避免签名错误
                params[k] = json.dumps(v, ensure_ascii=True)
            else:
                # 对字符串类型参数进行utf-8编码处理
                if isinstance(v, str):
                    params[k] = v.encode('utf-8').decode('utf-8')
                else:
                    params[k] = v
        # 生成签名
        params['sign'] = self._sign(params)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = urlencode(params)
        resp = requests.post(url, data=data, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    # 创建订单接口
    def create_trade(self, file_path):
        """
        创建订单（sales_trade_push.php）。
        :param file_path: 订单数据文件路径，格式参考接口文档
        :return: 接口响应json
        """
        # 读取Excel文件
        df = pd.read_excel(file_path, engine="openpyxl")

        # 假设Excel包含如下字段：店铺名称	原始单号	收件人	省	市	区	手机	固话	邮编	地址	发货方式	应收合计	邮费	优惠金额	COD买家费用	下单时间	付款时间	买家备注	客服备注	发票抬头	发票内容	支付方式	商家编码	货品数量	货品价格	货品总价	货品优惠	源子订单号	备注	分销商, 等
        # 需根据实际Excel字段进行映射
        # 按原始单号（tid）分组，将同一订单的货品合并到 order_list
        trades = {}
        #重复的tid列表
        duplicate_tids = []
        for i, row in df.iterrows():
            tid = str(row['原始单号'])
            order_item = {
                'oid': "AIOID" + str(int(time.time())) + str(i),
                'num': int(row['货品数量']),
                'price': (float(row['货品总价'])+float(row['货品优惠'])) / int(row['货品数量']) if int(row['货品数量']) != 0 else 0,
                'status': 30,  # 10-待付款
                'refund_status': 0,
                'goods_id': row['商家编码'],
                'spec_no': row['商家编码'],
                'goods_name': row['商家编码'],
                'adjust_amount': 0,
                'discount': row['货品优惠'] if pd.notna(row['货品优惠']) else 0,
                'share_discount': 0
            }
            if tid not in trades:
                # 这里需要查询tid订单是否已经存在。
                if any(d['tid'] == tid for d in duplicate_tids):
                    print(f"订单 {tid} 在历史订单中已经出现，跳过创建。")
                    continue
                if self._check_order_tid(tid):
                    print(f"订单 {tid} 已存在，跳过创建。")
                    duplicate_tids.append({'tid': tid, 'shop_name': row['店铺名称']})
                    continue

                trades[tid] = {
                    'tid': tid,
                    'shop_name': row['店铺名称'],
                    'trade_status': 30,
                    'delivery_term': 4, # 1:款到发货,2:货到付款(包含部分货到付款),3:分期付款,4:挂账
                    'trade_time': row['下单时间'] if pd.notna(row['下单时间']) else time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                    'pay_time': row['付款时间'] if pd.notna(row['付款时间']) else time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                    'fenxiao_nick': row['分销商'] if pd.notna(row['分销商']) else '',
                    'buyer_nick': row['网名'] if pd.notna(row['网名']) else '',
                    'receiver_name': row['收件人'],
                    'receiver_province': row['省'] if pd.notna(row['省']) else '',
                    'receiver_city': row['市'] if pd.notna(row['市']) else '',
                    'receiver_district': row['区'] if pd.notna(row['区']) else '',
                    # 处理地址字段：省、市、区字样后加空格，并用空格隔开
                    'receiver_address': (
                        str(row['地址'])
                        .replace('省', '省 ')
                        .replace('市', '市 ')
                        .replace('区', '区 ')
                        .replace('县', '县 ')
                    ),
                    'receiver_mobile': row['手机'],
                    'post_amount': row['邮费'] if pd.notna(row['邮费']) else 0,
                    "cod_amount": 0,
                    "ext_cod_fee": 0,
                    "other_amount": 0,
                    "paid": 0,
                    'order_list': []
                    # 可根据接口文档补充其他字段
                }
            trades[tid]['order_list'].append(order_item)
        trade_data_list = list(trades.values())

        #return trade_data_list

        shops = self.get_shops()

        # 按shop_name分组
        shop_trades = {}
        results = []
        for trade in trade_data_list:
            shop_name = trade.get('shop_name', '')
            shop_trades.setdefault(shop_name, []).append(trade)
        for shop_name, trades in shop_trades.items():
            # 根据shop_name查找对应的shop_no
            shop_no = ''
            for shop in shops:
                if shop.get('shop_name') == shop_name:
                    shop_no = shop.get('shop_no')
                    break

            # 按50条分批推送
            batch_size = 50
            for start in range(0, len(trades), batch_size):
                batch_trades = trades[start:start + batch_size]
                params = {
                    'shop_no': shop_no,
                    'switch': 0,
                    'trade_list': batch_trades
                }
                print(f"Creating trades for shop: {shop_name} (shop_no: {shop_no}), batch {start // batch_size + 1}, number of trades: {len(batch_trades)}")
                print(f"Params: {json.dumps(params, ensure_ascii=False)}")
                result = self._post('trade_push.php', params)
                #if result.get('error_count') != 0:
                #    results.append({'shop_name': shop_name, 'result': result})
                results.append({'shop_name': shop_name, 'result': result})

        #把duplicate_tids也加入结果中
        duplicate_results = []
        for tid_info in duplicate_tids:
            tid = tid_info.get('tid', '')
            shop_name = tid_info.get('shop_name', '')
            duplicate_results.append({'shop_name': shop_name, 'result': f"订单 {tid} 在历史订单中已经出现，跳过创建。"})

        return results
    
    # 订单tid校验接口
    def _check_order_tid(self, order_tid):
        """
        确认tid是否已经创建了订单。
        :param order_tid: 订单编号（原始单号）
        :return: 是否存在该订单
        """
        if not order_tid:
            raise ValueError("必须提供订单编号")

        params = {'src_tid': order_tid}
        result = self._post('sales_trade_query.php', params)

        trades = result.get('trades', []) if result else []

        if not trades:
            return False
        return True

    def get_shops(self):
        """
        获取店铺列表（shop.php），自动分页，查询全量数据。
        :return: 店铺信息列表
        """
        all_shops = []
        page_no = 0
        page_size = 100
        while True:
            params = {
                'page_no': page_no,
                'page_size': page_size,
                'is_disabled': '0'
            }
            result = self._post('shop.php', params)
            shops = result.get('shoplist', []) if result else []
            all_shops.extend(shops)
            # 如果返回数量小于page_size，说明已到最后一页
            if len(shops) < page_size:
                break
            page_no += 1
        return all_shops
    
    def get_stock_list(self):
        """
        获取仓库列表（warehouse_query.php），自动分页，查询全量数据。
        :return: 仓库信息列表
        """
        all_warehouses = []
        page_no = 0
        page_size = 100
        while True:
            params = {
            'page_no': page_no,
            'page_size': page_size,
            'is_disabled': '0'
            }
            result = self._post('warehouse_query.php', params)
            warehouses = result.get('warehouses', []) if result else []
            all_warehouses.extend(warehouses)
            # 如果返回数量小于page_size，说明已到最后一页
            if len(warehouses) < page_size:
                break
            page_no += 1
        return all_warehouses

    # 创建仓库盘点单接口 --- IGNORE ---
    def create_stock_check(self, file_path):
        """
        创建仓库盘点单（stock_sync_by_pd.php）。
        :param file_path: 盘点单数据文件路径，格式参考接口文档
        :return: 接口响应json
        """
        # 读取Excel文件
        df = pd.read_excel(file_path, engine="openpyxl")

        #获取文件名不含路径和扩展名
        file_name = file_path.split('/')[-1].split('.')[0]
        # 提取括号中的内容
        match = re.search(r'（(.*?)）', file_name)
        bracket_content = match.group(1) if match else ''
        print(bracket_content)  # 输出：渠道-京东-奇门-北京常温

        #查找店铺列表，获取仓库名称对应的仓库编号
        warehouses = self.get_stock_list()
        warehouse_name_to_no = {w['name']: w['warehouse_no'] for w in warehouses}
        #如果括号中的内容在仓库名称中，说明是指定仓库的盘点单

        warehouse_no = warehouse_name_to_no.get(bracket_content, '')
        if not warehouse_no:
            print(f"未找到指定的仓库：{bracket_content}，无法创建盘点单。")
            return {'code': 'error', 'message': f'未找到指定的仓库：{bracket_content}，无法创建盘点单。'}

        # 假设Excel包含如下字段：仓库名称	盘点单号	盘点时间	商品编码	规格编码	商品名称	规格名称	盘点数量	备注, 等
        # 需根据实际Excel字段进行映射
        # 不分组，所有记录都属于同一个盘点单，盘点warehouse_no的仓库
        goods_list = []
        for i, row in df.iterrows():
            # 跳过最后一行（汇总行）
            if i == len(df) - 1:
                continue
            #如果仓储库存和库存相同，则跳过。
            if pd.notna(row['仓储库存']) and pd.notna(row['库存']) and float(row['仓储库存']) == float(row['库存']):
                continue
            item = {
                'spec_no': row['商家编码'] if pd.notna(row['商家编码']) else '',
                'stock_num': float(row['仓储库存']) if pd.notna(row['仓储库存']) else 0
                # 可扩展：'position_no', 'batch_no', 'expire_date'等
            }
            goods_list.append(item)

        params = {
            'warehouse_no': warehouse_no,
            'mode': 0,
            'is_check': 1,
            'goods_list': goods_list
        }

        print(f"Creating stock check for warehouse_no: {warehouse_no}, number of items: {len(goods_list)}")
        print(f"Params: {json.dumps(params, ensure_ascii=False)}")
        result = self._post('stock_sync_by_pd.php', params)
        results = {'code': result.get('code', ''), 'message': result.get('message', '')}        

        return results

# 使用示例
# api = WangDianTongAPI(sid='xxx', appkey='xxx', appsecret='xxx', env='prod')
# result = api.get_trade_list(start_time='2024-01-01 00:00:00', end_time='2024-01-02 00:00:00')
# print(result)