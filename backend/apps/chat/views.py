from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import ChatHistory
from .serializers import ChatHistorySerializer, ChatQuerySerializer
from .gemini_service import GeminiChatService
from apps.balance_sheets.models import BalanceSheet


class ChatViewSet(viewsets.ModelViewSet):
    serializer_class = ChatHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        company_id = self.request.query_params.get('company')
        
        queryset = ChatHistory.objects.filter(user=user)
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['post'])
    def query(self, request):
        """Send a query and get AI response"""
        serializer = ChatQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        company_id = serializer.validated_data['company_id']
        query = serializer.validated_data['query']
        selected_ids = serializer.validated_data.get('selected_balance_sheet_ids', [])
        
        # Get company balance sheets (filter by selection if provided)
        balance_sheets = BalanceSheet.objects.filter(company_id=company_id)
        if selected_ids:
            balance_sheets = balance_sheets.filter(id__in=selected_ids)
        balance_sheets = balance_sheets.order_by('-year')
        balance_sheets_list = list(balance_sheets)
        
        # Generate AI response
        gemini_service = GeminiChatService()
        response = gemini_service.analyze_company_performance(query, balance_sheets_list)
        
        # Save to chat history
        try:
            from apps.companies.models import Company
            company = Company.objects.get(id=company_id)
            chat_history = ChatHistory.objects.create(
                user=request.user,
                company=company,
                query=query,
                response=response
            )
        except Exception:
            chat_history = None
        
        return Response({
            'query': query,
            'response': response,
            'created_at': chat_history.created_at if chat_history else None
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get chat history for a company"""
        company_id = request.query_params.get('company')
        
        if not company_id:
            return Response({'error': 'company parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(company_id=company_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
