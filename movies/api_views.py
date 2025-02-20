from django.db import models
from .models import Genre, Comment
from datetime import date
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import FormParser, MultiPartParser
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from django.shortcuts import get_object_or_404
from .models import Movie, Director
from .utils import validate_movie_data, get_or_create_genres
from .serializers import MovieSerializer, DirectorSerializer, CommentSerializer

GENRE_NAME_TO_CODE = {full: code for code, full in Genre.GENRE_CHOICES}


class MovieListAPI(APIView):
    permission_classes = [permissions.AllowAny]  # No restrictions for GET

    @swagger_auto_schema(
        operation_description='Get a list of movies',
        manual_parameters=[
            openapi.Parameter('genre', openapi.IN_QUERY, description="Filter by genre", type=openapi.TYPE_STRING),
            openapi.Parameter('filter', openapi.IN_QUERY, description="Filter by 'popular', 'top_rated', or 'upcoming'",
                              type=openapi.TYPE_STRING),
        ],
        responses={200: MovieSerializer(many=True)},
    )
    def get(self, request):
        movies = Movie.objects.all()
        genre_name = request.GET.get('genre', None)
        filter_type = request.GET.get('filter')

        if genre_name:
            genre_code = GENRE_NAME_TO_CODE.get(genre_name.title())
            if genre_code:
                try:
                    genre = Genre.objects.get(name=genre_code)
                    movies = movies.filter(genres=genre.id)
                except Genre.DoesNotExist:
                    return Response({"error": f"Genre '{genre_name}' not found."}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": f"Genre '{genre_name}' not found."}, status=status.HTTP_400_BAD_REQUEST)

        if filter_type:
            if filter_type == 'popular':
                movies = movies.annotate(comment_count=models.Count('comments')).filter(comment_count__gt=3)
            elif filter_type == 'top_rated':
                movies = movies.filter(rating__gte=3)
            elif filter_type == 'upcoming':
                movies = movies.filter(release_date__gt=date.today())
            else:
                return Response({"error": "Invalid filter. Use 'popular', 'top_rated', or 'upcoming'."},
                                status=status.HTTP_400_BAD_REQUEST)

        serializer = MovieSerializer(movies, many=True)
        return Response(serializer.data)


class DirectorAPI(APIView):

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAdminUser()]

    def get(self, request):
        items = Director.objects.all()
        serializer = DirectorSerializer(items, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_description='Create a New Director (Superusers only)',
        request_body=DirectorSerializer,
        responses={201: DirectorSerializer},
    )
    def post(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can add a new director."}, status=status.HTTP_403_FORBIDDEN)

        serializer = DirectorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MovieCreateAPI(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Create a new movie (Superusers only)",
        manual_parameters=[
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, description="Movie title"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING,
                              description="Movie description"),
            openapi.Parameter('release_date', openapi.IN_FORM, type=openapi.TYPE_STRING, format="date",
                              description="Release date (YYYY-MM-DD)"),
            openapi.Parameter('rating', openapi.IN_FORM, type=openapi.TYPE_NUMBER, description="Movie rating (0-5)"),
            openapi.Parameter('genres', openapi.IN_FORM, type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING),
                              description="List of genre names (e.g., ['Action', 'Comedy'])"),
            openapi.Parameter('director', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description="Director ID"),
            openapi.Parameter('poster', openapi.IN_FORM, type=openapi.TYPE_FILE,
                              description="Movie poster image (optional)"),
        ],
        consumes=["multipart/form-data"],
        responses={201: MovieSerializer, 403: "Forbidden", 400: "Bad Request"},
    )
    def post(self, request):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can add a new movie."}, status=status.HTTP_403_FORBIDDEN)

        data = request.data
        title = data.get('title')
        description = data.get('description', '').strip()
        release_date = data.get('release_date')
        rating = data.get('rating')
        selected_genres = data.getlist('genres')
        director_id = data.get('director')
        poster = request.FILES.get('poster')

        try:
            validate_movie_data(title, release_date, director_id, selected_genres, rating, poster)
            director = get_object_or_404(Director, id=director_id)

            movie = Movie.objects.create(
                title=title,
                description=description,
                release_date=release_date,
                poster=poster,
                rating=rating if rating else None,
                director=director,
            )

            with transaction.atomic():
                genre_ids = get_or_create_genres(selected_genres)
                movie.genres.set(genre_ids)

            serializer = MovieSerializer(movie)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Director.DoesNotExist:
            return Response({"error": "Selected director does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MovieUpdateAPI(APIView):
    permission_classes = [permissions.IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Edit an existing movie (Superusers only)",
        manual_parameters=[
            openapi.Parameter('movie_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Movie ID"),
            openapi.Parameter('title', openapi.IN_FORM, type=openapi.TYPE_STRING, description="Movie title"),
            openapi.Parameter('description', openapi.IN_FORM, type=openapi.TYPE_STRING,
                              description="Movie description"),
            openapi.Parameter('release_date', openapi.IN_FORM, type=openapi.TYPE_STRING, format="date",
                              description="Release date (YYYY-MM-DD)"),
            openapi.Parameter('rating', openapi.IN_FORM, type=openapi.TYPE_NUMBER, description="Movie rating (0-5)"),
            openapi.Parameter('genres', openapi.IN_FORM, type=openapi.TYPE_ARRAY,
                              items=openapi.Items(type=openapi.TYPE_STRING),
                              description="List of genre names (e.g., ['Action', 'Comedy'])"),
            openapi.Parameter('director', openapi.IN_FORM, type=openapi.TYPE_INTEGER, description="Director ID"),
            openapi.Parameter('poster', openapi.IN_FORM, type=openapi.TYPE_FILE,
                              description="Movie poster image (optional)"),
        ],
        consumes=["multipart/form-data"],
        responses={200: MovieSerializer, 403: "Forbidden", 400: "Bad Request", 404: "Not Found"},
    )
    def put(self, request, movie_id):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can edit a movie."}, status=status.HTTP_403_FORBIDDEN)

        movie = get_object_or_404(Movie, id=movie_id)
        data = request.data

        movie.title = data.get('title', movie.title)
        movie.description = data.get('description', movie.description).strip()
        movie.release_date = data.get('release_date', movie.release_date)
        movie.rating = data.get('rating', movie.rating)
        new_poster = request.FILES.get('poster')

        if new_poster:
            movie.poster = new_poster

        director_id = data.get('director', movie.director.id)
        try:
            movie.director = Director.objects.get(id=director_id)
        except Director.DoesNotExist:
            return Response({"error": "Selected director does not exist."}, status=status.HTTP_400_BAD_REQUEST)

        selected_genres = data.getlist('genres')
        if selected_genres:
            with transaction.atomic():
                genre_ids = get_or_create_genres(selected_genres)
                movie.genres.set(genre_ids)

        movie.save()

        serializer = MovieSerializer(movie)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MovieDeleteAPI(APIView):
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Delete an existing movie (Superusers only)",
        manual_parameters=[
            openapi.Parameter('movie_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Movie ID")],
        responses={204: "No Content", 403: "Forbidden", 404: "Not Found"},
    )
    def delete(self, request, movie_id):
        if not request.user.is_superuser:
            return Response({"error": "Only superusers can delete a movie."}, status=status.HTTP_403_FORBIDDEN)

        movie = get_object_or_404(Movie, id=movie_id)
        movie.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MovieDetailsAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get movie details",
        manual_parameters=[
            openapi.Parameter('movie_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Movie ID")],
        responses={200: MovieSerializer},
    )
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        serializer = MovieSerializer(movie)
        return Response(serializer.data)

class MovieCommentsAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Get comments for a movie",
        manual_parameters=[
            openapi.Parameter('movie_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Movie ID")],
        responses={200: CommentSerializer(many=True)},
    )
    def get(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        comments = movie.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

class MovieAddCommentAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Add a comment to a movie",
        manual_parameters=[
            openapi.Parameter('movie_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Movie ID"),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Comment text"),
            },
            required=['content'],
        ),
        responses={201: CommentSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def post(self, request, movie_id):
        movie = get_object_or_404(Movie, id=movie_id)
        content = request.data.get('content')

        if request.user.is_superuser:
            return Response({"error": "Superusers are not allowed to add comments."}, status=status.HTTP_403_FORBIDDEN)

        if not content:
            return Response({"error": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)

        comment = Comment.objects.create(
            movie=movie,
            profile=request.user.profile,
            content=content
        )

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class MovieDeleteCommentAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Delete a comment",
        manual_parameters=[
            openapi.Parameter('comment_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Comment ID"),
        ],
        responses={204: "No Content", 403: "Forbidden", 404: "Not Found"},
    )
    def delete(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.profile.user != request.user:
            return Response({"error": "You are not allowed to delete this comment."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class MovieEditCommentAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Edit a comment",
        manual_parameters=[
            openapi.Parameter('comment_id', openapi.IN_PATH, type=openapi.TYPE_INTEGER, description="Comment ID"),
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'content': openapi.Schema(type=openapi.TYPE_STRING, description="Comment text"),
            },
            required=['content'],
        ),
        responses={200: CommentSerializer, 400: "Bad Request", 403: "Forbidden", 404: "Not Found"},
    )
    def put(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)

        if comment.profile.user != request.user:
            return Response({"error": "You are not allowed to edit this comment."}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content')
        if not content:
            return Response({"error": "Comment text is required."}, status=status.HTTP_400_BAD_REQUEST)

        comment.content = content
        comment.save()

        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_200_OK)
