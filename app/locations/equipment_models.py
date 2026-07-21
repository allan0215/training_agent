from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LocationEquipmentRecord:
    location_id: int
    equipment_id: int
    equipment_code: str
    quantity: int | None
    minimum_weight: float | None
    maximum_weight: float | None
    weight_unit: str | None
    notes: str | None
