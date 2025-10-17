from whisper_ai_zxs.red_lib.red_auth_client import RedAuthClient
from whisper_ai_zxs.red_lib.red_store_client import RedStoreClient

def test_get_access_token():
    client = RedAuthClient(app_id="4b8ab3245c704723a6d1", secret="febb545d489bea34eae32879a88e1a55")
    access_token = client.get_access_token()
    assert isinstance(access_token, str) and len(access_token) > 0, "Access token should be a non-empty string"
    print(f"Access Token: {access_token}")

def test_get_order_info():
    client = RedStoreClient()
    order_id = "P757408722906106471"  # 替换为实际的订单ID
    try:
        order_info = client.getOrderInfo(order_id)
        assert isinstance(order_info, dict), "Order info should be a dictionary"
        print(f"Order Info: {order_info}")
    except Exception as e:
        print(f"Failed to get order info: {e}")

def test_add_order_note():
    client = RedStoreClient()
    order_id = "P757408722906106471"  # 替换为实际的订单ID
    note = "测试备注信息"
    try:
        result = client.addOrderNote(order_id, note)
        assert isinstance(result, dict), "Result should be a boolean indicating success"
        print(f"Modify Order Note Result: {result}")
    except Exception as e:
        print(f"Failed to modify order note: {e}")

def test_CollectSellingProduct():
    client = RedStoreClient("植想说小红书店")
    try:
        client.CollectSellingProduct()
    except Exception as e:
        print(f"Failed to collect selling products: {e}")
