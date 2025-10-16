import re
from .whisper_db import WhisperDB
import json
from .whisper_azure import WhisperAzure
from datetime import datetime
from .whisper_tools import WhisperTools_Qywx
import logging
logger = logging.getLogger("whisper_ai")

#from xbot import print

class AgentServicer:
    def __init__(self, kf_name):
        """ 初始化一个空字典用于存储函数 """
        self._functions = {}
        self._kf_name = kf_name
        self._shop_name = re.match(r'([^:]*):?.*', kf_name).group(1)
        self._status_now = 0
        self.user_reply_time_dic = {}
        self._error_count = 0
        # 使用 with 语句管理数据库连接
        logger.info("开始获取公司名称！")
        with WhisperDB() as db:  # 自动管理连接
            # 使用参数化查询来防止 SQL 注入
            query = """
                SELECT company FROM openai_kf_manage
                WHERE shop_name = %s;
            """
            # 获取查询结果
            result = db.query(query, (self._kf_name,))
        self._company_name = result[0][0] if result else "未设定"
        logger.info(f"公司名称！{self._company_name}")

    ###以下函数在不同的RPA中需要重载
    def call(self, name, *args, **kwargs):
        """
        调用注册的函数
        :param name: 需要调用的函数名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 返回调用结果
        """
        if name not in self._functions:
            raise KeyError(f"函数 '{name}' 未注册")
        return self._functions[name](*args, **kwargs)
        #run_module({ "module_path": self._functions[name] }, "main", SZEnv['rpa'], *args, **kwargs) 
    def register_all_function(self):
        pass
    
    ###以下是公共函数
    def get_kf_name(self):
        return self._kf_name;
    def get_shop_name(self):
        return self._shop_name;

    def register(self, name, func):
        """
        注册函数
        :param name: 作为函数键的名称
        :param func: 需要存储的函数
        """
        """
        if not callable(func):
            raise ValueError("注册的对象必须是可调用的函数")
        self._functions[name] = func
        """
        self._functions[name] = func
    def is_register(self, name):
        return name in self._functions
    def get_kf_status_now(self):
        return self._status_now
    def get_kf_status(self):
        # 使用 with 语句管理数据库连接
        with WhisperDB() as db:  # 自动管理连接
            # 使用参数化查询来防止 SQL 注入
            query = """
                SELECT * FROM openai_kf_manage
                WHERE shop_name = %s;
            """
            # 获取查询结果
            result = db.query(query, (self._kf_name,))

        # 如果查询结果存在，则返回第一行
        return {"manage_status":result[0][1], "status_now":result[0][2], "error_count":self._error_count} if result else None

    def set_kf_status(self, status):
        
        # 使用 with 语句管理数据库连接
        with WhisperDB() as db:  # 自动管理连接s
            # 使用参数化查询来防止 SQL 注入
            query = """
                UPDATE openai_kf_manage 
                SET status_now = %s, update_time = NOW() 
                WHERE shop_name = %s;
            """
            # 获取查询结果
            db.query(query, (status, self._kf_name))
            db.commit()
        self._status_now = status
        # 如果查询结果存在，则返回第一行
        return
    
    def heart_bit(self):
        # 创建数据库连接并执行 SQL 语句
        myDB = WhisperDB()
        # 查询数据的SQL语句
        query = """
            UPDATE openai_kf_manage 
            SET last_active = NOW() 
            WHERE shop_name = %s;
        """
        # 执行预处理语句并传递参数
        myDB.query(query, (self.get_kf_name()))
        # 提交更改
        myDB.commit()
        # 关闭数据库连接
        myDB.close()

    def listening_user(self): 
        user_list = self.call("get_customers_waiting")
        # print(f"user_list: {user_list}")
        
        for user in user_list:
            last_reply_time = self.user_reply_time_dic.get(user, {}).get("time", "")
            new_chat_list = self.call("get_new_chats", user, last_reply_time)
            if (len(new_chat_list) > 0) :
                if self.user_reply_time_dic.get(user, {}).get("continue_times", 0) < 10:
                    self.reply(user, new_chat_list)
                else:
                    WhisperTools_Qywx.send_to_error_robot(f"{self._kf_name}的顾客（{user}）连续10次发送消息，已经停止回复，请尽快确认！")

                continue_times = 0
                if user in self.user_reply_time_dic:
                    continue_times = self.user_reply_time_dic[user]["continue_times"]

                self.user_reply_time_dic[user] = {
                                                "time" : new_chat_list[-1]["time"],
                                                "real_time" : datetime.now(),
                                                "continue_times" : continue_times + 1
                                            } 
            else:
                self.user_reply_time_dic[user] = {
                                                "time" : self.user_reply_time_dic.get(user)["time"] if user in self.user_reply_time_dic else "",
                                                "real_time" : self.user_reply_time_dic.get(user)["real_time"] if user in self.user_reply_time_dic else datetime.now(),
                                                "continue_times" : 0
                                            } 

        for user in list(self.user_reply_time_dic.keys()):  # 先复制 key 的列表
            if (datetime.now() - self.user_reply_time_dic[user]["real_time"]).total_seconds() / 60 > 5:
                #如果从开始到结束，该用户都没有发过消息，则记录和反馈异常。
                #if (self.user_reply_time_dic[user]["time"] == ""):
                #    WhisperTools_Qywx.send_to_error_robot(f"{self._kf_name}的顾客（{user}）接入后未发任何信息就要结束对话！请尽快确认！")
                #    result = self.call("transfer_to_customer_care", user, self.get_human_kf_name(), "系统原因，未识别顾客对话，请协助确认。")
                #    transfer_detail = {
                #        "type": "系统故障",
                #        "reason": "系统原因，未识别顾客对话，请协助确认。" 
                #    }
                #    if result != "success":
                #        logger.error(f"顾客未答复，且转人工失败，提交工单处理！")

                #        self.report_transfer_fail(user, transfer_detail)
                #        try:
                #            self.call("close_chat", user)
                #            del self.user_reply_time_dic[user]
                #        except Exception as e:
                #            logger.error(f"关闭聊天失败: {e}")
                #    else:
                #        self.report_transfer_success(user, transfer_detail)
                #else:
                try:
                    self.call("close_chat", user)
                    del self.user_reply_time_dic[user]
                except Exception as e:
                    logger.error(f"关闭聊天失败: {e}")

    def listening_manage(self): 
        service_list = self.get_service_will_action()
        # print(f"service_list: {service_list}")
        
        for service in service_list:
            if not service["status"].startswith("待联系:"):
                continue
            if service["status"].startswith("待联系:转接人工"):
                to_name_list = re.findall(r"\((.*?)\)", service["status"])  # 提取所有括号内的内容
                if to_name_list:
                    to_name = to_name_list[0]
                else:
                    to_name = "未找到客服"
                self.call("contact_old_user", service["user_id"])
                result = self.call("transfer_to_customer_care", service["user_id"], to_name, "人工客服跟进工单")
                if result == "success":
                    self.set_service_status(service["id"], "待处理:已转接")
                    chat_list = [{
                        "type" : "text",
                        "content" : f"工单{service['id']}的处理进度通知：已经转人工处理了。"
                    }]
                    self.add_history(service["user_id"], chat_list)
                else:
                    self.set_service_status(service["id"], f"待处理:转人工（{to_name}）失败。{result}")
            elif service["status"].startswith("待联系:通知"):
                send_content_list = re.findall(r"\((.*?)\)", service["status"])  # 提取所有括号内的内容
                if send_content_list:
                    send_content = send_content_list[0]
                    self.call("contact_old_user", service["user_id"])
                    result = self.call("reply",service["user_id"], send_content)
                    if result == "success":
                        self.set_service_status(service["id"], "待处理:已通知客户进展")
                        chat_list = [{
                            "type" : "text",
                            "content" : f"工单{service['id']}的处理进度通知：{send_content}"
                        }]
                        self.add_history(service["user_id"], chat_list)
                    else:
                        self.set_service_status(service["id"], f"待处理:通知失败。{result}")
            elif service["status"].startswith("待联系:关闭工单"):
                self.set_service_status(service["id"], f"已关闭:关闭工单({datetime.now()})")
                chat_list = [{
                    "type" : "text",
                    "content" : f"工单{service['id']}已经关闭。"
                }]
                self.add_history(service["user_id"], chat_list)
            else:
                self.set_service_status(service["id"], f"待处理:还不支持此功能！({service['status']})")

    def reply(self, user, chat_list): 
        # print(f"deal_chat_list: {chat_list}")
        openAI = WhisperAzure(self)
        openAI.reply(user, chat_list)

    def add_history(self, user, chat_list): 
        # print(f"add_history_chat_list: {chat_list}")
        openAI = WhisperAzure(self)
        openAI.add_history(user, chat_list)

    def on_error(self, e): 
        self._error_count = self._error_count + 1
        WhisperTools_Qywx.send_to_error_robot(f"{self._kf_name}出现异常：第{self._error_count}次。({e}, {e.__traceback__.tb_lineno})")
        if (self._error_count > 3):
            result = self.call("activate", self.get_kf_name())
            logger.error(f"准备停止服务，强制激活的结果：{result}")
            if (result == True) :
                self.call("stop", self.get_kf_name())
            self.set_kf_status(0)

    def clear_error(self): 
        self._error_count = 0

    def get_human_kf_name(self):
        # 使用 with 语句管理数据库连接
        with WhisperDB() as db:  # 自动管理连接
            # 使用参数化查询来防止 SQL 注入
            query = """
                SELECT human_servicer FROM openai_kf_manage
                WHERE shop_name = %s;
            """
            # 获取查询结果
            result = db.query(query, (self._kf_name,))

        # 如果查询结果存在，则返回第一行
        return result[0][0] if result else "未设定"
    
    def get_company_name(self):
        return self._company_name

    def is_master(self):
        # 使用 with 语句管理数据库连接
        with WhisperDB() as db:  # 自动管理连接
            # 使用参数化查询来防止 SQL 注入
            query = """
                SELECT master_kf FROM openai_company
                WHERE name = %s;
            """
            # 获取查询结果
            result = db.query(query, (self._company_name,))

        # 如果查询结果存在，则返回第一行
        return result[0][0] == self._kf_name


    def get_vector_id(self):
        # 使用 with 语句管理数据库连接
        with WhisperDB() as db:  # 自动管理连接
            # 使用参数化查询来防止 SQL 注入
            query = """
                SELECT vector_id
                FROM openai_kf_manage
                JOIN openai_company ON openai_kf_manage.company = openai_company.name
                WHERE shop_name = %s;
            """
            # 获取查询结果
            result = db.query(query, (self._kf_name,))

        # 如果查询结果存在，则返回第一行
        return result[0][0] if result else "未设定"
    
    #售后工单相关处理函数
    def report_modify_address_sended(self, order_id, user_id, service_detail):
        return self._report("更改地址", order_id, user_id, service_detail)
    def report_logistic_error(self, order_id, user_id, service_detail):
        return self._report("物流异常", order_id, user_id, service_detail)
    def report_delivery_error(self, order_id, user_id, service_detail):
        return self._report("错发漏发", order_id, user_id, service_detail)
    def report_product_error(self, order_id, user_id, service_detail):
        return self._report("产品投诉", order_id, user_id, service_detail)
    def report_transfer_fail(self, user_id, service_detail):
        return self._report("转人工失败", "", user_id, service_detail)
    def report_transfer_success(self, user_id, service_detail):
        return self._report("转人工成功", "", user_id, service_detail, "已关闭")
    
    def _report(self, type, order_id, user_id, service_detail, status="待处理"):
        myDB = WhisperDB()
        
        # 直接使用参数化查询，确保 JSON 格式正确存储
        query = """
            INSERT INTO `openai_service_manage`
            (`type`, `shop`, `order_id`, `user_id`, `detail`, `kf_name`, `status`) 
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        detail_json = json.dumps(service_detail, ensure_ascii=False)
        # 使用参数化，避免 SQL 注入，并确保 JSON 格式正确存入数据库
        myDB.query(query, (type, self.get_shop_name(), order_id, user_id, detail_json, self.get_kf_name(), status))
        
        myDB.commit()
        last_insert_id = myDB.query("SELECT LAST_INSERT_ID();")  # 获取最后插入的 ID
        myDB.close()
        #WhisperTools_Qywx.send_to_kf_robot(self, f"{self.get_shop_name()}店铺的'{user_id}'提交了‘{type}’的工单({last_insert_id[0][0]})，请及时处理！")
        WhisperTools_Qywx.send_to_kf_robot_report(self, last_insert_id[0][0], self.get_shop_name(), user_id, type, detail_json)
        return last_insert_id[0][0]

    def get_service(self, user_id):
        myDB = WhisperDB()
        query = f"SELECT `id`, `type`, `order_id`, `detail`, `create_time`, `status`, `process` FROM `openai_service_manage` WHERE `shop` = {self.get_shop_name()} AND `user_id` = {user_id};"
        result = myDB.query(query)

        service_list=[]
        for row in result:
            service_list.append({
                "工单ID":row[0],
                "类型":row[1],
                "订单编号":row[2],
                "工单详细信息":row[3],
                "创建时间":row[4].isoformat(),
                "当前状态":row[5],
                "进展情况":row[6]
            })
        myDB.close()
        return service_list
    def get_service_will_action(self):
        myDB = WhisperDB()

        # 1. SQL 语句
        query = """SELECT `id`, `type`, `order_id`, `user_id`, `detail`, `create_time`, `status`, `process`
                FROM `openai_service_manage`
                WHERE `kf_name` = %s AND `status` LIKE '待联系%%';"""

        # 2. 确保 kf_name 作为元组传递
        result = myDB.query(query, (self.get_kf_name(),))  

        # 3. 获取列名
        column_names = ["id", "type", "order_id", "user_id", "detail", "create_time", "status", "process"]

        # 4. 将元组转换为字典
        service_list = [dict(zip(column_names, row)) for row in result]

        myDB.close()
        return service_list  # 返回字典列表
    def set_service_status(self, server_id, status):
        # 检查 status 是否包含 ":"
        if ":" not in status:
            raise ValueError("Invalid status format. Status must contain ':'")

        myDB = WhisperDB()
        
        # 使用 .split 分割，确保有安全的处理
        process = status.split(":", 1)[1]
        
        # 参数化查询避免 SQL 注入
        query = """
            UPDATE `openai_service_manage`
            SET `status` = %s,
                `process` = CONCAT(IFNULL(`process`, ''), '\\n', NOW(), ' - 结束:', %s)
            WHERE `id` = %s;
        """
        
        # 执行查询
        myDB.query(query, (status, process, server_id))
        
        # 提交事务
        myDB.commit()
        myDB.close()
        
        return True