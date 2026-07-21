from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MovementPatternSpec:
    code: str
    role: str = "primary"
    contribution_weight: float = 1.0


@dataclass(frozen=True)
class ExerciseCreateRequest:
    canonical_name: str
    korean_name: str | None
    category: str
    default_block_type: str

    catalog_scope: str = "personal"

    aliases: tuple[str, ...] = field(
        default_factory=tuple
    )

    movement_patterns: tuple[
        MovementPatternSpec,
        ...
    ] = field(default_factory=tuple)

    equipment_codes: tuple[str, ...] = field(
        default_factory=tuple
    )

    parent_exercise_id: int | None = None
    notes: str | None = None
