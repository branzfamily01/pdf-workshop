from __future__ import annotations
from typing import Sequence, TypeVar

T = TypeVar("T")


def imposed_page_numbers(page_count: int) -> list[int]:
    """Physical left-to-right sequence for a standard 2-up saddle booklet.

    Example: 8 -> [8,1,2,7,6,3,4,5]
    """
    if page_count <= 0 or page_count % 4:
        raise ValueError("booklet page_count must be a positive multiple of 4")
    out: list[int] = []
    sheets = page_count // 4
    for s in range(sheets):
        out.extend([
            page_count - 2 * s,
            1 + 2 * s,
            2 + 2 * s,
            page_count - 1 - 2 * s,
        ])
    return out


def deimpose(items: Sequence[T]) -> list[T]:
    """Convert standard booklet physical order back to logical 1..N order."""
    n = len(items)
    if n == 0 or n % 4:
        raise ValueError("item count must be a positive multiple of 4")
    physical_numbers = imposed_page_numbers(n)
    logical: list[T | None] = [None] * n
    for item, logical_num in zip(items, physical_numbers):
        logical[logical_num - 1] = item
    return [x for x in logical if x is not None]
