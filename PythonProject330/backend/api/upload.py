import os
import uuid
from flask import request, Blueprint
from backend.utils.response import success_response, error_response

# 创建上传接口蓝图
upload_bp = Blueprint('upload', __name__, url_prefix='/api')

# __file__ = D:/Python/PythonProjects/python-flask-demo/backend/api/upload.py
# 拼接上传文件保存的目录
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
# 允许上传的图片格式白名单
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# 判断文件后缀是否合法
def allowed_file(filename): # 接受参数filename，该参数代表要检查的文件名
    # 通过return语句来返回布尔值（True或False），标识文件名是否符合允许的扩展名
    # 只有文件名中包含.且文件名后缀在白名单中时，返回True，否则返回False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 图片上传接口 /api/upload POST
@upload_bp.route('/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:  # request.files是一个字典对象，用于保存上传的文件
        return error_response('请选择要上传的图片',400)
    file = request.files['file']
    # 文件格式不支持
    if not allowed_file(file.filename):
        return error_response('文件格式不支持',400)
    # 提取后缀
    ext = file.filename.rsplit('.', 1)[1].lower()
    # uuid随机唯一文件名，防止重名覆盖
    new_filename = f"{uuid.uuid4().hex}.{ext}" # uuid.uuid4().hex=生成一个全球唯一ID，.hex=转成字符串(32位纯文本，无横杠)

    # 完整保存路径(把“文件夹路径”和“文件名”拼在一起)
    filepath = os.path.join(UPLOAD_FOLDER, new_filename)

    # 保存图片到uplaods文件夹
    file.save(filepath)

    # 前端可访问的url地址
    image_url = f"/uploads/{new_filename}"
    return success_response(data={"image_url": image_url}, msg="上传成功")

