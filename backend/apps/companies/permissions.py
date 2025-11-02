from rest_framework import permissions
from apps.companies.models import CompanyAccess


class HasCompanyAccess(permissions.BasePermission):
    """Permission to check if user has access to a specific company"""
    
    def has_permission(self, request, view):
        # For list/create actions, check is done in get_queryset
        if view.action in ['list', 'create']:
            return True
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Group owners can see all companies
        if user.role == 'GROUP_OWNER':
            return True
        
        # Analysts can see all companies
        if user.role == 'ANALYST':
            return True
        
        # CEOs can only see their assigned companies
        if user.role == 'CEO':
            return CompanyAccess.objects.filter(user=user, company=obj).exists()
        
        return False


class CanUploadBalanceSheet(permissions.BasePermission):
    """Permission to upload balance sheets (only analysts)"""
    
    def has_permission(self, request, view):
        return request.user.role == 'ANALYST'


class CanCreateCompany(permissions.BasePermission):
    """Permission to create companies (Group Owners and Admins)"""
    
    def has_permission(self, request, view):
        if request.method == 'POST':
            return request.user.role == 'GROUP_OWNER' or request.user.is_staff
        return True

