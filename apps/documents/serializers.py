from rest_framework import serializers
from apps.documents.models import SourceDocument

class SourceDocumentSerializer(serializers.ModelSerializer):
    class Meta: model=SourceDocument; fields='__all__'
