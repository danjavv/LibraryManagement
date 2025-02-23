from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import json
import os
from .models import Author, Book, BorrowRecord
from .serializers import AuthorSerializer, BookSerializer, BorrowRecordSerializer
from .tasks import generate_report
from library_project import settings

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class BorrowRecordViewSet(viewsets.ModelViewSet):
    queryset = BorrowRecord.objects.all()
    serializer_class = BorrowRecordSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        book_id = request.data.get('book')
        book = get_object_or_404(Book, id=book_id)
        
        if book.available_copies <= 0:
            return Response(
                {"error": "No copies available for borrowing"},
                status=status.HTTP_400_BAD_REQUEST
            )

        book.available_copies -= 1
        book.save()
        
        return super().create(request, *args, **kwargs)

    @action(detail=True, methods=['put'])
    @transaction.atomic
    def return_book(self, request, pk=None):
        borrow_record = self.get_object()
        
        if borrow_record.return_date:
            return Response(
                {"error": "This book has already been returned"},
                status=status.HTTP_400_BAD_REQUEST
            )

        borrow_record.return_date = timezone.now()
        borrow_record.save()

        book = borrow_record.book
        book.available_copies += 1
        book.save()

        return Response({"message": "Book returned successfully"})

class ReportView(APIView):
    def get(self, request):
        # Get the latest report from the reports directory
        reports_dir = getattr(settings, 'REPORTS_DIR', os.path.join(settings.BASE_DIR, 'reports'))
        
        # Ensure the reports directory exists
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)  # Create the directory if it does not exist

        try:
            reports = os.listdir(reports_dir)
            if not reports:
                return Response(
                    {"error": "No reports available"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Filter reports to only include JSON files and sort them
            json_reports = [report for report in reports if report.endswith('.json')]
            if not json_reports:
                return Response(
                    {"error": "No JSON reports available"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Sort the JSON reports by modification time to get the latest one
            latest_report = max(json_reports, key=lambda x: os.path.getmtime(os.path.join(reports_dir, x)))
            with open(os.path.join(reports_dir, latest_report), 'r') as f:
                report_data = f.read()  # Read the file content as a string
            
            # Attempt to parse the report data as JSON
            try:
                report_data = json.loads(report_data)
            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON format in report"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(report_data)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        # Trigger the Celery task to generate a new report
        generate_report.delay()
        
        return Response(
            {"message": "Report generation started"},
            status=status.HTTP_202_ACCEPTED
        )
