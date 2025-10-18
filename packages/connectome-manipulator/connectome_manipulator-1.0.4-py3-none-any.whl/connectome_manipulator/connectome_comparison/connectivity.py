# This file is part of connectome-manipulator.
#
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2024 Blue Brain Project/EPFL
# Copyright (c) 2025 Open Brain Institute

"""Module for comparing connectomes based on connectivity features:

Structural comparison of two connectomes in terms of connection probability matrices for selected
pathways (including #synapses per connection), as specified by the config. For each connectome,
the underlying connectivity matrices are computed by the :func:`compute` function and will be saved
to a data file first. The individual connectivity matrices, together with a difference map
between the two connectomes, are then plotted by means of the :func:`plot` function.
"""

import matplotlib.pyplot as plt
import numpy as np
import progressbar
import pandas as pd

from scipy.spatial import KDTree
from scipy import sparse

from connectome_manipulator.access_functions import (
    get_edges_population,
    get_node_ids,
    get_connections,
    get_grouping,
)
from connectome_manipulator.utils import check_grouping


def within_max_distance_matrix(pre_neurons, post_neurons, max_dist, props_for_distance):
    """Computes a sparse bool matrix of neuron pairs within a specified maximum distance. The value of the matrix at i, j is True iff the pair of neuron i and neuron j are within that distance.

    Args:
        pre_neurons (tuple): A tuple of the node population object and the node ids for the first population of neurons. This population will be indexed along the first axis of the output
        post_neurons (tuple): A tuple of the node population object and the node ids for the second population of neurons. This population will be indexed along the second axis of the output
        max_dist (float): Maximum distance to use.
        props_for_distance (list): List of node properties that must be available for both populations. Their values must be numeric. They will be used to calculate the (Euclidean) distance.
    """
    nodes_pre, pre_ids = pre_neurons
    nodes_post, post_ids = post_neurons
    assert np.all([_p in nodes_pre.property_dtypes for _p in props_for_distance])
    assert np.all([_p in nodes_post.property_dtypes for _p in props_for_distance])
    if len(pre_ids) == 0 or len(post_ids) == 0:
        within_mat = sparse.csr_matrix((len(pre_ids), len(post_ids)), dtype=bool)
        return within_mat, pd.Series([]), pd.Series([])

    locs_pre = nodes_pre.get(pre_ids, props_for_distance)
    locs_post = nodes_post.get(post_ids, props_for_distance)

    lookup_pre = pd.Series(
        range(len(locs_pre)), index=locs_pre.index
    )  # from node id to 0, 1, 2, ...
    lookup_post = pd.Series(range(len(locs_post)), index=locs_post.index)

    tree_pre = KDTree(locs_pre)
    tree_post = KDTree(locs_post)

    pairs_within = tree_pre.query_ball_tree(tree_post, max_dist)
    indptr = np.cumsum([0] + list(map(len, pairs_within)))
    indices = np.hstack(pairs_within)
    within_mat = sparse.csr_matrix(
        (np.ones_like(indices, dtype=bool), indices, indptr), shape=(len(locs_pre), len(locs_post))
    )
    return within_mat, lookup_pre, lookup_post


def compute(
    circuit,
    group_by=None,
    sel_src=None,
    sel_dest=None,
    skip_empty_groups=False,
    edges_popul_name=None,
    max_distance=None,
    props_for_distance=None,
    **_,
):
    """Computes the average connection probabilities and #synapses/connection between groups of neurons of a given circuit's connectome.

    Args:
        circuit (bluepysnap.Circuit): Input circuit
        group_by (str/tuple): Neuron property name based on which to group connections, e.g., "synapse_class", "layer", or "mtype"; can be a tuple with two property names for source/target neurons; if omitted, the overall average is computed
        sel_src (str/list-like/dict): Source (pre-synaptic) neuron selection
        sel_dest (str/list-like/dict): Target (post-synaptic) neuron selection
        skip_empty_groups (bool): If selected, only group property values that exist within the given source/target selection are kept; otherwise, all group property values, even if not present in the given source/target selection, will be included
        edges_popul_name (str): Name of SONATA egdes population to extract data from
        max_distance (float): Optional. Maximum distance of pairs of neurons considered. If used, must also provide ``props_for_distance``.
        props_for_distance (list): Optional. To be provided with ``max_distance``. Numerical node properties that are used to calculate the pairwise distances.

    Returns:
        dict: Dictionary containing the computed data elements; see Notes

    Note:
        The returned dictionary contains the following data elements that can be selected for plotting through the structural comparison configuration file, together with a common dictionary containing additional information. Each data element is a dictionary with "data" (numpy.ndarray of size <source-group-size x target-group-size>), "name" (str), and "unit" (str) items.

        * "nsyn_conn": Mean number of synapses per connection
        * "nsyn_conn_std": Standard deviation of the number of synapses per connection
        * "nsyn_conn_sem": Standard error of the mean of the number of synapses per connection
        * "nsyn_conn_min": Minimum number of synapses per connection
        * "nsyn_conn_max": Maximum number of synapses per connection
        * "conn_prob": Average connection probability
    """
    if max_distance is not None:
        assert (
            props_for_distance is not None
        ), "When specifying distance cutoff, must also specify properties to use!"
    # Select edge population
    edges = get_edges_population(circuit, edges_popul_name)

    # Select corresponding source/target nodes populations
    src_nodes = edges.source
    tgt_nodes = edges.target

    # Get grouping selection
    src_group_by, tgt_group_by = check_grouping(group_by, src_nodes, tgt_nodes)
    src_group_sel, src_group_values = get_grouping(
        src_nodes, sel_src, src_group_by, skip_empty_groups
    )
    tgt_group_sel, tgt_group_values = get_grouping(
        tgt_nodes, sel_dest, tgt_group_by, skip_empty_groups
    )

    # Preselect neurons
    src_ids_base = get_node_ids(src_nodes, sel_src)
    tgt_ids_base = get_node_ids(tgt_nodes, sel_dest)

    if len(src_ids_base) == 0 or len(tgt_ids_base) == 0:
        print("WARNING: Empty source/target node selection(s)!")

    print(
        f"INFO: Computing connectivity (group_by={group_by}, sel_src={sel_src}, sel_dest={sel_dest}, N={len(src_group_values)}x{len(tgt_group_values)} groups, max_distance={max_distance} based on {props_for_distance})",
        flush=True,
    )

    syn_table = np.zeros((len(src_group_sel), len(tgt_group_sel)))  # Mean
    syn_table_std = np.zeros((len(src_group_sel), len(tgt_group_sel)))  # Std
    syn_table_sem = np.zeros((len(src_group_sel), len(tgt_group_sel)))  # SEM
    syn_table_min = np.zeros((len(src_group_sel), len(tgt_group_sel)))  # Min
    syn_table_max = np.zeros((len(src_group_sel), len(tgt_group_sel)))  # Max
    p_table = np.zeros((len(src_group_sel), len(tgt_group_sel)))
    pbar = progressbar.ProgressBar()
    for idx_pre in pbar(range(len(src_group_sel))):
        sel_pre = src_group_sel[idx_pre]
        for idx_post, _ in enumerate(tgt_group_sel):
            sel_post = tgt_group_sel[idx_post]
            pre_ids = get_node_ids(src_nodes, sel_pre)  # Grouping selection
            post_ids = get_node_ids(tgt_nodes, sel_post)  # Grouping selection
            pre_ids = np.intersect1d(pre_ids, src_ids_base)  # Merge with base selection
            post_ids = np.intersect1d(post_ids, tgt_ids_base)  # Merge with base selection
            conns = get_connections(edges, pre_ids, post_ids, with_nsyn=True)
            npairs = len(pre_ids) * len(post_ids)

            if conns.size > 0:
                if max_distance is not None and len(pre_ids) > 0 and len(post_ids) > 0:
                    M, lo_pre, lo_post = within_max_distance_matrix(
                        (src_nodes, pre_ids),
                        (tgt_nodes, post_ids),
                        max_distance,
                        props_for_distance,
                    )
                    is_within = np.asarray(M[lo_pre[conns[:, 0]], lo_post[conns[:, 1]]]).flatten()
                    conns = conns[is_within]
                    npairs = M.nnz

            if conns.size > 0:
                scounts = conns[:, 2]  # Synapse counts per connection
                ccount = len(scounts)  # Connection count

                syn_table[idx_pre, idx_post] = np.mean(scounts)
                syn_table_std[idx_pre, idx_post] = np.std(scounts)
                syn_table_sem[idx_pre, idx_post] = np.std(scounts) / np.sqrt(ccount)
                syn_table_min[idx_pre, idx_post] = np.min(scounts)
                syn_table_max[idx_pre, idx_post] = np.max(scounts)
                p_table[idx_pre, idx_post] = 100.0 * ccount / npairs

    syn_table_name = "Synapses per connection"
    syn_table_unit = "#syn/conn"
    p_table_name = "Connection probability"
    p_table_unit = "Conn. prob. (%)"

    all_res_dict = {}
    all_res_dict["nsyn_conn"] = {
        "data": syn_table,
        "name": syn_table_name,
        "unit": "Mean " + syn_table_unit,
    }
    all_res_dict["nsyn_conn_std"] = {
        "data": syn_table_std,
        "name": syn_table_name,
        "unit": "Std of " + syn_table_unit,
    }
    all_res_dict["nsyn_conn_sem"] = {
        "data": syn_table_sem,
        "name": syn_table_name,
        "unit": "SEM of " + syn_table_unit,
    }
    all_res_dict["nsyn_conn_min"] = {
        "data": syn_table_min,
        "name": syn_table_name,
        "unit": "Min " + syn_table_unit,
    }
    all_res_dict["nsyn_conn_max"] = {
        "data": syn_table_max,
        "name": syn_table_name,
        "unit": "Max " + syn_table_unit,
    }
    all_res_dict["conn_prob"] = {"data": p_table, "name": p_table_name, "unit": p_table_unit}
    all_res_dict["common"] = {
        "src_group_values": src_group_values,
        "tgt_group_values": tgt_group_values,
        "src_group_by": src_group_by,
        "tgt_group_by": tgt_group_by,
    }

    return all_res_dict


def plot(
    res_dict, common_dict, fig_title=None, vmin=None, vmax=None, isdiff=False, group_by=None, **_
):  # pragma:no cover
    """Plots a connectivity matrix or a difference matrix.

    Args:
        res_dict (dict): Results dictionary, containing selected data for plotting; must contain a "data" item with a connectivity matrix of type numpy.ndarray of size  <#source-group-values x #target-group-values>, as well as "name" and "unit" items containing strings.
        common_dict (dict): Common dictionary, containing additional information; must contain "src_group_values" and "tgt_group_values" items containing lists of source/target values of the grouped property, matching the size of the connectivity matrix in ``res_dict``
        fig_title (str): Optional figure title
        vmin (float): Minimum plot range
        vmax (float): Maximum plot range
        isdiff (bool): Flag indicating that ``res_dict`` contains a difference matrix; in this case, a symmetric plot range is required and a divergent colormap will be used
        group_by (str/tuple): Neuron property name based on which to group connections, e.g., "synapse_class", "layer", or "mtype"; can be a tuple with two property names for source/target neurons; if omitted, the overall average is computed
    """
    if isdiff:  # Difference plot
        assert -1 * vmin == vmax, "ERROR: Symmetric plot range required!"
        cmap = "PiYG"  # Symmetric (diverging) colormap
    else:  # Regular plot
        cmap = "hot_r"  # Regular colormap

    plt.imshow(res_dict["data"], interpolation="nearest", cmap=cmap, vmin=vmin, vmax=vmax)

    if fig_title is None:
        plt.title(res_dict["name"])
    else:
        plt.title(fig_title)

    if "src_group_by" in common_dict and "tgt_group_by" in common_dict:
        src_group_by = common_dict["src_group_by"]
        tgt_group_by = common_dict["tgt_group_by"]
    else:
        # Backward compatibility
        src_group_by, tgt_group_by = check_grouping(group_by)

    src_lbl = tgt_lbl = "(all)"
    if src_group_by:
        src_lbl = str(src_group_by)
    if tgt_group_by:
        tgt_lbl = str(tgt_group_by)
    plt.xlabel(f"Postsynaptic {tgt_lbl}")
    plt.ylabel(f"Presynaptic {src_lbl}")

    n_grp = np.maximum(len(common_dict["src_group_values"]), len(common_dict["tgt_group_values"]))
    font_size = max(13 - n_grp / 6, 1)  # Font scaling
    if len(common_dict["src_group_values"]) > 0:
        plt.yticks(
            range(len(common_dict["src_group_values"])),
            common_dict["src_group_values"],
            rotation=0,
            fontsize=font_size,
        )

    if len(common_dict["tgt_group_values"]) > 0:
        if max(len(str(grp)) for grp in common_dict["tgt_group_values"]) > 1:
            rot_x = 90
        else:
            rot_x = 0
        plt.xticks(
            range(len(common_dict["tgt_group_values"])),
            common_dict["tgt_group_values"],
            rotation=rot_x,
            fontsize=font_size,
        )

    cb = plt.colorbar()
    cb.set_label(res_dict["unit"])
