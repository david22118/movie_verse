from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from drf_yasg import openapi
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from drf_yasg.utils import swagger_auto_schema

from .models import Profile
from .serializers import ProfileSerializer


class SignupAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="New user registration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="username"),
                'password': openapi.Schema(type=openapi.FORMAT_PASSWORD, description="password"),
                'email': openapi.Schema(type=openapi.FORMAT_EMAIL, description="email"),
                'additional_info': openapi.Schema(type=openapi.TYPE_STRING, description="additional_info"),
            },
            required=['username', 'password', 'email'],
        ),
        responses={201: ProfileSerializer, 400: "Bad Request", 404: "Not Found"},
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        additional_info = request.data.get('additional_info')
        if not username or not password:
            return Response({"error": "Username and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            profile = Profile.objects.create(user=user, additional_info=additional_info)
            serializer = ProfileSerializer(profile)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({"error": "Username or email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginAPI(APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="User login",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="username"),
                'password': openapi.Schema(type=openapi.FORMAT_PASSWORD, description="password"),
            },
            required=['username', 'password'],
        ),
        responses={200: "Login successful", 401: "Unauthorized"},
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = User.objects.filter(username=username).first()
        if user:
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return Response({"message": "Login successful."}, status=status.HTTP_200_OK)
        return Response({"error": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutAPI(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="User logout",
        responses={200: "Logout successful", 401: "Unauthorized"},
    )
    def post(self, request):
        try:
            logout(request)
            return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)
