#接口说明

## activate 

## collect_info

## start
    参数：
        kf_name:客服的短名称

## stop
    参数：
        kf_name:客服的短名称

        # self.register("stop", process26)   #多开版
        self.register("reply", process3)
        self.register("get_customers_waiting", process4)
        self.register("get_new_chats", process5)
        self.register("close_chat", process6)
        self.register("transfer_to_customer_care", process8)
        self.register("get_recently_order", process9)
        self.register("specify_logistic", process12)
        self.register("recommend_product", process13)
        self.register("modify_notes", process16)
        self.register("modify_address", process22)
        self.register("contact_old_user", process23)