from rest_framework import serializers
from .models import ChatHistory
from apps.companies.serializers import CompanySerializer


class ChatHistorySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = ChatHistory
        fields = ['id', 'user', 'company', 'company_id', 'query', 'response', 'created_at']
        read_only_fields = ['user', 'created_at']


class ChatQuerySerializer(serializers.Serializer):
    company_id = serializers.IntegerField()
    query = serializers.CharField()
    selected_balance_sheet_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

