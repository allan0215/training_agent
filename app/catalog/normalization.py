from __future__ import annotations


def normalize_alias(value: str) -> str:
    """
    운동명과 별칭 비교를 위한 정규화.

    - 앞뒤 공백 제거
    - 영문 대소문자 통일
    - 연속된 공백 하나로 통일
    """
    return " ".join(
        value.strip().casefold().split()
    )


def detect_language(value: str) -> str:
    for character in value:
        if "\uac00" <= character <= "\ud7a3":
            return "ko"

    return "en"
