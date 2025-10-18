"""
Geode-Explicit Python binding for Section
"""
from __future__ import annotations
import opengeode.bin.opengeode_py_mesh
import opengeode.bin.opengeode_py_model
__all__: list[str] = ['ExplicitSectionLibrary', 'SectionExplicitModeler']
class ExplicitSectionLibrary:
    @staticmethod
    def initialize() -> None:
        ...
class SectionExplicitModeler:
    def __init__(self) -> None:
        ...
    def add_curve(self, arg0: opengeode.bin.opengeode_py_mesh.EdgedCurve2D) -> None:
        ...
    def add_section(self, arg0: opengeode.bin.opengeode_py_model.Section) -> None:
        ...
    def build(self) -> opengeode.bin.opengeode_py_model.Section:
        ...
