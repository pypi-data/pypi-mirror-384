from openai import AzureOpenAI
from .whisper_db import WhisperDB
from .whisper_tools import WhisperTools_Qywx
import os
import json
from collections import defaultdict
import logging
logger = logging.getLogger("whisper_ai")

class AgentTrainer:
    def __init__(self):
        """ 初始化一个空字典用于存储函数 """
        self.assistant_id = "asst_7VzwDP4SBDltl3sEBB21baxx"
        self.task_list_done = []
        self.task_list = [
            "coach_get_selling_product",
            "coach_get_completed_order",
#            "daily_report",
        ]
        self._error_count = 0

    def run(self, agent_list):
        #超过3次错误，就不再尝试！
        if self._error_count > 3:
            logger.error(f"错误次数超过3次，不再执行教练任务！！")
            return
        for agent in agent_list:
            #logger.info(f"{agent.get_kf_name()}准备执行教练任务！")
            for task_name in self.task_list:
                task = {
                    "task_name":task_name,
                    "kf_name":agent.get_kf_name()
                }
                if (task not in self.task_list_done):
                    logger.info(f"{agent.get_kf_name()}的{task_name}任务开始执行！")
                    if (task_name == "daily_report"):
                        if (agent.is_master()):
                            self.daily_report(agent)
                    else:
                        agent.call(task_name, agent.get_kf_name())
                    self.task_list_done.append({"task_name":task_name, "kf_name":agent.get_kf_name()})
                    return True
        #logger.info(f"所有任务已执行完成！")
        return False

    def clear_run(self):
        self.task_list_done = []
        self._error_count = 0
    def on_error(self, e):
        self._error_count = self._error_count + 1
        WhisperTools_Qywx.send_to_error_robot(f"AI教练出现异常：({e}，{e.__traceback__.tb_lineno})")    

    def clear_error(self): 
        self._error_count = 0

    def daily_report(self, agent_kf): 
        with WhisperDB() as db:
            # 检查是否已经存在相同的 company 和 date
            check_query = """
                SELECT COUNT(*) FROM `openai_daily_report` 
                WHERE `company` = %s AND `date` = CURDATE() - INTERVAL 1 DAY
            """
            count = db.query(check_query, (agent_kf.get_company_name(),))
            
            # 如果记录不存在，则插入新记录
            if count[0][0] == 1:
                logger.info(f"{agent_kf.get_company_name()}的日报已经存在，不再重复生成。")
                return

        # 设置OpenAI客户端
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_version="2024-05-01-preview",
        )


        my_updated_assistant = client.beta.assistants.update(
            self.assistant_id,
            tool_resources={
                "file_search":{
                    "vector_store_ids": [agent_kf.get_vector_id()]
                }
            }
        )
        logger.info(my_updated_assistant)
        my_thread = client.beta.threads.create()

        result1 = self.get_yesterday_chat_list_for_company(agent_kf)
        result2 = self.get_yesterday_chat_summary_for_company(agent_kf)
        result = {
            "chat_summary":result2,
            "chat_list":result1
        }
        # 如果查询结果存在
        if result:
            # 导出为 JSON 文件
            output_path = r"D:\WhisperAgent\信息收集\openai_chat_history.json"  # 替换为你想保存的路径
            with open(output_path, 'w', encoding='utf-8') as json_file:
                json.dump(result, json_file, ensure_ascii=False, indent=4)

            logger.info(f"数据已成功导出到 {output_path}")
        else:
            logger.info("没有查询到数据")
            return

        if os.getenv('TEST_ENV') == 'true':  #测试环境下无往下执行了。
            return

        file = client.files.create(
            file=open(output_path, "rb"),
            purpose="assistants"
        )
        #logger.info("文件：", file)
        thread_message = client.beta.threads.messages.create(
            my_thread.id,
            role="user",
            content=[
                {
                    "type": "text",
                    "text": """这个文件是昨日的聊天记录，请根据聊天记录生成一份客服分析日报，日报中包含如下信息：
                            1、数据信息：包括总接待的客户人数，其中，售后几人、售前几人。
                            2、客户最关心的问题：不超过3个。
                            3、客户最不满意的服务：（不超过3个）
                            4、在客服知识库中希望增加和修改的信息。（不超过三点）
                            注意：如果附件中文件为空或者没有文件，则不用生成日报。
                            报告内容以HTML代码的形式输出，除了html外，不用描述任何其他内容。
                        """,
                }
            ],
            attachments=[
                {
                    "file_id":file.id,
                    "tools":[
                        {"type":"code_interpreter"},
                        {"type":"file_search"}
                    ]
                }
            ]
        )
        logger.info(thread_message)

        run = client.beta.threads.runs.create_and_poll(
            thread_id=my_thread.id,
            assistant_id=self.assistant_id
        )

        if run.status == 'completed': 
            messages = client.beta.threads.messages.list(
                thread_id=my_thread.id,
                limit=1
            )
            logger.info(f"获取消息: {messages}")
            
            try:
                extracted_contents = []
                for message in messages.data:
                    # 确保 message.content 不是空的，并正确处理每个 TextContentBlock
                    if message.content:
                        for content in message.content:
                            # 确保 content 是 TextContentBlock 类型
                            if content.type == "text" and content.text:
                                extracted_contents.append(content.text.value)
                            else:
                                logger.warning(f"警告: 未找到有效的文本内容: {content}")
                    else:
                        logger.warning("没有消息内容")

                logger.info(f"开始写入数据库！{json.dumps(extracted_contents[0], ensure_ascii=False)}")
                with WhisperDB() as db:
                    query = """
                        INSERT INTO 
                            `openai_daily_report`
                            (`company`, `date`, `html`, `annotations`) VALUES 
                            (%s, CURDATE() - INTERVAL 1 DAY, %s, %s)
                    """
                    result = db.query(query, (agent_kf.get_company_name(), json.dumps(extracted_contents[0], ensure_ascii=False), "", ))
                    db.commit()
            except Exception as e:
                logger.error(f"写入数据库时出错: {e}")

        else:
            logger.error(f"Run 失败: {run}")
            return  # 任务未完成时返回 None

        WhisperTools_Qywx.send_to_kf_robot(agent_kf, f"昨日客服日报已经生成，共接待{result2['总店铺数量']}个店铺，{result2['总客户数量']}人，对话{result2['总对话数量']}次。请注意查收！")    

    def get_yesterday_chat_list_for_company(self, agent_kf):
        with WhisperDB() as db:
            query = """
                SELECT `chat_time`, `chat_name`, `sender`, `act`, `content`
                FROM openai_chat_list
                JOIN `openai_kf_manage` ON `openai_chat_list`.`shop_name` = `openai_kf_manage`.`shop_name`
                WHERE `company` = %s AND (`act` = 'ask' OR `act` = 'reply')
                AND DATE(chat_time) = CURDATE() - INTERVAL 1 DAY;
            """
            result = db.query(query, (agent_kf.get_company_name(),))

        if result:
            result_dict = defaultdict(list)  # 以 chat_name 为 key，值是列表

            for row in result:
                result_dict["会话:" + row[1]].append({
                    "chat_time": row[0].isoformat(),
                    "sender": "客服" if row[2] == "chatGPT" else row[2],
                    "act": row[3],
                    "content": row[4],
                })

            return dict(result_dict)  # 转换回普通字典返回
        return {}  # 返回空字典，而不是 None

    def get_yesterday_chat_summary_for_company(self, agent_kf):
        with WhisperDB() as db:
            query = """
                SELECT  COUNT(DISTINCT `chat_name`) as customer_count, COUNT(`chat_name`) as chat_count, COUNT(DISTINCT(SUBSTRING_INDEX(`openai_chat_list`.shop_name, ":", 1))) as shop_count
                FROM `openai_chat_list`
                JOIN `openai_kf_manage` ON `openai_chat_list`.`shop_name` = `openai_kf_manage`.`shop_name`
                WHERE `company` = %s AND (`act` = 'ask' OR `act` = 'reply')
                AND DATE(chat_time) = CURDATE() - INTERVAL 1 DAY;
            """
            result = db.query(query, (agent_kf.get_company_name(),))

        if result:
            return {
                "总客户数量":result[0][0],
                "总对话数量":result[0][1],
                "总店铺数量":result[0][2]
            }
        return {}  # 返回空字典，而不是 None


"""
                        #annotations = content.text.annotations  # 提取引用信息                        
                        # 解析引用信息
                        #citations = []
                        #for annotation in annotations:
                        #    if hasattr(annotation, "file_citation"):  # 过滤文件引用
                        #        file_id = annotation.file_citation.file_id
                        #        ref_text = annotation.text  # 显示的引用文本
                        #        citations.append(f"{ref_text} -> 文件ID: {file_id}")
                        
                        # 组合文本和引用
                        formatted_text = text_value
                        #if citations:
                        #    formatted_text += "\n\n🔍 **引用信息:**\n" + "\n".join(citations)
                        
                        extracted_contents.append(formatted_text)
                        #extracted_annotations.append(annotations)

"""