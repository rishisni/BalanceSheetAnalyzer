from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User model with role-based access control"""
    
    ROLE_CHOICES = [
        ('ANALYST', 'Analyst'),
        ('CEO', 'CEO'),
        ('GROUP_OWNER', 'Group Owner'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ANALYST')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"
