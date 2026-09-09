import logging
from candidates.kafka_producer import get_producer


class KafkaLogHandler(logging.Handler):
    def emit(self, record):

        try:
            producer = get_producer()

            payload = {
                "service": "candidate-service",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "timestamp": record.created,
            }

            producer.send(
                "application-logs",
                value=payload,
            )

            print("logging applications done")

        except Exception as e:
            print(f"Kafka logging failed: {e}")
