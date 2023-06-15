from app import db


class users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(db.Enum("user", "admin"), default="user", nullable=False)
    username = db.Column(db.VARCHAR(200), nullable=False)
    password = db.Column(db.VARCHAR(200), nullable=False)
    name = db.Column(db.VARCHAR(200), nullable=True)
    photo = db.Column(db.VARCHAR(200), nullable=True)
    email = db.Column(db.VARCHAR(200), nullable=True)
    real_name = db.Column(db.VARCHAR(200), nullable=True)
    money = db.Column(db.Float, default=0, nullable=False)
    credit = db.Column(db.Enum("正常", "黑名单", "冻结"), default="正常", nullable=False)


class orders(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    seller_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.VARCHAR(200), nullable=False)
    description = db.Column(db.VARCHAR(200), nullable=False)
    picture = db.Column(db.VARCHAR(200), nullable=True)
    game = db.Column(db.VARCHAR(200), nullable=False)
    resources = db.Column(db.VARCHAR(200), nullable=False)
    status = db.Column(db.Enum("待审核", "已通过", "待验货", "待重审", "待发货", "已结束", "异常1", "异常2"), default="待审核", nullable=False)
    price = db.Column(db.Float, nullable=False)
    money = db.Column(db.Enum("否", "是", "已结束"), default="否", nullable=False)
    buyer_id = db.Column(db.Integer, nullable=True)


class bids(db.Model):
    __tablename__ = 'bids'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, nullable=False)
    buyer_id = db.Column(db.Integer, nullable=False)
    buyer_name = db.Column(db.VARCHAR(200), nullable=True)
    price = db.Column(db.Float, nullable=False)
    message = db.Column(db.VARCHAR(200), nullable=True)
    time = db.Column(db.TIMESTAMP(True), nullable=False)


class messages(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    message = db.Column(db.VARCHAR(200), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    time = db.Column(db.TIMESTAMP(True), nullable=False)


class collections(db.Model):
    __tablename__ = 'collections'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, nullable=False)
    order_title = db.Column(db.VARCHAR(200), nullable=False)
    order_picture = db.Column(db.VARCHAR(200), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)


class reports(db.Model):
    __tablename__ = 'reports'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    suspected_id = db.Column(db.Integer, nullable=False)
    message = db.Column(db.VARCHAR(200), nullable=False)
    time = db.Column(db.TIMESTAMP(True), nullable=False)
    status = db.Column(db.Enum("待审核", "已审核"), default="待审核", nullable=False)
