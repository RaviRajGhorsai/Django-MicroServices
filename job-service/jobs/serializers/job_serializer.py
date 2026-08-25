from rest_framework import serializers
from jobs.models import Job


class JobSerializer(serializers.ModelSerializer):
    """
    Standard ModelSerializer for Job model.
    """
    class Meta:
        model = Job
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
