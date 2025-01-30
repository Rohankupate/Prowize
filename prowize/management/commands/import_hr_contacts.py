import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from prowize.models import HRContact

class Command(BaseCommand):
    help = 'Import HR contacts from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                # Validate CSV structure
                required_fields = {'SNo', 'Name', 'Email', 'Title', 'Company'}
                csv_fields = set(reader.fieldnames)
                if not required_fields.issubset(csv_fields):
                    missing_fields = required_fields - csv_fields
                    self.stderr.write(self.style.ERROR(
                        f'Missing required fields in CSV: {", ".join(missing_fields)}'
                    ))
                    return
                
                contacts = []
                with transaction.atomic():
                    # Clear existing contacts
                    HRContact.objects.all().delete()
                    
                    # Import new contacts
                    for row in reader:
                        try:
                            contact = HRContact(
                                sno=int(row['SNo']),
                                name=row['Name'].strip(),
                                email=row['Email'].strip(),
                                title=row['Title'].strip(),
                                company=row['Company'].strip(),
                            )
                            contacts.append(contact)
                        except ValueError as e:
                            self.stderr.write(self.style.WARNING(
                                f'Skipping row {row["SNo"]}: {str(e)}'
                            ))
                    
                    # Bulk create contacts
                    HRContact.objects.bulk_create(contacts)
                
                self.stdout.write(self.style.SUCCESS(
                    f'Successfully imported {len(contacts)} HR contacts'
                ))
                
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f'File not found: {csv_file_path}'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error importing contacts: {str(e)}'))
