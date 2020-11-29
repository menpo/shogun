import sys
from distutils.version import StrictVersion
from typing import Any, Container, Dict, Mapping

PY_VER = StrictVersion(f"{sys.version_info.major}.{sys.version_info.minor}")


IS_PYTHON_36 = PY_VER == StrictVersion("3.6")
IS_PYTHON_37 = PY_VER == StrictVersion("3.7")
IS_GT_PYTHON_38 = PY_VER >= StrictVersion("3.8")


def filter_dict(dct: Mapping[str, Any], remove_keys: Container[str]) -> Dict[str, Any]:
    return {key: value for key, value in dct.items() if key not in remove_keys}


def remove_dict_nones(dct: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in dct.items() if value is not None}
