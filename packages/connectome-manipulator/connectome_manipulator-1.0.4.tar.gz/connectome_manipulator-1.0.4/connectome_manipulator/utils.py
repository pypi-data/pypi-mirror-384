# This file is part of connectome-manipulator.
#
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Blue Brain Project/EPFL
# Copyright (c) 2025 Open Brain Institute

"""Various utility functions"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np


def _apply_recursively(func, obj, origin=(0, 0, 0)):
    origin = np.array(origin)

    if hasattr(obj, "soma"):
        obj.soma.points = origin + func(obj.soma.points - origin)
    for s in obj.iter():
        s.points = origin + func(s.points - origin)


def transform(obj, A):
    """Apply transformation matrix `A` to a given morphology object.

    Note:
        This comes out of bluepysnap

    Args:
        obj: Morphology / Section
        A: rotation matrix (4 x 4 NumPy array)
    """
    if A is None:
        return
    A = np.asarray(A)
    if A.shape != (4, 4):
        raise ValueError(f"`A` should be 4 x 4 matrix (got: {A.shape})")
    A = A.transpose()

    def func(p):
        return np.dot(np.column_stack((p, np.ones(len(p)))), A)[:, :3]

    _apply_recursively(func, obj)


def create_dir(path: os.PathLike) -> Path:
    """Create directory and parents if it doesn't already exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(filepath: os.PathLike) -> Dict[Any, Any]:
    """Load from JSON file."""
    return json.loads(Path(filepath).read_bytes())


def write_json(filepath: os.PathLike, data: Dict[Any, Any], indent: int = 2) -> None:
    """Write json file."""
    with open(filepath, "w", encoding="utf-8") as fd:
        json.dump(data, fd, indent=indent)


def reduce_config_paths(config: dict, config_dir: os.PathLike) -> dict:
    """Reduces absolute paths with respect to base_dir.

    Args:
        config (dict): Input config with absolute paths and no manifest.
        config_dir (str|Path): The path to the directory of the config.

    Returns:
        A new config with the paths reduced to being relative to the config dir.

    Note: Paths that are not in config_dir's tree will stay absolute.
    """
    if not Path(config_dir).is_absolute():
        raise ValueError(f"Circuit config's directory is not absolute: {config_dir}")

    if "manifest" in config:
        raise ValueError(
            f"A reduced config with absolute paths and no manifest must be provided.\n"
            f"Got instead: {config}"
        )

    reduced_config = {
        "version": config.get("version", "1"),
        "manifest": {"$BASE_DIR": "."},
    }

    if "node_sets_file" in config:
        reduced_config["node_sets_file"] = _reduce_path(config["node_sets_file"], config_dir)

    if "components" in config:
        # Reduce components dict recursively (may have nested dicts!)
        reduced_config["components"] = _reduce_dict(config["components"], config_dir)

    reducer = {
        "nodes_file": _reduce_path,
        "node_types_file": _reduce_path,
        "edges_file": _reduce_path,
        "edge_types_file": _reduce_path,
        "populations": _reduce_populations,
    }

    reduced_config["networks"] = {
        network_type: [
            {
                key: (reducer[key](value, config_dir) if key in reducer else value)
                for key, value in net_dict.items()
            }
            for net_dict in network_list
        ]
        for network_type, network_list in config["networks"].items()
    }
    return reduced_config


def _reduce_path(path: str, base_dir: os.PathLike) -> str:
    if not path or path.startswith("$"):
        return path

    path = Path(path)

    if path.is_absolute():
        if path.is_relative_to(base_dir):
            return str(Path("$BASE_DIR", path.relative_to(base_dir)))

    return str(Path("$BASE_DIR", path))


def _reduce_populations(populations_dict: dict, base_dir: os.PathLike) -> dict:
    def reduce_entry(key, value):
        if key.endswith(("file", "dir")):
            return _reduce_path(value, base_dir)

        if key == "alternate_morphologies":
            return {
                alt_key: _reduce_path(alt_path, base_dir) for alt_key, alt_path in value.items()
            }

        return value

    return {
        pop_name: {key: reduce_entry(key, value) for key, value in pop_dict.items()}
        for pop_name, pop_dict in populations_dict.items()
    }


def _reduce_dict(entry: dict, base_dir: os.PathLike) -> dict:
    reduced_dict = {}
    for key, value in entry.items():
        if isinstance(value, dict):
            reduced_dict[key] = _reduce_dict(value, base_dir)
        else:
            reduced_dict[key] = _reduce_path(value, base_dir)
    return reduced_dict


def _check_node_property(property_name, nodes):
    if nodes is None or property_name in nodes.property_names:
        return property_name
    else:
        return None


def check_grouping(group_by, src_nodes=None, tgt_nodes=None):
    """Helper function to check grouping for source/target neurons.

    Args:
        group_by (str/tuple): Neuron property name based on which to group connections, e.g., "synapse_class", "layer", or "mtype"; can be a tuple with two property names for source/target neurons or omitted
        src_nodes (bluepysnap.nodes.NodePopulation): Source node population (optional)
        tgt_nodes (bluepysnap.nodes.NodePopulation): Target node population (optional)

    Returns:
        str: Source grouping property name
        str: Target grouping property name

    Note:
        Includes some logic so that if a given property name only exists in either the source or target node
        population, it will apply grouping only on the population where it exists (instead of raising an error).
    """
    if not isinstance(group_by, tuple):
        if group_by is None:
            group_by = (group_by, group_by)
        else:
            group_by_lbl = str(group_by)
            # If only one grouping property is provided, propagate only to the populations where it actually exists
            group_by = (
                _check_node_property(group_by, src_nodes),
                _check_node_property(group_by, tgt_nodes),
            )
            # But make sure it exists in at least one of the source/target populations
            assert any(
                _g is not None for _g in group_by
            ), f"ERROR: Grouping property '{group_by_lbl}' does not exist in either source or target node population!"

    assert (
        len(group_by) == 2
    ), "ERROR: 'group_by' must be a tuple with two elements for source/target neurons!"

    src_group_by = group_by[0]
    tgt_group_by = group_by[1]

    assert src_group_by is None or isinstance(
        src_group_by, str
    ), "ERROR: Source 'group_by' must be a string (or None)!"
    assert tgt_group_by is None or isinstance(
        tgt_group_by, str
    ), "ERROR: Target 'group_by' must be a string (or None)!"

    if src_group_by is not None:
        assert (
            _check_node_property(src_group_by, src_nodes) is not None
        ), f"ERROR: Grouping property '{src_group_by}' does not exist in source node population!"
    if tgt_group_by is not None:
        assert (
            _check_node_property(tgt_group_by, tgt_nodes) is not None
        ), f"ERROR: Grouping property '{tgt_group_by}' does not exist in target node population!"

    return src_group_by, tgt_group_by


class ConsoleColors:
    """Helper class for formatting console text."""

    BLACK, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, _, DEFAULT = range(30, 40)
    NORMAL, BOLD, DIM, UNDERLINED, BLINK, INVERTED, HIDDEN = [a << 8 for a in range(7)]

    # These are the sequences needed to control output
    _CHANGE_SEQ = "\033[{}m"
    _RESET_SEQ = "\033[0m"

    @classmethod
    def reset(cls):
        """Reset colors."""
        return cls._RESET_SEQ

    @classmethod
    def set_text_color(cls, color):
        """Change text color."""
        return cls._CHANGE_SEQ.format(color)

    @classmethod
    def format_text(cls, text, color, style=None):
        """Format the text."""
        style = (style or color) >> 8
        format_seq = str(color & 0x00FF) + ((";" + str(style)) if style else "")
        return cls._CHANGE_SEQ.format(format_seq) + text + cls._RESET_SEQ
