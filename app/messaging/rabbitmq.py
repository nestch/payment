import json
import os
import time
from typing import Any

import pika

from app.config import settings


def _connection_parameters() -> pika.ConnectionParameters:
    return pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_pass),
        heartbeat=30,
        blocked_connection_timeout=30,
        connection_attempts=5,
        retry_delay=3,
        socket_timeout=10,
    )


def get_connection() -> pika.BlockingConnection:
    return pika.BlockingConnection(_connection_parameters())


def ensure_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    channel.exchange_declare(exchange=settings.rabbitmq_exchange, exchange_type="direct", durable=True)

    channel.queue_declare(
        queue=settings.rabbitmq_queue,
        durable=True,
        arguments={
            "x-dead-letter-exchange": settings.rabbitmq_exchange,
            "x-dead-letter-routing-key": settings.rabbitmq_dlq,
        },
    )
    channel.queue_bind(
        exchange=settings.rabbitmq_exchange,
        queue=settings.rabbitmq_queue,
        routing_key=settings.rabbitmq_queue,
    )

    channel.queue_declare(queue=settings.rabbitmq_dlq, durable=True)
    channel.queue_bind(
        exchange=settings.rabbitmq_exchange,
        queue=settings.rabbitmq_dlq,
        routing_key=settings.rabbitmq_dlq,
    )


def publish_message(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    routing_key: str,
    payload: dict[str, Any],
    message_id: str,
    correlation_id: str,
) -> None:
    channel.basic_publish(
        exchange=settings.rabbitmq_exchange,
        routing_key=routing_key,
        body=json.dumps(payload).encode("utf-8"),
        properties=pika.BasicProperties(
            delivery_mode=2,
            content_type="application/json",
            message_id=message_id,
            correlation_id=correlation_id,
            timestamp=int(time.time()),
        ),
        mandatory=False,
    )


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}
