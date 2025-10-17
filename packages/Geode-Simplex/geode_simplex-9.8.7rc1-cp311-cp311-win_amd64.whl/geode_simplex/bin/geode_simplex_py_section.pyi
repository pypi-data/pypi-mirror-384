"""
Geode-Simplex Python binding for section
"""
from __future__ import annotations
import geode_common.bin.geode_common_py_metric
import opengeode.bin.opengeode_py_model
__all__: list[str] = ['SimplexSectionLibrary', 'section_simplex_remesh']
class SimplexSectionLibrary:
    @staticmethod
    def initialize() -> None:
        ...
def section_simplex_remesh(arg0: opengeode.bin.opengeode_py_model.Section, arg1: geode_common.bin.geode_common_py_metric.Metric2D) -> tuple[opengeode.bin.opengeode_py_model.Section, opengeode.bin.opengeode_py_model.ModelCopyMapping]:
    ...
