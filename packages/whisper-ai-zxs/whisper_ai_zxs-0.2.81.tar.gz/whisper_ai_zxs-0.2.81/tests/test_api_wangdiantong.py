from whisper_ai_zxs.api_wangdiantong import APIWangDianTong

def test_create_trade():
    client = APIWangDianTong()
    result = client.create_trade("tests/data/旺店通导单(RPA)_new.xlsx")
    #assert isinstance(result, dict), "Result should be a dictionary"
    print(f"Create Trade Result: {result}")

def test_get_shops():
    client = APIWangDianTong()
    shops = client.get_shops()
    assert isinstance(shops, list), "Shops should be a list"
    print(f"Shops: {shops}")