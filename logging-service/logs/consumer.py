import json

from kafka import KafkaConsumer

from database import logs_collection

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
