import pytest
from manage import app, db
from app.config import redis_store

headers = {
    'Authorization': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhc2Rhc2QiLCJ1aWQiOjEsImFjY2VzcyI6ImFkbWluIn0.2JvH_dyg1_3dFjfz4vUpWMl-vpImrgH9yxXSPciidi4"}
headers1 = {
    'Authorization': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhc2QiLCJ1aWQiOjIsImFjY2VzcyI6InVzZXIifQ.APSqznKibp-818jK1at7nIeOyF6KmHPF5Df8Pt0pQgQ"}


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_hello(client):
    r = client.get('/')
    assert r.get_data(as_text=True) == "hello"


def test_home(client):
    r = client.get('/home')
    assert r.json.get("message") == "success"


@pytest.mark.parametrize('data, message', [
    (
            {"title": "xxx", "description": "xxx", "game": "原神！",
             "resources": "xxx", "price": "1.14514"},
            "提交成功，请等待审核"
    ),
    (
            {"title": "", "description": "xxx", "game": "原神！",
             "resources": "xxx", "price": "1.14514"},
            "请补充完整商品信息"
    ),
    (
            {"title": "xxx", "description": "xxx", "game": "原神！",
             "resources": "xxx", "price": "xxx"},
            "价格应为数字"
    )
])
def test_neworder(client, data, message):
    with open('D:/Users/asus/Desktop/youxi/static/code.jpg', 'rb') as f:
        data["picture"] = (f, 'code.jpg')
        r = client.post('/neworder', data=data, content_type='multipart/form-data', headers=headers)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    (
            {"order_id": 6, "title": "", "description": "",
             "game": "", "resources": "zzz", "price": ""},
            "商品信息修改成功，请重新等待审核"
    ),
    (
            {"order_id": 6, "title": "", "description": "",
             "game": "", "resources": "zzz", "price": ""},
            "用户无权限"
    ),
    (
            {"order_id": 6, "title": "", "description": "",
             "game": "", "resources": "", "price": "zzz"},
            "价格应为数字"
    )
])
def test_order_updating(client, data, message):
    with open('D:/Users/asus/Desktop/youxi/static/code.jpg', 'rb') as f:
        data["picture"] = (f, 'code.jpg')
        if message == "用户无权限":
            r = client.put('/order/updating', data=data, content_type='multipart/form-data', headers=headers1)
        else:
            r = client.put('/order/updating', data=data, content_type='multipart/form-data', headers=headers)
    assert r.json.get("message") == message


def test_order_view(client):
    data = {"page": 1}
    r = client.get('/order/view', query_string=data)
    assert r.json.get("message") == "success"


@pytest.mark.parametrize('page, message', [
    (1, "操作无权限"),
    (2, "success")
])
def test_order_view_verifying(client, page, message):
    query_string = {"page": page}
    if message == "操作无权限":
        r = client.get('/order/view/verifying', query_string=query_string, headers=headers1)
    else:
        r = client.get('/order/view/verifying', query_string=query_string, headers=headers)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    (
            {"verifying": "True", "order_id": 6}, "success"
    ),
    (
            {"verifying": "False", "order_id": 6}, "操作无权限"
    )
])
def test_order_verifying(client, data, message):
    if message == "success":
        r = client.put('/order/verifying', json=data, content_type='application/json', headers=headers)
    else:
        r = client.put('/order/verifying', json=data, content_type='application/json', headers=headers1)
    assert r.json.get("message") == message


def test_order_searching(client):
    query_string = {"keyword": "原神！", "page": 1}
    r = client.get('/order/searching', query_string=query_string)
    assert r.json.get("message") == "success"


@pytest.mark.parametrize('data, message', [
    (
            {"order_id": 2}, "success"
    ),
    (
            {"order_id": "xxx"}, "参数错误"
    )
])
def test_order_information(client, data, message):
    r = client.get('/order/information', query_string=data)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    (
            {"order_id": 7, "price": 100, "message": "太贵了！！！"}, "出价成功"
    ),
    (
            {"order_id": 7, "price": "xxx", "message": "太贵了！！！"}, "价格应为数字"
    ),
    (
            {"order_id": 7, "price": None, "message": "太贵了！！！"}, "请填写出价"
    ),
    (
            {"order_id": 6, "price": 200, "message": "太贵了！！！"}, "不能给自己的商品出价哦"
    )
])
def test_order_bidding(client, data, message):
    r = client.post('/order/bidding', json=data, content_type='application/json', headers=headers)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data', [
    (
            {"order_id": 2, "page": 1}
    )
])
def test_bid_searching(client, data):
    query_string = {"order_id": 2, "page": 1}
    r = client.get('/bid/searching', query_string=query_string)
    assert r.json.get("message") == "success"


@pytest.mark.parametrize('data, message', [
    (
            {"order_id": 8}, "支付成功"
    ),
    (
            {"order_id": 7}, "账户余额不足"
    ),
    (
            {"order_id": 6}, "不能购买自己的商品哦"
    )
])
def test_order_paying(client, data, message):
    r = client.put('/order/paying', json=data, headers=headers)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    (
            {"order_id": 8, "confirming": "False"}, "success"
    ),
    (
            {"order_id": 8, "confirming": "True"}, "success"
    ),
    (
            {"order_id": 7, "confirming": "False"}, "用户无权限"
    )
])
def test_order_confirming(client, data, message):
    r = client.put('/order/confirming', json=data, headers=headers)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    (
            {"order_id": 8, "delivering": "True"}, "success"
    ),
    (
            {"order_id": 8, "delivering": "False"}, "success"
    ),
    (
            {"order_id": 6, "delivering": "False"}, "用户无权限"
    )
])
def test_order_delivering(client, data, message):
    r = client.put('/order/delivering', json=data, headers=headers1)
    assert r.json.get("message") == message


