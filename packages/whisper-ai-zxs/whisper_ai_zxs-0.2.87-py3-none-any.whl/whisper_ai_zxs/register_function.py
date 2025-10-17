# 使用提醒:
# 1. xbot包提供软件自动化、数据表格、Excel、日志、AI等功能
# 2. package包提供访问当前应用数据的功能，如获取元素、访问全局变量、获取资源文件等功能
# 3. 当此模块作为流程独立运行时执行main函数
# 4. 可视化流程中可以通过"调用模块"的指令使用此模块

import xbot
from xbot import print, sleep
from .import package
from .package import variables as glv

from openai import OpenAI
import json

def main(args):

    # 设置OpenAI客户端11
    client = OpenAI(
        #base_url="https://gateway.ai.cloudflare.com/v1/c4e6487dd03c420877ba096cdf551afc/open-ai/openai/",
        base_url="http://e78e9fddbd7d736f363e6314d1b70180.api-forwards.com/v1",
        api_key="sk-proj-MsUkxNYAeWY5UogJ3v8CT3BlbkFJdoLGQKm9GCVjYCzFY0C9",
        default_headers={"OpenAI-Beta": "assistants=v2"}
    )

    tools = [
        {"type": "file_search"},
        {"type": "code_interpreter"},
        {
            "type": "function",
            "function": {
                "name": "get_recently_order",
                "description": "Order query function to query customer orders from the past 3 months. The returned order list includes recipient name, recipient phone number, and detailed delivery address in the 'shipping information'.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "modify_address",
                "description": "When a customer wants to modify the address, this function can be called to make the changes. The order must be in an unshipped status. Relevant parameters can be obtained through get_recently_order function, and even if the customer does not modify certain information, the real information must still be provided when calling this function.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order to be modified"
                        },
                        "order_status": {
                            "type": "string",
                            "description": "The status of the order. Only orders that have not been shipped can be modified."
                        },
                        "new_address_name": {
                            "type": "string",
                            "description": "The name of the recipient after the address is modified"
                        },
                        "new_address_tele": {
                            "type": "string",
                            "description": "The phone number of the recipient after the address is modified. Even if the customer does not modify the phone number, they still need to provide feedback."
                        },
                        "new_address_detail": {
                            "type": "string",
                            "description": "The detailed address of the recipient after the address is modified"
                        }
                    },
                    "required": [
                        "order_id",
                        "order_status",
                        "new_address_name",
                        "new_address_tele",
                        "new_address_detail"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "specify_logistic",
                "description": "The shop defaults to using ZTO Express for shipping. If the customer wants to specify a particular courier, this interface can be used to do so. Only orders that have not been shipped can have their logistics company specified. If the order has already been shipped, the logistics company cannot be changed.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order for which the logistics need to be specified. This order ID can be obtained through get_recently_order function."
                        },
                        "order_status": {
                            "type": "string",
                            "description": "The status of the order to be modified. Logistics can only be specified for orders in the 'awaiting shipment' status."
                        },
                        "logistic_name": {
                            "type": "string",
                            "description": "Only the following couriers can be chosen. Due to restrictions on shipping skincare products by air, SF Express is not an option.",
                            "enum": [
                                "中通",
                                "顺丰陆运",
                                "韵达",
                                "邮政"
                            ]
                        }
                    },
                    "required": [
                        "order_id",
                        "order_status",
                        "logistic_name"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "recommend_product",
                "description": "When a customer shows interest in a product, this function can be called to recommend the product. The function will send a product purchase card and a purchase link to the customer to encourage them to place an order. However, if the customer has already indicated that they have seen the product link, there is no need to call this function.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_code": {
                            "type": "string",
                            "description": "Product code, The product code is used to uniquely identify a product in the shop. The product code must be obtained through the get_selling_product function and cannot be self-defined or assumed."
                        }
                    },
                    "required": [
                        "product_code"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "transfer_to_customer_care",
                "description": "When the customer's problem cannot be resolved or handled, such as for exchanges, refunds, complaints, etc., this function is called to transfer the conversation to a more professional customer service manager for handling. This function can also be called when the customer requests a transfer to a human agent.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for the transfer. A brief description of why the issue cannot be handled based on the customer's actual problem."
                        }
                    },
                    "required": [
                        "reason"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "modify_notes",
                "description": "When encountering a customer's request related to free samples, shipping packaging, or other small requests, you can use this interface to add order notes, informing the shipping staff to perform the relevant special operations. These operations include holding the shipment, shipping, packaging precautions, and adding free samples. The order must be in the 'unpaid' or 'pending shipment' status to call this function. If there are no 'unpaid' or 'pending shipment' orders, remind the customer to place an order first and then inform customer service to add the notes.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID for which the notes need to be added. This order ID can be obtained through get_recently_order function."
                        },
                        "order_status": {
                            "type": "string",
                            "description": "The status of the order for which the notes need to be added. This order status can be obtained through get_recently_order function. It must be in 'unpaid' or 'awaiting shipment' status."
                        },
                        "notes": {
                            "type": "string",
                            "description": "The notes that need to be added."
                        }
                    },
                    "required": [
                        "order_id",
                        "order_status",
                        "notes"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "report_delivery_error",
                "description": "When customers report issues of missing or incorrect item shipments, this function is used to register work orders for missing or incorrect shipments and follow up on them. However, this does not include cases where customers receive extra products. If customers receive extra products, this function is not needed, and the extra products can be given directly to the customers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID with missing or wrong delivery items. This order ID can be obtained through get_recently_order function."
                        },
                        "error_type": {
                            "type": "string",
                            "description": "Type of issue encountered by the customer.",
                            "enum": [
                                "错发",
                                "漏发",
                                "其他"
                            ]
                        },
                        "products_images": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "In case of wrong delivery, it is recommended to provide photos of the wrongly delivered items. In case of missing delivery, it is recommended to provide photos of all items in the package. Photos should be provided using file_id, generated after the customer uploads the images. No more than 3 photos."
                        },
                        "logistic_images": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Provide photos of the logistics bill. Photos should be provided using file_id, generated after the customer uploads the images. No more than 3 photos."
                        },
                        "error_detail": {
                            "type": "string",
                            "description": "Detailed description of the wrong or missing delivery issue encountered by the customer."
                        },
                        "prefer_method": {
                            "type": "string",
                            "description": "The customer's preferred method of handling.",
                            "enum": [
                                "补发处理",
                                "退款退货处理",
                                "其他"
                            ]
                        },
                        "name": {
                            "type": "string",
                            "description": "When the customer wants a resend, they need to provide the recipient's name."
                        },
                        "telephone": {
                            "type": "string",
                            "description": "When the customer wants a resend, they need to provide the recipient's phone number. The phone number must be re-obtained from the user, as the phone number obtained from the order query function is encrypted and cannot be reused."
                        },
                        "address": {
                            "type": "string",
                            "description": "When the customer wants a resend, they need to provide the recipient's detailed address."
                        }
                    },
                    "required": [
                        "order_id",
                        "error_type",
                        "error_detail",
                        "prefer_method"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "report_logistic_error",
                "description": "When customer service reports a logistics issue with an order, this function is called to report the logistics exception work order for follow-up.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID with logistics issues. This order ID can be obtained through get_recently_order function."
                        },
                        "error_type": {
                            "type": "string",
                            "description": "Type of logistics issue encountered by the customer.",
                            "enum": [
                                "物流长时间无更新",
                                "物流路径异常",
                                "物流已到达网点未派送",
                                "物流反馈丢件",
                                "未收到货已签收",
                                "其他"
                            ]
                        },
                        "error_images": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Photos corresponding to the logistics exception order, no more than 3 photos. The file_id is generated after the customer uploads the images."
                        },
                        "error_detail": {
                            "type": "string",
                            "description": "Detailed description of the logistics issue encountered by the customer."
                        },
                        "prefer_method": {
                            "type": "string",
                            "description": "The customer's preferred method of handling.",
                            "enum": [
                                "退款退货",
                                "联系快递派送",
                                "旺旺联系我",
                                "电话联系我",
                                "其他"
                            ]
                        }
                    },
                    "required": [
                        "order_id",
                        "error_type",
                        "error_images",
                        "error_detail",
                        "prefer_method"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_production_date",
                "description": "When customers want to know the production date or expiration date of a product, this function can be called to query the validity period of all products now.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "report_modify_address_sended",
                "description": "Interface for reporting address modification after the order has been shipped. When the order has already been shipped and the customer still wants to modify the address, this function is called to report the address modification work order. The order ID parameter can be obtained through get_recently_order function. The recipient's name, phone number, and detailed address must all be confirmed with the customer and passed into the parameters.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The ID of the order to be modified. This order ID can be obtained through get_recently_order function."
                        },
                        "new_address_name": {
                            "type": "string",
                            "description": "The name of the recipient after the address is modified"
                        },
                        "new_address_tele": {
                            "type": "string",
                            "description": "The phone number of the recipient after the address is modified. The phone number must be re-obtained from the user, as the phone number obtained from the order query function is encrypted and cannot be reused."
                        },
                        "new_address_detail": {
                            "type": "string",
                            "description": "The detailed address of the recipient after the address is modified"
                        }
                    },
                    "required": [
                        "order_id",
                        "new_address_name",
                        "new_address_tele",
                        "new_address_detail"
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "report_product_error",
                "description": "When a customer reports an issue with product quality, use this function to submit a product quality issue ticket. After submission, a dedicated representative will contact the customer.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "The order ID with product quality issues. This order ID can be obtained through get_recently_order function."
                        },
                        "products_images": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "Photos corresponding to the product quality order, no more than 3 photos. The file_id is generated after the customer uploads the images."
                        },
                        "error_detail": {
                            "type": "string",
                            "description": "Detailed description of the product quality issue encountered by the customer."
                        }
                    },
                    "required": [
                        "order_id",
                        "error_detail",
                    ]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_selling_product",
                "description": "When a customer inquires about promotional activities, whether a product is on sale, available discounts/offers, or details of empty bottle recycling activities, this function can be called to query information about all store activities, product codes of items on sale, product discounts/offers, and the specific availability of product specifications.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }
    ]


    try:
        tools_json = json.dumps(tools, ensure_ascii=False)
        print(tools_json)
    except UnicodeDecodeError as e:
        print(f"Unicode decode error: {e}")

    # 然后传递 tools_json 给你的 API
    try:
        my_updated_assistant = client.beta.assistants.update(
            "asst_T6eFyJiXVMNd7MHgpTY7Pj35",
            tools=tools,
            response_format="auto"
        )
        print(my_updated_assistant)
    except Exception as e:
        print(f"Error updating assistant: {e}")

    # 然后传递 tools_json 给你的 API
    try:
        my_updated_assistant = client.beta.assistants.update(
            "asst_bkbRlyErGzADiHZW6hZUgPpv",
            tools=tools,
            response_format="auto"
        )
        print(my_updated_assistant)
    except Exception as e:
        print(f"Error updating assistant: {e}")

    pass
