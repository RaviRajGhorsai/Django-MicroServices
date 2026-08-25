from rest_framework import serializers
from candidates.models import JobApplication


class JobApplicationSerializer(serializers.ModelSerializer):
    """
    Serializer for the JobApplication model.
    """
    class Meta:
        model = JobApplication
        fields = [
            'id',
            'candidate',
            'job_id',
            'job_title',
            'job_company',
            'job_location',
            'cover_letter',
            'status',
            'applied_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'applied_at', 'updated_at']

    def validate_status(self, value):
        valid_statuses = [choice[0] for choice in JobApplication.STATUS_CHOICES]
        if value not in valid_statuses:
            raise serializers.ValidationError(
                f"Invalid status '{value}'. Choice must be one of {valid_statuses}."
            )
        return value

    def validate(self, attrs):
        candidate = attrs.get('candidate') or (self.instance.candidate if self.instance else None)
        job_id = attrs.get('job_id') or (self.instance.job_id if self.instance else None)

        if candidate and job_id:
            qs = JobApplication.objects.filter(candidate=candidate, job_id=job_id)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    {"non_field_errors": ["Candidate has already applied for this job."]}
                )
        return attrs

