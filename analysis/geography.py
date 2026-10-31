"""Normalise official NSW LHD labels without changing geographic attribution."""
import re

def join_key(name: str) -> str:
    value = str(name).strip().lower()
    value = re.sub(r"\b(local health district|lhd)\b", "", value, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", value)
