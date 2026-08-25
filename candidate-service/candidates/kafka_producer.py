import json
import logging
from kafka import KafkaProducer
from django.conf import settings

logger = logging.getLogger(__name__)
_producer = None

def get_producer():
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
        )
    return _producer

def publish_event(topic: str, key: str, payload: dict):
    try:
        producer = get_producer()
        future = producer.send(topic, key=key, value=payload)
        producer.flush()
        record = future.get(timeout=10)
        logger.info(f"Published → {topic} | partition={record.partition} offset={record.offset}")
    except Exception as e:
        logger.error(f"Kafka publish error on topic {topic}: {e}")
        raise