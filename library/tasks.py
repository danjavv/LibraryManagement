import json
import os
from datetime import datetime
from celery import shared_task
from library_project import settings
from django.db.models import Count
from .models import Author, Book, BorrowRecord


@shared_task
def generate_report():
    # Gather statistics
    total_authors = Author.objects.count()
    total_books = Book.objects.count()
    total_borrowed = BorrowRecord.objects.filter(return_date__isnull=True).count()

    # Create report data
    report_data = {
        'generated_at': datetime.now().isoformat(),
        'statistics': {
            'total_authors': total_authors,
            'total_books': total_books,
            'total_borrowed': total_borrowed,
        }
    }

    # Ensure reports directory exists
    reports_dir = getattr(settings, 'REPORTS_DIR', os.path.join(settings.BASE_DIR, 'reports'))  # Use current working directory
    os.makedirs(reports_dir, exist_ok=True)

    # Generate filename with timestamp
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(reports_dir, filename)

    # Write report to file
    with open(filepath, 'w') as f:
        json.dump(report_data, f, indent=2)

    return filepath