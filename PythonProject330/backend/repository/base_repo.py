# backend/repository/base_repo.py
from backend.extensions import db


class BaseRepo:
    model = None  # 子类必须指定具体操作哪个表

    @classmethod
    def get_by_id(cls, id):
        return cls.model.query.get(id)

    @classmethod
    def get_all(cls):
        """获取所有记录"""
        return cls.model.query.all()

    @classmethod
    def create(cls, **kwargs):
        obj = cls.model(**kwargs)
        db.session.add(obj)
        db.session.commit()
        return obj

    @classmethod
    def delete(cls, obj):
        db.session.delete(obj)
        db.session.commit()
