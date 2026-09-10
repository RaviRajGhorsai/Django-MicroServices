import json, logging
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer
from django.conf import settings
from jobs.websockets.helper import send_websocket_notification


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Kafka consumer — job-service"

    def handle(self, *args, **kwargs):
        consumer = KafkaConsumer(
            "application.submitted",
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="job-service-group",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        self.stdout.write("[job-consumer] Running...")
        for message in consumer:
            self.dispatch(message.value)

    def dispatch(self, event: dict):
        etype = event.get("event_type")
        if etype == "application.submitted":
            self.on_application_submitted(event)

    def on_application_submitted(self, event: dict):
        from jobs.models import Application
        from jobs.tasks import (
            index_application_in_opensearch,
            send_application_notification,
        )

        logger.info(
            "Application submission event received",
            extra={
                "job_id": event["job_id"],
                "candidate_id": event["candidate_id"],
            },
        )

        application, created = Application.objects.get_or_create(
            job_id=event["job_id"],
            candidate_id=event["candidate_id"],
            defaults={
                "candidate_data": event.get("candidate_data", {}),  # ← single field
                "cover_letter": event.get("cover_letter", ""),
            },
        )
        if created:
            logger.info(
                "Application created successfully",
                extra={
                    "application_id": application.id,
                    "job_id": event["job_id"],
                    "candidate_id": event["candidate_id"],
                },
            )

            index_application_in_opensearch.delay(application.id)
            send_application_notification.delay(
                job_id=event["job_id"],
                candidate_name=event["candidate_data"].get("name", ""),
                candidate_email=event["candidate_data"].get("email", ""),
            )
            
            print("kafka consumer ok event received.")
            print(f"Posted BY: {application.job.posted_by.id}")
            send_websocket_notification(
                application.job.posted_by.id,
                {
                    "type": "Application Submitted",
                    "message": f"New application submitted from {event['candidate_data'].get('name', '')}",
                    "job_id": event["job_id"],
                    "job_title": event["job_title"],
                    "data": None,
                },
            )
