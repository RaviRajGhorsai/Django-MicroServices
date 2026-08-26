from rest_framework import serializers
from jobs.models import Application


class ApplicationSerializer(serializers.ModelSerializer):

    # Expose nested candidate info cleanly in API responses
    candidate_name  = serializers.SerializerMethodField()
    candidate_email = serializers.SerializerMethodField()
    candidate_skills = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            'id', 'job', 'candidate_id', 'candidate_data',
            'candidate_name', 'candidate_email', 'candidate_skills',
            'cover_letter', 'status', 'applied_at', 
        ]
        read_only_fields = [
            'candidate_data', 'status', 'applied_at',
        ]

    def get_candidate_name(self, obj):
        return obj.candidate_data.get('name', '')

    def get_candidate_email(self, obj):
        return obj.candidate_data.get('email', '')

    def get_candidate_skills(self, obj):
        return obj.candidate_data.get('skills', [])