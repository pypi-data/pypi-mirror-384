"""
Geode-Simplex Python binding for brep
"""
from __future__ import annotations
import geode_common.bin.geode_common_py_metric
import opengeode.bin.opengeode_py_model
__all__: list[str] = ['SimplexBRepLibrary', 'brep_simplex_remesh']
class SimplexBRepLibrary:
    @staticmethod
    def initialize() -> None:
        ...
def brep_simplex_remesh(arg0: opengeode.bin.opengeode_py_model.BRep, arg1: geode_common.bin.geode_common_py_metric.Metric3D) -> tuple[opengeode.bin.opengeode_py_model.BRep, opengeode.bin.opengeode_py_model.ModelCopyMapping]:
    ...
