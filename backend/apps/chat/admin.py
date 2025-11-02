from django.contrib import admin
from .models import ChatHistory


@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'created_at']
    list_filter = ['company', 'created_at']
    search_fields = ['user__username', 'company__name', 'query']
