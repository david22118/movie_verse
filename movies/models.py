from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import Profile


class Genre(models.Model):
    GENRE_CHOICES = [
        ('ACT', 'Action'),
        ('COM', 'Comedy'),
        ('DRM', 'Drama'),
        ('HOR', 'Horror'),
        ('SCI', 'Science Fiction'),
        ('ROM', 'Romance'),
        ('ANI', 'Animation'),
        ('THR', 'Thriller'),
        ('FNT', 'Fantasy'),
        ('DOC', 'Documentary'),
        ('ADV', 'Adventure'),
        ('MUS', 'Musical'),
    ]
    name = models.CharField(max_length=4, choices=GENRE_CHOICES, unique=True)

    def __str__(self):
        return self.get_name_display()


class Director(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    birth_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Movie(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=255, blank=True, null=True)
    release_date = models.DateField()
    poster = models.ImageField(upload_to='posters/', blank=True, null=True)
    rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    genres = models.ManyToManyField(Genre, related_name='movies')
    director = models.ForeignKey(Director, on_delete=models.CASCADE, related_name='movies')

    @property
    def comments_count(self):
        return self.comments.count()

    def __str__(self):
        return self.title


class Comment(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='comments')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(max_length=255)

    def __str__(self):
        return f'{self.profile.user.username} - {self.movie.title}'
