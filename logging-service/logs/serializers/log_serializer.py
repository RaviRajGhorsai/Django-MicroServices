from rest_framework import serializers


class LogSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    service = serializers.CharField()
    level = serializers.CharField()
    logger = serializers.CharField()
    message = serializers.CharField()
    timestamp = serializers.FloatField()
