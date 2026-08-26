from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from candidates.models import Candidate


class CandidateSerializer(serializers.ModelSerializer):
    """
    Serializer for the Candidate model, including User creation.
    """
    username = serializers.CharField(write_only=True, required=False)
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    
    class Meta:
        model = Candidate
        fields = [
            'id',
            'username',
            'password',
            'name',
            'email',
            'phone',
            'skills',
            'experience_years',
            'location',
            'resume_text',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_experience_years(self, value):
        if value < 0:
            raise serializers.ValidationError("Experience years cannot be negative.")
        return value

    def validate_skills(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list.")
        return value

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        email = validated_data.get('email')

        user = None
        if username and password:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
            )

        candidate = Candidate.objects.create(user=user, **validated_data)
        return candidate
