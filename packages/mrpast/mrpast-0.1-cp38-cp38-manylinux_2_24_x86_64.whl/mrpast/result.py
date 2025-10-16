# Migration Rate and Population Size Across Space and Time (mrpast)
# Copyright (C) 2025 April Wei
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# with this program.  If not, see <https://www.gnu.org/licenses/>.
from tabulate import tabulate
from typing import Optional, Dict, Any, List, Iterable, Tuple
import itertools
import json
import math
import mrpast.model
import numpy as np
import numpy as np
import pandas as pd

try:
    import networkx as nx
    import matplotlib.pyplot as plt
    import matplotlib as mpl
except ImportError:
    nx = None  # type: ignore
    plt = None  # type: ignore


# A fixed parameter is a constant value specified by the user, and not used by the solver.
def _param_is_fixed(parameter: Dict[str, Any]) -> bool:
    return parameter["lb"] == parameter["ub"]


# A synthetic parameter is either fixed or constructed, and is invisible to the user.
def _param_is_synthetic(parameter: Dict[str, Any]) -> bool:
    return parameter["kind_index"] < 0


# A constructed parameter is a user-visible parameter that is completely determined by the
# value(s) of other parameters.
def _param_is_constructed(parameter: Dict[str, Any]) -> bool:
    return len(parameter.get("one_minus", [])) > 0


def load_json_pandas(
    filename: str, interval_field: Optional[str] = None, skip_fixed: bool = True
) -> pd.DataFrame:
    """
    Load a solver output JSON file as a Pandas DataFrame.

    :param filename: The JSON filename.
    :param interval_field: Optionally, the name of a field in the JSON file (on each
        parameter) to use for computing the parameter confidence intervals. Typically
        this is "gim_ci", which is present on an output file if the "mrpast confidence"
        command was used to generate the JSON.
    :param skip_fixed: Set to False to keep the fixed values that were part of the solution, otherwise
        only the parameters will be returned.
    :return: Pandas DataDrame, where coalescent rates have been converted into effective
        population sizes (Ne).
    """
    result = []
    with open(filename) as f:
        data = json.load(f)
    ploidy = data["ploidy"]

    def clamp(param, value):
        if value < param["lb"]:
            return param["lb"]
        if value > param["ub"]:
            return param["ub"]
        return value

    def get_interval(param, idx):
        if interval_field is not None and not (
            _param_is_fixed(param) or _param_is_constructed(param)
        ):
            if isinstance(interval_field, str):
                return param[interval_field][idx]
            return param[interval_field[idx]]
        return float("NaN")

    epochs = data.get("epoch_times_gen")
    for i, p in enumerate(epochs if epochs else []):
        v = clamp(p, p["final"])
        del p["apply_to"]
        is_fixed = _param_is_fixed(p)
        if is_fixed and skip_fixed:
            continue
        p.update(
            {
                "label": f"E{i}",
                "Ground Truth": clamp(p, p["ground_truth"]),
                "err_low": v - clamp(p, get_interval(p, 0)),
                "err_hi": clamp(p, get_interval(p, 1)) - v,
                "Optimized Value": v,
                "Parameter Type": "Epoch time",
                "Fixed": is_fixed,
            }
        )
        result.append(p)
    mcounter = 0
    ncounter = 0
    gcounter = 0
    for p in data["smatrix_values_ne__gen"]:
        is_fixed = _param_is_fixed(p)
        if is_fixed and skip_fixed:
            continue
        if p["kind"] == "migration":
            v = clamp(p, p["final"])
            epochs = list(sorted(set([a.get("epoch") for a in p["apply_to"]])))
            del p["apply_to"]
            p.update(
                {
                    "label": f"M{mcounter}",
                    "Ground Truth": clamp(p, p["ground_truth"]),
                    "err_low": v - clamp(p, get_interval(p, 0)),
                    "err_hi": clamp(p, get_interval(p, 1)) - v,
                    "Optimized Value": v,
                    "Parameter Type": "Migration rate",
                    "Epochs": epochs,
                    "Fixed": is_fixed,
                }
            )
            result.append(p)
            mcounter += 1
        elif p["kind"] == "growth":
            v = clamp(p, p["final"])
            epochs = list(sorted(set([a.get("epoch") for a in p["apply_to"]])))
            del p["apply_to"]
            p.update(
                {
                    "label": f"G{gcounter}",
                    "Ground Truth": clamp(p, p["ground_truth"]),
                    "err_low": v - clamp(p, get_interval(p, 0)),
                    "err_hi": clamp(p, get_interval(p, 1)) - v,
                    "Optimized Value": v,
                    "Parameter Type": "Growth rate",
                    "Epochs": epochs,
                    "Fixed": is_fixed,
                }
            )
            result.append(p)
            gcounter += 1
        elif p["kind"] == "coalescence":

            def coal2ne(rate):
                return 1 / (ploidy * clamp(p, rate))

            epochs = list(sorted(set([a.get("epoch") for a in p["apply_to"]])))
            del p["apply_to"]
            v = coal2ne(p["final"])
            # These are flipped because of coal2ne...
            lower_ci = coal2ne(get_interval(p, 1))
            upper_ci = coal2ne(get_interval(p, 0))
            p.update(
                {
                    "label": f"P{ncounter}",
                    "Ground Truth": coal2ne(p["ground_truth"]),
                    "err_low": v - lower_ci,
                    "err_hi": upper_ci - v,
                    "Optimized Value": v,
                    "Parameter Type": "Effective popsize",
                    "Epochs": epochs,
                    "Fixed": is_fixed,
                }
            )
            result.append(p)
            ncounter += 1
    for acounter, p in enumerate(data.get("amatrix_parameters", []) or []):
        v = clamp(p, p["final"])
        del p["apply_to"]
        is_fixed = _param_is_fixed(p)
        if is_fixed and skip_fixed:
            continue
        p.update(
            {
                "label": f"A{acounter}",
                "Ground Truth": (
                    clamp(p, p["ground_truth"]) if not is_fixed else p["init"]
                ),
                "err_low": v - clamp(p, get_interval(p, 0)),
                "err_hi": clamp(p, get_interval(p, 1)) - v,
                "Optimized Value": v,
                "Parameter Type": "Admixture proportion",
                "Epochs": [],  # TODO
                "Fixed": is_fixed,
            }
        )
        if "one_minus" in p:
            del p["one_minus"]
        result.append(p)

    return pd.DataFrame.from_dict(result)


def summarize_bootstrap_data(
    bootstrap_df: pd.DataFrame,
    use_median: bool = True,
    interval_conf: float = 0.95,
) -> pd.DataFrame:
    """
    Given a Pandas DataFrame loaded from a bootstrap CSV file, produce a new DataFrame
    that summarizes the data. Confidence intervals are calculated, and the resulting
    parameter estimates are the mean (or median) of the value over all bootstrap samples.

    :param bootstrap_df: A DataFrame as loaded via pandas.read_csv() with the CSV that is
        generated by "mrpast confidence --bootstrap".
    :param use_median: Set to False if you want to use the mean instead of the median for
        summarizing parameter values over all bootstrap samples. The median is more robust
        to parameter estimates that hit the lower or upper bounds during maximum likelihood
        estimation.
    :param interval_conf: Defaults to 0.95. Set to one of 0.99, 0.95, 0.9, 0.75 or 1.0.
        1.0 means use the entire range of the bootstrap values instead of the standard
        deviation plus a confidence interval. The other values are the confidence for the
        normal distribution confidence intervals based on sample standard deviation.
    :return: DataFrame with one row per parameter, summarizing the value and confidence
        interval.
    """
    ci_mult = {0.99: 2.576, 0.95: 1.96, 0.9: 1.645, 0.75: 1.150}.get(interval_conf)
    assert (
        ci_mult is not None or interval_conf == 1.0
    ), f"Unsupported confidence {interval_conf}; try 1.0, 0.99, 0.95, 0.9, or 0.75"

    def get_singular(df, label, field):
        value = set(df[df["label"] == label][field])
        assert len(value) == 1
        return list(value)[0]

    new_data = []
    for label in set(bootstrap_df["label"]):
        truth = get_singular(bootstrap_df, label, "Ground Truth")
        values = bootstrap_df[bootstrap_df["label"] == label]["Optimized Value"]
        median = np.median(values)
        mean = np.average(values)
        value = median if use_median else mean
        if ci_mult is None:
            c95_low = value - min(values)
            c95_hi = max(values) - value
            std_err = None
        else:
            # numpy defaults to population stddev, so set degrees of freedom to 1
            std_err = np.std(values, ddof=1)
            c95_low = max(0, (ci_mult * std_err))
            c95_hi = max(0, (ci_mult * std_err))
        new_data.append(
            {
                "label": label,
                "kind": get_singular(bootstrap_df, label, "kind"),
                "description": get_singular(bootstrap_df, label, "description"),
                "Parameter Type": get_singular(bootstrap_df, label, "Parameter Type"),
                "Ground Truth": truth,
                "Optimized Value": value,
                "err_low": c95_low,
                "err_hi": c95_hi,
                "min": min(values),
                "max": max(values),
                "std": std_err,
                "Epochs": get_singular(bootstrap_df, label, "Epochs"),
                "covered": (truth >= (value - c95_low) and truth <= (value + c95_hi)),
                "param_index": get_singular(bootstrap_df, label, "Unnamed: 0"),
            }
        )
    return pd.DataFrame.from_dict(new_data).sort_values("param_index")


def draw_graphs(
    model_file: str,
    ax,
    grid_cols: Optional[int] = None,
    epoch_spacing: float = 0.5,
    epoch_label_spacing: Optional[float] = 0.15,
    max_node_size: int = 800,
    migrate_color: Optional[str] = None,
    popsize_color: Optional[str] = None,
    x_offset: float = 0.25,
    coal_values: Optional[List[float]] = None,
    mig_values: Optional[List[float]] = None,
    cax=None,
    cmap=None,
    min_max_migrate: Optional[Tuple[float, float]] = None,
):
    """
    Draw the topology of the given input mrpast model file on the given matplotlib axis.

    :param model_file: The mrpast model filename.
    :param ax: The matplotlib axis object.
    :param grid_cols: Default is None. When set to an integer, layout the graphs in a grid
        with the given number of columns. For example, if you have a 6-deme model then you
        might want to set grid_cols=2 or grid_cols=3 to lay the graph out as 3x2 or 2x3.
    :param epoch_spacing: Spacing between each epoch in the figure.
    :param epoch_label_spacing: Spacing between the epoch label and the epoch graph. Set to
        None to disable epoch labels.
    :param max_node_size: The maximum size that a particular node can be.
    :param migrate_color: The color to use for migration edges. By default, a spectrum of
        colors is used which indicates a higher (darker color) or lower (lighter color) rate.
    :param popsize_color: The color to use for deme nodes. By default, the
        matplotlib.pyplot.cm.Dark2 colormap is used.
    :param x_offset: The offset from the X-axis to start drawing.
    :param coal_values: If non-None, use this list of coalescence rate values instead of the
        ground-truth values from the model. This only works if the model has densely packed
        parameters, with no parameter index gaps.
    :param mig_values: If non-None, use this list of migration rate values instead of the
        ground-truth values from the model. This only works if the model has densely packed
        parameters, with no parameter index gaps.
    :param min_max_migrate: Optional tuple of (min, max) float values, which are the minimum
        and maximum possible migration rate values for the purposes of coloring the edges.
    """
    assert (
        nx is not None and plt is not None
    ), "Plotting requires networkx and matplotlib; run 'pip install networkx matplotlib'"
    if cmap is None:
        cmap = plt.cm.RdYlBu  # type: ignore
    G = nx.DiGraph()
    model = mrpast.model.UserModel.from_file(model_file)
    base_node_id = 0
    node_sizes = []
    node_colors = []
    y_offset = 0.0
    pos: Optional[Dict[Any, Any]] = None

    # FIXME: neither of these functions work if there are gaps in the parameter indexing.
    def get_coal_value(coal_param_idx):
        if coal_values is not None:
            return coal_values[coal_param_idx - 1]
        return model.coalescence.get_parameter(coal_param_idx).ground_truth

    def get_mig_value(mig_param_idx):
        if mig_values is not None:
            return mig_values[mig_param_idx - 1]
        return model.migration.get_parameter(mig_param_idx).ground_truth

    # Use the average of the ground truth values as our normalizing factor.
    avg_mig = 0.0
    for p in model.migration.parameters:
        avg_mig += p.ground_truth
    avg_mig /= len(model.migration.parameters)

    def norm_mig(mr):
        return math.log10(mr / avg_mig)

    max_popsize = 0
    for entry in model.coalescence.entries:
        if isinstance(entry.rate, mrpast.model.ParamRef):
            cr = get_coal_value(entry.rate.param)
        else:
            cr = entry.rate
        pop_size = 1 / (model.ploidy * cr)
        if pop_size > max_popsize:
            max_popsize = pop_size

    for epoch in reversed(range(model.num_epochs)):
        pop_sizes = [0 for _ in range(model.num_demes)]
        for i in range(model.num_demes):
            entry = model.coalescence.get_entry(epoch, i)
            if entry is not None:
                if isinstance(entry.rate, mrpast.model.ParamRef):
                    cr = get_coal_value(entry.rate.param)
                else:
                    cr = entry.rate
                pop_sizes[i] = 1 / (model.ploidy * cr)

        nodes = [i for i in range(model.num_demes) if pop_sizes[i] > 0]
        node_sizes.extend(
            [max(0, (pop_sizes[i] / max_popsize) * max_node_size) for i in nodes]
        )
        node_colors.extend(nodes)

        for i in nodes:
            G.add_node(base_node_id + i)
            for j in range(model.num_demes):
                entry = model.migration.get_entry(epoch, i, j)
                if entry is not None:
                    if isinstance(entry.rate, mrpast.model.ParamRef):
                        w = norm_mig(get_mig_value(entry.rate.param))
                    else:
                        w = norm_mig(entry.rate)
                    G.add_edge(
                        base_node_id + i,
                        base_node_id + j,
                        weight=w,
                    )

        if grid_cols is not None:
            if pos is None:
                pos = {}
            pos.update(
                {
                    base_node_id
                    + node: (x_offset + (i % grid_cols), y_offset - (i // grid_cols))
                    for i, node in enumerate(nodes)
                }
            )
            if epoch_label_spacing is not None:
                ax.text(x_offset, y_offset + epoch_label_spacing, f"Epoch {epoch}")
            y_offset -= (len(nodes) // grid_cols) + epoch_spacing
        else:
            pos = None
        base_node_id += model.num_demes

    weights = [G[u][v]["weight"] for u, v in G.edges()]
    min_edge_color = (
        norm_mig(min_max_migrate[0]) if min_max_migrate else min(weights)
    ) * 1.25
    max_edge_color = norm_mig(min_max_migrate[1]) if min_max_migrate else max(weights)
    if popsize_color is None:
        node_options = {
            "node_size": node_sizes,
            "node_color": node_colors,
            "cmap": plt.cm.Dark2,  # type: ignore
            "linewidths": 2,
        }
    else:
        node_options = {
            "node_size": node_sizes,
            "node_color": popsize_color,
            "linewidths": 2,
        }
    if migrate_color is None:
        edge_options = {
            "edge_color": weights,
            "width": 2,
            "edge_vmin": min_edge_color,
            "edge_vmax": max_edge_color,
            "edge_cmap": cmap,
            "connectionstyle": "arc3,rad=0.1",
        }
    else:
        edge_options = {
            "edge_color": migrate_color,
            "width": 2,
            "connectionstyle": "arc3,rad=0.1",
        }
    # print(f"Node sizes: {node_sizes}")
    # print(f"Edge weights: {weights}")
    nx.draw_networkx_nodes(G, pos=pos, **node_options, ax=ax)
    nx.draw_networkx_edges(G, pos=pos, **edge_options, ax=ax)
    ax.axis("off")

    # Colorbar "legend"
    norm_weights = mpl.colors.Normalize(vmin=min_edge_color, vmax=max_edge_color)
    if cax is not None:
        plt.colorbar(
            plt.cm.ScalarMappable(cmap=cmap, norm=norm_weights),
            orientation="vertical",
            cax=cax,
        )


def get_matching_colors(num_demes, demes=[]):
    if demes:
        return {
            f"{demes[i]}": plt.cm.Dark2(c)
            for i, c in enumerate(np.linspace(0, 1, num_demes))
        }
    return {
        f"pop_{i}": plt.cm.Dark2(c) for i, c in enumerate(np.linspace(0, 1, num_demes))
    }


def tab_show(filename: str, sort_by: str = "Index"):
    """
    Print an ASCII table showing the parameter values and their error from ground truth, for the
    given JSON output from the solver.
    """
    with open(filename) as f:
        output = json.load(f)

    parameter_keys = (
        "epoch_times_gen",
        "smatrix_values_ne__gen",
        "amatrix_parameters",
    )

    all_params: Iterable[Dict[str, Any]] = itertools.chain.from_iterable(
        map(lambda k: output.get(k, []) or [], parameter_keys)
    )
    results = []
    total_rel = 0.0
    total_abs = 0.0
    for param_idx, param in enumerate(all_params):
        if _param_is_synthetic(param) or _param_is_fixed(param):
            continue
        gt = param["ground_truth"]
        final = param["final"]
        abserr = abs(gt - final)
        total_abs += abserr
        relerr = abserr / gt
        total_rel += relerr
        epochs = set()
        for app in param["apply_to"]:
            epochs.add(app["epoch"])
        results.append(
            (
                param_idx,
                param["description"],
                relerr,
                abserr,
                gt,
                final,
                list(sorted(epochs)),
            )
        )

    headers = [
        "Index",
        "Description",
        "Relative Error",
        "Absolute Error",
        "Truth",
        "Final",
        "Epochs",
    ]

    try:
        sort_key = headers.index(sort_by)
    except ValueError:
        raise RuntimeError(f"Unexpected sort_by key: {sort_by}. Try one of {headers}.")
    results = sorted(results, key=lambda x: x[sort_key])
    print(tabulate(results, headers=headers))
    print()
    print(f"Total absolute error: {total_abs}")
    print(f"Total relative error: {total_rel}")

    return total_rel
