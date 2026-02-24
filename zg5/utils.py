import re

def waliduj_kod(kod: str) -> bool:
    """Sprawdza czy kod produktu ma format xxx-xxxx-xxx (same cyfry)."""
    pattern = r'^\d{3}-\d{4}-\d{3}$'
    return re.match(pattern, kod) is not None