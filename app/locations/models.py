from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocationRecord:
    id: int
    user_id: int
    name: str
    location_type: str
    notes: str | None
    is_active: bool
    created_at: str
    updated_at: str
