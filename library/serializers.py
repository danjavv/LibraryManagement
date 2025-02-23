from rest_framework import serializers
from .models import Author, Book, BorrowRecord

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'available_copies', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def validate_isbn(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("ISBN must contain only digits")
        if len(value) != 13:
            raise serializers.ValidationError("ISBN must be 13 digits long")
        return value

class BorrowRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = BorrowRecord
        fields = ['id', 'book', 'borrowed_by', 'borrow_date', 'return_date', 'created_at', 'updated_at']
        read_only_fields = ['borrow_date', 'created_at', 'updated_at']