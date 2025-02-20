from django.urls import path
from .views import movie_list,  add_movie, add_director, movie_info, delete_comment, edit_comment, delete_movie

urlpatterns = [
    path('', movie_list, name='movie_list'),
    path('add_movie/', add_movie, name='add_movie'),
    path('add-director/', add_director, name='add_director'),
    path('movie/<int:movie_id>/', movie_info, name='movie_info'),
    path('movie/<int:movie_id>/delete/', delete_movie, name='delete_movie'),
    path('comment/<int:comment_id>/delete/', delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/edit/', edit_comment, name='edit_comment'),
]
