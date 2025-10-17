# -*- coding: utf-8 -*-
from collections import Counter
from dataclasses import dataclass
from enum import StrEnum
from typing import Optional, List, Union, Tuple
import re
import zipfile as zf

import numpy as np
from jsonpatch import JsonPatch

from ...errors import ValidationErrors, DuplicateElementsError
from ...project.utils import load_single_tensor

VariableReference = Union[str, Tuple[str, int]]


class NpyFilepath(str):
    """
    A string representing a file path to a .npy file.
    This class validates the file path to ensure it ends with '.npy'.
    """

    # Compile the regex pattern once for efficiency
    _pattern = re.compile(r"^.*\.(npy)$")

    def __new__(cls, value):
        """
        Overrides the default object creation method to add validation.
        """
        # Validate the input value against the regex pattern
        if not cls._pattern.fullmatch(value):
            raise ValueError(f"'{value}' is not a valid .npy file path. ")

        return super().__new__(cls, value)


class ConstraintForm(StrEnum):
    """The form of the constraint, currently only 'delta' is supported"""

    delta = "delta"


@dataclass
class VariableConstraints:
    """
    A class representing constraints for a variable.
    This class is used to define constraints on the variables in the VFG.
    """

    form: ConstraintForm
    """The form of the constraint, currently only 'delta' is supported"""


@dataclass
class Variable:
    class Domain(StrEnum):
        Real = "real"
        NonNegativeReal = "nonnegative_real"
        PositiveReal = "positive_real"
        PositiveDefinite = "positive_definite"
        PositiveSemidefinite = "positive_semidefinite"
        Simplex = "simplex"
        Categorical = "categorical"

    domain: Domain
    """The domain of the variable"""
    shape: List[int]
    """The shape of the variable"""
    constraints: Optional[VariableConstraints] = None
    """The constraints of the variable"""
    elements: Optional[List[str]] = None
    """The elements of the variable"""
    messages: Optional[np.ndarray] = None
    """The messages file path for the stored vector"""
    observation: Optional[np.ndarray] = None
    """The observation file path for the stored vector"""
    control_state: bool = False
    """Whether the variable is a control state variable (default: False)"""

    def __eq__(self, other, exclude_tensor_values: bool = False):
        """
        Checks if two Variable instances are equal, excluding observation values if specified.
        Args:
            other (Variable): The other Variable instance to compare with.
            exclude_tensor_values (bool): If True, excludes any tensor value from the comparison.
        Returns:
            bool: True if the Variable instances are equal, False otherwise.
        """
        if not (isinstance(other, Variable) or (isinstance(other, StructureOnlyVariable) and exclude_tensor_values)):
            return False

        return (
            self.domain == other.domain
            and self.constraints == other.constraints
            and self.shape == other.shape
            and self.elements == other.elements
            and self.control_state == other.control_state
            and self.control_state == other.control_state
            and (exclude_tensor_values or self._eq_tensor_variables(other))
        )

    def _eq_tensor_variables(self, other: "Variable") -> bool:
        """
        Checks the equality of all the tensor variables of the Variable instance.
        Returns:
            bool: True if the tensor variables are equal, False otherwise.
        """
        messages_are_none = self.messages is None and other.messages is None
        observations_are_none = self.observation is None and other.observation is None

        return (messages_are_none or np.allclose(self.messages, other.messages)) and (
            observations_are_none or np.allclose(self.observation, other.observation)
        )

    def equals_besides_tensor_values(self, other):
        """
        Checks if two Variable instances are equal, ignoring observation values.
        """
        return self.__eq__(other, exclude_tensor_values=True)

    # todo vfg2.0: check this. remember to validate tensors shape
    def validate(self, var_name: str, raise_exceptions: bool = True):
        errors = ValidationErrors(errors=[])
        ele_counter = Counter(self.elements)
        for ele_name, ele_count in ele_counter.items():
            if ele_count > 1:
                new_elements = []
                i = 1
                for e in self.elements:
                    ele = e
                    if e == ele_name:
                        if i > 1:
                            ele = f"{e}_{i}"
                        i += 1
                    new_elements.append(ele)
                patch = JsonPatch(
                    [
                        {
                            "op": "replace",
                            "path": f"/variables/{var_name}/elements",
                            "value": new_elements,
                        }
                    ]
                )
                errors.extend(DuplicateElementsError(var_name, ele_name, ele_count - 1, patch))
        if errors and raise_exceptions:
            raise errors
        return errors


@dataclass
class StructureOnlyVariable:
    domain: Variable.Domain
    """The constraints of the variable"""
    shape: List[int]
    """The domain of the variable"""
    constraints: Optional[VariableConstraints] = None
    """The shape of the variable"""
    elements: Optional[List[str]] = None
    """The elements of the variable"""
    messages: Optional[NpyFilepath] = None
    """The messages file path for the stored vector"""
    observation: Optional[NpyFilepath] = None
    """The observation file path for the stored vector"""
    control_state: bool = False
    """Whether the variable is a control state variable (default: False)"""

    def __eq__(self, other, exclude_tensor_values: bool = False) -> bool:
        if not (isinstance(other, StructureOnlyVariable) or (isinstance(other, Variable) and exclude_tensor_values)):
            return False
        return (
            self.domain == other.domain
            and self.constraints == other.constraints
            and self.shape == other.shape
            and self.elements == other.elements
            and self.control_state == other.control_state
            and (exclude_tensor_values or self._eq_tensor_filepaths(other))
        )

    def _eq_tensor_filepaths(self, other: "StructureOnlyVariable") -> bool:
        return self.observation == other.observation and other.messages == other.messages

    def equals_besides_tensor_values(self, other):
        """
        Checks if two Variable instances are equal, ignoring observation values.
        """
        return self.__eq__(other, exclude_tensor_values=True)

    def load(self, name: str, file: zf.ZipFile) -> Variable:
        obs = None
        msgs = None
        if self.observation is not None:
            obs = load_single_tensor(file, name, self.observation)
        if self.messages is not None:
            msgs = load_single_tensor(file, name, self.messages)
        return Variable(
            domain=self.domain,
            constraints=self.constraints,
            shape=self.shape,
            elements=self.elements,
            messages=msgs,
            observation=obs,
            control_state=self.control_state if self.control_state is not None else False,
        )
