import logging
logger = logging.getLogger("whisper_ai")

class AgentTest:
    def __init__(self, reg):
        """ 初始化一个空字典用于存储函数 """
        self._agent_kf = reg

    def test(self):
        #初始化
        Agent = self._agent_kf
        kf_name = Agent.get_kf_name()
        user_list = Agent.call("get_customers_waiting")
        logger.info("user_list:", user_list)
        for user in user_list:
            chat_list = Agent.call("get_new_chats", user, "")
            logger.info("chat_list:", chat_list)
            Agent.call("reply", user, "This is a test!")
            Agent.call("transfer_to_customer_care", user, "人工客服", "test")
            order_list = Agent.call("get_recently_order", user)
            Agent.call("specify_logistic", user, order_list[0]["订单ID"], "顺丰陆运")
            Agent.call("recommend_product", user, "大马士革玫瑰纯露")
            Agent.call("modify_notes", user, order_list[0]["订单ID"], "待发货", "test")
            Agent.call("recommend_product", user, "大马士革玫瑰纯露")
            # Agent.call("modify_address", user, "大马士革玫瑰纯露")
            Agent.call("contact_old_user", user)
            self._agent_kf.call("close_chat", user)
            Agent.call("activate", kf_name)
            



        