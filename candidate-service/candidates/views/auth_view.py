from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.request import Request

from rest_framework_simplejwt.tokens import RefreshToken

from candidates.serializers.candidate_serializer import CandidateRegisterSerializer, CandidateDetailSerializer

class CandidateToken(RefreshToken):
    """
    Adds role='candidate' to both access and refresh token payloads.
    """
    @classmethod
    def for_user(cls, user):
        token = super().for_user(user)

        # Custom claims — available in both access and refresh token
        token['role']    = 'candidate'
        token['email']   = user.email

        return token

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'])
    def register(self, request: Request):
        serializer = CandidateRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = CandidateToken.for_user(user)

        return Response({
            'data': {
                'user':          CandidateDetailSerializer(user.candidate_profile).data,
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

        refresh = CandidateToken.for_user(user)

        return Response({
            'data': {
                'user':          CandidateDetailSerializer(user.candidate_profile).data,
                'access_token':  str(refresh.access_token),
                'refresh_token': str(refresh),
            },
            'message': 'Login successful.',
        }, status=status.HTTP_200_OK)
         