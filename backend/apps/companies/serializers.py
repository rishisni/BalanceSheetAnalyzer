from rest_framework import serializers
from .models import Company, CompanyAccess


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'parent_company', 'created_at']
        read_only_fields = ['created_at']


class CompanyAccessSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = CompanyAccess
        fields = ['id', 'user', 'company', 'company_id', 'created_at']
        read_only_fields = ['created_at']


class CompanyWithSubsidiariesSerializer(serializers.ModelSerializer):
    subsidiaries = CompanySerializer(many=True, read_only=True)
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'parent_company', 'subsidiaries', 'created_at']

