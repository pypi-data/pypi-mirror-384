"""Shared async Kafka producer for EmpowerNow platform.

Usage
-----
from empowernow_common.kafka.platform_producer import publish, publish_structured

await publish("crud.operations", key="user:123", value={...})
await publish_structured("crud.create", payload={...})

The producer is lazily initialised once per process. If ``aiokafka`` is missing
or ``KAFKA_ENABLED=false``, all functions become no-ops so external users are
not forced to install Kafka dependencies.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any, Optional

try:
    from aiokafka import AIOKafkaProducer  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    AIOKafkaProducer = None  # type: ignore

logger = logging.getLogger(__name__)

KAFKA_ENABLED = os.getenv("KAFKA_ENABLED", "true").lower() in {"1", "true", "yes"}
BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
CLIENT_ID = os.getenv("KAFKA_CLIENT_ID", "platform-producer")
SERVICE_NAME = os.getenv("SERVICE_NAME", os.getenv("HOSTNAME", "unknown-service"))

# ---------------------------------------------------------------------------
# Lazy singleton
# ---------------------------------------------------------------------------
_producer: Optional["AIOKafkaProducer"] = None
_start_lock = asyncio.Lock()


async def _ensure_producer() -> Optional["AIOKafkaProducer"]:
    """Start producer on first use; safe for concurrent awaits."""
    global _producer
    if _producer or not KAFKA_ENABLED or AIOKafkaProducer is None:
        return _producer
    async with _start_lock:
        if _producer:  # pragma: no cover – race resolved
            return _producer
        try:
            _producer = AIOKafkaProducer(
                bootstrap_servers=BOOTSTRAP,
                client_id=CLIENT_ID,
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode(),
                key_serializer=lambda k: (
                    None if k is None
                    else k if isinstance(k, bytes)
                    else k.encode("utf-8") if isinstance(k, str)
                    else str(k).encode("utf-8")
                ),
            )
            await _producer.start()
            logger.info("Platform Kafka producer connected (%s)", ",".join(BOOTSTRAP))
        except Exception as exc:
            logger.error("Failed to start platform Kafka producer: %s", exc)
            _producer = None
        return _producer


async def publish(topic: str, key: str | None, value: Any) -> None:  # noqa: D401
    """Publish *value* to *topic* using *key*.

    Returns immediately (no-op) only if KAFKA_ENABLED=false or if Kafka is unavailable or publish fails.
    """
    if not KAFKA_ENABLED:
        return

    producer = await _ensure_producer()
    if producer is None:
        error_msg = f"Kafka producer unavailable - cannot publish to {topic}"
        logger.error(error_msg)
        return

    try:
        await producer.send_and_wait(topic, key=key, value=value)
    except Exception as exc:
        logger.error("Kafka publish failed: topic=%s, key=%s, error=%s", topic, key, exc)


async def publish_structured(event_type: str, payload: dict, *, topic: str | None = None, key: str | None = None) -> None:
    """Publish a structured event with a standard envelope."""
    envelope = {
        "event_id": uuid.uuid4().hex,
        "event_type": event_type,
        "service": SERVICE_NAME,
        "ts": time.time(),
        "payload": payload,
    }
    await publish(topic or event_type.split(".")[0], key, envelope)


async def shutdown():  # pragma: no cover
    """Gracefully stop the global producer (for ASGI lifespan hooks)."""
    global _producer
    if _producer:
        try:
            await _producer.stop()
        finally:
            _producer = None 