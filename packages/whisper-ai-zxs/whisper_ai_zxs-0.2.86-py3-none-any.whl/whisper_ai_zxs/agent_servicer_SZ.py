from .agent_servicer import AgentServicer
from projects.rpaRoot import SZEnv
from ..global_data import run_module
class FunctionRegistry_ShiZai(AgentServicer):
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
        #return self._functions[name](*args, **kwargs)
        return run_module({ "module_path": self._functions[name] }, "main", SZEnv['rpa'], *args, **kwargs) 


