from django.urls import path
from .api_views import MovieListAPI, DirectorAPI, MovieCreateAPI, MovieUpdateAPI, MovieDeleteAPI, MovieDetailsAPI, \
    MovieAddCommentAPI, MovieCommentsAPI, MovieDeleteCommentAPI, MovieEditCommentAPI

urlpatterns = [
    path('movie-list/', MovieListAPI.as_view(), name='movie_list_api'),
    path('director/', DirectorAPI.as_view(), name='director_api'),
    path('movie/', MovieCreateAPI.as_view(), name='create_movie_api'),
    path('movie/<int:movie_id>/', MovieUpdateAPI.as_view(), name='edit_movie_api'),
    path('movie/<int:movie_id>/delete/', MovieDeleteAPI.as_view(), name='delete_movie_api'),
    path('movie/<int:movie_id>/details/', MovieDetailsAPI.as_view(), name='movie_details_api'),
    path('movie/<int:movie_id>/comment/', MovieAddCommentAPI.as_view(), name='add_comment_api'),
    path('movie/<int:movie_id>/comments/', MovieCommentsAPI.as_view(), name='movie_comments_api'),
    path('comment/<int:comment_id>/delete/', MovieDeleteCommentAPI.as_view(), name='delete_comment_api'),
    path('comment/<int:comment_id>/edit/', MovieEditCommentAPI.as_view(), name='edit_comment_api'),
]
