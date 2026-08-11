from common.base_repo import BaseRepo
from apps.scriptgen.models import ScriptFile, ScriptGenerationJob, ScriptVersion
class ScriptFileRepo(BaseRepo):
    model=ScriptFile
    @classmethod
    def get_latest_by_suite(cls,suite_id): return cls.model.objects.filter(suite_id=suite_id).order_by("-id").first()
    @classmethod
    def update_record(cls,record,**fields):
        for k,v in fields.items(): setattr(record,k,v)
        record.save(update_fields=list(fields.keys())); return record
class ScriptGenerationJobRepo(BaseRepo): model=ScriptGenerationJob
    @classmethod
    def update_record(cls,record,**fields):
        for k,v in fields.items(): setattr(record,k,v)
        record.save(update_fields=list(fields.keys())); return record
class ScriptVersionRepo(BaseRepo):
    model=ScriptVersion
    @classmethod
    def get_next_version(cls,script_file): return cls.model.objects.filter(script_file=script_file).count()+1
    @classmethod
    def update_record(cls,record,**fields):
        for k,v in fields.items(): setattr(record,k,v)
        record.save(update_fields=list(fields.keys())); return record
