import json
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer

from config.database import logs_collection


class Command(BaseCommand):
    help = "kafka consumer - logging-service"

    def handle(self, *args, **kwargs):
        consumer = KafkaConsumer(
            "application-logs",
            bootstrap_servers=["kafka:9092"],
            group_id="logging-service",
            value_deserializer=lambda value: json.loads(value.decode("utf-8")),
        )

        print("Logging service started...")

        for message in consumer:
            log = message.value

            print("Received:", log)

            try:
                result = logs_collection.insert_one(log)
                print(f"MongoDB inserted: {result.inserted_id}")
            except Exception as e:
                print(f"MongoDB insert failed: {e}")
