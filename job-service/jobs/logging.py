import logging
from jobs.kafka_producer import get_producer


class KafkaLogHandler(logging.Handler):
    def emit(self, record):

        try:
            producer = get_producer()

            payload = {
                "service": "jobs-service",
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
            print(payload)

        except Exception:
            self.handleError(record)
