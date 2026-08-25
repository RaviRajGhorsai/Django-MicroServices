import json, logging
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Kafka consumer — candidate-service'

    def handle(self, *args, **kwargs):
        consumer = KafkaConsumer(
            'job.created',
            'job.updated',
            'application.status_updated',
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id='candidate-service-group',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )
        self.stdout.write('[candidate-consumer] Running...')
        for message in consumer:
            self.dispatch(message.value)

    def dispatch(self, event: dict):
        etype = event.get('event_type')
        if etype == 'job.created':
            self.on_job_created(event)
        elif etype == 'job.updated' and event.get('status') == 'closed':
            self.on_job_closed(event)
        elif etype == 'application.status_updated':
            self.on_status_updated(event)

    def on_job_created(self, event: dict):
        from candidates.models import Candidate
        from candidates.tasks import send_job_match_notification
        job_skills = set(event.get('skills_required', []))
        for candidate in Candidate.objects.all():
            overlap = job_skills & set(candidate.skills)
            if overlap:
                send_job_match_notification.delay(
                    candidate_id=candidate.id,
                    candidate_email=candidate.email,
                    job_title=event['title'],
                    matched_skills=list(overlap),
                )

    def on_job_closed(self, event: dict):
        from candidates.models import JobApplication
        JobApplication.objects.filter(
            job_id=event['job_id'], status='pending'
        ).update(status='rejected')

    def on_status_updated(self, event: dict):
        from candidates.models import JobApplication
        JobApplication.objects.filter(
            job_id=event['job_id'],
            candidate_id=event['candidate_id'],
        ).update(status=event['new_status'])