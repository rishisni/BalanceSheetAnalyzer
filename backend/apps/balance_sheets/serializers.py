from rest_framework import serializers
from .models import BalanceSheet, FinancialData
from apps.companies.serializers import CompanySerializer


class FinancialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialData
        fields = [
            'id', 'balance_sheet', 'total_assets', 'current_assets', 'non_current_assets',
            'total_liabilities', 'current_liabilities', 'non_current_liabilities',
            'total_equity', 'revenue', 'sales',
            'operating_cash_flow', 'investing_cash_flow', 'financing_cash_flow', 'net_cash_flow',
            'current_ratio', 'debt_to_equity', 'roe', 'additional_data',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class BalanceSheetSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)
    uploaded_by = serializers.StringRelatedField(read_only=True)
    financial_data = FinancialDataSerializer(read_only=True, many=True)
    
    class Meta:
        model = BalanceSheet
        fields = [
            'id', 'company', 'company_id', 'pdf_file', 'year', 'quarter',
            'uploaded_by', 'uploaded_at', 'extracted_at', 'extraction_status',
            'financial_data'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at', 'extracted_at', 'extraction_status']


class BalanceSheetUploadSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = BalanceSheet
        fields = ['company_id', 'pdf_file', 'year', 'quarter']

