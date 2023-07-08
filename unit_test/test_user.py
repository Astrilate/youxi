import random

import pytest
from sqlalchemy import and_

from app.model import reports
from manage import app, db
from app.config import redis_store

headers = {'Authorization': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhc2Rhc2QiLCJ1aWQiOjEsImFjY2VzcyI6ImFkbWluIn0.2JvH_dyg1_3dFjfz4vUpWMl-vpImrgH9yxXSPciidi4"}
headers1 = {'Authorization': "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhc2QiLCJ1aWQiOjIsImFjY2VzcyI6InVzZXIifQ.APSqznKibp-818jK1at7nIeOyF6KmHPF5Df8Pt0pQgQ"}


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_code(client):
    r = client.get('/code')
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
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    ({"username": str(random.randint(1, 100000000)), "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8"}, "注册成功"),
    ({"username": "asdasd", "password": "5fd924625f6ab16a19cc9807c7c506ae1813490e4ba675f843d5a10e0baacdb8"}, "用户名已存在")
])
def test_register(client, data, message):
    r = client.post('/register', json=data, content_type='application/json')
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    ({"token": None}, "token无权限"),
    ({"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhc2Rhc2QiLCJ1aWQiOjEsImFjY2VzcyI6ImFkbWluIiwiZXhwIjoxNjgwMzY4OTgwfQ.ynp_FXaOskEdf15X8374V7FZsjqL0A77dDfNtbg59To"}, "token已过期"),
    ({"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhc2Rhc2QiLCJ1aWQiOjEsImFjY2VzcyI6ImFkbWluIn0.2JvH_dyg1_3dFjfz4vUpWMl-vpImrgH9yxXSPciidi4"}, "success")
])
def test_temp(client, data, message):
    token = data.get("token")
    header = {'Authorization': token}
    r = client.post('/temp/login', headers=header, content_type='application/json')
    assert r.json.get("message") == message


def test_info(client):
    r = client.get('/information', content_type='application/json', headers=headers)
    assert r.json.get("message") == "查询成功"


@pytest.mark.parametrize('data, message', [
    ({"uid": 1, "email": "1348330522@qq.com"}, "发送成功"),
    ({"uid": 1, "email": "xxxxxxxxxx"}, "邮箱格式有误")
])
def test_email_code(client, data, message):
    r = client.post('/email', json=data, content_type='application/json', headers=headers)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    ({"name": "lihua", "real_name": "xiaoming", "email": "1348330522@qq.com", "ecode": ""}, "个人信息修改成功"),
    ({"name": "lihua", "real_name": "xiaoming", "email": "xxxxxxxxx", "ecode": ""}, "未输入邮箱验证码"),
    ({"name": "lihua", "real_name": "xiaoming", "email": "xxxxxxxx", "ecode": "xxxxxx"}, "邮箱地址或验证码有误")
])
def test_updating_inform(client, data, message):
    if message == "个人信息修改成功":
        data.update({"ecode": str(redis_store.get("ecode"))})
    r = client.put('/information/updating', data=data, content_type='multipart/form-data', headers=headers)
    assert r.json.get("message") == message


def test_user_information(client):
    data = {"id": 1}
    r = client.get('/user/information', query_string=data)
    assert r.json.get("message") == "success"


@pytest.mark.parametrize('data, message', [
    ({"money": 100, "operation": "in"}, "success"),
    ({"money": 50, "operation": "out"}, "success")
])
def test_money_recharge_and_withdraw(client, data, message):
    r = client.put('/money', json=data, content_type='application/json', headers=headers)
    assert r.json.get("message") == message


def test_money_view(client):
    r = client.get('/money', content_type='application/json', headers=headers)
    assert r.json.get("message") == "success"


@pytest.mark.parametrize('data,  message', [
    ({"suspected_id": 3, "message": "举报信息"}, "您已举报过该用户"),
    ({"suspected_id": 1, "message": "举报信息"}, "success")
])
def test_reporting(client, data, message):
    r = client.post('/reporting', json=data, content_type='application/json', headers=headers)
    if message == "success":
        report_filter = {
            and_(
                reports.user_id == 1,
                reports.suspected_id == 1
            )
        }
        reports.query.filter(*report_filter).delete()
    db.session.commit()
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    ({"page": 1}, "success"),
    ({"page": 1}, "操作无权限")
])
def test_report_view_verifying(client, data, message):
    if message == "success":
        r = client.get('/report/view/verifying', query_string=data, headers=headers)
    else:
        r = client.get('/report/view/verifying', query_string=data, headers=headers1)
    assert r.json.get("message") == message


@pytest.mark.parametrize('data, message', [
    ({"report_id": 1, "verifying": "True"}, "success"),
    ({"report_id": 1, "verifying": "False"}, "success"),
    ({"report_id": 1, "verifying": "True"}, "操作无权限"),
])
def test_report_verifying(client, data, message):
    if message == "操作无权限":
        r = client.put('/report/verifying', json=data, content_type='application/json', headers=headers1)
    else:
        r = client.put('/report/verifying', json=data, content_type='application/json', headers=headers)
    assert r.json.get("message") == message
