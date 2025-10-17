
from whisper_ai_zxs.agent_servicer_TestStub import Agent_TestStub
import pytest

agent = Agent_TestStub("植想说小红书店:亮亮")

def test_run1():
    assert agent.get_company_name() == "whisper"
    assert agent.get_kf_name() == "植想说小红书店:亮亮"
    assert agent.is_master() == False

