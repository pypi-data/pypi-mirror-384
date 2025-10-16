from whisper_ai_zxs.wx_lib.wx_auth_client import WXAuthClient
from whisper_ai_zxs.wx_lib.wx_store_client import WXStoreClient

def test_get_access_token():
    client = WXAuthClient(appid="wx99c7fd9e318b8575", secret="39de4d2977a6caf6763433bfd2a3b3b2")
    access_token = client.get_access_token()
    assert isinstance(access_token, str) and len(access_token) > 0, "Access token should be a non-empty string"
    print(f"Access Token: {access_token}")

def test_get_order_info():
    client = WXStoreClient()
    order_id = "3724048244855933952"  # 替换为实际的订单ID
    try:
        order_info = client.getOrderInfo(order_id)
        assert isinstance(order_info, dict), "Order info should be a dictionary"
        print(f"Order Info: {order_info}")
    except Exception as e:
        print(f"Failed to get order info: {e}")

def test_add_order_note():
    client = WXStoreClient()
    order_id = "3724048244855933952"  # 替换为实际的订单ID
    note = "测试备注信息"
    try:
        result = client.addOrderNote(order_id, note)
        assert isinstance(result, dict), "Result should be a boolean indicating success"
        print(f"Modify Order Note Result: {result}")
    except Exception as e:
        print(f"Failed to modify order note: {e}")

def test_collectSellingProduct():
    client = WXStoreClient()
    try:
        client.collectSellingProduct("植想说视频号小店")
        print("Collect Selling Product succeeded")
    except Exception as e:
        print(f"Failed to collect selling product: {e}")