from .whisper_db import WhisperDB
import json
import logging
logger = logging.getLogger("whisper_ai")

class AIFunctionRegistry(type):
    """元类实现类自动注册"""
    registry = {}

    def __new__(cls, name, bases, class_dict):
        new_class = super().__new__(cls, name, bases, class_dict)
        if name != "BaseClass":  # 避免基类自身注册
            cls.registry[name] = new_class
        return new_class

class BaseClass(metaclass=AIFunctionRegistry):
    """基类，所有子类都会自动注册"""
    def call(self, arguments):
        pass
    pass

# 定义新的子类
class get_recently_order(BaseClass):
    def call(self, user, arguments, agent):
        result = agent.call(self.__class__.__name__, user)
        return json.dumps(result)
    pass

class modify_address(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        if agent.is_register(self.__class__.__name__):
            result = agent.call(self.__class__.__name__, user, 
                            arguments_dict['order_id'], 
                            arguments_dict.get("new_address_name",""),
                            arguments_dict.get("new_address_tele",""),
                            arguments_dict.get("new_address_detail","")
                        )
        else:
            service_detail = {
                "new_address_name":arguments_dict.get("new_address_name",""),
                "new_address_tele":arguments_dict.get("new_address_tele",""),
                "new_address_detail":arguments_dict.get("new_address_detail","")
            }
            service_id = agent.report_modify_address_sended(arguments_dict['order_id'], user, service_detail)
            result = f"已经提交工单，工单ID为：{service_id}"
        return json.dumps(result)
    pass

class specify_logistic(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        result = agent.call(self.__class__.__name__, user, 
                            arguments_dict['order_id'], 
                            arguments_dict.get("logistic_name","")
                        )
        return json.dumps(result)
    pass

class recommend_product(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        result = agent.call(self.__class__.__name__, user, 
                            arguments_dict['product_code']
                        )
        return json.dumps(result)
    pass
class modify_notes(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        result = agent.call(self.__class__.__name__, user, 
                            arguments_dict['order_id'], 
                            arguments_dict['order_status'],
                            arguments_dict.get("notes","")
                        )
        return json.dumps(result)
    pass

#如下函数涉及工单系统，无Agent注册时，使用内部工单系统
class report_modify_address_sended(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        if agent.is_register(self.__class__.__name__):
            result = agent.call(self.__class__.__name__, user, 
                arguments_dict['order_id'], 
                arguments_dict.get("new_address_name",""),
                arguments_dict.get("new_address_tele",""),
                arguments_dict.get("new_address_detail","")
            )
        else:
            service_detail = {
                "new_address_name":arguments_dict.get("new_address_name",""),
                "new_address_tele":arguments_dict.get("new_address_tele",""),
                "new_address_detail":arguments_dict.get("new_address_detail","")
            }
            service_id = agent.report_modify_address_sended(arguments_dict['order_id'], user, service_detail)
            result = f"已经提交工单，工单ID为：{service_id}"
        return json.dumps(result)
    pass

class report_logistic_error(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        if agent.is_register(self.__class__.__name__):
            result = agent.call(self.__class__.__name__, user, 
                arguments_dict['order_id'], 
                arguments_dict['error_type'],
                arguments_dict.get("error_images",[""]),
                arguments_dict['error_detail'],
                arguments_dict['prefer_method']
            )
        else:
            service_detail = {
                "error_type":arguments_dict['error_type'],
                "error_detail":arguments_dict['error_detail'],
                "prefer_method":arguments_dict['prefer_method']
            }
            service_id = agent.report_logistic_error(arguments_dict['order_id'], user, service_detail)
            result = f"已经提交工单，工单ID为：{service_id}"
        return json.dumps(result)
    pass
class report_delivery_error(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        if agent.is_register(self.__class__.__name__):
            result = agent.call(self.__class__.__name__, user, 
                arguments_dict['order_id'], 
                arguments_dict['error_type'],
                arguments_dict.get("products_images",[""]),
                arguments_dict.get("logistic_images",[""]),
                arguments_dict['error_detail'],
                arguments_dict['prefer_method'],
                arguments_dict.get("name",[""]),
                arguments_dict.get("telephone",[""]),
                arguments_dict.get("address",[""])
            )
        else:
            service_detail = {
                "error_type":arguments_dict['error_type'],
                "error_detail":arguments_dict['error_detail'],
                "prefer_method":arguments_dict['prefer_method'],
                "name":arguments_dict.get("name",[""]),
                "telephone":arguments_dict.get("telephone",[""]),
                "address":arguments_dict.get("address",[""])
            }
            service_id = agent.report_delivery_error(arguments_dict['order_id'], user, service_detail)
            result = f"已经提交工单，工单ID为：{service_id}"
        return json.dumps(result)
    pass

class report_product_error(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        if agent.is_register(self.__class__.__name__):
            result = agent.call(self.__class__.__name__, user, 
                arguments_dict['order_id'], 
                arguments_dict.get("products_images",[""]),
                arguments_dict['error_detail']
            )
        else:
            service_detail = {
                "error_detail":arguments_dict['error_detail']
            }
            service_id = agent.report_product_error(arguments_dict['order_id'], user, service_detail)
            result = f"已经提交工单，工单ID为：{service_id}"
        return json.dumps(result)
    pass

class goto_rest(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        arguments_dict = json.loads(arguments)
        """
        p_arg = {
            "reason":arguments_dict['reason']
            }
            """
        result = "待实现"
        return json.dumps(result)
    pass

#以下函数不需要RPA参与进行查询
class get_production_date(BaseClass):
    # 该函数并不适用与所有客户，未来还需要再改造！
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        #arguments_dict = json.loads(arguments)
        myDB = WhisperDB()
        # 检查是否存在有效的ThreadID
        query = f"SELECT `货品编号`,`货品名称`,`商家编码`,`规格名称`,`生产日期`,`有效期`,`库存数量` FROM `erp_production_date` WHERE `仓库` = '植想说云仓-旺店通wms';"

        result = myDB.query(query)

        product_list=[]
        for row in result:
            product_list.append({
                "产品编码":row[0],
                "产品名称":row[1],
                "商品编码":row[2],
                "规格名称":row[3],
                "生产日期":row[4].isoformat(),
                "有效期":row[5].isoformat(),
                "库存数量":row[6],
            })


        myDB.close()
        return json.dumps(product_list)
    pass


class get_selling_product(BaseClass):
    def call(self, user, arguments, agent):
        # 将 arguments 解析为字典
        #arguments_dict = json.loads(arguments)
        myDB = WhisperDB()
        query = f"SELECT `product_code`,`product_name`, `discount_plan`, `on_sale_sku`,`off_sale_sku`, `purchase_link` FROM `tm_selling_product` WHERE `shop_name`='{agent.get_shop_name()}'"

        result = myDB.query(query)
        product_list = []
        for row in result:
            product_list.append({
                "产品编码":row[0],
                "产品名称":row[1],
                "当前折扣":row[2],
                "在售规格":row[3],
                "停售规格":row[4],
                "购买链接":row[5],
            })

        query = f"SELECT ta.activity_name, ta.begin_date, ta.end_date, ta.content FROM tm_activities ta JOIN tm_activities_shop_list tasl ON ta.id = tasl.activity_id WHERE tasl.shop_name = '{agent.get_shop_name()}' AND ta.`end_date` >=now();"

        result = myDB.query(query)
        activity_list = []
        for row in result:
            activity_list.append({
                "活动名称":row[0],
                "开始时间":row[1].strftime('%Y-%m-%d %H:%M:%S'),
                "结束时间":row[2].strftime('%Y-%m-%d %H:%M:%S'),
                "活动内容":row[3],
            })

        myDB.close()
        result = {
            "店铺活动":activity_list,
            "在售商品":product_list
        }
        return json.dumps(result)
    pass


# 使用
# print(AIFunctionRegistry.registry)  
# 输出: {'Foo': <class '__main__.Foo'>, 'Bar': <class '__main__.Bar'>}

# 通过注册表动态创建实例
# cls_name = "Foo"
# instance = AIFunctionRegistry.registry[cls_name]()
# print(type(instance))  # <class '__main__.Foo'>
