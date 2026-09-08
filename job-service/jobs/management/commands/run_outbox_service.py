import json
import time

from django.core.management.base import BaseCommand
from django.utils import timezone
from jobs.models import OutBoxEvent
from kafka import KafkaProducer


class Command(BaseCommand):
    help = "Publishes unpublished outbox events to Kafka"

    def create_producer(self):
        return KafkaProducer(
            bootstrap_servers=["kafka:9092"],
            value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            acks="all",
            retries=5,
        )

    def handle(self, *args, **kwargs):

        producer = None

        while True:

            try:
                # Create/recreate producer if necessary
                if producer is None:
                    self.stdout.write("Connecting to Kafka...")
                    producer = self.create_producer()
                    self.stdout.write("Kafka producer created.")

                events = list(
                    OutBoxEvent.objects.filter(
                        status=OutBoxEvent.Status.PENDING
                    ).order_by("created_at")[:50]
                )

                if not events:
                    time.sleep(2)
                    continue

                for event in events:

                    try:
                        self.stdout.write(
                            f"Publishing event #{event.id}"
                        )

                        future = producer.send(
                            event.topic,
                            key=event.key.encode("utf-8"),
                            value=event.payload,
                        )

                        # Wait for Kafka acknowledgement
                        future.get(timeout=10)

                        event.status = OutBoxEvent.Status.PUBLISHED
                        event.published_at = timezone.now()

                        event.save(
                            update_fields=[
                                "status",
                                "published_at",
                            ]
                        )

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Published event #{event.id}"
                            )
                        )

                    except Exception as exc:

                        self.stderr.write(
                            self.style.ERROR(
                                f"Failed event #{event.id}: {exc}"
                            )
                        )

                        # Producer may be disconnected/broken
                        producer.close()
                        producer = None

                        break

                time.sleep(2)

            except Exception as exc:

                self.stderr.write(
                    self.style.ERROR(
                        f"Outbox worker error: {exc}"
                    )
                )

                if producer:
                    try:
                        producer.close()
                    except Exception:
                        pass

                    producer = None

                time.sleep(5)
