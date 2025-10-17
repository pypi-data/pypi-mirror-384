# -*- coding: utf-8 -*-
import json
import zipfile
from typing import List, Any, Dict

from .model import GeniusProjectFile
from .utils import get_models_list
from ..versions.v_2_0_0.vfg_2_0_0 import VFG as VFG_2_0_0, StructureOnlyVFG


def load_project_200(file: GeniusProjectFile) -> List[VFG_2_0_0]:
    """
    Will load a Genius Project File into a VFG 2.0.0, with loaded tensors.
    """

    models = []
    with zipfile.ZipFile(file, "r") as zf:
        # read manifest at root level to see the list of models we have available
        model_prefixes: List[str] = get_models_list(zf)

        # for each model name ("prefix") in the manifest
        for prefix in model_prefixes:
            # Get the JSON file
            with zf.open(f"{prefix}/vfg.json") as f:
                vfg_json: Dict[str, Any] = json.load(f)

            # and finally, load the dict into a single model
            vfg = StructureOnlyVFG.from_dict(vfg_json)
            vfg.name = prefix
            vfg = vfg.load(zf)
            models.append(vfg)

    return models
