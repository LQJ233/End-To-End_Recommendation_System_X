"""Hash-based ID -> index mapping shared between training and inference.

Why hashing instead of a learned vocabulary: keeps the on-line path
zero-lookup on unknown users. Unknown ids deterministically map to index 0
which is reserved for ``<UNK>``.
"""
from __future__ import annotations

import hashlib


def hash_id(raw: str | int | None, vocab_size: int) -> int:
    if raw is None or raw == "" or raw == "<UNK>":
        return 0
    s = str(raw)
    h = hashlib.md5(s.encode("utf-8")).hexdigest()
    return 1 + (int(h, 16) % max(1, vocab_size - 1))
