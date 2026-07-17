import datetime

from rest_framework import serializers
from books.models import Book, Author, Comment, Genre


class AuthorByNameField(serializers.Field):
    def to_internal_value(self, data):
        if not isinstance(data, str) or not data.strip():
            raise serializers.ValidationError('Error name')
        author = Author.objects.filter(name__iexact=data).first()
        if not author:
            author = Author.objects.create(name=data)
        return author

    def to_representation(self, value):
        return value.slug
    

class BookSerializer(serializers.ModelSerializer):
    author = AuthorByNameField()
    genre = serializers.PrimaryKeyRelatedField(many=True, queryset=Genre.objects.all())

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'genre', 'description', 'year', 'book_file', 'book_avatar', 'posted_by', 'is_published']
        read_only_fields = ['posted_by']  

    def get_fields(self):
        fields = super().get_fields()

        if isinstance(self.instance, Book):
                for field_name in fields:
                    if field_name != 'is_published':
                        fields[field_name].read_only = True
                if self.instance.is_published:
                    fields['is_published'].read_only = True
        return fields
    
    def validate(self, attrs):
        if self.instance is not None and self.instance.is_published:
            raise serializers.ValidationError(
                {'is_published': 'Книга уже опубликована, повторная публикация недоступна.'}
            )
        return attrs
    def validate_year(self, value):
        current_year = datetime.datetime.now().year
        if value < -10000 or value > current_year:
            raise serializers.ValidationError('Ошибка указания года')
        return value
    
    
class NewestBooksQuerySerializer(serializers.Serializer):
    number = serializers.IntegerField(required=False, default=5, min_value=1, max_value=50)


class AuthorsListSerializer(serializers.ModelSerializer):
    books_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Author
        fields = ['name','slug','author_description', 'books_count']


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'book', 'user', 'text']
        read_only_fields = ['user']

