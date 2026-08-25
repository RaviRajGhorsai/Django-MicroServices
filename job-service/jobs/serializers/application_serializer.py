from rest_framework import serializers
from jobs.models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    """
    Standard ModelSerializer for Application model.
    """
    class Meta:
        model = Application
        fields = '__all__'
        read_only_fields = ['id', 'applied_at']
