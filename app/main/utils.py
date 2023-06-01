import string
from datetime import timedelta, datetime
import random
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.header import Header

import jwt
from flask import jsonify, request

from app.model import users

SECRET_KEY = "asjcklqencoiwrev45y6"
ALGORITHM = "HS256"


def jpg(x):
    # return "http://127.0.0.1:5000" + x
    return "https://7f1192d863.imdo.co" + x


class token:
    def create_token(self, username, access, uid):
        access_token_expires = timedelta(seconds=6000)
        expire = datetime.utcnow() + access_token_expires
        payload = {
            "sub": username,
            "uid": uid,
            "access": access,
            "exp": expire
        }
        access_token = jwt.encode(payload, SECRET_KEY, ALGORITHM)
        return access_token

    def check_token(self, para):
        para = str(para)
        def wrapper(func):
            def decorate():
                token = request.headers.get("Authorization")
                try:
                    payload = jwt.decode(token, SECRET_KEY, ALGORITHM)
                    access = payload.get("access")
                    username = payload.get("sub")
                    uid = payload.get("uid")
                    credit = users.query.filter(users.id == uid).first().credit
                    p = int(para)
                    if p == 1:
                        if credit == "黑名单":
                            return jsonify(code=401, message="黑名单用户无权限访问")
                        else:
                            return func(dict(username=username, uid=uid, access=access))
                    else:
                        return func(dict(username=username, uid=uid, access=access))
                except jwt.DecodeError:
                    return jsonify(code=401, message="token无权限")
                except jwt.ExpiredSignatureError:
                    return jsonify(code=401, message="token已过期")
                except jwt.PyJWTError:
                    return jsonify(code=401, message="无法检验token")
            decorate.__name__ = func.__name__
            return decorate
        wrapper.__name__ = para
        return wrapper


class e_mail:
    def create_code(self):
        clist = random.sample(string.ascii_letters, 6)
        return ''.join(clist)

    def send_email(self, receiver, ecode):
        sender = '<1348330522@qq.com>'  # 邮箱账号和发件者签名
        content = f"您的邮箱验证码为{ecode}"
        # 实例化邮件对象，并指定邮件的关键信息
        message = MIMEText(content, 'html', 'utf-8')
        message['Subject'] = Header('邮箱验证码', 'utf-8')
        message['From'] = sender
        message['To'] = receiver
        # QQ邮件服务器的链接
        smtpObj = SMTP_SSL('smtp.qq.com')
        smtpObj.login(user='1348330522@qq.com', password='ooyvhpzuvhnhjjda')
        smtpObj.sendmail(sender, receiver, str(message))
        smtpObj.quit()
