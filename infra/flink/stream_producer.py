"""KappaLake streaming producer: emits faker user records to Redpanda topic 'users'."""
import json
import os
import time

from faker import Faker
from kafka import KafkaProducer

REDPANDA_BOOTSTRAP = os.getenv("REDPANDA_BOOTSTRAP", "redpanda:29092")
TOPIC = "users"
INTERVAL_SECONDS = float(os.getenv("STREAM_INTERVAL_SECONDS", "10"))

fake = Faker()


def make_record():
    return {
        "id": fake.random_int(min=100000, max=999999),
        "name": fake.name(),
        "email": fake.email(),
        "age": fake.random_int(min=18, max=80),
        "gender": fake.random_element(elements=("Male", "Female", "Non-binary")),
        "nationality": fake.country(),
        "language": fake.language_name(),
        "occupation": fake.job(),
        "created_at": fake.iso8601(),
    }


def main():
    print(f"Connecting to Redpanda at {REDPANDA_BOOTSTRAP}, topic '{TOPIC}'")
    producer = KafkaProducer(
        bootstrap_servers=REDPANDA_BOOTSTRAP,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )
    while True:
        record = make_record()
        producer.send(TOPIC, value=record)
        producer.flush()
        print(f"Produced {record['id']}")
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
