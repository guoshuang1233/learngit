from backend.repository.base_repo import BaseRepo
from backend.models import Goods

class GoodsRepo(BaseRepo):
    """商品表数据访问层"""
    model = Goods

    @classmethod
    def get_list(cls, page=1, size=20, cid=0, keyword=None):
        """获取商品列表（分页+筛选+搜索）"""
        query = cls.model.query.filter(Goods.status == 1)
        if cid and cid != 0:
            query = query.filter(Goods.cid == cid)
        if keyword:
            query = query.filter(Goods.name.like(f'%{keyword}%'))
        return query.order_by(Goods.update_time.desc()).paginate(page=page, per_page=size, error_out=False)
