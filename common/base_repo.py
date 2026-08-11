class BaseRepo:
    model = None

    @classmethod
    def get_all(cls):
        return cls.model.objects.all()

    @classmethod
    def get_by_id(cls, pk):
        return cls.model.objects.get(pk=pk)

    @classmethod
    def create(cls, **data):
        return cls.model.objects.create(**data)

    @classmethod
    def update(cls, pk, **data):
        obj = cls.get_by_id(pk)
        for k, v in data.items():
            setattr(obj, k, v)
        obj.save()
        return obj

    @classmethod
    def delete(cls, pk):
        obj = cls.get_by_id(pk)
        obj.delete()
        return obj
