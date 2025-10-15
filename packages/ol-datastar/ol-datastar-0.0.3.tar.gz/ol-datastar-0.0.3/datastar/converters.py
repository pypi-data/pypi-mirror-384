"""Utility functions for mapping Python-native structures to API payloads and back."""

from __future__ import annotations

from typing import Dict, Iterable, List, Tuple


def mapping_tuples_to_json(
    mapping: Iterable[Tuple[str, str]],
) -> List[Dict[str, str]]:

    assert mapping is not None

    return [
        {"sourceColumn": str(source), "targetColumn": str(target)}
        for source, target in mapping
    ]


def mapping_json_to_tuples(payload: Iterable[Dict[str, str]]) -> List[Tuple[str, str]]:

    return [(entry["sourceColumn"], entry["targetColumn"]) for entry in payload]
