import os
import time

from flask import jsonify, request
from flask_cors import CORS
from sqlalchemy import or_, and_

from app import db, app
from app.config import redis_store
from app.main import view
from app.main.utils import token, jpg
from app.model import users, orders, bids, messages, collections
from app.main.imagecode import ImageCode


CORS(view, supports_credentials=True)


@view.route('/', methods=['GET', 'OPTIONS'])
def hello():
    app.logger.info("this is an info")
    app.logger.error("this is an error")
    return "hello"


@view.route('/code', methods=['GET', 'OPTIONS'])
def code():
    a, b = ImageCode().draw_verify_code()
    a = a.resize((80, 40))
    b = b.lower()
    redis_store.set("code", b, 60)
    print("答案是", b)
    a.save("./static/code.jpg", 'GIF')
    return jsonify(image=jpg("/static/code.jpg"))


@view.route('/home', methods=['GET', 'OPTIONS'])
def home():
    all_data = []
    Order = orders.query.filter(orders.status == "已通过").limit(5)
    for each in Order:
        idata = {}
        idata.update(order_id=each.id, order_title=each.title,
                     order_picture=jpg(each.picture))
        all_data.append(idata)
    return jsonify(code=200, message="success", data=all_data)


@view.route('/neworder', methods=['POST', 'OPTIONS'])
@token().check_token("1")
# form-data
# {
#     "picture" (file): xxx,
#     "title" (string): "xxx",
#     "description" (string): "xxx",
#     "game" (string): "xxx",
#     "resources" (string): "xxx",
#     "price" (number): "xxx"
# }
def neworder(x):
    uid = x["uid"]
    picture = request.files['picture']
    title = request.form['title']
    description = request.form['description']
    game = request.form['game']
    resources = request.form['resources']
    price = request.form['price']
    try:
        float(price)
    except ValueError:
        return jsonify(code=400, message="价格应为数字")
    if bool(picture) is False or bool(title) is False or bool(description) is False \
            or bool(game) is False or bool(resources) is False or bool(price) is False:
        return jsonify(code=400, message="请补充完整商品信息")
    else:
        a = orders(seller_id=uid, title=title,
                   description=description, game=game,
                   resources=resources, price=price)
        db.session.add(a)
        db.session.commit()
        order_id = orders.query.filter(orders.seller_id == uid).filter(orders.picture == None).first().id
        redis_store.set("delete_order_id", order_id, 60)
        orders.query.filter(orders.id == order_id).update({"picture": '/static/picture/' + str(order_id) + '.jpg'})
        picture.save(os.path.join('./static/picture/', str(order_id) + '.jpg'))
        db.session.commit()
        return jsonify(code=200, message="提交成功，请等待审核")


@view.route('/order/updating', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# form-data
# {
#     "picture" (file): xxx,
#     "order_id" (integer): xxx,
#     "title" (string): "xxx",
#     "description" (string): "xxx",
#     "game" (string): "xxx",
#     "resources" (string): "xxx",
#     "price" (number): "xxx"
# }
def order_updating(x):
    uid = x["uid"]
    picture = request.files['picture']
    order_id = request.form['order_id']
    title = request.form['title']
    description = request.form['description']
    game = request.form['game']
    resources = request.form['resources']
    price = request.form['price']
    seller_id = orders.query.filter(orders.id == order_id).first().seller_id
    app.logger.info("price----------" + price)
    if seller_id != uid:
        return jsonify(code=401, message="用户无权限")
    else:
        if bool(picture):
            picture.save(os.path.join('./static/picture/', str(order_id) + '.jpg'))
        if bool(title):
            orders.query.filter(orders.id == order_id).update({"title": title})
        if bool(description):
            orders.query.filter(orders.id == order_id).update({"description": description})
        if bool(game):
            orders.query.filter(orders.id == order_id).update({"game": game})
        if bool(resources):
            orders.query.filter(orders.id == order_id).update({"resources": resources})
        if bool(price):
            try:
                float(price)
            except ValueError:
                return jsonify(code=400, message="价格应为数字")
            orders.query.filter(orders.id == order_id).update({"price": price})
        orders.query.filter(orders.id == order_id).update({"status": "待审核"})
        db.session.commit()
        return jsonify(code=200, message="商品信息修改成功，请重新等待审核")


@view.route('/order/view', methods=['GET', 'OPTIONS'])
# 地址传参/order/view?page=xxx
def order_view():
    all_data = []
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    search = orders.query.filter(orders.status == "已通过").offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(order_id=each.id, title=each.title,
                         picture=jpg(each.picture))
        all_data.append(each_data)
    return jsonify(code=200, message="success", data=all_data)


@view.route('/order/view/verifying', methods=['GET', 'OPTIONS'])
@token().check_token("1")
# 地址传参/order/view/verifying?page=xxx
def order_view_verifying(x):
    access = x['access']
    if access == "admin":
        all_data = []
        page = int(request.args.get("page"))
        offset = (page - 1) * 10
        order_filter = {
            or_(
                orders.status == "待审核",
                orders.status == "待重审"
            )}
        search = orders.query.filter(*order_filter).offset(offset).limit(10).all()
        for each in search:
            each_data = {}
            each_data.update(order_id=each.id, title=each.title,
                             price=each.price, picture=jpg(each.picture))
            all_data.append(each_data)
        return jsonify(code=200, message="success", data=all_data)
    else:
        return jsonify(code=401, message="操作无权限")


@view.route('/order/verifying', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx
#     "verifying": "True/False"
# }
def order_verifying(x):
    access = x['access']
    if access == "admin":
        Order = orders.query.filter(orders.id == request.get_json().get("order_id"))
        seller_id = Order.first().seller_id
        status = Order.first().status
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if request.get_json().get("verifying") == "True":
            if status == "待审核":
                Order.update({"status": "已通过"})
                a = messages(user_id=seller_id, time=time_now,
                             message=f"您标题为[{Order.first().title}]的商品已通过审核")
            else:
                Order.update({"status": "待验货"})
                a = messages(user_id=seller_id, time=time_now,
                             message=f"您标题为[{Order.first().title}]的商品已通过重审，请与买家协商再次验货")
            db.session.add(a)
        else:
            if status == "待审核":
                Order.update({"status": "已结束"})
                a = messages(user_id=seller_id, time=time_now,
                             message=f"您标题为[{Order.first().title}]的商品未通过审核")
                db.session.add(a)
            else:
                a = messages(user_id=seller_id, time=time_now,
                             message=f"您标题为[{Order.first().title}]的商品未通过重审，请重新认真确认账户资源信息")
                db.session.add(a)
        db.session.commit()
        return jsonify(code=200, message="success")
    else:
        return jsonify(code=401, message="操作无权限")


@view.route('/order/searching', methods=['GET', 'OPTIONS'])
# 地址传参/order/searching?keyword=xxx&page=xxx
def order_searching():
    all_data = []
    keyword = request.args.get("keyword")
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    order_filter = {
        or_(
            orders.title.like(f'%{keyword}%'),
            orders.description.like(f'%{keyword}%'),
            orders.game.like(f'%{keyword}%')
        ),
        and_(
            orders.status == "已通过"
        )
    }
    search = orders.query.filter(*order_filter).offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(order_id=each.id, title=each.title,
                         picture=jpg(each.picture), price=each.price,
                         description=each.description)
        all_data.append(each_data)
    return jsonify(code=200, message="success", data=all_data)


@view.route('/order/information', methods=['GET', 'OPTIONS'])
# 地址传参/order/information?order_id=xxx
def order_information():
    all_data = []
    idata = {}
    order_id = request.args.get("order_id")
    Order = orders.query.filter(orders.id == order_id).first()
    if bool(Order):
        idata.update(order_id=Order.id, seller_id=Order.seller_id,
                     order_title=Order.title, order_description=Order.description,
                     order_game=Order.game, order_price=Order.price,
                     order_status=Order.status, order_picture=jpg(Order.picture))
        all_data.append(idata)
        return jsonify(code=200, message="success", data=all_data)
    else:
        return jsonify(code=400, message="参数错误")


@view.route('/order/bidding', methods=['POST', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx,
#     "price": xxx,
#     "message": "xxx",
# }
def order_bidding(x):
    uid = x["uid"]
    order_id = request.get_json().get("order_id")
    price = request.get_json().get("price")
    message = request.get_json().get("message")
    buyer_name = users.query.filter(users.id == uid).first().name
    title = orders.query.filter(orders.id == order_id).first().title
    seller_id = orders.query.filter(orders.id == order_id).first().seller_id
    time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    if seller_id == uid:
        return jsonify(code=400, message="不能给自己的商品出价哦")
    else:
        if price is None:
            return jsonify(code=400, message="请填写出价")
        else:
            try:
                float(price)
            except ValueError:
                return jsonify(code=400, message="价格应为数字")
            a = bids(order_id=order_id, buyer_id=uid,
                     buyer_name=buyer_name, price=price,
                     message=message, time=time_now)
            b = messages(message=f"您标题为[{title}]的商品被用户[{buyer_name}]出价[{price}]元",
                         user_id=seller_id, time=time_now)
            db.session.add_all([a, b])
            db.session.commit()
        return jsonify(code=200, message="出价成功")


@view.route('/bid/searching', methods=['GET', 'OPTIONS'])
# 地址传参/bid/searching?order_id=xxx&page=xxx
def bid_searching():
    all_data = []
    order_id = int(request.args.get("order_id"))
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    search = bids.query.filter(bids.order_id == order_id).offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(bid_id=each.id, buyer_name=each.buyer_name, price=each.price,
                         message=each.message, time=each.time)
        all_data.append(each_data)
    return jsonify(code=200, message="success", data=all_data)


@view.route('/order/paying', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx
# }
def order_paying(x):
    uid = x["uid"]
    order_id = request.get_json().get("order_id")
    Order = orders.query.filter(orders.id == order_id)
    price = Order.first().price
    seller_id = Order.first().seller_id
    User = users.query.filter(users.id == uid)
    if uid != seller_id:
        if User.first().money >= price:
            User.update({"money": User.first().money - price})
            Order.update({"money": "是", "status": "待验货", "buyer_id": uid})
            order_title = Order.first().title
            time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            a = messages(user_id=uid, time=time_now,
                         message=f"您已对商品[{order_title}]进行付款，支付金现暂存平台，请与卖家协商验货")
            b = messages(user_id=seller_id, time=time_now,
                         message=f"您挂出的商品[{order_title}]已受到付款，支付金现暂存平台，请与买家协商验货")
            db.session.add_all([a, b])
            db.session.commit()
            return jsonify(code=200, message="支付成功")
        else:
            return jsonify(code=400, message="账户余额不足")
    else:
        return jsonify(code=400, message="不能购买自己的商品哦")


@view.route('/order/confirming', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx,
#     "confirming": "True/False"
# }
def order_confirming(x):
    uid = x["uid"]
    order_id = request.get_json().get("order_id")
    confirm = request.get_json().get("confirming")
    Order = orders.query.filter(orders.id == order_id)
    seller_id = Order.first().seller_id
    time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    if uid == Order.first().buyer_id:
        if confirm == "True":
            Order.update({"status": "待发货"})
            a = messages(time=time_now, user_id=seller_id,
                         message=f"您出售的商品[{Order.first().title}]买家验货通过，请决定是否发货")
        else:
            Order.update({"status": "待重审"})
            a = messages(time=time_now, user_id=seller_id,
                         message=f"您出售的商品[{Order.first().title}]买家验货不通过，您可选择取消交易或者提交新的资源信息等待审核")
        db.session.add(a)
        db.session.commit()
        idata = {}
        idata.update(order_id=Order.first().id, title=Order.first().title,
                     status=Order.first().status, price=Order.first().price,
                     picture=jpg(Order.first().picture))
        return jsonify(code=200, message="success", data=idata)
    else:
        return jsonify(code=401, message="用户无权限")


@view.route('/order/delivering', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx,
#     "delivering": "True/False"
# }
def order_delivering(x):
    uid = x["uid"]
    order_id = request.get_json().get("order_id")
    delivering = request.get_json().get("delivering")
    Order = orders.query.filter(orders.id == order_id)
    order_buyer_id = Order.first().buyer_id
    order_title = Order.first().title
    order_seller_id = Order.first().seller_id
    price = Order.first().price
    time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    if Order.first().seller_id == uid:
        if delivering == "True":
            Order.update({"status": "已结束", "money": "已结束"})
            User = users.query.filter(users.id == Order.first().seller_id)
            User.update({"money": User.first().money + (price * 0.7)})
            order_resources = Order.first().resources
            a = messages(time=time_now, user_id=order_buyer_id,
                         message=f"您购买的商品[{order_title}]信息如下:[{order_resources}]")
            b = messages(time=time_now, user_id=order_seller_id,
                         message=f"您的商品[{order_title}]已发货，交易金额经协议比例折算后为[{price * 0.7}]元已汇入您的账户")
            db.session.add_all([a, b])
        else:
            a = messages(time=time_now, user_id=order_buyer_id,
                         message=f"您购买的商品[{order_title}]由于卖家拒绝发货，本次交易取消，交易金额已退还账户")
            b = messages(time=time_now, user_id=order_seller_id,
                         message=f"由于您拒绝发货商品[{order_title}]，本次交易已取消")
            User = users.query.filter(users.id == order_buyer_id)
            User.update({"money": User.first().money + price})
            Order.update({"buyer_id": None, "money": "否", "status": "已通过"})
            db.session.add_all([a, b])
        idata = {}
        idata.update(order_id=Order.first().id, title=Order.first().title,
                     status=Order.first().status, price=Order.first().price,
                     picture=jpg(Order.first().picture))
        db.session.commit()
        return jsonify(code=200, message="success", data=idata)
    else:
        return jsonify(code=401, message="用户无权限")


@view.route('/order/canceling', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx
# }
def order_canceling(x):
    uid = x["uid"]
    order_id = request.get_json().get("order_id")
    Order = orders.query.filter(orders.id == order_id)
    if uid == Order.first().seller_id or uid == Order.first().buyer_id:
        order_buyer_id = Order.first().buyer_id
        order_title = Order.first().title
        order_seller_id = Order.first().seller_id
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if uid == Order.first().seller_id:
            obj1 = "卖家"
            obj2 = "您"
        else:
            obj1 = "您"
            obj2 = "买家"
        a = messages(time=time_now, user_id=order_buyer_id,
                     message=f"您预购的商品[{order_title}]由于{obj1}取消订单，本次交易取消，若已付交易金则已退还账户")
        b = messages(time=time_now, user_id=order_seller_id,
                     message=f"由于{obj2}取消商品[{order_title}]的订单，本次交易已取消")
        if Order.first().money == "是":
            price = Order.first().price
            User = users.query.filter(users.id == order_buyer_id)
            User.update({"money": User.first().money + price})
        Order.update({"buyer_id": None, "money": "否", "status": "已通过"})
        db.session.add_all([a, b])
        db.session.commit()
        return jsonify(code=200, message="success")
    else:
        return jsonify(code=401, message="用户无权限")


@view.route('/order/deleting', methods=['DELETE', 'OPTIONS'])
@token().check_token("1")
# 地址传参/order/deleting?order_id=xxx
def order_deleting(x):
    uid = x["uid"]
    order_id = int(request.args.get("order_id"))
    Order = orders.query.filter(orders.id == order_id)
    order_seller_id = Order.first().seller_id
    if uid == order_seller_id:
        order_buyer_id = Order.first().buyer_id
        order_title = Order.first().title
        time_now = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if order_buyer_id:
            if Order.first().money == "是":
                User = users.query.filter(users.id == order_buyer_id)
                User.update({"money": User.first().money + Order.first().price})
            a = messages(time=time_now, user_id=order_buyer_id,
                         message=f"您预购的商品[{order_title}]由于卖家下架商品，本次交易取消，若已付交易金则已退还账户")
            b = messages(time=time_now, user_id=uid,
                         message=f"由于您下架商品[{order_title}]，本次交易已取消")
            db.session.add_all([a, b])
        else:
            c = messages(time=time_now, user_id=uid,
                         message=f"您已下架商品[{order_title}]")
            db.session.add(c)
        bids.query.filter(bids.order_id == order_id).delete()
        collections.query.filter(collections.order_id == order_id).delete()
        Order.delete()
        db.session.commit()
        return jsonify(code=200, message="success")
    else:
        return jsonify(code=401, message="用户无权限")


@view.route('/message', methods=['GET', 'OPTIONS'])
@token().check_token("0")
# 地址传参/message?page=xxx
def message(x):
    uid = x["uid"]
    all_data = []
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    search = messages.query.filter(messages.user_id == uid).offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(message=each.message, time=each.time)
        all_data.append(each_data)
    return jsonify(code=200, message="success", data=all_data)


@view.route('/order/collecting', methods=['PUT', 'OPTIONS'])
@token().check_token("1")
# {
#     "order_id": xxx
# }
def order_collecting(x):
    uid = x["uid"]
    order_id = request.get_json().get("order_id")
    Order = orders.query.filter(orders.id == order_id).first()
    order_filter = {
        and_(
            collections.order_id == order_id,
            collections.user_id == uid
        )
    }
    collection = collections.query.filter(*order_filter).first()
    if collection is not None:
        return jsonify(code=401, message="您已收藏过此商品了")
    else:
        a = collections(order_id=order_id, order_title=Order.title,
                        order_picture=Order.picture, user_id=uid)
        db.session.add(a)
        db.session.commit()
        return jsonify(code=200, message="success")


@view.route('/order/view/collection', methods=['GET', 'OPTIONS'])
@token().check_token("1")
# 地址传参/order/view/collection?page=xxx
def order_view_collection(x):
    uid = x["uid"]
    all_data = []
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    search = collections.query.filter(collections.user_id == uid).offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(order_id=each.order_id, title=each.order_title,
                         picture=jpg(each.order_picture))
        all_data.append(each_data)
    return jsonify(code=200, message="success", data=all_data)


@view.route('/order/view/mine', methods=['GET', 'OPTIONS'])
@token().check_token("1")
# 地址传参/order/view/mine?type=buying/selling&page=xxx
def order_view_mine(x):
    uid = x["uid"]
    all_data = []
    Type = request.args.get("type")
    page = int(request.args.get("page"))
    offset = (page - 1) * 10
    if Type == "selling":
        search = orders.query.filter(orders.seller_id == uid).offset(offset).limit(10).all()
    else:
        search = orders.query.filter(orders.buyer_id == uid).offset(offset).limit(10).all()
    for each in search:
        each_data = {}
        each_data.update(order_id=each.id, title=each.title,
                         status=each.status, price=each.price,
                         picture=jpg(each.picture))
        all_data.append(each_data)
    return jsonify(code=200, message="success", data=all_data)
