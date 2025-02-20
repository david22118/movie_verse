from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from urllib.parse import unquote
from .forms import CommentForm
from .models import Genre, Director, Movie, Comment
from datetime import date
from django.db import models

from .utils import get_or_create_genres, validate_movie_data


def movie_list(request):
    genre_id = request.GET.get('genre', None)
    filter_option = request.GET.get('filter', None)
    movies = Movie.objects.all()

    if genre_id:
        movies = movies.filter(genres__id=genre_id)

    if filter_option == 'popular':
        movies = movies.annotate(comment_count=models.Count('comments')).filter(comment_count__gt=3)
    elif filter_option == 'top_rated':
        movies = movies.filter(rating__gte=3)
    elif filter_option == 'upcoming':
        movies = movies.filter(release_date__gt=date.today())

    genres = Genre.objects.all()

    return render(request, 'movies/movie_list.html',
                  {'movies': movies, 'filter_option': filter_option, 'genres': genres,
                   'selected_genre': genre_id, })


def add_director(request):
    form_data = {
        'title': unquote(request.GET.get('title', '')),
        'description': unquote(request.GET.get('description', '')),
        'release_date': unquote(request.GET.get('release_date', '')),
        'rating': unquote(request.GET.get('rating', '')),
        'genres': [unquote(genre) for genre in request.GET.getlist('genres')],
        'director': unquote(request.GET.get('director', '')),
        'edit_mode': unquote(request.GET.get('edit_mode', 'false')),
        'movie_id': unquote(request.GET.get('movie_id', '')),
    }

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        birth_date = request.POST.get('birth_date')

        # Create a new director
        Director.objects.create(first_name=first_name, last_name=last_name, birth_date=birth_date)
        redirect_url = (
            f"{reverse('add_movie')}?title={form_data['title']}"
            f"&description={form_data['description']}"
            f"&release_date={form_data['release_date']}"
            f"&rating={form_data['rating']}"
            f"&genres={','.join(form_data['genres'])}"
            f"&director={form_data['director']}"
            f"&edit_mode={form_data['edit_mode']}"
            f"&movie_id={form_data['movie_id']}"
        )
        return redirect(redirect_url)

    return render(request, 'movies/add_director.html', {'pre_filled_data': form_data})


def add_movie(request):
    genres = Genre.GENRE_CHOICES
    directors = Director.objects.all()
    movie_id = request.GET.get('movie_id')
    edit_mode = request.GET.get('edit_mode', 'false').lower() in ('true', '1', 'yes')
    pre_filled_data = {}

    if edit_mode and movie_id:
        movie = get_object_or_404(Movie, id=movie_id)
        pre_filled_data = {
            'title': request.GET.get('title', movie.title) or movie.title,
            'description': request.GET.get('description', movie.description).strip() or movie.description.strip(),
            'release_date': request.GET.get('release_date', movie.release_date) or movie.release_date,
            'rating': request.GET.get('rating', movie.rating) or movie.rating,
            'genres': request.GET.get('genres', ','.join([genre.name for genre in movie.genres.all()])).split(',') or [
                genre.name for genre in movie.genres.all()],
            'director': request.GET.get('director', movie.director.id) or movie.director.id,
            'movie_id': movie.id,
            'edit_mode': edit_mode,
        }
    else:
        pre_filled_data = {
            'title': request.GET.get('title', ''),
            'description': request.GET.get('description', '').strip(),
            'release_date': request.GET.get('release_date', ''),
            'rating': request.GET.get('rating', ''),
            'genres': request.GET.get('genres', '').split(','),
            'director': request.GET.get('director', ''),
        }

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        release_date = request.POST.get('release_date')
        poster = request.FILES.get('poster')
        rating = request.POST.get('rating')
        selected_genres = request.POST.getlist('genres')
        director_id = request.POST.get('director')

        try:
            validate_movie_data(title, release_date, director_id, selected_genres, rating, poster)
            director = Director.objects.get(id=director_id)

            if edit_mode and movie_id:
                # Update existing movie
                movie = get_object_or_404(Movie, id=movie_id)
                movie.title = title
                movie.description = description
                movie.release_date = release_date
                if poster:  # Update poster only if provided
                    movie.poster = poster
                movie.rating = rating if rating else None
                movie.director = director
                movie.save()

                # Update genres
                with transaction.atomic():
                    genre_ids = get_or_create_genres(selected_genres)
                    movie.genres.set(genre_ids)
            else:
                # Create a new movie
                movie = create_movie(title, description, release_date, poster, rating, director)
                with transaction.atomic():
                    genre_ids = get_or_create_genres(selected_genres)
                    movie.genres.set(genre_ids)

            return redirect('movie_info', movie_id=movie.id)

        except ValidationError as e:
            error = str(e.message)
        except Director.DoesNotExist:
            error = "Selected director does not exist."
        except Exception as e:
            error = "An unexpected error occurred. Please try again."

        return render(request, 'movies/add_movie.html', {
            'genres': genres,
            'directors': directors,
            'pre_filled_data': pre_filled_data,
            'error': error,
            'edit_mode': edit_mode,
        })

    return render(request, 'movies/add_movie.html', {
        'genres': genres,
        'directors': directors,
        'pre_filled_data': pre_filled_data,
        'edit_mode': edit_mode,
    })


def create_movie(title, description, release_date, poster, rating, director):
    return Movie.objects.create(
        title=title,
        description=description,
        release_date=release_date,
        poster=poster,
        rating=rating if rating else None,
        director=director,
    )


def movie_info(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    comments = movie.comments.all()

    # Handle comment submission
    if request.method == 'POST' and request.user.is_authenticated:
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.movie = movie
            comment.profile = request.user.profile
            comment.save()
            return redirect('movie_info', movie_id=movie.id)
    else:
        form = CommentForm()

    return render(request, 'movies/movie_info.html', {
        'movie': movie,
        'comments': comments,
        'form': form,
        'is_superuser': request.user.is_superuser,
    })


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.profile.user != request.user:
        return HttpResponseForbidden("You are not allowed to delete this comment.")

    comment.delete()

    return redirect('movie_info', movie_id=comment.movie.id)


def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.profile.user != request.user:
        return HttpResponseForbidden("You are not allowed to edit this comment.")

    if request.method == 'POST':
        new_content = request.POST.get('content', '').strip()

        if new_content:
            comment.content = new_content
            comment.save()
            return redirect('movie_info', movie_id=comment.movie.id)
        else:
            return HttpResponseForbidden("Comment content cannot be empty.")

    return redirect('movie_info', movie_id=comment.movie.id)


def delete_movie(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)

    if not request.user.is_authenticated or not request.user.is_superuser:
        return HttpResponseForbidden("You are not allowed to delete this movie.")
    movie.delete()

    return redirect('movie_list')
