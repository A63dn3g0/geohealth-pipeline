"""Normalize labels for matching; never infer geographic allocations."""
import re

def join_key(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", re.sub(r"\bLHD\b", "", str(name), flags=re.I).lower())
