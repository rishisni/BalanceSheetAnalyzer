from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Company, CompanyAccess
from .serializers import CompanySerializer, CompanyAccessSerializer, CompanyWithSubsidiariesSerializer
from .permissions import HasCompanyAccess, CanCreateCompany


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Group owners see all companies
        if user.role == 'GROUP_OWNER':
            return Company.objects.all()
        
        # Analysts see all companies
        if user.role == 'ANALYST':
            return Company.objects.all()
        
        # CEOs see only their assigned companies
        if user.role == 'CEO':
            accessible_companies = CompanyAccess.objects.filter(user=user).values_list('company_id', flat=True)
            return Company.objects.filter(id__in=accessible_companies)
        
        return Company.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'retrieve' and 'subsidiaries' in self.request.query_params:
            return CompanyWithSubsidiariesSerializer
        return CompanySerializer
    
    def get_permissions(self):
        """Assign permissions based on action"""
        if self.action == 'create':
            return [IsAuthenticated(), CanCreateCompany()]
        elif self.action == 'retrieve':
            return [IsAuthenticated(), HasCompanyAccess()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['get'])
    def subsidiaries(self, request, pk=None):
        company = self.get_object()
        subsidiaries = company.subsidiaries.all()
        serializer = CompanySerializer(subsidiaries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def assign_access(self, request):
        """Assign company access to a user (for CEOs)"""
        user = request.user
        
        # Only Group Owners can assign access
        if user.role != 'GROUP_OWNER' and not user.is_staff:
            return Response(
                {'error': 'Only Group Owners can assign company access'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        company_id = request.data.get('company_id')
        user_id = request.data.get('user_id')
        
        if not company_id or not user_id:
            return Response(
                {'error': 'company_id and user_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            company = Company.objects.get(id=company_id)
            from apps.users.models import User
            target_user = User.objects.get(id=user_id)
            
            access, created = CompanyAccess.objects.get_or_create(
                user=target_user,
                company=company
            )
            
            if created:
                return Response(
                    {'message': f'Access granted to {target_user.username} for {company.name}'},
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'message': 'Access already exists'},
                    status=status.HTTP_200_OK
                )
        except Company.DoesNotExist:
            return Response(
                {'error': 'Company not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
