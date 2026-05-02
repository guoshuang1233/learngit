from datetime import datetime

from flask import Blueprint, request
from backend.extensions import db
from backend.models import Goods, User, Category
from backend.utils.response import success_response
from backend.utils.exceptions import ApiException
from backend.utils.jwt_auth import jwt_required

admin_goods_bp = Blueprint('admin_goods', __name__, url_prefix='/api/admin/goods')
@admin_goods_bp.route('/list', methods=['GET'])
@jwt_required
def admin_goods_list():
    """管理员查询商品列表"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role != 1:
        raise ApiException('无权限', 403)

    page = int(request.args.get('page', 1))
    size = int(request.args.get('size', 20))
    status = request.args.get('status', 'all')
    keyword = request.args.get('keyword', '')

    # 我准备查商品表，但现在还不查，先把这个 “查询对象” 存起来。(多条件动态筛选)
    query = Goods.query
    if status == 'draft':
       query = query.filter(Goods.status == 0)
    elif status == 'on_sale':
        query = query.filter(Goods.status == 1)
    elif status == 'off_shelf':
        query = query.filter(Goods.status == 2)

    if keyword:
        query = query.filter(Goods.name.like(f'%{keyword}%'))

    total = query.count()
    # 分页对象
    page_data = query.order_by(Goods.update_time.desc()).paginate(page=page, per_page=size, error_out=False)

    res_list = [{
        "id": g.id,
        "name": g.name,
        "price": g.price,
        "img": g.img,
        "cid": g.cid,
        "stock": g.stock,
        "status": g.status,
        "category_name": Category.query.get(g.cid).name if g.cid and Category.query.get(g.cid) else "",
        "status_text": {0: '草稿箱', 1: '上架', 2: '下架'}.get(g.status, '未知'),
        "update_time": g.update_time.strftime('%Y-%m-%d %H:%M:%S') if g.update_time else None,
        "editor": "管理员"
    }for g in page_data.items] # g就是每个商品的小名

    return success_response(data={
        "total": total,
        "list": res_list
    })

# put（专门用来修改资源）
@admin_goods_bp.route('/<int:goods_id>', methods=['put'])
@jwt_required
def update_goods(goods_id):
    """管理员修改商品"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role != 1:
        raise ApiException('无权限', 403)
    goods = Goods.query.get(goods_id)
    if not goods:
        raise ApiException('商品不存在', 404)
    data = request.get_json()
    goods.name = data.get('name', goods.name)
    goods.price = data.get('price', goods.price)
    goods.img = data.get('img', goods.img)
    goods.cid = data.get('cid', goods.cid)
    goods.stock = data.get('stock', goods.stock)

    goods.update_time = datetime.now()
    db.session.commit()
    return success_response(msg="更新成功", data={"id": goods.id})

@admin_goods_bp.route('/<int:goods_id>', methods=['delete'])
@jwt_required
def delete_goods(goods_id):
    """管理员删除商品"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role != 1:
        raise ApiException('无权限', 403)
    goods = Goods.query.get(goods_id)
    if not goods:
        raise ApiException('商品不存在', 404)
    db.session.delete(goods)
    db.session.commit()
    return success_response(msg="删除成功")

@admin_goods_bp.route('/<int:goods_id>/status', methods=['post'])
@jwt_required
def change_goods_status(goods_id):
    """管理员修改商品状态"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role != 1:
        raise ApiException('无权限', 403)
    goods = Goods.query.get(goods_id)
    if not goods:
        raise ApiException('商品不存在', 404)
    data = request.get_json()
    new_status = data.get('status', -1)

    if new_status not in [0, 1, 2]:
        raise ApiException('状态值无效，必须为 0/1/2', 400)

    goods.status = new_status
    goods.update_time = datetime.now()
    db.session.commit()
    return success_response(msg="修改成功", data={"id": goods.id, "status": goods.status})

@admin_goods_bp.route('', methods=['POST'])
@jwt_required
def add_goods():
    """管理员添加商品"""
    user_id = request.current_user_id
    user = User.query.get(user_id)
    if not user or user.role != 1:
        raise ApiException('无权限', 403)

    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock', 0)
    cid = data.get('cid')
    img = data.get('img', '')
    status = data.get('status', 1)

    if not name:
        raise ApiException('商品名称不能为空', 400)
    if price is None or price <= 0:
        raise ApiException('商品价格必须大于0', 400)
    if stock < 0:
        raise ApiException('商品库存不能小于0', 400)

    new_goods = Goods(name=name, price=price, stock=stock, cid=cid, img=img, status=status)
    db.session.add(new_goods)
    db.session.commit()
    return success_response(msg="添加成功", data={"id": new_goods.id})









