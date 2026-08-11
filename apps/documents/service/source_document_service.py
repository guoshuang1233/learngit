from pathlib import Path

from apps.documents.models import SourceDocument


class SourceDocumentService:
    @staticmethod
    def extract_text_from_upload(source_file):
        if not source_file:
            return ""

        raw = source_file.read()
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            pass

        for encoding in ("utf-8", "gb18030", "gbk"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore")

    @staticmethod
    def _default_title(title="", source_file=None, fallback="Untitled"):
        title = (title or "").strip()
        if title:
            return title
        if source_file and getattr(source_file, "name", ""):
            stem = Path(source_file.name).stem.strip()
            if stem:
                return stem
        return fallback

    @classmethod
    def _create_document(cls, *, project, title="", source_file=None, extracted_text="", uploaded_by=None, metadata=None, doc_type):
        if source_file and hasattr(source_file, "seek"):
            try:
                source_file.seek(0)
            except Exception:
                pass
        return SourceDocument.objects.create(
            project=project,
            title=cls._default_title(title, source_file),
            doc_type=doc_type,
            source_file=source_file,
            extracted_text=extracted_text,
            uploaded_by=uploaded_by,
            metadata=metadata or {},
        )

    @classmethod
    def create_requirement_document(cls, *, project, title="", source_file=None, extracted_text="", uploaded_by=None, metadata=None):
        return cls._create_document(
            project=project,
            title=title,
            source_file=source_file,
            extracted_text=extracted_text,
            uploaded_by=uploaded_by,
            metadata=metadata,
            doc_type=SourceDocument.DOC_TYPE_REQUIREMENT,
        )

    @classmethod
    def create_suite_document(cls, *, project, title="", source_file=None, extracted_text="", uploaded_by=None, metadata=None):
        return cls._create_document(
            project=project,
            title=title,
            source_file=source_file,
            extracted_text=extracted_text,
            uploaded_by=uploaded_by,
            metadata=metadata,
            doc_type=SourceDocument.DOC_TYPE_SUITE,
        )

    @classmethod
    def create_api_document(cls, *, project, title="", source_file=None, extracted_text="", uploaded_by=None, metadata=None):
        return cls._create_document(
            project=project,
            title=title,
            source_file=source_file,
            extracted_text=extracted_text,
            uploaded_by=uploaded_by,
            metadata=metadata,
            doc_type=SourceDocument.DOC_TYPE_API,
        )
