from whisper_ai_zxs.whisper_function import get_recent_activities
from whisper_ai_zxs.agent_servicer_TestStub import Agent_TestStub

def test_get_recent_activities():
    activities = get_recent_activities()
    arguments = "{}"
    agent = Agent_TestStub("植想说小红书店:亮亮")
    result = activities.call("testuser", arguments, agent)
    print("Recent Activities:", result)