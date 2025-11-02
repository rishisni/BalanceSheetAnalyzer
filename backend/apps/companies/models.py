from django.db import models
from django.conf import settings


class Company(models.Model):
    """Company model with hierarchical structure for parent-subsidiary relationships"""
    
    name = models.CharField(max_length=255)
    parent_company = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subsidiaries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Companies"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CompanyAccess(models.Model):
    """Junction table for user-company permissions"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='company_accesses'
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='user_accesses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Company Accesses"
        unique_together = ['user', 'company']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} -> {self.company.name}"
