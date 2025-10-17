from .whisper_db import WhisperDB
import os
import json
from openai import AzureOpenAI
from .whisper_handler import EventHandler
from .whisper_tools import WhisperTools_ChatRecord
import logging
logger = logging.getLogger("whisper_ai")

import base64
from mimetypes import guess_type

class WhisperAzure:
    def __init__(self, reg):
        self._registry = reg

    # Function to encode a local image into data URL 
    def _local_image_to_data_url(self, image_path):
        # Guess the MIME type of the image based on the file extension
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'  # Default MIME type if none is found

        # Read and encode the image file
        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

        # Construct the data URL
        return f"data:{mime_type};base64,{base64_encoded_data}"

    def reply(self, fromUserID, msgList):

        logger.info(msgList)

        if len(msgList)==0:
            return

        # 判断长度并保留后10项
        if len(msgList) > 10:
            msgList = msgList[-10:]

        # 设置OpenAI客户端
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version="2024-05-01-preview",
        )

        newchatFlag = True

        # 创建数据库连接
        myDB2 = WhisperDB()
        query2 = """
            SELECT assistant_id FROM openai_kf_manage WHERE shop_name=%s;
        """
        # 获取查询结果
        result2 = myDB2.query(query2, (self._registry.get_kf_name(),))

        # 假设 result 是包含单条记录的列表，并且每条记录是一个元组
        row = result2[0] if result2 else None
        assistant_id = row[0] if row else None  # 访问元组的第一个元素

        # 打印结果
        logger.info(f"assistant_id : {assistant_id}")
        my_assistant = client.beta.assistants.retrieve(assistant_id)

        # 关闭数据库连接
        myDB2.close()

        myDB = WhisperDB()

        # 检查是否存在有效的ThreadID
        query = f"SELECT `ThreadID` FROM `openai_user_list` WHERE `UserID` = '{self._registry.get_shop_name()}-{fromUserID}' AND (`UpdateTime` >= NOW() - INTERVAL 3 DAY)"
        result = myDB.query(query)

        my_thread = None
        if result:
            try:
                my_thread = client.beta.threads.retrieve(result[0][0])
            except Exception as e:
                my_thread = None

        if my_thread:
            logger.info(f"找到老的沟通记录。{my_thread.id}")
            newchatFlag = False
            #检查上一次run是否执行完成，没有执行完成，则取消run
            runs = client.beta.threads.runs.list(
                my_thread.id,limit = 1
            )
            if len(runs.data) > 0 :
                run = client.beta.threads.runs.retrieve(
                    thread_id=my_thread.id,
                    run_id=runs.data[0].id
                )
                if run.status != "completed" and run.status != "expired" and run.status != "failed":
                    #print("终止老的run！")
                    #run = client.beta.threads.runs.cancel(
                    #    thread_id=my_thread.id,
                    #    run_id=runs.data[0].id
                    #)
                    my_thread = client.beta.threads.create()
                    logger.info(f'新创建沟通线程。{my_assistant.id},{my_thread.id}')  
                    newchatFlag = True
        else:
            my_thread = client.beta.threads.create()
            logger.info(f'新创建沟通线程。{my_assistant.id},{my_thread.id}')  
            newchatFlag = True

        insert_update_query = f"""
            INSERT INTO `openai_user_list` (`UserID`, `ThreadID`, `AssistantID`, `UpdateTime`)
            VALUES ('{self._registry.get_shop_name()}-{fromUserID}', '{my_thread.id}', '{my_assistant.id}', NOW())
            ON DUPLICATE KEY UPDATE
            `ThreadID` = VALUES(`ThreadID`),
            `AssistantID` = VALUES(`AssistantID`),
            `UpdateTime` = NOW(),
            `Interactions` = `openai_user_list`.`Interactions` + 1;
        """
        myDB.query(insert_update_query)
        myDB.commit()
        myDB.close()

        content = []

        for item in msgList:
            #print (item)
            #print("chatGPT create msg:" + item["msgType"])
            if item["type"] == "text":
                #做容错特殊处理
                if (item["content"] == ""):
                    logger.info("收到一条空消息！")
                    item["content"] = "【空消息】"
                content.append({"type":"text","text":item["content"]})
            elif item["type"] == "good_card":
                content.append({"type":"text","text":"我刚刚看过了你们家“"+item["product_name"]+"”商品链接。"})
            elif item["type"] == "image":
                image_url = item["url"]  # 替换为图片的URL

                #imageObject = client.files.create(
                #    file=open(image_url, "rb"),
                #    purpose="vision"
                #)
                #content.append({"type":"image_file","image_file":{"file_id":imageObject.id}})            
                data_url = self._local_image_to_data_url(image_url)
                logger.info("Data URL:", data_url)
                response = client.chat.completions.create(
                    model="gpt-4o-new",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": """这一张图片或者表情。
                                        如果是图片，请以‘我发了一张图片，系统协助识别图片内容为：......’格式分析和评论这张图片内容，有订单编号或订单ID的话，请提取出来；
                                        如果是表情，直接用文字符号替换该表情，不用任何其他描述。""",
                                },
                                {"type":"image_url","image_url": {"url":data_url}},
                            ],
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.4
                )
                logger.info("Vision Assistant Message: " + response.choices[0].message.content)
                #content.append({"type":"image_url","image_url": {"url":data_url}})
                content.append({"type":"text","text":"" + response.choices[0].message.content})

        WhisperTools_ChatRecord.record_user_chat(self._registry.get_kf_name(), fromUserID, json.dumps(content))

        # print(content)
        thread_message = client.beta.threads.messages.create(
            my_thread.id,
            role="user",
            content=content,
        )

        pro_event_handler = EventHandler(self._registry)
        pro_event_handler.set_userName(fromUserID)
        pro_event_handler.set_transferFlag(False)
        pro_event_handler.set_transferReason("", "")
        
        with client.beta.threads.runs.stream(
            thread_id=my_thread.id,
            assistant_id=my_assistant.id,
            event_handler=pro_event_handler,
        ) as stream:
            stream.until_done()
            pro_event_handler.proEnd()

        pass
    
    def add_history(self, fromUserID, msgList):
        if len(msgList)==0:
            return

        # 判断长度并保留后10项
        if len(msgList) > 10:
            msgList = msgList[-10:]

        # 设置OpenAI客户端
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version="2024-05-01-preview",
        )
        # 创建数据库连接
        myDB2 = WhisperDB()
        query2 = """
            SELECT assistant_id FROM openai_kf_manage WHERE shop_name=%s;
        """
        # 获取查询结果
        result2 = myDB2.query(query2, (self._registry.get_kf_name(),))

        # 假设 result 是包含单条记录的列表，并且每条记录是一个元组
        row = result2[0] if result2 else None
        assistant_id = row[0] if row else None  # 访问元组的第一个元素

        # 打印结果
        logger.info("assistant id: {assistant_id}")
        my_assistant = client.beta.assistants.retrieve(assistant_id)

        # 关闭数据库连接
        myDB2.close()

        myDB = WhisperDB()

        # 检查是否存在有效的ThreadID
        query = f"""SELECT `ThreadID` 
                    FROM `openai_user_list` 
                    WHERE `UserID` = '{self._registry.get_shop_name()}-{fromUserID}' 
                    AND `UpdateTime` >= DATE_SUB(NOW(), INTERVAL 5 DAY)
                """
        result = myDB.query(query)

        my_thread = None
        if result:
            try:
                my_thread = client.beta.threads.retrieve(result[0][0])
            except Exception as e:
                my_thread = None

        if my_thread:
            logger.info(f"找到老的沟通记录。{my_thread.id}")
            newchatFlag = False
            #检查上一次run是否执行完成，没有执行完成，则取消run
            runs = client.beta.threads.runs.list(
                my_thread.id,limit = 1
            )
            if len(runs.data) > 0 :
                run = client.beta.threads.runs.retrieve(
                    thread_id=my_thread.id,
                    run_id=runs.data[0].id
                )
                if run.status != "completed" and run.status != "expired" and run.status != "failed":
                    #print("终止老的run！")
                    #run = client.beta.threads.runs.cancel(
                    #    thread_id=my_thread.id,
                    #    run_id=runs.data[0].id
                    #)
                    my_thread = client.beta.threads.create()
                    logger.info(f'新创建沟通线程。{my_assistant.id},{my_thread.id}')  
                    newchatFlag = True
        else:
            my_thread = client.beta.threads.create()
            logger.info(f'新创建沟通线程。{my_assistant.id},{my_thread.id}')  
            newchatFlag = True

        insert_update_query = f"""
            INSERT INTO `openai_user_list` (`UserID`, `ThreadID`, `AssistantID`, `UpdateTime`)
            VALUES ('{self._registry.get_shop_name()}-{fromUserID}', '{my_thread.id}', '{my_assistant.id}', NOW())
            ON DUPLICATE KEY UPDATE
            `ThreadID` = VALUES(`ThreadID`),
            `AssistantID` = VALUES(`AssistantID`),
            `UpdateTime` = NOW(),
            `Interactions` = `openai_user_list`.`Interactions` + 1;
        """
        myDB.query(insert_update_query)
        myDB.commit()
        myDB.close()

        content = []

        for item in msgList:
            #print (item)
            #print("chatGPT create msg:" + item["msgType"])
            if item["type"] == "text":
                content.append({"type":"text","text":item["content"]})
                WhisperTools_ChatRecord.record_chatGPT_action(self._registry.get_kf_name(), fromUserID, "reply", item["content"])

        logger.info(f"开始插入AI对话记录：{content}")
        # print(content)
        thread_message = client.beta.threads.messages.create(
            my_thread.id,
            role="assistant",
            content=content,
        )
        logger.info(thread_message)
        pass
