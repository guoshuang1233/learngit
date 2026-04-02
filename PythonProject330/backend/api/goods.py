# 商品接口+分页+分类+搜索
from backend.app import app, db #app.py文件中导入app对象。通常，这个app对象是使用Flask框架创建的应用实例，并在这个实例上定义路由、试图和其它设置。
from flask import jsonify, request
from backend.models import Goods # 从 ORM模型导入
from backend.utils.response import success_response


# 商品数据
# cid指的是类别ID（手机、电脑、家电等）。这个字段用于将每个商品与其所属类别关联起来。

# goods_list = [
#     {"id": 1, "name": "iPhone 15", "price": 5999, "img": "https://picsum.photos/200/150?1", "cid": 1},
#     {"id": 2, "name": "MacBook Pro", "price": 12999, "img": "https://picsum.photos/200/150?2", "cid": 2},
#     {"id": 3, "name": "小米电视", "price": 3299, "img": "https://picsum.photos/200/150?3", "cid": 3},
#     {"id": 4, "name": "华为手机", "price": 4999, "img": "https://picsum.photos/200/150?4", "cid": 1},
#     {"id": 5, "name": "联想笔记本", "price": 6599, "img": "https://picsum.photos/200/150?5", "cid": 2},
#     {"id": 6, "name": "海尔冰箱", "price": 2899, "img": "https://picsum.photos/200/150?6", "cid": 3},
#     {"id": 7, "name": "OPPO手机", "price": 3499, "img": "https://picsum.photos/200/150?7", "cid": 1},
#     {"id": 8, "name": "戴尔台式机", "price": 5499, "img": "https://picsum.photos/200/150?8", "cid": 2},
# ]

#定义路由
@app.route('/api/goods', methods=['GET'])
def get_goods(): # 负责处理请求并返回数据
    # request.args是Flask中用来访问URL查询参数的对象
    page = int(request.args.get('page', 1)) # 从请求的查询参数中获取名为 page的参数。如果没有提供该参数，则默认值为1
    size = int(request.args.get('size', 6)) # 从请求的查询参数值获取名为size的参数。如果没有提供该参数，则默认值为6
    cid = int(request.args.get('cid', 0)) # 类别ID，用于过滤商品，默认为None
    name = request.args.get('name', '') # 用于搜索商品的名称，默认为空字符串

    # 从数据库查询
    query = Goods.query

    # 筛选分类
    if cid != 0:
        query = query.filter(Goods.cid == cid)
    # 搜索------(在Python中，空字符串、None和其它一些特定值（如0、空列表等）都被视为False
    # 如果name是一个空字符串（”“）或者没有被定义（None），那么if name条件将评估为False
    if name:
        query = query.filter(Goods.name.like(f'%{name}%'))
    # 分页
    total = query.count()
    # error_out=True:请求的页码超出范围时抛出404错误；error_out=False:请求的页码超出范围时返回空的结果集，而不是抛出错误
    page_data = query.paginate(page=page, per_page=size, error_out=False)
    # 调用paginate后，可以方便地访问当前页的数据、总记录数以及分页状态
    # current_items = page_data.items//获取当前页的商品列表
    # total_items = page_data.total//获取总记录数
    # has_next_page = page_data.has_next //获取是否有下一页
    # has_prev_page = page_data.has_prev //获取是否有上一页

    # 将数据库对象转化成字段需要的JSON格式
    res_list = []
    for g in page_data.items:
        res_list.append({
            "id": g.id,
            "name": g.name,
            "price": g.price,
            "img": g.img,
            "cid": g.cid
        })
    return success_response(data={"total": total, "list": res_list})
