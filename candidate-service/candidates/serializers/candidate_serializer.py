from rest_framework import serializers
from candidates.models import Candidate


class CandidateSerializer(serializers.ModelSerializer):
    """
    Serializer for the Candidate model.
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
