from django.db import models
from django.conf import settings


class ChatHistory(models.Model):
    """Chat history for AI-powered financial analysis conversations"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_history'
    )
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='chat_history'
    )
    query = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Chat Histories"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.company.name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
