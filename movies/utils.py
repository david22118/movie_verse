from django.core.exceptions import ValidationError


from movies.models import Genre


def get_or_create_genres(selected_genres):
    genre_ids = []
    for genre_code in selected_genres:
        genre, created = Genre.objects.get_or_create(
            name=genre_code,
            defaults={'name': genre_code}
        )
        genre_ids.append(genre.id)
    return genre_ids

def validate_movie_data(title, release_date, director_id, selected_genres, rating, poster):
    if not title or not release_date or not director_id or not selected_genres:
        raise ValidationError("All required fields must be filled.")
    if rating and (int(rating) < 1 or int(rating) > 5):
        raise ValidationError("Rating must be between 1 and 5.")
    if not poster:
        raise ValidationError("Please upload a movie poster.")