from django.contrib import admin
from .models import BalanceSheet, FinancialData, PDFChunk


@admin.register(BalanceSheet)
class BalanceSheetAdmin(admin.ModelAdmin):
    list_display = ['company', 'year', 'quarter', 'uploaded_by', 'extraction_status', 'uploaded_at']
    list_filter = ['company', 'year', 'extraction_status']
    search_fields = ['company__name']


@admin.register(FinancialData)
class FinancialDataAdmin(admin.ModelAdmin):
    list_display = ['balance_sheet', 'total_assets', 'revenue', 'created_at']
    list_filter = ['balance_sheet__company', 'balance_sheet__year']


@admin.register(PDFChunk)
class PDFChunkAdmin(admin.ModelAdmin):
    list_display = ['balance_sheet', 'section_type', 'page_range', 'period', 'confidence', 'created_at']
    list_filter = ['section_type', 'balance_sheet__company']
    search_fields = ['content', 'balance_sheet__company__name']
