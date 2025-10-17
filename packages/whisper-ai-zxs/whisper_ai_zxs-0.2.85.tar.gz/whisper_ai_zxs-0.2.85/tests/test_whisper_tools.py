from whisper_ai_zxs.whisper_tools import WhisperTools_QYWX


def test_get_group_info():
    qywx = WhisperTools_QYWX()
    group_name = qywx._get_group_name("wru252DAAAqRwvzxPdi0AbiIghCxGEHQ")
    print("group_name:", group_name)
    user_name = qywx._get_user_name("wmu252DAAAW5_g9R2KERY55kzyifRaOQ")
    print("user_name:", user_name)
    user_name = qywx._get_user_name("zhizhushou")
    print("user_name:", user_name)
    group_name = qywx._get_group_name("wmu252DAAAW5_g9R2KERY55kzyifRaOQ")
    print("group_name:", group_name)
    group_name = qywx._get_group_name("wru252DAAA7hHieFuCbX8KuiKYlddPXw")
    print("group_name:", group_name)
    group_name = qywx._get_group_name("wru252DAAA7FJV4O3baZDp0ndETmWJow")
    print("group_name:", group_name)
    group_name = qywx._get_group_name("wru252DAAAlv7973vdMX2-KKe8ikGLUQ")
    print("group_name:", group_name)
    group_name = qywx._get_group_name("wru252DAAAr9wNvHbjHRhKuEVrYE90iQ")
    print("group_name:", group_name)

    
 

def test_whisper_tools_QYWX():
    qywx = WhisperTools_QYWX()
    reply = qywx.get_reply_msg()
    print("reply:", reply)
    assert reply is not None

    qywx.set_reply_sended("1")

def test_get_reply_msg():
    qywx = WhisperTools_QYWX()
    reply = qywx.get_reply_msg()
    print("reply:", reply)
    assert reply is not None

def test_get_action_msg():
    qywx = WhisperTools_QYWX()
    reply = qywx.get_action_msg()
    print("reply:", reply)
    assert reply is not None

def test_add_reply_sended():
    qywx = WhisperTools_QYWX()
    qywx.add_reply_msg("测试群不存在的群", "text", "Test reply message！", "reply")