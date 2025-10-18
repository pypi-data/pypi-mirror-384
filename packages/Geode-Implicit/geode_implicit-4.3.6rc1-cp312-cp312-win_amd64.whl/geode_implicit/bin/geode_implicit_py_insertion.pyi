"""
Geode-Implicit Python binding
"""
from __future__ import annotations
import opengeode.bin.opengeode_py_mesh
import opengeode.bin.opengeode_py_model
import opengeode_geosciences.bin.opengeode_geosciences_py_implicit
__all__: list[str] = ['ImplicitInsertionLibrary', 'StratigraphicModelInserter', 'StratigraphicSectionInserter']
class ImplicitInsertionLibrary:
    @staticmethod
    def initialize() -> None:
        ...
class StratigraphicModelInserter:
    def __init__(self, arg0: opengeode_geosciences.bin.opengeode_geosciences_py_implicit.StratigraphicModel) -> None:
        ...
    def insert_and_build(self) -> opengeode.bin.opengeode_py_model.BRep:
        ...
    def select_stratigraphic_surface_to_insert(self, arg0: opengeode.bin.opengeode_py_mesh.TriangulatedSurface3D) -> None:
        ...
class StratigraphicSectionInserter:
    def __init__(self, arg0: opengeode_geosciences.bin.opengeode_geosciences_py_implicit.StratigraphicSection) -> None:
        ...
    def insert_and_build(self) -> opengeode.bin.opengeode_py_model.Section:
        ...
    def select_stratigraphic_curve_to_insert(self, arg0: opengeode.bin.opengeode_py_mesh.EdgedCurve2D) -> None:
        ...
