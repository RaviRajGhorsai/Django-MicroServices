from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from jobs.models import HRProfile


class HRRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    company  = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'password', 'company']

    def create(self, validated_data):
        company = validated_data.pop('company')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
        )
        HRProfile.objects.create(user=user, company=company)
        return user


class HRProfileSerializer(serializers.ModelSerializer):
    email    = serializers.EmailField(source='user.email')
    username = serializers.CharField(source='user.username')

    class Meta:
        model  = HRProfile
        fields = ['id', 'email', 'username', 'company', 'created_at']