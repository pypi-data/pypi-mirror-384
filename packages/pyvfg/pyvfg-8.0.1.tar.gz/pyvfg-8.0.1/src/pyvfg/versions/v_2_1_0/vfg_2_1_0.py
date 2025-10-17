# -*- coding: utf-8 -*-

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import (
    Dict,
    List,
    Literal,
    Type,
    Optional,
)  # import needed for a correct operation of StructureOnlyVFG.from_dict
import zipfile as zf

from ..v_2_0_0 import VFG as VFG_2_0_0, StructureOnlyVFG as StructureOnlyVFG_2_0_0, Variable, Factor, NpyFilepath
from ..v_2_0_0.variable import (
    StructureOnlyVariable,
)  # import needed for a correct operation of StructureOnlyVFG.from_dict

__all__ = ["VFG", "Plate", "NpyFilepath", "Variable", "Factor", "StructureOnlyVFG", "Optional", "StructureOnlyVariable"]

from ... import ValidationError, ValidationErrors

warnings.simplefilter("always", ResourceWarning)


@dataclass
class Plate:
    factors: List[str]
    """The factors that are part of this plate"""
    variables: List[str]
    """The variables that are part of this plate"""
    size: int
    """The size of the plate (number of repetitions)"""


@dataclass
class VFG(VFG_2_0_0):
    version: Literal["2.1.0"] = "2.1.0"
    plates: Dict[str, Plate] = field(default_factory=dict)

    def __init__(self, plates: Optional[Dict[str, Plate]] = None, **kwargs):
        super().__init__(**kwargs)
        self.plates = plates or {}

    def validate(
        self,
        raise_exceptions: bool = True,
    ) -> ValidationErrors:
        """
        Determines if the given VFG is valid and tries to infer its type.
        This method extends the standard VFG 2.0.0 validation to also implement plate validation.

        Args:
            raise_exceptions (bool): If True, raise an exception on any validation warning
        Returns:
            ValidationErrors if the VFG is invalid, otherwise an empty list of errors, and the inferred VFG type
        """
        errors: List[ValidationError] = []

        # just carry out plate validation
        defined_factor_keys = set(self.factors.keys())

        for plate_name, plate in self.plates.items():
            for factor_name in plate.factors:
                if factor_name not in defined_factor_keys:
                    errors.append(
                        ValidationError(
                            message=f"Factor '{factor_name}' in plate '{plate_name}' is not defined in the graph's main factors.",
                            parameters={"plate": plate_name, "factor": factor_name},
                        )
                    )

        # handle return
        errors_obj = super().validate(raise_exceptions=raise_exceptions)
        errors_obj.errors.extend(errors)
        if raise_exceptions and len(errors) > 0:
            raise errors_obj
        else:
            return errors_obj

    @classmethod
    def from_2_0_0(cls, vfg: VFG_2_0_0) -> "VFG":
        """
        Converts a VFG 2.0.0 object to a VFG 2.1.0 object.
        Note that this does not perform any validation or inference; it simply copies the data over.

        Args:
            vfg (VFG_2_0_0): The VFG 2.0.0 object to convert
        Returns:
            A VFG 2.1.0 object
        """
        return cls(version="2.1.0", name=vfg.name, variables=vfg.variables, factors=vfg.factors, plates={})


@dataclass
class StructureOnlyVFG(StructureOnlyVFG_2_0_0):
    version: Literal["2.1.0"] = "2.1.0"
    plates: Dict[str, Plate] = field(default_factory=dict)

    def load(self, file: zf.ZipFile) -> VFG:
        vfg = super().load(file=file)
        vfg.plates = self.plates
        return vfg

    @classmethod
    def _init_type(cls) -> Type["VFG"]:
        return VFG

    @classmethod
    def from_2_0_0(cls, data: StructureOnlyVFG_2_0_0) -> "StructureOnlyVFG":
        return StructureOnlyVFG(name=data.name, variables=data.variables, factors=data.factors, plates={})
