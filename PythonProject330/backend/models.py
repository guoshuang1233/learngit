import os
import sys
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

from backend.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt

class Goods(db.Model):
    __tablename__ = 'goods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(255))
    cid = db.Column(db.Integer, index=True)
    stock = db.Column(db.Integer, default=0, comment='库存数量')
    status = db.Column(db.Integer, default=1, comment='商品状态：0草稿 1出售中 2已下架')
    create_time = db.Column(db.DateTime, default=datetime.now, comment='创建时间')
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment='更新时间')

# backref = 'user'的意思是反向引用，作用：在Cart对象上增加一个属性user，指向这个购物车所属的用户，python
    # 如：cart = Cart.query.first()，print(cart.user.name)  # 通过 cart.user 访问所属的用户
    # carts = db.relationship('Cart', backref='goods', lazy='dynamic')

# 分类表
class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# ====================== 用户表 用户模型======================
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    avatar = db.Column(db.String(255), nullable=True, default='https://ui-avatars.com/api/')
    role = db.Column(db.Integer, default=0, nullable=False, comment='用户角色：0普通用户 1管理员')
    create_time = db.Column(db.DateTime, default=datetime.now)

    # carts = db.relationship('Cart', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_jwt_token(self, expires_in=3600):
        payload = {
            'user_id' : self.id,
            'username' : self.username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        }
        secret_key = os.getenv('SECRET_KEY', 'fallback-key-change-me')
        token = jwt.encode(payload, key=secret_key, algorithm='HS256')
        return token

    @staticmethod
    def verify_jwt_token(token):
        try:
            secret_key = os.getenv('SECRET_KEY', 'fallback-key-change-me')
            payload = jwt.decode(token, key=secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except (jwt.InvalidTokenError, jwt.exceptions.DecodeError):
            return None

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'phone': self.phone,
            'email': self.email,
            'avatar': self.avatar or f'https://ui-avatars.com/api/?name={self.username}&background=667eea&color=fff&size=120',
            'role': self.role,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None
        }
# 1. 购物车表
class Cart(db.Model):
    __tablename__ = "carts"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="关联用户ID")
    goods_id = db.Column(db.Integer, db.ForeignKey("goods.id"), nullable=False, comment="关联商品ID")
    count = db.Column(db.Integer, nullable=False, default=1, comment="商品数量")
    is_selected = db.Column(db.Boolean, default=True, comment="是否选中结算")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

# 关联关系
    user = db.relationship("User", backref="carts")
    goods = db.relationship("Goods", backref="carts")

#  订单主表
class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.String(32), primary_key=True, comment="订单号（自定义生成")
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="关联用户ID")
    total_amount = db.Column(db.DECIMAL(10, 2), nullable=False, comment="订单总金额")
    status = db.Column(db.Integer, default=0, comment="订单状态：0待付款 1已付款 2已发货 3已完成 4已取消")
    address_id = db.Column(db.Integer, db.ForeignKey("addresses.id"), nullable=False, comment="收货地址ID")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="下单时间")
    pay_time = db.Column(db.DateTime, comment="付款时间")
    ship_time = db.Column(db.DateTime, comment="发货时间")
    finish_time = db.Column(db.DateTime, comment="完成时间")
    cancel_time = db.Column(db.DateTime, comment="取消时间")

    user = db.relationship("User", backref="orders")
    # address = db.relationship("Address", backref="orders")
    # 下面代码指的是：对父对象做几乎所有操作，子对象都会跟着做。如果子对象不再属于任何父对象（孤儿），它会被自动删除。用在一对多关系中常见，例如：删除用户，自动删除该用户的所有购物车
    items = db.relationship("OrderItem", backref="order", cascade="all, delete-orphan")

    # 订单明细表（一个订单对应多个商品）
class OrderItem(db.Model):
    __tablename__ = "order_items"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.String(32), db.ForeignKey("orders.id"), nullable=False, comment="关联订单ID")
    goods_id = db.Column(db.Integer, db.ForeignKey("goods.id"), nullable=False, comment="关联商品ID")
    goods_name = db.Column(db.String(100), nullable=False, comment="商品快照名称")
    goods_price = db.Column(db.DECIMAL(10, 2), nullable=False, comment="商品快照单价")
    count = db.Column(db.Integer, nullable=False, comment="购买数量")
    total_price = db.Column(db.DECIMAL(10, 2), nullable=False, comment="商品小计")

    goods = db.relationship("Goods", backref="order_items")

# 收获地址表
class Address(db.Model):
    __tablename__ = "addresses"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, comment="关联用户ID")
    receiver = db.Column(db.String(50), nullable=False, comment="收货人")
    phone = db.Column(db.String(20), nullable=False, comment="手机号")
    province = db.Column(db.String(50), nullable=False, comment="省")
    city = db.Column(db.String(50), nullable=False, comment="市")
    district = db.Column(db.String(50), nullable=False, comment="区/县")
    detail = db.Column(db.String(100), nullable=False, comment="详细地址")
    is_default = db.Column(db.Boolean, default=False, comment="是否默认地址")
    create_time = db.Column(db.DateTime, default=datetime.now, comment="创建时间")

    user = db.relationship("User", backref="addresses")

