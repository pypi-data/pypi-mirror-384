from whisper_ai_zxs.whisper_handler import EventHandler
from whisper_ai_zxs.agent_servicer_TestStub import Agent_TestStub

class DeltaObject:
    def __init__(self, value):
        self.value = value

def test_whisper_handler():
    agent = Agent_TestStub("植想说天猫店:亮亮")
    pro_event_handler = EventHandler(agent)
    pro_event_handler.on_text_created("test")
    delta = DeltaObject("这是一个测试。")
    pro_event_handler.on_text_delta(delta, 1)
    delta = DeltaObject("好的。")
    pro_event_handler.on_text_delta(delta, 1)
    delta = DeltaObject("这是一个测试。")
    pro_event_handler.on_text_delta(delta, 1)
    delta = DeltaObject("这是一个测试。")
    pro_event_handler.on_text_delta(delta, 1)
    pro_event_handler.on_text_done("test")
