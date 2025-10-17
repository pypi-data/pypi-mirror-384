# -*- coding: utf-8 -*-
import importlib.metadata
import copy
import json
from typing import Union

from pyvfg.versions.common import is_version_higher_than
from pyvfg.versions.v_2_0_0 import VFG as VFG_2_0_0, StructureOnlyVFG as StructureOnlyVFG_2_0_0
from pyvfg.versions.v_2_1_0.vfg_2_1_0 import VFG as VFG_2_1_0, StructureOnlyVFG as StructureOnlyVFG_2_1_0
from pyvfg.versions.v_2_0_0.vfg_2_0_0_utils import vfg_upgrade as vfg_upgrade_2_0_0, infer_variable_domain

VERSION = importlib.metadata.version("pyvfg")

__all__ = [
    "VERSION",
    "vfg_from_json",
    "vfg_upgrade",
    "infer_variable_domain",
]


def vfg_from_json(json_data: Union[dict, str]) -> VFG_2_1_0:
    """
    See vfg_upgrade
    :param json_data: The json data to up-convert
    :return: The VFG data
    """
    return vfg_upgrade(json_data)


def vfg_upgrade(
    json_data: Union[dict, str], force_use_factor_values: bool = False
) -> Union[StructureOnlyVFG_2_1_0, VFG_2_1_0]:
    """
    Upgrades the incoming VFG from JSON data to version 2.1.0.
    If factor counts are available and meaningful, they will be used; otherwise, factor values will be used.

    Args:
        json_data (Union[dict, str]): Incoming json data, in either dictionary or string format
        force_use_factor_values (bool): If True, forces the use of factor values instead of counts even if counts are available and meaningful
    Returns:
        A VFG object, in the 2.1.0 schema.
    """

    if isinstance(json_data, str):
        data = json.loads(json_data)
    elif isinstance(json_data, dict):
        data = json_data
    else:
        raise ValueError("json_data must be dict or str")

    if data["version"] == "2.1.0":
        # already in the latest version
        return StructureOnlyVFG_2_1_0.from_dict(data)

    if is_version_higher_than(data["version"], "2.1.0"):
        raise ValueError(
            f"Cannot upgrade VFG from version {data['version']} to 2.1.0, "
            f"as it is already higher than the target version."
        )

    upgraded_vfg: Union[VFG_2_0_0, StructureOnlyVFG_2_0_0] = vfg_upgrade_2_0_0(data, force_use_factor_values)
    if isinstance(upgraded_vfg, StructureOnlyVFG_2_0_0):
        return StructureOnlyVFG_2_1_0.from_2_0_0(upgraded_vfg)
    else:
        return VFG_2_1_0.from_2_0_0(upgraded_vfg)
