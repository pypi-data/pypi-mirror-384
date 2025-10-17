from .agent_servicer import AgentServicer
import logging
logger = logging.getLogger("whisper_ai")

class Agent_YD(AgentServicer):
    def call(self, name, *args, **kwargs):
        """
        调用注册的函数
        :param name: 需要调用的函数名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 返回调用结果
        """
        if name not in self._functions:
            #raise KeyError(f"RPA流程 '{name}' 未注册")
            return "未注册"

        # 将 args 转换为字典
        arg_dict = {str(i): v for i, v in enumerate(args)}
        arg_dict.update(kwargs)  # 合并 kwargs
        p_arg = {
            "arg" : arg_dict,
            "result" : ""
        }
        self._functions[name].main(p_arg)
        #result = json.dumps(p_arg["result"])
        return p_arg["result"]
        #return self._functions[name](*args, **kwargs)
        #return run_module({ "module_path": self._functions[name] }, "main", SZEnv['rpa'], *args, **kwargs) 