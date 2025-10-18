"""
Dictionary utilities for opticedge_cloud_utils package
"""

def deep_merge(base: dict, updates: dict, delete_nulls: bool = True) -> dict:
    """
    Recursively merge two dictionaries.
    
    Args:
        base (dict): Original dictionary.
        updates (dict): Updates to merge into the base.
        delete_nulls (bool): If True, remove keys with value None in updates.

    Returns:
        dict: A new dictionary with updates merged into base.
    """
    result = base.copy()
    for k, v in updates.items():
        if delete_nulls and v is None:
            result.pop(k, None)
        elif isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v, delete_nulls)
        else:
            result[k] = v
    return result
