import os
from openai import AzureOpenAI
import json
import logging
logger = logging.getLogger("whisper_ai")

class OpenAIFunction:
    @staticmethod
    def main():

        # 设置OpenAI客户端
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version="2024-05-01-preview",
        )

        print("Client initialized successfully")
        
        tools=[{"type": "file_search"},{"type": "code_interpreter"},
            {
                "type": "function",
                "function": {
                    "name": "get_recently_order",
                    "description": "订单查询函数，查询客户近3个月的订单信息。返回的订单列表信息中，‘收货信息’中包含了收件人姓名、收件人电话、收货详细地址等信息",
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
                    "description": "当客户希望修改地址时，调用此函数进行修改。修改的订单必须是未发货状态。相关参数通过订单查询函数进行调用获取，客户不修改的信息也需要补充真实的信息进行调用此函数。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "需要修改的订单ID"
                        },
                        "order_status": {
                            "type": "string",
                            "description": "订单的状态，只有未发货状态订单才支持修改"
                        },
                        "new_address_name": {
                            "type": "string",
                            "description": "修改后的收件人姓名"
                        },
                        "new_address_tele": {
                            "type": "string",
                            "description": "修改后的收件人电话，客户不修改手机的情况下，也需要客户让重新反馈。"
                        },
                        "new_address_detail": {
                            "type": "string",
                            "description": "修改后的收件人详细地址"
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
                    "description": "植想说店铺的商品默认发送中通快递，若客户希望指定某个快递发货，则可以调用此接口进行指定。只能针对未发货的订单进行指定物流公司，如果已经发货，则不能重新指定物流公司。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "需要指定物流的订单ID，该订单ID可通过订单查询函数进行查询。"
                        },
                        "order_status": {
                            "type": "string",
                            "description": "待修改订单的状态，只有代发货状态下才能够进行物流指定。"
                        },
                        "logistic_name": {
                            "type": "string",
                            "description": "只能选择如下物流，由于护肤品不能空运，不可选择顺丰特快。",
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
                    "description": "当顾客对某个商品感兴趣时，可以调用此函数进行商品推荐，该函数会发出商品购买卡片、商品购买链接给客户，以促进客户的下单。但是，如果顾客已经反馈看过商品链接了，则就不需要调用此函数。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "product_code": {
                            "type": "string",
                            "description": "产品编码，用于唯一标识植想说的某个商品，产品编码可通过 在售商品查询函数 获取。"
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
                    "description": "当客户的问题无法解答或者处理如换货、退款、投诉等问题时，调用此函数将对话转接给更专业的客服经理进行处理。当客户主动要求转接给人工时，也可调用此函数处理。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {
                                "type": "string",
                                "description": "转接原因说明，可根据客户实际的问题，简单描述处理不了的原因。"
                            },
                            "type": {
                                "type": "string",
                                "description": "转人工的原因类别。根据转交人工的原因，进行分类。",
                                "enum": [
                                    "知识库信息缺失",
                                    "客户不满意AI回答",
                                    "客户直接要求",
                                    "其他"
                                ]
                            }
                        },
                        "required": [
                            "reason",
                            "type"
                        ]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "modify_notes",
                    "description": "当遇到客户提出跟赠送小样、发货包装等相关的小要求时，可通过此接口进行订单备注，通知发货工作人员进行相关特殊操作。相关操作包括 暂不发货、可以发货、包装注意事项、赠送小样等情况。订单需要是‘未付款’或者‘待发货’状态才能调用此函数。如果没有‘未付款’或者‘待发货’订单，则提醒客户下单后，再通知客服添加备注。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "需要添加备注的订单编号，此订单编号通过订单查询函数进行查询获取。"
                        },
                        "order_status": {
                            "type": "string",
                            "description": "需要添加备注的订单状态，此订单状态通过订单查询函数进行查询获取。必须是‘未付款’或者‘待发货’状态。"
                        },
                        "notes": {
                            "type": "string",
                            "description": "需要添加的备注信息。"
                        }
                        },
                        "required": [
                        "order_id",
                        "order_status",
                        "note"
                        ]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "report_delivery_error",
                    "description": "当客户反馈商品漏发、错发的问题时，通过此函数进行商品漏发、错发工单登记。进行跟进处理。但是，不包括多收到产品。当客户多收到产品时，不需要通过此函数处理。多发产品直接赠送客户。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "有商品错发、漏发的订单编号，此订单编号通过订单查询函数进行查询获取。如果获取到多个订单，使用最后的订单的ID。"
                        },
                        "error_type": {
                            "type": "string",
                            "description": "客户碰到的错发、漏发问题的类型。",
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
                            "description": "错发时，建议提供错发商品的照片。漏发时，建议提供快递内所有商品的照片。照片均用file_id方式传入此参数。file_id为客户发出的图片上传后生成的id。不超过3张照片。"
                        },
                        "logistic_images": {
                            "type": "array",
                            "items": {
                            "type": "string"
                            },
                            "description": "提供快递面单的照片。照片用file_id方式传入此参数。file_id为客户发出的图片上传后生成的id。不超过3张照片。"
                        },
                        "error_detail": {
                            "type": "string",
                            "description": "客户碰到的商品错发、漏发问题的详细描述。"
                        },
                        "prefer_method": {
                            "type": "string",
                            "description": "客户期望的处理方式。",
                            "enum": [
                            "补发处理",
                            "退款退货处理",
                            "其他"
                            ]
                        },
                        "name": {
                            "type": "string",
                            "description": "当客户希望补发处理方式，且需要更改收件人姓名时，提供此信息。其他处理方式下，不需要用户提供此信息。"
                        },
                        "telephone": {
                            "type": "string",
                            "description": "当客户希望补发处理方式时，需要客户提供收件人电话。其他处理方式下，不需要用户提供此信息。"
                        },
                        "address": {
                            "type": "string",
                            "description": "当客户希望补发处理方式，且需要更改收件详细地址时，提供此信息。其他处理方式下，不需要用户提供此信息。"
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
                    "description": "当客服反馈订单物流问题时，通过此函数进行物流异常工单上报，跟进处理。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "有物流异常的订单编号，此订单编号通过订单查询函数进行查询获取。如果获取到多个进行中订单，使用最后的订单的ID。"
                        },
                        "error_type": {
                            "type": "string",
                            "description": "客户碰到的物流问题的类型。",
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
                            "description": "物流异常订单，对应的图片file_id，最多不超过3张。该file_id为客户发出的图片上传后生成的id。"
                        },
                        "error_detail": {
                            "type": "string",
                            "description": "客户碰到的物流问题的详细描述。"
                        },
                        "prefer_method": {
                            "type": "string",
                            "description": "客户期望的处理方式。",
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
                    "description": "当客户希望了解商品的生产日期或者有效期等信息时，调用此函数进行当前时刻全部商品有效期查询。如果客户隔段时间再询问，需要重新查询。",
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
                    "description": "已发货订单地址修改上报接口。当订单已经发货后，客户仍希望修改地址时，调用此函数进行修改地址工单上报。订单ID参数通过订单查询函数进行调用获取，客户收件人、收件电话、详细地址均需要补充和客户确认，并传入参数中。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                        "order_id": {
                            "type": "string",
                            "description": "需要修改的订单ID，此订单编号通过订单查询函数进行查询获取。如果获取到多个进行中订单，使用最后的订单的ID。"
                        },
                        "new_address_name": {
                            "type": "string",
                            "description": "修改后的收件人姓名，若无变化，则无需提供。"
                        },
                        "new_address_tele": {
                            "type": "string",
                            "description": "修改后的收件人电话，电话号码必须重新向用户索取，订单查询函数中获取的收件人电话号码是加密后的，不能再次使用。"
                        },
                        "new_address_detail": {
                            "type": "string",
                            "description": "修改后的收件人详细地址，若无变化，则无需提供。"
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
                    "description": "当客户反馈商品质量问题时，调用此函数提交商品质量问题工单。提交后，会有专人和客户联系。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "order_id": {
                                "type": "string",
                                "description": "有产品质量问题的订单 ID。此订单 ID 可以通过 get_recently_order 函数获取。如果获取到多个订单，使用最后的订单的ID。"
                            },
                            "products_images": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                },
                                "description": "对应产品质量问题订单的照片，不超过 3 张。file_id 在客户上传图片后生成。"
                            },
                            "error_detail": {
                                "type": "string",
                                "description": "客户遇到的产品质量问题的详细描述。"
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
                    "description": "当客户询问当前的优惠活动、商品是否销售、有哪些折扣/优惠、空瓶回收活动细节时，可调用此函数查询店铺现在进行的所有活动、在售商品的产品编码、产品折扣/优惠、产品具体规格在售情况等信息。每次客户询问时，都需要调用此函数查询最新情况。",
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
                    "name": "get_recent_activities",
                    "description": "当客户询问当前和近期即将开展的优惠活动、折扣/优惠、空瓶回收活动的详细内容、开始/结束时间等时，可调用此函数查询。每次客户询问时，都需要调用此函数查询最新情况。",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
        ]


        try:
            tools_json = json.dumps(tools, ensure_ascii=False)
            print(tools_json)
        except UnicodeDecodeError as e:
            print(f"Unicode decode error: {e}")

        # 然后传递 tools_json 给你的 API ——manreya：小助手
        try:
            my_updated_assistant = client.beta.assistants.update(
                "asst_MeXyTH324p4dzL1R502ijeFf",
                tools=tools,
                response_format="auto"
            )
            print(my_updated_assistant)
        except Exception as e:
            print(f"Error updating assistant: {e}")

        pass

        # 然后传递 tools_json 给你的 API——————薰衣草
        try:
            my_updated_assistant = client.beta.assistants.update(
                "asst_ONhM3rpfr9skqBbNY6tsa2yN",
                tools=tools,
                response_format="auto"
            )
            print(my_updated_assistant)
        except Exception as e:
            print(f"Error updating assistant: {e}")

        # 然后传递 tools_json 给你的 API  ————亮亮
        try:
            my_updated_assistant = client.beta.assistants.update(
                "asst_pxbRLCXVgaDSMyVMhipy1tMf",
                tools=tools,
                response_format="auto"
            )
            print(my_updated_assistant)
        except Exception as e:
            print(f"Error updating assistant: {e}")

        pass

if __name__ == "__main__":
    print("Running OpenAIFunction.main()...")
    OpenAIFunction.main()