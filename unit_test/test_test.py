import pytest
import json
import requests

from app.config import redis_store


# def setup_module():
#     print('\n *** 初始化-模块 ***')
#
#
# def teardown_module():
#     print('\n ***   清除-模块 ***')


url = "http://127.0.0.1:5000"


class Test_1:
    @pytest.mark.login
    def test_code(self):
        r = requests.get(url + "/code")
        assert r.json()["image"] == "https://7f1192d863.imdo.co/static/code.jpg"

    @pytest.mark.login
    def test_login(self):
        query_params = {
            "username": "asdasd",
            "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8",
            "code": redis_store.get("code")
        }
        post_headers = {'Content-Type': 'application/json'}
        r = requests.post(url + "/login", data=json.dumps(query_params), headers=post_headers)
        assert r.status_code == 200
        assert r.json()["message"] == "登录成功"

