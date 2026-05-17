from backend.repository.goods_repo import GoodsRepo
from backend.repository.category_repo import CategoryRepo
from backend.models import Category
from backend.utils.exceptions import ApiException


class GoodsService:
    """商品业务逻辑层"""

    def get_goods_list(self, page=1, size=6, cid=0, name=''):
        """获取商品列表（分页+筛选+搜索）"""
        return GoodsRepo.get_list(page, size, cid, name)

    def create_goods(self, name, price, stock=0, cid=None, img='', status=1):
        """添加商品"""
        if not name or not name.strip():
            raise ApiException("商品名称不能为空", 400)
        if price is None or price <= 0:
            raise ApiException("价格必须大于0", 400)
        if stock < 0:
            raise ApiException("库存不能小于0", 400)

        cid = int(cid) if cid else None
        return GoodsRepo.create(
            name=name.strip(), price=price, stock=stock,
            cid=cid, img=img, status=status
        )

    def update_goods(self, goods_id, **kwargs):
        """更新商品信息"""
        goods = GoodsRepo.get_by_id(goods_id)
        if not goods:
            raise ApiException("商品不存在", 404)

        if 'price' in kwargs and kwargs['price'] <= 0:
            raise ApiException("价格必须大于0", 400)

        return GoodsRepo.update(goods, **kwargs)

    def delete_goods(self, goods_id):
        """删除商品"""
        goods = GoodsRepo.get_by_id(goods_id)
        if not goods:
            raise ApiException("商品不存在", 404)
        GoodsRepo.delete(goods)
