from flask import jsonify, request
from flask_cors import CORS
from sqlalchemy import or_

from app import db
from app.main import exception
from app.main.utils import token, e_mail, jpg
from app.model import users, orders, bids, messages

CORS(exception, supports_credentials=True)


@exception.route('/exception/100', methods=['POST', 'OPTIONS'])
def exception_100():
    try:
        order_id = request.get_json().get("order_id")
    except exception:
        print(exception)
        return jsonify(code=400, message="无法获取id")
    print(order_id)
    seller_id = orders.query.filter(orders.id == order_id).first().seller_id
    try:
        orders.query.filter(orders.id == order_id).update({"status": "异常1"})
    except exception:
        print(exception)
        return jsonify(code=400, message="无法修改商品状态")
    try:
        users.query.filter(users.id == seller_id).update({"credit": "冻结"})
        # {
        # 此处发送信息给管理员提醒新的异常商品
        # }
        db.session.commit()
        return jsonify(code=200, message="成功反馈")
    except exception:
        print(exception)
        return jsonify(code=400, message="无法冻结用户")


@exception.route('/exception/110', methods=['POST', 'OPTIONS'])
def exception_110():
    type_ = request.get_json().get("type")
    orders_id = request.get_json().get("orders_id")
    seller_id = orders.query.filter(orders.id == orders_id).first().seller_id
    buyer_id = bids.query.filter(bids.order_id == orders_id).first().buyer_id
    bids_id = orders.query.filter(orders.id == orders_id).first().id
    order_price = orders.query.filter(orders.id == orders_id).first().price
    seller_money = users.query.filter(users.id == seller_id).first().money
    buyer_money = users.query.filter(users.id == buyer_id).first().money
    if not type_:
        if seller_money >= order_price:
            try:
                users.query.filter(users.id == seller_id).update({"money": seller_money - order_price})
                users.query.filter(users.id == buyer_id).update({"money": buyer_money + order_price})
                users.query.filter(users.id == seller_id).update({"credit": "黑名单"})
                bids.query.filter(bids.id == bids_id).delete()
                orders.query.filter(orders.id == orders_id).delete()
                db.session.commit()
                return jsonify(code=200, message="卖家金钱足够，成功返回买家金钱")
            except exception:
                print(exception)
                return jsonify(code=400, message="异常错误1")
        if seller_money <= order_price:
            try:
                users.query.filter(users.id == seller_id).update({"money": 0})
                users.query.filter(users.id == buyer_id).update({"money": buyer_money + order_price})
                users.query.filter(users.id == seller_id).update({"credit": "黑名单"})
                bids.query.filter(bids.id == bids_id).delete()
                orders.query.filter(orders.id == orders_id).delete()
                # 加入讨债列表
                db.session.commit()
                return jsonify(code=200, message="卖家金钱不够，成功返回买家金钱，加入讨债列表")
            except exception:
                print(exception)
                return jsonify(code=400, message="异常错误2")
    else:
        try:
            orders.query.filter(orders.id == orders_id).update({"status": "已通过"})
        except exception:
            print(exception)
            return jsonify(code=400, message="无法修改商品状态")
        try:
            users.query.filter(users.id == seller_id).update({"credit": "正常"})
            # {
            # 此处发送信息给管理员提醒新的异常商品
            # }
            db.session.commit()
            return jsonify(code=200, message="账号未被找回，交易正常")
        except exception:
            print(exception)
            return jsonify(code=400, message="无法冻结用户")


# 管理员获取待审核列表
@exception.route('/exception/1000', methods=['GET', 'OPTIONS'])
def exception_1000():
    data = []
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    search = orders.query.filter(or_(orders.status == "异常1", orders.status == "异常2")).offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(order_id=each.id, title=each.title, type=each.status,
                         picture=jpg(each.picture))
        data.append(each_data)
    return jsonify(code=200, message="success", data=data)


@exception.route('/exception/200', methods=['POST', 'OPTIONS'])
def exception_200():
    order_id = request.get_json().get("order_id")
    print(order_id)
    try:
        orders.query.filter(orders.id == order_id).update({"status": "异常2"})
        # {
        # 此处发送信息给管理员提醒新的异常商品
        # }
    except exception:
        print(exception)
        return jsonify(code=400, message="异常错误3")
    db.session.commit()
    return jsonify(code=200, message="提交异常成功")


@exception.route('/exception/210', methods=['POST', 'OPTIONS'])
def exception_210():
    orders_id = request.get_json().get("orders_id")
    percent = float(request.get_json().get("percent"))
    type_ = request.get_json().get("type")
    seller_id = orders.query.filter(orders.id == orders_id).first().seller_id
    buyer_id = bids.query.filter(bids.orders_id == orders_id).first().buyer_id
    bids_id = orders.query.filter(orders.id == orders_id).first().id
    order_price = orders.query.filter(orders.id == orders_id).first().price
    seller_money = users.query.filter(users.id == seller_id).first().money
    buyer_money = users.query.filter(users.id == buyer_id).first().money
    if type_:
        if 0 <= percent < 1:
            try:
                users.query.filter(users.id == seller_id).update({"money": seller_money + percent * order_price})
                users.query.filter(users.id == buyer_id).update({"money": buyer_money + (1 - percent) * order_price})
                bids.query.filter(bids.id == bids_id).delete()
                orders.query.filter(orders.id == orders_id).delete()
                db.session.commit()
                return jsonify(code=200, message="异常解决成功")
            except exception:
                print(exception)
                return jsonify(code=400, message="异常错误5")
        if percent == 1:
            try:
                users.query.filter(users.id == seller_id).update({"money": seller_money + order_price})
                # {
                #    此处通知买家
                # }
                users.query.filter(users.id == buyer_id).update({"credit": "黑名单"})
                bids.query.filter(bids.id == bids_id).delete()
                orders.query.filter(orders.id == orders_id).delete()
                db.session.commit()
                return jsonify(code=200, message="异常解决成功")
            except exception:
                print(exception)
                return jsonify(code=400, message="异常错误6")
    else:
        try:
            bids.query.filter(bids.id == bids_id).delete()
            orders.query.filter(orders.id == orders_id).delete()
        except exception:
            print(exception)
            return jsonify(code=400, message="无法取消交易过程")
        try:
            users.query.filter(users.id == buyer_id).update({"money": buyer_money + order_price})
            db.session.commit()
            return jsonify(code=200, message="异常成功解决，交易取消")
        except exception:
            print(exception)
            return jsonify(code=400, message="异常错误4")


# 卖家不同意的协调程序：
# 300：创建一个管理员与买卖家的三人聊天室
@exception.route('/exception/300', methods=['POST', 'OPTIONS'])  # 开启协调程序事件
def harmonize():
    pass
