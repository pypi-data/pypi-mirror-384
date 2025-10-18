"""Utils for cache."""


def get_cache_key_ares(number: str) -> str:
    """Get cache key for ARES."""
    return f'vvn_ares_{number}'


def get_cache_key_vies(number: str) -> str:
    """Get cache key for VIES."""
    return f'vvn_vies_{number}'
