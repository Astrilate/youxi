import os
import re
import time
import random

import jwt
from flask import jsonify, request
from flask_cors import CORS
from sqlalchemy import and_
from alipay import AliPay

from app import db, app
from app.config import redis_store
from app.main import user
from app.main.utils import token, SECRET_KEY, ALGORITHM, e_mail, jpg

from app.model import users, reports, messages, orders

CORS(user, supports_credentials=True)


@user.route('/register', methods=['POST', 'OPTIONS'])
# {
#     "username": "asdasd",
#     "password": "asdasd"
# }
# 用户注册接口
def register():
    get_json = request.get_json()
    app.logger.info("/register   " + get_json.get('username') + "--" + get_json.get('password'))
    ch = users.query.filter(users.username == get_json.get('username')).first()
    if ch is not None:
        app.logger.error("/register   " + "用户名已存在")
        return jsonify(code=400, message="用户名已存在")
    else:
        a = users(username=get_json.get('username'),
                  password=get_json.get('password'),
                  name=get_json.get('username'))
        db.session.add(a)
        db.session.commit()
        app.logger.info("/register   " + "注册成功")
        return jsonify(code=200, message="注册成功")


@user.route('/login', methods=['POST', 'OPTIONS'])
# {
#     "username": "asdasd",
#     "password": "asdasd",
#     "code": "abcd"
# }
# 用户登录接口
def login():
    idata = {}
    get_json = request.get_json()
    username = get_json.get("username")
    password = get_json.get('password')
    code = get_json.get("code").lower()
    app.logger.info("/login   " + username + "--" + password + "--" + code + "//" + redis_store.get("code"))
    ch = users.query.filter(users.username == username).first()
    if code == redis_store.get("code"):
        if ch is not None:
            if ch.password != password:
                app.logger.error("/login   " + "密码错误")
                return jsonify(code=400, message="密码错误")
            else:
                search = users.query.filter(users.username == get_json.get('username')).first()
                uid = search.id
                access = search.type
                access_token = token().create_token(username, access, uid)
                idata.update(username=username, id=uid, type=access, token=access_token)
                app.logger.info("/login   " + "登录成功")
                return jsonify(code=200, message="登录成功", data=idata)
        else:
            app.logger.error("/login   " + "用户名不存在")
            return jsonify(code=400, message="用户名不存在")
    else:
        app.logger.error("/login   " + "验证码错误")
        return jsonify(code=400, message="验证码错误")


@user.route('/temp/login', methods=['POST', 'OPTIONS'])
# token登录接口
def temp_login():
    token = request.headers.get("Authorization")
    app.logger.info("/temp/login   " + token)
    try:
        payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
        access = payload.get("access")
        username = payload.get("sub")
        uid = payload.get("uid")
        return jsonify(code=200, data=dict(id=uid, type=access, token=token, username=username), message="success")
    except jwt.DecodeError:
        app.logger.error("/temp/login   " + "token无权限")
        return jsonify(code=401, message="token无权限")
    except jwt.ExpiredSignatureError:
        app.logger.error("/temp/login   " + "token已过期")
        return jsonify(code=401, message="token已过期")


@user.route('/information', methods=['GET', 'OPTIONS'])
@token().check_token("0")
# 用户个人信息查询
def information(x):
    app.logger.info("/information   " + str(x["uid"]))
    all_data = []
    search = users.query.filter(users.id == x["uid"]).first()
    idata = {}
    idata.update(username=search.username, name=search.name,
                 real_name=search.real_name, money=search.money,
                 email=search.email, credit=search.credit,
                 photo=jpg(search.photo))
    all_data.append(idata)
    app.logger.info("/information   " + "查询成功")
    return jsonify(code=200, message="查询成功", data=all_data)


@user.route('/information/updating', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# form-data
# {
#     "photo" (file): xxx,
#     "name" (string): "xxx",
#     "real_name" (string): "xxx",
#     "email" (string): "xxx",
#     "ecode" (string): "xxx"
# }
# 用户个人信息修改
def updating_inform(x):
    uid = x["uid"]
    try:
        photo = request.files['photo']
    except:
        photo = None
    name = request.form['name']
    real_name = request.form['real_name']
    email = request.form['email']
    ecode = request.form['ecode']
    app.logger.info("/information/updating   " + str(uid) + "--" + name + "--" + real_name + "--" + email
                    + "--" + ecode + "//" + redis_store.get("check_email"))
    if bool(photo):
        photo.save(os.path.join('./static/photo/   ', str(uid) + '.jpg'))
        users.query.filter(users.id == uid).update({"photo": '/static/photo/' + str(uid) + '.jpg'})
    if bool(name):
        users.query.filter(users.id == uid).update({"name": name})
    if bool(real_name):
        users.query.filter(users.id == uid).update({"real_name": real_name})
    if bool(email):
        if bool(ecode):
            if str(uid) + email + ecode == redis_store.get("check_email"):
                users.query.filter(users.id == uid).update({"email": email})
            else:
                app.logger.error("/information/updating   " + "邮箱地址或验证码有误")
                return jsonify(code=400, message="邮箱地址或验证码有误")
        else:
            app.logger.error("/information/updating   " + "未输入邮箱验证码")
            return jsonify(code=400, message="未输入邮箱验证码")
    db.session.commit()
    app.logger.info("/information/updating   " + "个人信息修改成功")
    return jsonify(code=200, message="个人信息修改成功")


@user.route('/email', methods=['POST', 'OPTIONS'])
@token().check_token("1")
# {
#     "email": "xxxxxxxxxx@xxx.com"
# }
# 用户邮箱验证码发送
def email_code(x):
    uid = x["uid"]
    email = request.get_json().get('email')
    app.logger.info("/email   "  + email)
    if not re.match(r'^[0-9a-zA-Z_]{0,19}@[0-9a-zA-Z]{1,13}.com', email):
        app.logger.error("/email   " + "邮箱格式有误")
        return jsonify(code=400, message="邮箱格式有误")
    ecode = e_mail().create_code().lower()
    redis_store.set("ecode", ecode, 300)
    redis_store.set("check_email", str(uid) + email + ecode, 300)
    app.logger.info("/email   " + redis_store.get("check_email"))
    try:
        e_mail().send_email(email, ecode)
        app.logger.info("/email   " + "发送成功")
        return jsonify(code=200, message="发送成功")
    except:
        app.logger.error("/email   " + "发送失败")
        return jsonify(essage="发送失败")


@user.route('/user/information', methods=['GET', 'OPTIONS'])
# 地址传参/user/information?id=xxx
# 其他用户信息显示
def user_information():
    all_data = []
    idata = {}
    user_id = int(request.args.get("id"))
    app.logger.info("/user/information   " + str(user_id))
    name = users.query.filter(users.id == user_id).first().username
    photo = users.query.filter(users.id == user_id).first().photo
    if bool(photo):
        photo = jpg(photo)
    order = len(orders.query.filter(orders.seller_id == user_id).all())
    idata.update(name=name, orders=order,
                 photo=photo)
    all_data.append(idata)
    app.logger.info("/user/information   " + "success")
    return jsonify(code=200, message="success", data=all_data)


@user.route('/money', methods=['PUT', 'GET', 'OPTIONS'])
@token().check_token("0")
# {
#     "money": xxx,
#     "operation": "in/out"
# }
# 用户余额显示或者充值提现
def money(x):
    uid = x["uid"]
    User = users.query.filter(users.id == uid)
    if request.method == "GET":
        money = User.first().money
        app.logger.info("/money   " + str(uid) + "--" + str(money))
        idata = {}
        idata.update(money=money)
        app.logger.info("/money   " + "success")
        return jsonify(code=200, message="success", data=idata)
    else:
        money = request.get_json().get("money")
        operation = request.get_json().get("operation")
        app.logger.info("/money   " + str(uid) + "--" + str(money) + "--" + operation)
        try:
            float(money)
        except ValueError:
            app.logger.error("/money   " + "金额应为数字")
            return jsonify(code=400, message="金额应为数字")
        if money <= 0:
            app.logger.error("/money   " + "金额应为正数")
            return jsonify(code=400, message="金额应为正数")
        if operation == "in":
            User.update({"money": User.first().money + money})
            private_key = open(os.path.join(os.path.dirname(__file__),
                                            "../../../keys/keys/app_private_key.pem")).read()
            public_key = open(os.path.join(os.path.dirname(__file__),
                                           "../../../keys/keys/alipay_public_key.pem")).read()
            alipay = AliPay(
                appid="9021000122686870",
                app_notify_url=None,
                app_private_key_string=private_key,
                alipay_public_key_string=public_key,
                sign_type="RSA2",
                debug=True,
            )
            random_int = random.randint(1, 1000000000000000)
            order_string = alipay.api_alipay_trade_page_pay(
                out_trade_no=str(random_int),
                total_amount=str(money),
                subject="用户充值",
                return_url="youxi://xxx.com/paysuccess",
                notify_url=None
            )
            pay_url = "https://openapi-sandbox.dl.alipaydev.com/gateway.do?" + order_string
            db.session.commit()
            return jsonify(code=200, message="success", data={"pay_url": pay_url})
        else:
            if User.first().money - money < 0:
                app.logger.error("/money   " + "账户余额不足")
                return jsonify(code=400, message="账户余额不足")
            User.update({"money": User.first().money - money})
            db.session.commit()
            app.logger.info("/money   " + "success")
            return jsonify(code=200, message="success")


@user.route('/reporting', methods=['POST', 'OPTIONS'])
@token().check_token("1")
# {
#     "suspected_id": xxx,
#     "message": xxx
# }
# 用户对用户的举报
def reporting(x):
    uid = x["uid"]
    suspected_id = request.get_json().get("suspected_id")
    message = request.get_json().get("message")
    app.logger.info("/reporting   " + str(uid) + "--" + str(suspected_id) + "--" + message)
    time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    reports_filter = {
        and_(
            reports.user_id == uid,
            reports.suspected_id == suspected_id
        )
    }
    search = reports.query.filter(*reports_filter).first()
    if search:
        app.logger.error("/reporting   " + "您已举报过该用户")
        return jsonify(code=200, message="您已举报过该用户")
    else:
        a = reports(user_id=uid, suspected_id=suspected_id,
                    message=message, time=time_now)
        b = messages(time=time_now, user_id=uid,
                     message=f"您的举报已受理，请等待审核")
        db.session.add_all([a, b])
        db.session.commit()
        app.logger.info("/reporting   " + "success")
        return jsonify(code=200, message="success")


@user.route('/report/view/verifying', methods=['GET', 'OPTIONS'])
@token().check_token("1")
# 地址传参/report/view/verifying?page=xxx
# 管理员查看用户举报记录预览
def report_view_verifying(x):
    access = x['access']
    app.logger.info("/report/view/verifying   " + str(x["uid"]) + "--" + access)
    if access == "admin":
        all_data = []
        page = int(request.args.get("page"))
        offset = (page - 1) * 10
        search = reports.query.filter(reports.status == "待审核").offset(offset).limit(10).all()
        for each in search:
            each_data = {}
            each_data.update(report_id=each.id, user_id=each.user_id,
                             suspected_id=each.suspected_id, message=each.message)
            all_data.append(each_data)
        app.logger.info("/report/view/verifying   " + "success")
        return jsonify(code=200, message="success", data=all_data)
    else:
        app.logger.error("/report/view/verifying   " + "操作无权限")
        return jsonify(code=401, message="操作无权限")


@user.route('/report/verifying', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "report_id": xxx,
#     "verifying": True/False
# }
# 管理员审核举报
def report_verifying(x):
    access = x['access']
    app.logger.info("/report/verifying   " + str(x["uid"]) + "--" + access)
    if access == "admin":
        report_id = request.get_json().get("report_id")
        verifying = request.get_json().get("verifying")
        app.logger.info("/report/verifying   " + str(report_id) + "--" + verifying)
        user_id = reports.query.filter(reports.id == report_id).first().user_id
        suspected_id = reports.query.filter(reports.id == report_id).first().suspected_id
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if verifying == "True":
            users.query.filter(users.id == suspected_id).update({"credit": "黑名单"})
            a = messages(time=time_now, user_id=user_id,
                         message=f"您举报的用户[{users.query.filter(users.id == user_id).first().username}]经核查确有违规行为，已被记入黑名单")
            b = messages(time=time_now, user_id=suspected_id,
                         message=f"您被举报查实出现违规行为，已被记入黑名单")
            db.session.add_all([a, b])
            db.session.commit()
        else:
            a = messages(time=time_now, user_id=user_id,
                         message=f"您举报的用户[{users.query.filter(users.id == user_id).first().username}]经核查未发现违规行为")
            db.session.add(a)
            db.session.commit()
        reports.query.filter(reports.id == report_id).update({"status": "已审核"})
        db.session.commit()
        app.logger.info("/report/verifying   " + "success")
        return jsonify(code=200, message="success")
    else:
        app.logger.error("/report/verifying   " + "操作无权限")
        return jsonify(code=401, message="操作无权限")
