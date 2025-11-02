from django.core.management.base import BaseCommand
from apps.companies.models import Company, CompanyAccess
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create sample data for testing'

    def handle(self, *args, **options):
        # Create companies
        self.stdout.write("Creating companies...")
        reliance_industries, created = Company.objects.get_or_create(name="Reliance Industries Limited")
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created: {reliance_industries.name}"))
        
        jio_platforms, created = Company.objects.get_or_create(
            name="Jio Platforms Limited",
            defaults={'parent_company': reliance_industries}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created: {jio_platforms.name}"))
        
        reliance_retail, created = Company.objects.get_or_create(
            name="Reliance Retail Ventures Limited",
            defaults={'parent_company': reliance_industries}
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created: {reliance_retail.name}"))

        # Create users
        User = get_user_model()
        self.stdout.write("\nCreating users...")

        # Analyst
        analyst, created = User.objects.get_or_create(
            username='analyst',
            defaults={'email': 'analyst@example.com', 'role': 'ANALYST'}
        )
        if created:
            analyst.set_password('analyst123')
            analyst.save()
            self.stdout.write(self.style.SUCCESS("Created Analyst: analyst / analyst123"))

        # CEO for Jio Platforms
        jio_ceo, created = User.objects.get_or_create(
            username='jio_ceo',
            defaults={'email': 'jio_ceo@example.com', 'role': 'CEO'}
        )
        if created:
            jio_ceo.set_password('ceo123')
            jio_ceo.save()
            CompanyAccess.objects.get_or_create(user=jio_ceo, company=jio_platforms)
            self.stdout.write(self.style.SUCCESS("Created Jio CEO: jio_ceo / ceo123"))

        # CEO for Reliance Retail
        retail_ceo, created = User.objects.get_or_create(
            username='retail_ceo',
            defaults={'email': 'retail_ceo@example.com', 'role': 'CEO'}
        )
        if created:
            retail_ceo.set_password('ceo123')
            retail_ceo.save()
            CompanyAccess.objects.get_or_create(user=retail_ceo, company=reliance_retail)
            self.stdout.write(self.style.SUCCESS("Created Retail CEO: retail_ceo / ceo123"))

        # Group Owner
        group_owner, created = User.objects.get_or_create(
            username='group_owner',
            defaults={'email': 'group_owner@example.com', 'role': 'GROUP_OWNER'}
        )
        if created:
            group_owner.set_password('owner123')
            group_owner.save()
            self.stdout.write(self.style.SUCCESS("Created Group Owner: group_owner / owner123"))

        self.stdout.write(self.style.SUCCESS("\nSample data created successfully!"))

