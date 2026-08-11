from common.base_repo import BaseRepo
from apps.documents.models import SourceDocument
class SourceDocumentRepo(BaseRepo):
    model=SourceDocument
    @classmethod
    def update_record(cls,record,**fields):
        for k,v in fields.items(): setattr(record,k,v)
        record.save(update_fields=list(fields.keys())); return record
