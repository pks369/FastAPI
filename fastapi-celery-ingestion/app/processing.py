from __future__ import annotations
from datetime import datetime
from typing import Any, Tuple
from app.utils import idempotency_key

# Normalization returns: (entity_dict, external_id)

def normalize(provider: str, raw: dict) -> Tuple[dict, str]:
    if provider == "jsonplaceholder":
        external_id = str(raw["id"])  # required
        name = str(raw.get("title") or "Untitled")
        amt = None
        currency = None
        event_time = datetime.utcnow()
        derived = len(name)
    elif provider == "dummyjson":
        external_id = str(raw["id"])  # required
        name = str(raw.get("title") or "Unknown Product")
        amt = int(raw.get("price") or 0)
        currency = "USD"
        event_time = datetime.utcnow()
        derived = int(raw.get("rating") or 0)
    elif provider == "reqres":
        external_id = str(raw["id"])  # required
        name = f"{raw.get('first_name','')} {raw.get('last_name','')}".strip() or "Unknown User"
        amt = None
        currency = None
        event_time = datetime.utcnow()
        derived = len(name)
    else:
        raise ValueError(f"unknown provider: {provider}")

    entity = {
        "provider": provider,
        "external_id": external_id,
        "idempotency_key": idempotency_key(provider, external_id),
        "name": name,
        "currency": currency,
        "amount": amt,
        "event_time": event_time,
        "derived_score": derived,
    }
    return entity, external_id
