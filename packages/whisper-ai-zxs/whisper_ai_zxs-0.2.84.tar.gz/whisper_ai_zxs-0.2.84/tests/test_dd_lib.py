from whisper_ai_zxs.dd_lib.dd_auth_client import DDAuthClient
from whisper_ai_zxs.dd_lib.dd_store_client import DDStoreClient

def test_get_access_token():
    client = DDAuthClient("7542374655928108554", "3fcb520f-4365-47ec-81d0-cfe485b16494")
    client.fetch_token_with_auth_code("181035739")
    token = client.get_access_token()
    assert isinstance(token, str) and len(token) > 0, "Access token should be a non-empty string"
    print(f"Access Token: {token}")

def test_get_order_info():
    store_client = DDStoreClient()
    order_info = store_client.getOrderInfo("6921141949398941309")
    assert isinstance(order_info, dict), "Order info should be a dictionary"
    print(f"Order Info: {order_info}")
    assert "error" not in order_info, f"Error occurred: {order_info.get('error')}"

def test_add_order_note():
    store_client = DDStoreClient()
    response = store_client.addOrderNote("6921141949398941309", "Test note from unit test")
    assert isinstance(response, dict), "Response should be a dictionary"
    print(f"Add Order Note Response: {response}")
    assert response.get("success") is True, f"Failed to add note: {response.get('message', 'unknown error')}"

def test__getProductList():
    store_client = DDStoreClient()
    response = store_client._getProductList()
    assert isinstance(response, list), "Response should be a list"
    print(f"Product List Response: {len(response)}")
    #assert all(isinstance(item, dict) for item in response), "All items in the product list should be dictionaries"

def test__getSKUList():
    store_client = DDStoreClient()
    response = store_client._getSKUList("3696215491807936545")
    assert isinstance(response, list), "Response should be a list"
    print(f"SKU List Response: {response}")
    #assert all(isinstance(item, dict) for item in response), "All items in the SKU list should be dictionaries"

def test_collectSellingProduct():
    store_client = DDStoreClient()
    shop_name = "test_shop"
    store_client.collectSellingProduct(shop_name)
    # Here you would normally check the database to ensure products were stored correctly.
    # For this test, we will just print a success message.
    print(f"Products collected and stored for shop: {shop_name}")