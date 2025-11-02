"""
Management command to generate embeddings for existing PDF chunks.
Useful for backfilling embeddings after adding RAG support.
"""
from django.core.management.base import BaseCommand
from apps.balance_sheets.models import PDFChunk
from apps.balance_sheets.embedding_service import EmbeddingService
from tqdm import tqdm


class Command(BaseCommand):
    help = 'Generate embeddings for existing PDF chunks that don\'t have them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--balance-sheet-id',
            type=int,
            help='Only process chunks for a specific balance sheet',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Regenerate embeddings even if they already exist',
        )

    def handle(self, *args, **options):
        embedding_service = EmbeddingService()
        
        if not embedding_service.client:
            self.stdout.write(self.style.ERROR('Embedding service not available. Check GEMINI_API_KEY.'))
            return
        
        # Get chunks without embeddings
        queryset = PDFChunk.objects.all()
        
        if options['balance_sheet_id']:
            queryset = queryset.filter(balance_sheet_id=options['balance_sheet_id'])
        
        if not options['force']:
            # Only chunks without embeddings
            queryset = queryset.filter(embedding__isnull=True) | queryset.filter(embedding=[])
        
        chunks = list(queryset)
        
        if not chunks:
            self.stdout.write(self.style.SUCCESS('No chunks need embeddings.'))
            return
        
        self.stdout.write(f'Generating embeddings for {len(chunks)} chunks...')
        
        success_count = 0
        error_count = 0
        
        for chunk in tqdm(chunks, desc="Generating embeddings"):
            try:
                if not chunk.content:
                    self.stdout.write(self.style.WARNING(f'Chunk {chunk.id} has no content, skipping'))
                    continue
                
                embedding = embedding_service.create_embedding(chunk.content)
                
                if embedding:
                    chunk.embedding = embedding
                    chunk.save(update_fields=['embedding'])
                    success_count += 1
                else:
                    error_count += 1
                    self.stdout.write(self.style.WARNING(f'Failed to generate embedding for chunk {chunk.id}'))
                    
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Error processing chunk {chunk.id}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nComplete! Generated {success_count} embeddings, {error_count} errors'
        ))

