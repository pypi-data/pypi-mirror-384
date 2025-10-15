from __future__ import annotations

from importlib import import_module
from typing import Union

_native = import_module("pf_bindings_python")


def verify_bet(receipt_json: str, transcript_json: str) -> None:
    _native.verify_bet(receipt_json, transcript_json)


def register_gdp_package(bytes_like: Union[bytes, bytearray, memoryview]) -> None:
    _native.register_gdp_package(bytes(bytes_like))
