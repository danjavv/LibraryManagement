from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import Author, Book, BorrowRecord
from django.utils import timezone

class AuthorTests(APITestCase):
    def setUp(self):
        self.author_data = {
            'name': 'Danish Javed',
            'bio': 'A test author'
        }

    def test_create_author(self):
        url = reverse('author-list')
        response = self.client.post(url, self.author_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Author.objects.count(), 1)
        self.assertEqual(Author.objects.get().name, 'Danish Javed')

    def test_get_author_list(self):
        # Ensure the database is empty before the test
        Author.objects.all().delete()
        
        # Create multiple authors for testing
        author1 = Author.objects.create(name='Danish Javed', bio='A test author')
        author2 = Author.objects.create(name='Jane Smith', bio='Another test author')
        
        url = reverse('author-list')
        response = self.client.get(url)
        
        # Check status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check response data structure
        self.assertIsInstance(response.data['results'], list)  # Adjusted to check 'results' key
        
        # Check the count of authors
        self.assertEqual(len(response.data['results']), 2)  # Adjusted to check 'results' key
        
        # Verify the content of the response
        self.assertEqual(response.data['results'][0]['name'], author1.name)  # Adjusted to check 'results' key
        self.assertEqual(response.data['results'][0]['bio'], author1.bio)  # Adjusted to check 'results' key
        self.assertEqual(response.data['results'][1]['name'], author2.name)  # Adjusted to check 'results' key
        self.assertEqual(response.data['results'][1]['bio'], author2.bio)  # Adjusted to check 'results' key

        # Verify against database count
        self.assertEqual(len(response.data['results']), Author.objects.count())  # Adjusted to check 'results' key

class BookTests(APITestCase):
    def setUp(self):
        self.author = Author.objects.create(name='Jane Doe')
        self.book_data = {
            'title': 'DanishBook',
            'author': self.author.id,
            'isbn': '1234567890123',
            'available_copies': 5
        }

    def test_create_book(self):
        url = reverse('book-list')
        response = self.client.post(url, self.book_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Book.objects.count(), 1)
        self.assertEqual(Book.objects.get().title, 'DanishBook')

    def test_borrow_book(self):
        # First create a book
        book = Book.objects.create(
            title='DanishBook',
            author=self.author,
            isbn='1234567890123',
            available_copies=1
        )

        url = reverse('borrowrecord-list')
        borrow_data = {
            'book': book.id,
            'borrowed_by': 'Test User'
        }

        # Test borrowing
        response = self.client.post(url, borrow_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if available copies were reduced
        book.refresh_from_db()
        self.assertEqual(book.available_copies, 0)

        # Test borrowing when no copies available
        response = self.client.post(url, borrow_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_return_book(self):
        # Create a book
        book = Book.objects.create(
            title='DanishBook',
            author=self.author,
            isbn='1234567890123',
            available_copies=0
        )

        # Create a borrow record
        borrow_record = BorrowRecord.objects.create(
            book=book,
            borrowed_by='Test User'
        )

        # Return the book
        url = reverse('borrowrecord-return-book', args=[borrow_record.id])
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if available copies were increased
        book.refresh_from_db()
        self.assertEqual(book.available_copies, 1)

        # Check if return date was set
        borrow_record.refresh_from_db()
        self.assertIsNotNone(borrow_record.return_date)

class ReportTests(APITestCase):
    def test_generate_report(self):
        url = reverse('reports')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_get_report(self):
        # First generate a report
        url = reverse('reports')
        self.client.post(url)
        
        # Then try to get it
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

       