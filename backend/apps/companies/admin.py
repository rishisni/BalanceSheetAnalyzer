from django.contrib import admin
from .models import Company, CompanyAccess


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent_company', 'created_at']
    list_filter = ['parent_company']
    search_fields = ['name']


@admin.register(CompanyAccess)
class CompanyAccessAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'created_at']
    list_filter = ['company', 'created_at']
    search_fields = ['user__username', 'company__name']
