import time
from .agent_trainer import AgentTrainer
from datetime import datetime
from .whisper_tools import WhisperTools_Qywx
import logging
import traceback
logger = logging.getLogger("whisper_ai")

class WhisperAI:
    def __init__(self, server_name="未配置"):
        """ 初始化一个空字典用于存储函数 """
        self._agent_kf = []
        self._agent_trainer = AgentTrainer()
        self._server_name = server_name

    def add_agent(self, reg):
        """ 初始化一个空字典用于存储函数 """
        self._agent_kf.append(reg)

    def run(self):
        logger.info("AI客服系统启动！")
        #初始化
        for agent in self._agent_kf:
            agent.register_all_function()
            agent.call("stop", agent.get_kf_name())
            agent.set_kf_status(0)
            time.sleep(3)

        count = 0
        while True:
            if (count % 10 == 0):
                for agent in self._agent_kf:
                    self.auto_start(agent)
            for agent in self._agent_kf:
                try:
                    if (agent.get_kf_status_now() == 1):
                        agent.call("activate", agent.get_kf_name())
                        agent.listening_user()
                        agent.listening_manage()
                        agent.heart_bit()
                        agent.clear_error()
                except Exception as e:
                    logger.error(f"{agent.get_kf_name()}循环出现异常: {type(e).__name__}: {e}")
                    logger.error("异常堆栈信息:\n" + traceback.format_exc())
                    agent.on_error(e)
                
                time.sleep(1)
            count = count + 1
            if (count >= 10000):
                count = 0

            if (count % 30 == 0):
                #判断时间，如果是凌晨3~4点开始，处理教练相关事项：
                if (datetime.now().hour >= 3 and datetime.now().hour <= 4):
                    try:
                        result = self._agent_trainer.run(self._agent_kf)
                        #当教练程序成功执行时，才清除错误记录
                        if (result):
                            self._agent_trainer.clear_error()
                    except Exception as e:
                        logger.error(f"AI教练出现异常，错误类型: {type(e).__name__}")
                        logger.error(f"AI教练出现异常，错误信息: {e}")
                        logger.error(f"AI教练出现异常，异常发生在: {e.__traceback__.tb_lineno} 行")
                        self._agent_trainer.on_error(e)
                #判断时间，如果是凌晨5~6点开始，初始化教练任务：
                if (datetime.now().hour >= 5 and datetime.now().hour <= 6):
                    self._agent_trainer.clear_run()

    def auto_start(self, agent): 
        """
        启动AI，依据 kfStatus 调用 start 或 stop
        """
        kfStatus = agent.get_kf_status()
        # print(f"Auto Start {agent.get_kf_name()}-Status:{kfStatus}")
        if kfStatus:
            try:
                # 如果获取到状态信息，进行处理
                if kfStatus["manage_status"] == 0:
                    result = agent.call("activate", agent.get_kf_name())
                    # print ("activate result", result)
                    if (result == True) :
                        agent.call("stop", agent.get_kf_name())
                    agent.set_kf_status(0)
                    agent.clear_error()
                elif (kfStatus["status_now"] == 0 and kfStatus["error_count"]<=3):
                    agent.call("start", agent.get_kf_name())
                    agent.set_kf_status(1)
            except Exception as e:
                logger.error(f"{agent.get_kf_name()}自动启停出现异常{e}！")
                agent.on_error(e)
        else:
            # 如果没有找到对应的 kfStatus，可以记录错误或执行默认行为
            logger.error(f"Error: kfStatus for {agent.get_kf_name()} not found")
        