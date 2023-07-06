from flask import jsonify, request
from flask_cors import CORS
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.main import exception
from app.main.utils import token, e_mail, jpg
from app.model import users, orders, bids, messages

CORS(exception, supports_credentials=True)


@exception.route('/exception/100', methods=['POST', 'OPTIONS'])
def exception_100():
    try:
        order_id = request.get_json().get("order_id")
        try:
            seller_id = orders.query.filter(orders.id == order_id).first().seller_id
            try:
                orders.query.filter(orders.id == order_id).update({"status": "异常1"})
                users.query.filter(users.id == seller_id).update({"credit": "冻结"})
                # {
                # 此处发送信息给管理员提醒新的异常商品
                # }
                db.session.commit()
                return jsonify(code=200, message="成功反馈")
            except SQLAlchemyError as e:
                db.session.rollback()
                print(e)
                return jsonify(code=400, message="无法冻结用户，或无法修改商品状态")
        except SQLAlchemyError as e:
            db.session.rollback()
            print(e)
            return jsonify(code=404, message="无法获取卖家信息")
    except exception:
        print(exception)
        return jsonify(code=404, message="此id商品不存在")


@exception.route('/exception/110', methods=['POST', 'OPTIONS'])
def exception_110():
    try:
        type_ = request.get_json().get("type")
        orders_id = request.get_json().get("orders_id")
        try:
            seller_id = orders.query.filter(orders.id == orders_id).first().seller_id
            buyer_id = orders.query.filter(orders.id == orders_id).first().buyer_id
            order_price = orders.query.filter(orders.id == orders_id).first().price
            seller_money = users.query.filter(users.id == seller_id).first().money
            buyer_money = users.query.filter(users.id == buyer_id).first().money
            if not type_:
                if seller_money >= order_price:
                    try:
                        users.query.filter(users.id == seller_id).update({"money": seller_money - order_price})
                        users.query.filter(users.id == buyer_id).update({"money": buyer_money + order_price})
                        users.query.filter(users.id == seller_id).update({"credit": "黑名单"})
                        orders.query.filter(orders.id == orders_id).delete()
                        db.session.commit()
                        return jsonify(code=200, message="卖家金钱足够，成功返回买家金钱")
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        print(e)
                        return jsonify(code=404, message="数据库错误，无法修改用户金钱或无法将用户状态改为黑名单")
                if seller_money <= order_price:
                    try:
                        users.query.filter(users.id == seller_id).update({"money": 0})
                        users.query.filter(users.id == buyer_id).update({"money": buyer_money + order_price})
                        users.query.filter(users.id == seller_id).update({"credit": "黑名单"})
                        orders.query.filter(orders.id == orders_id).delete()
                        db.session.commit()
                        return jsonify(code=200, message="卖家金钱不够，成功返回买家金钱，加入讨债列表")
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        print(e)
                        return jsonify(code=404, message="数据库错误，无法修改用户金钱或无法将用户状态改为黑名单")
            else:
                try:
                    orders.query.filter(orders.id == orders_id).update({"status": "已通过"})
                    users.query.filter(users.id == seller_id).update({"credit": "正常"})
                    # {
                    # 此处发送信息给管理员提醒新的异常商品
                    # }
                    db.session.commit()
                    return jsonify(code=200, message="账号未被找回，交易正常")
                except SQLAlchemyError as e:
                    print(e)
                    db.session.rollback()
                return jsonify(code=404, message="无法修改更正用户信息为正常，或无法恢复商品正常状态")
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            return jsonify(code=404, message="获取数据库数据失败，对应商品，订单或用户信息不存在")
    except exception as e:
        print(e)
        return jsonify(code=404, message="未成功获取前端数据")


# 管理员获取待审核列表
@exception.route('/exception/1000', methods=['GET', 'OPTIONS'])
def exception_1000():
    try:
        data = []
        page = int(request.args.get("page"))
        offset = (page - 1) * 10
        search = orders.query.filter(or_(orders.status == "异常1", orders.status == "异常2")).offset(offset).limit(
            10).all()
        for each in search:
            each_data = {}
            each_data.update(order_id=each.id, title=each.title, type=each.status,
                             picture=jpg(each.picture))
            data.append(each_data)
        return jsonify(code=200, message="success", data=data)
    except exception as e:
        print(e)
        return jsonify(code=404, message="数据库错误")


@exception.route('/exception/200', methods=['POST', 'OPTIONS'])
def exception_200():
    try:
        order_id = request.get_json().get("order_id")
        try:
            orders.query.filter(orders.id == order_id).update({"status": "异常2"})
            # {
            # 此处发送信息给管理员提醒新的异常商品
            # }
            db.session.commit()
            return jsonify(code=200, message="提交异常成功")
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            return jsonify(code=400, message="无法修改商品信息")
    except exception as e:
        print(e)
        return jsonify(code=404, message="未成功获取前端数据")


@exception.route('/exception/210', methods=['POST', 'OPTIONS'])
def exception_210():
    try:
        orders_id = request.get_json().get("orders_id")
        percent = float(request.get_json().get("percent"))
        type_ = request.get_json().get("type")
        try:
            seller_id = orders.query.filter(orders.id == orders_id).first().seller_id
            buyer_id = orders.query.filter(orders.id == orders_id).first().buyer_id
            order_price = orders.query.filter(orders.id == orders_id).first().price
            seller_money = users.query.filter(users.id == seller_id).first().money
            buyer_money = users.query.filter(users.id == buyer_id).first().money
            if not type_:
                if 0 <= percent < 1:
                    try:
                        users.query.filter(users.id == seller_id).update(
                            {"money": seller_money + percent * order_price})
                        users.query.filter(users.id == buyer_id).update(
                            {"money": buyer_money + (1 - percent) * order_price})
                        orders.query.filter(orders.id == orders_id).delete()
                        db.session.commit()
                        return jsonify(code=200, message="异常解决成功")
                    except SQLAlchemyError as e:
                        print(e)
                        db.session.rollback()
                        return jsonify(code=400, message="无法修改用户金钱")
                if percent == 1:
                    try:
                        users.query.filter(users.id == seller_id).update({"money": seller_money + order_price})
                        # {
                        #    此处通知买家
                        # }
                        users.query.filter(users.id == buyer_id).update({"credit": "黑名单"})
                        orders.query.filter(orders.id == orders_id).delete()
                        db.session.commit()
                        return jsonify(code=200, message="异常解决成功")
                    except SQLAlchemyError as e:
                        db.session.rollback()
                        print(e)
                        return jsonify(code=400, message="无法修改用户状态")
            else:
                try:
                    orders.query.filter(orders.id == orders_id).delete()
                    users.query.filter(users.id == buyer_id).update({"money": buyer_money + order_price})
                    db.session.commit()
                    return jsonify(code=200, message="异常成功解决，交易取消")
                except SQLAlchemyError as e:
                    print(e)
                    db.session.rollback()
                    return jsonify(code=400, message="订单无异常，但无法取消商品交易")
        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            return jsonify(code=400, message="数据库异常，无法获取数据库相关消息")
    except exception as e:
        print(e)
        return jsonify(code=400, message="无法获取前端消息")


# 卖家不同意的协调程序：
# 300：创建一个管理员与买卖家的三人聊天室
@exception.route('/exception/300', methods=['POST', 'OPTIONS'])  # 开启协调程序事件
def harmonize():
    pass
