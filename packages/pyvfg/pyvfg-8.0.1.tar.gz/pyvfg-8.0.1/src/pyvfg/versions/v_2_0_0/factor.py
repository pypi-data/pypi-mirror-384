# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from enum import StrEnum
from typing import List, Optional, Dict, Union
from .variable import VariableReference, ConstraintForm
from ... import ValidationErrors


@dataclass
class NodeConstraint:
    variables: List[VariableReference]
    """The variables involved in the constraint"""
    form: ConstraintForm = ConstraintForm.delta
    """The form of the constraint, currently only 'delta' is supported"""
    p_substitutions: Optional[List[VariableReference]] = None
    """The p-substitution for the constraint"""


@dataclass
class Function:
    class Type(StrEnum):
        Categorical = "categorical"
        ConditionalCategorical = "conditional_categorical"
        Dirichlet = "dirichlet"
        Gaussian = "gaussian"
        LinearGaussian = "linear_gaussian"
        Mixture = "mixture"
        GMM = "gmm"
        Wishart = "wishart"
        MatrixNormalWishart = "matrix_normal_wishart"
        NormalInverseWishart = "normal_inverse_wishart"
        Softmax = "softmax"
        MNLRegression = "mnlr"
        Potential = "potential"
        Plus = "+"
        Minus = "-"
        Multiply = "*"
        Custom = "custom"

        @classmethod
        def from_value(cls, value: str):
            """
            Returns the Function.Type enum member corresponding to the given value.
            Args:
                value (str): The value to convert.
            Returns:
                Function.Type: The corresponding enum member.
            Raises:
                ValueError: If the value does not match any enum member.
            """
            if value == "categorical_conditional":
                return Function.Type.ConditionalCategorical
            if value == "logits":
                return Function.Type.Softmax
            return cls(value)

    output: List[VariableReference]
    """The output variables of the function"""
    function: Type = field(default=Type.Categorical)
    """The type of the function (distribution)"""
    parameters: Optional[Dict[str, Union[VariableReference, List[VariableReference]]]] = field(default_factory=dict)
    """The parameters of the function"""
    constraints: Optional[Dict[str, NodeConstraint]] = field(default=None)
    """The constraints of the function, if any"""
    control_target: Optional[bool] = False
    """Whether the function is a control target (default: False)"""


@dataclass
class Factor:
    output: List[VariableReference]
    function: Function.Type = Function.Type.Categorical
    parameters: Optional[Dict[str, Union[VariableReference, List[VariableReference]]]] = None
    constraints: Optional[Dict[str, NodeConstraint]] = None
    control_target: Optional[bool] = False

    def __eq__(self, other):
        if not isinstance(other, Factor):
            return False

        parameters_are_equal = True
        for key, value in self.parameters.items():
            if isinstance(value, list):
                parameters_are_equal &= all(x in other.parameters[key] for x in value)
            else:
                parameters_are_equal &= value == other.parameters[key]

        return (
            self.function == other.function
            and self.output == other.output
            and parameters_are_equal
            and self.constraints == other.constraints
            and self.control_target == other.control_target
        )

    def factor_validate(self, factor_idx: Optional[int], raise_exceptions: bool) -> ValidationErrors:
        return ValidationErrors([])
