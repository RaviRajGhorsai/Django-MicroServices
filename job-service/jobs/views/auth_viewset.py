from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework_simplejwt.tokens import RefreshToken

from jobs.serializers.hr_serializer import HRRegisterSerializer, HRProfileSerializer

class HRToken(RefreshToken):
    """
    Adds role='recruiter' to both access and refresh token payloads.
    """
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        # Custom claims — available in both access and refresh token
        token['role']    = 'recruiter'
        token['email']   = user.email
        token['company'] = user.hr_profile.company

        return token

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request: Request):
        serializer = HRRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = HRToken.for_user(user)

        return Response({
            'data': {
                'user':          HRProfileSerializer(user.hr_profile).data,
                'access_token':  str(refresh.access_token),
                'refresh_token': str(refresh),
            },
            'message': 'Registration successful.',
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request: Request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'message': 'username and password are required.',
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request=request, username=username, password=password)

        if not user:
            return Response({
                'message': 'Invalid credentials.',
            }, status=status.HTTP_401_UNAUTHORIZED)

        refresh = HRToken.for_user(user)

        return Response({
            'data': {
                'user':          HRProfileSerializer(user.hr_profile).data,
                'access_token':  str(refresh.access_token),
                'refresh_token': str(refresh),
            },
            'message': 'Login successful.',
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='me',
            permission_classes=[])  # IsAuthenticated from settings kicks in

    def me(self, request: Request):
        """GET /api/auth/me/ — returns the authenticated HR's profile."""
        return Response({
            'data':    HRProfileSerializer(request.user.hr_profile).data,
            'message': 'Profile retrieved successfully.',
        }, status=status.HTTP_200_OK)