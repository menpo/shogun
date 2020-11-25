from typing import Any, Container, Dict


def filter_dict(dct: Dict[str, Any], remove_keys: Container[str]) -> Dict[str, Any]:
    return {key: value for key, value in dct.items() if key not in remove_keys}


def remove_dict_nones(dct: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in dct.items() if value is not None}
