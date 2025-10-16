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

def test_get_stock_list():
    client = APIWangDianTong()
    warehouses = client.get_stock_list()
    assert isinstance(warehouses, list), "Warehouses should be a list"
    print(f"Warehouses: {warehouses}")

def test_create_stock_check():
    client = APIWangDianTong()
    result = client.create_stock_check("tests/data/仓库数据/库存详细信息（渠道-京东-奇门-广州常温）.xlsx")
    #assert isinstance(result, dict), "Result should be a dictionary"
    print(f"Create Stock Check Result: {result}")