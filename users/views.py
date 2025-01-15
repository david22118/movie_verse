from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import  Profile


def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        additional_info = request.POST.get('additional_info')
        if username and email and password:
            user = User.objects.create_user(username=username, email=email, password=password)
            Profile.objects.create(user=user, additional_info=additional_info)
        return redirect('movie_list')
    else:
        return render(request, 'users/signup.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('movie_list')
        else:
            return render(
                request,
                'users/login.html',
                {'error': 'Invalid username or password'}
            )
    return render(request, 'users/login.html')

def user_logout(request):
    logout(request)
    return redirect('movie_list')
