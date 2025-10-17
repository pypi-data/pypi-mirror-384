"""
OpenGeode Python binding for gdal
"""
from __future__ import annotations
__all__: list[str] = ['initialize_gdal', 'ostream_redirect']
class ostream_redirect:
    def __enter__(self) -> None:
        ...
    def __exit__(self, *args) -> None:
        ...
    def __init__(self, stdout: bool = True, stderr: bool = True) -> None:
        ...
def initialize_gdal() -> None:
    ...
