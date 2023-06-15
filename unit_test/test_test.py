import pytest
from manage import app
from app.config import redis_store

# post_headers = {'Content-Type': 'application/json'}

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_0(client):
    r = client.get('/code')
    print(redis_store.get("code"))
    assert r.json.get("image") == "https://7f1192d863.imdo.co/static/code.jpg"


@pytest.mark.parametrize('data, message', [
    ({"username": "asdasd", "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8", "code": "1"}, "登录成功"),
    ({"username": "", "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8","code": "1"}, "用户名不存在"),
    ({"username": "asdasd", "password": "", "code": "1"}, "密码错误"),
    ({"username": "asdasd", "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8", "code": ""}, "验证码错误")
])
def test_1(client, data, message):
    if data["code"] != "":
        data.update(code=redis_store.get("code"))
    r = client.post('/login', json=data, content_type='application/json')
    print(r)
    assert r.json.get("message") == message

#
# class Test_login:
#     def test_code(self):
#         r = requests.get(url + "/code")
#         assert r.json()["image"] == "https://7f1192d863.imdo.co/static/code.jpg"
#
#     def test_login(self):
#         login_params = {
#             "username": "asdasd",
#             "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8",
#             "code": str(redis_store.get("code"))
#         }
#         r = requests.post(url + "/login", data=json.dumps(login_params), headers=post_headers)
#         assert r.json()["code"] == 200
#         assert r.json()["message"] == "登录成功"
#
#     def test_login1(self):
#         login_params = {
#             "username": "",
#             "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8",
#             "code": str(redis_store.get("code"))
#         }
#         r = requests.post(url + "/login", data=json.dumps(login_params), headers=post_headers)
#         assert r.json()["code"] == 400
#         assert r.json()["message"] == "用户名不存在"
#
#     def test_login2(self):
#         login_params = {
#             "username": "asdasd",
#             "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8",
#             "code": ""
#         }
#         r = requests.post(url + "/login", data=json.dumps(login_params), headers=post_headers)
#         assert r.json()["code"] == 400
#         assert r.json()["message"] == "验证码错误"
#
#     def test_login3(self):
#         login_params = {
#             "username": "asdasd",
#             "password": "",
#             "code": str(redis_store.get("code"))
#         }
#         r = requests.post(url + "/login", data=json.dumps(login_params), headers=post_headers)
#         assert r.json()["code"] == 400
#         assert r.json()["message"] == "密码错误"
#
#     def test_register(self):
#         register_params = {
#             "username": "asdasd",
#             "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8"
#         }
#         r = requests.post(url + "/register", data=json.dumps(register_params), headers=post_headers)
#         assert r.json()["code"] == 400
#         assert r.json()["message"] == "用户名已存在"
#
#     def test_register1(self):
#         register_params = {
#             "username": "asdasdd",
#             "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8"
#         }
#         r = requests.post(url + "/register", data=json.dumps(register_params), headers=post_headers)
#         assert r.json()["code"] == 200
#         assert r.json()["message"] == "注册成功"
