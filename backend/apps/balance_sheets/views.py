from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import BalanceSheet, FinancialData, PDFChunk
from .serializers import BalanceSheetSerializer, FinancialDataSerializer, BalanceSheetUploadSerializer
from .pdf_processor import PDFProcessor
from .gemini_pdf_extractor import GeminiPDFExtractor
from .pdf_chunker import PDFChunker
from .embedding_service import EmbeddingService
from apps.companies.permissions import CanUploadBalanceSheet


class BalanceSheetViewSet(viewsets.ModelViewSet):
    """ViewSet for managing balance sheets with PDF processing and RAG indexing."""
    
    serializer_class = BalanceSheetSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        company_id = self.request.query_params.get('company')
        
        queryset = BalanceSheet.objects.all()
        
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        # Apply access control based on user role
        if user.role == 'CEO':
            from apps.companies.models import CompanyAccess
            accessible_companies = CompanyAccess.objects.filter(user=user).values_list('company_id', flat=True)
            queryset = queryset.filter(company_id__in=accessible_companies)
        
        return queryset.order_by('-year', '-uploaded_at')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return BalanceSheetUploadSerializer
        return BalanceSheetSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), CanUploadBalanceSheet()]
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """Process balance sheet upload: extract data, create records, and index for RAG."""
        balance_sheet = serializer.save(uploaded_by=self.request.user)
        
        try:
            pdf_file = balance_sheet.pdf_file
            pdf_file.open()
            
            # Extract financial data
            financial_data, additional_data = self._extract_financial_data(pdf_file)
            
            # Create financial data record
            self._create_financial_data_record(balance_sheet, financial_data, additional_data)
            
            # Process PDF chunks for RAG
            self._process_pdf_chunks(balance_sheet, pdf_file)
            
            pdf_file.close()
            
            balance_sheet.extraction_status = 'COMPLETED'
            balance_sheet.save()
            
        except Exception:
            balance_sheet.extraction_status = 'FAILED'
            balance_sheet.save()
    
    def _extract_financial_data(self, pdf_file):
        """Extract financial data from PDF using Gemini or fallback processor."""
        try:
            gemini_extractor = GeminiPDFExtractor()
            result = gemini_extractor.extract_financial_data(pdf_file)
            
            if result['confidence']['overall'] >= 0.5:
                financial_data = result['data']
                additional_data = {
                    'confidence': result['confidence'],
                    'validation': result['validation'],
                    'metadata': result['metadata']
                }
                return financial_data, additional_data
            else:
                raise Exception("Low confidence")
                
        except Exception:
            # Fallback to old PDFProcessor
            processor = PDFProcessor()
            pdf_file.seek(0)
            financial_data = processor.extract_financial_data(pdf_file)
            return financial_data, {}
    
    def _create_financial_data_record(self, balance_sheet, financial_data, additional_data):
        """Create FinancialData record from extracted data."""
        FinancialData.objects.create(
            balance_sheet=balance_sheet,
            # Assets
            total_assets=financial_data.get('total_assets'),
            current_assets=financial_data.get('current_assets'),
            non_current_assets=financial_data.get('non_current_assets'),
            # Liabilities
            total_liabilities=financial_data.get('total_liabilities'),
            current_liabilities=financial_data.get('current_liabilities'),
            non_current_liabilities=financial_data.get('non_current_liabilities'),
            # Equity
            total_equity=financial_data.get('total_equity'),
            # Income
            revenue=financial_data.get('revenue'),
            sales=financial_data.get('sales'),
            # Cash flows
            operating_cash_flow=financial_data.get('operating_cash_flow'),
            investing_cash_flow=financial_data.get('investing_cash_flow'),
            financing_cash_flow=financial_data.get('financing_cash_flow'),
            net_cash_flow=financial_data.get('net_cash_flow'),
            # Ratios
            current_ratio=financial_data.get('current_ratio'),
            debt_to_equity=financial_data.get('debt_to_equity'),
            roe=financial_data.get('roe'),
            # Additional flexible fields
            additional_data=additional_data
        )

    
    def _process_pdf_chunks(self, balance_sheet, pdf_file):
        """Process PDF into chunks and create embeddings for RAG."""
        try:
            pdf_file.open()
            chunker = PDFChunker()
            chunks_data = chunker.process_pdf(pdf_file, balance_sheet)
            
            if chunks_data:
                self._create_chunks_with_embeddings(balance_sheet, chunks_data)
            
            pdf_file.close()
            
        except Exception:
            if pdf_file:
                pdf_file.close()
    
    def _create_chunks_with_embeddings(self, balance_sheet, chunks_data):
        """Create PDFChunk records with embeddings for RAG indexing."""
        embedding_service = EmbeddingService()
        
        for idx, chunk_data in enumerate(chunks_data):
            content = chunk_data.get('content', '')
            page_num = chunk_data.get('page_num', chunk_data.get('start_page', idx+1))
            
            # Create embedding for RAG
            embedding_vector = []
            if embedding_service.client and content:
                try:
                    embedding_vector = embedding_service.create_embedding(content)
                except Exception:
                    embedding_vector = []
            
            # Create chunk record
            try:
                PDFChunk.objects.create(
                    balance_sheet=balance_sheet,
                    section_type=chunk_data.get('section_type', 'OTHER'),
                    chunk_type=chunk_data.get('chunk_type', 'Narrative_General'),
                    start_page=chunk_data.get('start_page', chunk_data.get('page_num', 1)),
                    end_page=chunk_data.get('end_page', chunk_data.get('page_num', 1)),
                    page_num=page_num,
                    source_title=chunk_data.get('source_title', ''),
                    content=content,
                    extracted_data={},
                    confidence=0.85,
                    embedding=embedding_vector,
                )
            except Exception:
                continue
    
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        """Get analytics data for a balance sheet."""
        balance_sheet = self.get_object()
        financial_data = balance_sheet.financial_data.first()
        
        if not financial_data:
            return Response({'error': 'No financial data available'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = FinancialDataSerializer(financial_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def analytics_summary(self, request):
        """Get comprehensive analytics with ratios, growth, and KPIs for selected balance sheets."""
        company_id = request.query_params.get('company')
        selected_ids = request.query_params.getlist('ids')
        
        if not company_id:
            return Response({'error': 'Company ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        balance_sheets = self._get_filtered_balance_sheets(company_id, selected_ids, request.user)
        analytics_data = self._prepare_analytics_data(balance_sheets)
        kpis = self._calculate_kpis(analytics_data)
        
        return Response({
            'analytics': analytics_data,
            'kpis': kpis,
            'periods_count': len(analytics_data)
        })
    
    def _get_filtered_balance_sheets(self, company_id, selected_ids, user):
        """Get balance sheets filtered by company, selection, and user access."""
        balance_sheets = BalanceSheet.objects.filter(company_id=company_id)
        
        # Apply access control
        if user.role == 'CEO':
            from apps.companies.models import CompanyAccess
            accessible_companies = CompanyAccess.objects.filter(user=user).values_list('company_id', flat=True)
            balance_sheets = balance_sheets.filter(company_id__in=accessible_companies)
        
        # Filter by selected IDs if provided
        if selected_ids:
            try:
                selected_ids_int = [int(id) for id in selected_ids]
                balance_sheets = balance_sheets.filter(id__in=selected_ids_int)
            except ValueError:
                pass
        
        return balance_sheets.order_by('year', 'quarter')
    
    def _prepare_analytics_data(self, balance_sheets):
        """Prepare analytics data from balance sheets."""
        analytics_data = []
        previous_data = None
        
        for bs in balance_sheets:
            fd = bs.financial_data.first()
            if not fd:
                continue
            
            # Calculate metrics
            current_assets = float(fd.current_assets or 0)
            current_liab = float(fd.current_liabilities or 0)
            total_assets = float(fd.total_assets or 0)
            total_liab = float(fd.total_liabilities or 0)
            total_equity = float(fd.total_equity or 0)
            revenue = float(fd.revenue or fd.sales or 0)
            
            # Calculate ratios
            current_ratio = current_assets / current_liab if current_liab > 0 else None
            debt_to_equity = total_liab / total_equity if total_equity > 0 else None
            working_capital = current_assets - current_liab
            asset_turnover = revenue / total_assets if total_assets > 0 else None
            
            # Calculate growth
            growth = self._calculate_growth(total_assets, revenue, total_equity, previous_data)
            
            period_data = {
                'id': bs.id,
                'year': bs.year,
                'quarter': bs.quarter,
                'period': f"{bs.year}{' Q' + bs.quarter if bs.quarter else ''}",
                'total_assets': total_assets,
                'current_assets': current_assets,
                'non_current_assets': float(fd.non_current_assets or 0),
                'total_liabilities': total_liab,
                'current_liabilities': current_liab,
                'non_current_liabilities': float(fd.non_current_liabilities or 0),
                'total_equity': total_equity,
                'revenue': revenue,
                'sales': float(fd.sales or 0),
                'operating_cash_flow': float(fd.operating_cash_flow or 0),
                'investing_cash_flow': float(fd.investing_cash_flow or 0),
                'financing_cash_flow': float(fd.financing_cash_flow or 0),
                'net_cash_flow': float(fd.net_cash_flow or 0),
                'current_ratio': current_ratio or float(fd.current_ratio or 0) if fd.current_ratio else None,
                'debt_to_equity': debt_to_equity or float(fd.debt_to_equity or 0) if fd.debt_to_equity else None,
                'roe': float(fd.roe or 0) if fd.roe else None,
                'working_capital': working_capital,
                'asset_turnover': asset_turnover,
                'growth': growth,
                'current_ratio_status': self._get_ratio_status(current_ratio, 'current'),
                'debt_to_equity_status': self._get_ratio_status(debt_to_equity, 'debt'),
            }
            
            analytics_data.append(period_data)
            previous_data = {
                'total_assets': total_assets,
                'revenue': revenue,
                'total_equity': total_equity,
            }
        
        return analytics_data
    
    def _calculate_growth(self, total_assets, revenue, total_equity, previous_data):
        """Calculate growth percentages from previous period."""
        growth = {}
        
        if previous_data:
            prev_assets = previous_data.get('total_assets', 0)
            prev_revenue = previous_data.get('revenue', 0)
            prev_equity = previous_data.get('total_equity', 0)
            
            if prev_assets > 0:
                growth['assets'] = ((total_assets - prev_assets) / prev_assets) * 100
            if prev_revenue > 0:
                growth['revenue'] = ((revenue - prev_revenue) / prev_revenue) * 100
            if prev_equity > 0:
                growth['equity'] = ((total_equity - prev_equity) / prev_equity) * 100
        
        return growth
    
    def _calculate_kpis(self, analytics_data):
        """Calculate overall KPIs from analytics data."""
        kpis = {}
        
        if analytics_data:
            latest = analytics_data[-1]
            kpis = {
                'total_assets': latest['total_assets'],
                'revenue': latest['revenue'],
                'current_ratio': latest['current_ratio'],
                'debt_to_equity': latest['debt_to_equity'],
                'working_capital': latest['working_capital'],
                'roe': latest['roe'],
                'asset_turnover': latest['asset_turnover'],
            }
            
            # Calculate CAGR if multiple periods
            if len(analytics_data) > 1:
                first = analytics_data[0]
                kpis['assets_growth'] = latest['growth'].get('assets')
                kpis['revenue_growth'] = latest['growth'].get('revenue')
                
                if first['total_assets'] > 0:
                    kpis['total_assets_cagr'] = (((latest['total_assets'] / first['total_assets']) ** 
                                                 (1 / (len(analytics_data) - 1))) - 1) * 100
                if first['revenue'] > 0:
                    kpis['revenue_cagr'] = (((latest['revenue'] / first['revenue']) ** 
                                            (1 / (len(analytics_data) - 1))) - 1) * 100
        
        return kpis
    
    def _get_ratio_status(self, ratio, ratio_type):
        """Get status indicator for a ratio."""
        if ratio is None:
            return 'unknown'
        
        if ratio_type == 'current':
            if ratio >= 1.5:
                return 'good'
            elif ratio >= 1.0:
                return 'attention'
            else:
                return 'bad'
        elif ratio_type == 'debt':
            if ratio <= 0.5:
                return 'good'
            elif ratio <= 1.0:
                return 'moderate'
            else:
                return 'high'
        
        return 'unknown'
