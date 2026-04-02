# backend/app.py
from flask import Flask
from flask_cors import CORS
# 连接数据库+ORM操作
from flask_sqlalchemy import SQLAlchemy
#==============MySQL配置===========
# 第一步，创建Flask应用实例
app = Flask(__name__)
CORS(app) #跨域

# 第二步，配置数据库连接信息
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:AAaa123456@localhost:3306/testdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 第三步，初始化ORM，即初始化SQLAlchemy
db = SQLAlchemy(app)
# 第四步，导入路由模板
from api.goods import *
from api.category import *

#-----------新增全局异常捕获========
from utils.response import success_response, error_response
from utils.exceptions import ApiException



# 全局捕获自定义异常
@app.errorhandler(ApiException)
def handle_api_exception(e):
    return error_response(e.msg, e.code)

# 全局捕获服务器500错误
@app.errorhandler(500)
def server_error(e):
    return error_response("服务器内部错误", 500)

# 404 异常，当访问没有定义的路由时，Flask会自动抛出一个404 Not Found错误
@app.errorhandler(404)
def not_found(e):
    return error_response("接口不存在", 404)
#====================================================全局异常捕获结束==








if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)