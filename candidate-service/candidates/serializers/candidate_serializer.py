from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from candidates.models import Candidate


class CandidateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for the Candidate model, including User creation.
    """
    
    class Meta:
        model = Candidate
        fields = [
            'id',
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


class CandidateRegisterSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
        )

        Candidate.objects.create(
            user=user,
            name=user.username,
        )

        return user

class CandidateDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "name",
            "email",
            "phone",
            "skills",
            "experience_years",
            "location",
            "resume_text",
            "created_at",
            "updated_at",
        ]