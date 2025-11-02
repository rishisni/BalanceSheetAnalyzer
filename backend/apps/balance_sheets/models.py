from django.db import models
from django.conf import settings
# NOTE: Ensure 'apps.companies' exists and has a 'Company' model.


class BalanceSheet(models.Model):
    """Balance sheet PDF storage and metadata"""
    
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='balance_sheets'
    )
    pdf_file = models.FileField(upload_to='balance_sheets/')
    year = models.IntegerField()
    quarter = models.CharField(max_length=20, blank=True, null=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_balance_sheets'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_at = models.DateTimeField(null=True, blank=True)
    extraction_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    
    class Meta:
        unique_together = ['company', 'year', 'quarter']
        ordering = ['-year', '-uploaded_at']
    
    def __str__(self):
        quarter_str = f" Q{self.quarter}" if self.quarter else ""
        return f"{self.company.name} - {self.year}{quarter_str}"


class FinancialData(models.Model):
    """Structured financial metrics extracted from balance sheets"""
    
    balance_sheet = models.ForeignKey(
        BalanceSheet,
        on_delete=models.CASCADE,
        related_name='financial_data'
    )
    
    # Assets
    total_assets = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    current_assets = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_current_assets = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Liabilities
    total_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    current_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    non_current_liabilities = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Equity
    total_equity = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Revenue/Sales
    revenue = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    sales = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Cash flows
    operating_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    investing_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    financing_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    net_cash_flow = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    
    # Key ratios
    current_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    debt_to_equity = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    roe = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)  # Return on Equity
    
    # Additional data stored as JSON for flexibility
    additional_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Financial Data"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.balance_sheet.company.name} - {self.balance_sheet.year}"


class PDFChunk(models.Model):
    """Chunks of PDF content organized by section type for efficient retrieval"""
    
    SECTION_TYPES = [
        ('BALANCE_SHEET', 'Balance Sheet'),
        ('INCOME_STATEMENT', 'Income Statement / P&L'),
        ('CASH_FLOW', 'Cash Flow Statement'),
        ('NOTES', 'Notes to Accounts'),
        ('RATIOS', 'Financial Ratios'),
        ('OTHER', 'Other'),
    ]
    
    CHUNK_TYPES = [
        ('Table_FS', 'Financial Statement Table'),
        ('Narrative_Text', 'Narrative Text'),
        ('Narrative_Note', 'Narrative Note'),
        ('Narrative_Intro', 'Narrative Introduction'),
        ('Narrative_General', 'General Narrative'),
    ]
    
    balance_sheet = models.ForeignKey(
        BalanceSheet,
        on_delete=models.CASCADE,
        related_name='chunks'
    )
    section_type = models.CharField(max_length=30, choices=SECTION_TYPES, default='OTHER')
    chunk_type = models.CharField(max_length=30, choices=CHUNK_TYPES, default='Narrative_General', help_text="Type of chunk content")
    page_range = models.CharField(max_length=50, blank=True, help_text="e.g., '5-12' or '15-20'")
    start_page = models.IntegerField()
    end_page = models.IntegerField()
    page_num = models.IntegerField(default=1, help_text="Primary page number for this chunk")
    source_title = models.CharField(max_length=500, blank=True, help_text="Title/source of this chunk (e.g., 'Consolidated Balance Sheet')")
    period = models.CharField(max_length=50, blank=True, null=True, help_text="Year/Quarter this chunk represents")
    content = models.TextField(help_text="Extracted text content from this section")
    extracted_data = models.JSONField(default=dict, blank=True, help_text="Structured data if applicable")
    confidence = models.FloatField(default=0.85, help_text="Extraction confidence score")
    content_summary = models.TextField(blank=True, help_text="Brief summary of chunk content")
    
    # ⭐ NEW FIELD FOR RAG: Storing the embedding vector
    embedding = models.JSONField(default=list, blank=True, help_text="Vector embedding for semantic search (RAG)") 
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "PDF Chunks"
        ordering = ['start_page', 'section_type']
        indexes = [
            models.Index(fields=['balance_sheet', 'section_type']),
            models.Index(fields=['balance_sheet', 'start_page']),
        ]
    
    def __str__(self):
        title = self.source_title[:30] if self.source_title else self.section_type
        return f"{self.balance_sheet.company.name} - {title} (Page {self.page_num})"
    
    def save(self, *args, **kwargs):
        # Auto-generate page_range if not provided
        if not self.page_range:
            if self.start_page == self.end_page:
                self.page_range = str(self.start_page)
            else:
                self.page_range = f"{self.start_page}-{self.end_page}"
        # Ensure page_num is set
        if not self.page_num:
            self.page_num = self.start_page
        super().save(*args, **kwargs)