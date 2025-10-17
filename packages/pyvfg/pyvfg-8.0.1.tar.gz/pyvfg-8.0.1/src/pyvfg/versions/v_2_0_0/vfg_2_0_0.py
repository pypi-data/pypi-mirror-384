# -*- coding: utf-8 -*-

from __future__ import annotations

import dataclasses
import warnings
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Literal, Any, Annotated, Type, get_args

import numpy as np
import zipfile as zf
from dataclass_wizard import json_key
from dataclass_wizard.enums import LetterCase
from dataclass_wizard.serial_json import JSONWizard
from deprecation import deprecated
from jsonpatch import JsonPatch

from .variable import Variable, StructureOnlyVariable
from .factor import Factor

from ..common import (
    initialize_factors,
    normalize_factors,
    apply_patches_to_vfg,
    ModelType,
    FactorInitialization,
    load_model_schema,
)
from ...errors import (
    ValidationError,
    ValidationErrors,
)
from ...project.model import GeniusProjectFile

warnings.simplefilter("always", ResourceWarning)


DUMMY_CONTROL_STATE_NAME = "dummy_control_state"


@dataclass
class StructureOnlyVFG(JSONWizard):
    """
    Primarily used for deserialization and testing.
    Does *not* have loaded tensors in memory.
    """

    class _(JSONWizard.Meta):
        v1 = True
        v1_unsafe_parse_dataclass_in_union = True
        key_transform_with_dump = LetterCase.NONE
        key_transform_with_load = LetterCase.NONE

    name: Optional[str] = None
    version: str = "2.0.0"
    variables: Dict[str, StructureOnlyVariable] = field(default_factory=dict)
    factors: Dict[str, Factor] = field(default_factory=dict)

    def load(self, file: zf.ZipFile) -> "VFG":
        """
        Loads the VFG, including all tensors from the given zip file.
        Args:
            file: The zip file to load the tensors from.
        Returns:
            The loaded VFG.
        Raises:
            ValueError if self.name is None.
        """
        if self.name is None:
            raise ValueError("Cannot load VFG without a name.")

        variables = {k: v.load(self.name, file) for k, v in self.variables.items()}
        return type(self)._init_type()(name=self.name, factors=self.factors, variables=variables)

    @classmethod
    def _init_type(cls) -> Type["VFG"]:
        return VFG


@dataclass
class VFG:
    name: Optional[str] = None
    version: Literal["2.0.0"] = "2.0.0"
    variables: Dict[str, Variable] = field(default_factory=dict)
    factors: Dict[str, Factor] = field(default_factory=dict)

    def __init__(
        self,
        name: Optional[str] = None,
        variables: Optional[Dict[str, Variable]] = None,
        factors: Optional[Dict[str, Factor]] = None,
        **kwargs,
    ):
        if (
            variables is not None
            and len(variables.keys()) > 0
            and isinstance(variables[next(iter(variables))], get_args(Dict[str, dict]))
        ) or (
            factors is not None
            and len(factors.keys()) > 0
            and isinstance(factors[next(iter(factors))], get_args(Dict[str, dict]))
        ):
            raise ValueError(
                "VFG constructor expects Variables and Factors, not dictionaries. Use StructureOnlyVFG.from_dict(**dict) and then .load(file: zf.ZipFile) to get a VFG."
            )
        self.name = name
        self.variables = variables if variables is not None else {}
        self.factors = factors if factors is not None else {}

    # Private fields
    _model_type: Annotated[Optional[ModelType], json_key(dump=False)] = field(init=False, compare=False, default=None)

    @deprecated("8.0.0")
    def __enter__(self):
        """No longer necessary, as no file reference is kept."""
        return self

    @deprecated("8.0.0")
    def __exit__(self, exc_type, exc_val, exc_tb):
        """No longer necessary, as no file reference is kept."""
        pass

    # region Properties

    @property
    def vars_set(self):
        return set(self.variables.keys())

    @property
    def var_shapes(self):
        return {v: self.variables[v].shape for v in self.variables}

    @property
    def model_type(self):
        """
        Returns the model type of the VFG.
        """
        if not self._model_type:
            self._model_type = self.validate()[1]
        return self._model_type

    # endregion

    def __eq__(self, other, exclude_variable_observation_values=True):
        """
        Checks if two VFG instances are equal, excluding observation values of variables if specified.
        Args:
            other (VFG): The other VFG instance to compare with.
            exclude_variable_observation_values (bool): If True, excludes observation values from the comparison.
        Returns:
            bool: True if the VFG instances are equal, False otherwise.
        """
        if not (
            isinstance(other, VFG) or (isinstance(other, StructureOnlyVFG) and exclude_variable_observation_values)
        ):
            return False

        return (
            self.version == other.version
            and self.factors == other.factors
            and (
                all(self.variables[x].equals_besides_tensor_values(other.variables[x]) for x in self.variables.keys())
                if exclude_variable_observation_values
                else self.variables == other.variables
            )
        )

    def equals_besides_variable_observation_values(self, other):
        """
        Checks if two Variable instances are equal, ignoring observation values.
        """
        return self.__eq__(other, exclude_variable_observation_values=True)

    # region From/To methods

    def to_gpf_pieces(self) -> Tuple[str, Dict[str, Any], Dict[str, np.ndarray]]:
        """
        Saves the VFG to a Genius Project File (GPF).
        Returns:
            Tuple[str, Dict[str, Any], Dict[str, np.ndarray]]: A tuple containing the model name, the VFG structure as a dictionary,
            and a dictionary of tensor names to their corresponding numpy arrays.
        """
        # import here to avoid circular imports
        model_name = self.name or "model1"

        # collect all tensors from the VFG
        tensors = {}
        vfg_dict = dataclasses.asdict(self, dict_factory=lambda x: {k: v for (k, v) in x if v is not None})
        for var_name, variable in vfg_dict["variables"].items():
            # save the tensors to the .npy files
            if "observation" in variable:
                tensor_name = f"{var_name}_observation.npy"
                tensors[tensor_name] = variable["observation"]
                variable["observation"] = tensor_name

            if "messages" in variable:
                tensor_name = f"{var_name}_messages.npy"
                tensors[tensor_name] = variable["messages"]
                variable["messages"] = tensor_name

        return model_name, vfg_dict, tensors

    def to_gpf(self, file: GeniusProjectFile, model_name: Optional[str] = None) -> None:
        """
        Writes the given VFG to a file.
        Args:
            file: The file to write to.
            model_name: If specified, will override the model name in the VFG.

        Returns: None.
        """
        from pyvfg.project.utils import write_vfg_pieces_to_gpf

        (actual_model_name, vfg_json, tensors) = self.to_gpf_pieces()
        viz_metadata = {}
        if model_name is not None:
            actual_model_name = model_name
        write_vfg_pieces_to_gpf(file, actual_model_name, vfg_json, tensors, viz_metadata)

    @staticmethod
    def from_gpf(file: GeniusProjectFile, model_name: Optional[str] = None) -> Union["VFG", None, List["VFG"]]:
        """
        Loads a VFG from a Genius Project File.
        Args:
            file (GeniusProjectFile): The Genius Project File to load the VFG from.
            model_name (Optional[str]): The name of the model to load. If None, all the models in the GPF will be loaded.
        Returns:
            VFG: If there is only 1 model in the GPF file or if `model_name` is specified and present in the GPF file.
            None: If the GPF file contains no models or if `model_name` is specified but not present in the GPF file.
            List[VFG]: If the GPF contains multiple models and `model_name` is None.
        """
        # import here to avoid circular imports
        from ...project.serialization import load_project_200

        models = load_project_200(file)

        if len(models) == 0:
            return None

        if model_name is None:
            if len(models) == 1:
                return models[0]
            return models

        for model in models:
            if model.name == model_name:
                return model

        # If we reach here, the model_name was specified but not found
        return None

    # endregion

    def get_observation_values_for_variables(self, variables: List[str]) -> Dict[str, np.ndarray]:
        """
        Returns the observation values for the given variables.
        """
        return {name: self.variables[name].observation for name in variables}

    def apply_patches(
        self,
        patches: Union[ValidationErrors, list[ValidationError], JsonPatch, list[JsonPatch]],
    ) -> VFG:
        return apply_patches_to_vfg(self, patches)

    def initialize_factors(self, init_strategy: FactorInitialization | dict[str, FactorInitialization]):
        initialize_factors(self, init_strategy)

    def normalize_factors(self):
        normalize_factors(self)

    def validate(
        self,
        raise_exceptions: bool = True,
    ) -> ValidationErrors:
        """
        Determines if the given VFG, is valid and tries to infer its type.

        Args:
            raise_exceptions (bool): If True, raise an exception on any validation warning
        Returns:
            ValidationErrors if the VFG is invalid, otherwise an empty list of errors, and the inferred VFG type
        """
        errors: List[ValidationError] = []

        for factor in self.factors.values():
            # self-validate factors
            factor.factor_validate(factor_idx=None, raise_exceptions=raise_exceptions)
            # validate factor inputs and outputs exist
            for var_name in factor.output:
                if isinstance(var_name, tuple):
                    var_name = var_name[0]
                if var_name not in self.variables:
                    errors.append(ValidationError(f"Variable '{var_name}' is not defined in the VFG variables."))
            for parameter_type, var_value in factor.parameters.items():
                # iterate over probability and input variables
                if parameter_type == "probabilities" or parameter_type == "input":
                    # unify between list and singular from json
                    var_value = var_value if isinstance(var_value, list) else [var_value]
                    # for each of those...
                    for var_name in var_value:
                        # if it's subscripted, take the name without the subscript
                        if isinstance(var_name, tuple):
                            var_name = var_name[0]
                        # verify the name exists as a variable
                        if var_name not in self.variables:
                            errors.append(
                                ValidationError(
                                    f"Variable '{var_name}' is not defined in the VFG variables.",
                                    parameters={"factor": factor.output},
                                )
                            )

        errors_obj = ValidationErrors(errors=errors)
        if raise_exceptions and len(errors) > 0:
            raise errors_obj
        else:
            return errors_obj

    def _correct(
        self,
        raise_exceptions: bool = True,
    ) -> Tuple[VFG, list[ValidationError]]:
        """
        Implementation of the 'correct' method (shared by subclasses).
        """
        errors = self.validate(raise_exceptions=False)
        vfg = self.apply_patches(errors) if errors else self

        nre = errors.non_recoverable_errors
        if nre and raise_exceptions:
            raise nre

        return vfg, nre

    def correct(
        self,
        raise_exceptions: bool = True,
    ) -> Tuple[VFG, list[ValidationError]]:
        """
        Corrects the VFG by automatically applying patches where possible.
        Currently implemented to call _correct().

        Args:
            raise_exceptions (bool): If True, raises an exception on any validation warning that can't be recovered from.
        Returns:
            A corrected VFG and a list of non-recoverable errors
        """
        return self._correct(raise_exceptions=raise_exceptions)

    @classmethod
    def model_json_schema(cls) -> dict[str, Any]:
        return load_model_schema(cls.version)
