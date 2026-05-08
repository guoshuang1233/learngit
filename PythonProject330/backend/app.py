# backend/app.py
import os

from flask import Flask
from flask_cors import CORS
from backend.extensions import db

#==============MySQL配置===========
# 第一步，创建Flask应用实例
app = Flask(__name__)

# 👇 就加这一行！解决中文返回乱码
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'
# 第二步，配置数据库连接信息
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:AAaa123456@localhost:3306/testdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 最大图片不超过50MB

# 第三步，初始化ORM，初始化所有扩展
db.init_app(app)
CORS(app)

# 第四步：导入蓝图并注册
from backend.api.goods import goods_bp
from backend.api.category import category_bp
from backend.api.user import user_bp
from backend.api.auth import auth_bp
from backend.api.cart import cart_bp
from backend.api.chat import rag_bp
from backend.api.upload import upload_bp
from backend.api.stock import stock_bp
from backend.api.admin_goods import admin_goods_bp
from backend.api.order import order_bp
from backend.api.address import address_bp

app.register_blueprint(goods_bp)
app.register_blueprint(category_bp)
app.register_blueprint(user_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(rag_bp)
app.register_blueprint(upload_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(admin_goods_bp)
app.register_blueprint(order_bp)
app.register_blueprint(address_bp)

# from api.goods import *
# from api.category import *
#----------第五步新增全局异常捕获========
from backend.utils.response import success_response, error_response
from backend.utils.exceptions import ApiException
# from api.goods import *
# from api.category import *
# from api.auth import *

# 全局捕获自定义异常
@app.errorhandler(ApiException)
def handle_api_exception(e):
    return error_response(e.msg, e.code)

# 全局捕获服务器500错误
@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return error_response("服务器内部错误", 500)

# 404 异常，当访问没有定义的路由时，Flask会自动抛出一个404 Not Found错误
@app.errorhandler(404)
def not_found(e):
    db.session.rollback()
    return error_response("接口不存在", 404)

# 访问网址：http://127.0.0.1:5000/uploads/filename就能显示你上传的图片
@app.route('/uploads/<filename>')
def upload_file(filename):
    # send_from_directory函数是Flask提供的一个函数，用于发送文件或图片给浏览器的工具，参数是文件所在目录和文件名
    from flask import send_from_directory
    # 拼接上传文件保存的目录
    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
    # 去uploads文件夹里，找到filename对应的图片，返回给浏览器显示！
    return send_from_directory(upload_folder, filename)


#=================== =================================全局异常捕获结束==
# 6.启动服务
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("=" * 50)
    print("🚀 后端服务启动成功!")
    print("📍 访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True)
