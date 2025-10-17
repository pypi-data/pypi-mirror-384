
from whisper_ai_zxs.agent_trainer import AgentTrainer
from whisper_ai_zxs.agent_servicer_TestStub import Agent_TestStub
import pytest

agent = Agent_TestStub("植想说小红书店:亮亮")
tools1 = AgentTrainer()
# 测试函数，接收输入参数和预期结果
@pytest.mark.parametrize(
    "input_data, expected_result",
    [
        ([agent], True),      # 测试用例 1
        ([agent], True),     # 测试用例 2
#        ([agent], True),     # 测试用例 3
        ([agent], False)      # 测试用例 4
    ]
)

def test_run1(input_data, expected_result):
    assert tools1.run(input_data) == expected_result

def test_clear_run():
    tools1.clear_run()

# 测试函数，接收输入参数和预期结果
@pytest.mark.parametrize(
    "input_data, expected_result",
    [
        ([agent], True),      # 测试用例 1
        ([agent], True),     # 测试用例 2
#        ([agent], True),     # 测试用例 3
        ([agent], False)      # 测试用例 4
    ]
)
def test_run2(input_data, expected_result):
    assert tools1.run(input_data) == expected_result

def test_daily_report():
    #tools1.daily_report(agent)
    pass
