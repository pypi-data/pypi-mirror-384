import random
from typing import Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

import os
import plotly.io as pio

pio.renderers.default = os.getenv(
    "BREATHE_PLOTLY_RENDERER", "plotly_mimetype+notebook_connected"
)


# =====================================================================
# Monte Carlo Generator
# =====================================================================


def make_manufacturing_variations(
    base_design: dict[str, Any],
    n_samples: int = 10,
    bound_range: float | list[float] = 0.05,
    sigma_fraction: float | list[float] | None = None,
    seed: int | None = None,
    param_pairs: list[tuple[str, str]] | None = None,
    round_ndigits: int = 5,
    eps: float = 1e-12,
    design_name_format: str = "MC Variation sample #%i",
) -> list[dict[str, float]]:
    """Returns a list of dicts. Each dict contains the parameters that changed
    (vs. base_design) for that Monte Carlo sample, plus a designName.

    - Auto-detects anode/cathode numeric pairs by matching "anode{S}" with "cathode{S}".
    - Each parameter varies *independently*.
    - Values are clipped to ±`bound_range` around base values.
    - Includes a "designName" for each sample.

    Args:
        base_design (dict[str, Any]): The base design dictionary.
        n_samples (int, optional): Number of samples to generate. Defaults to 10.
        bound_range (float | list[float], optional): Sample variations are bound between ± this fraction of the base value.  A list of fractions for each parameter can be provided, or, a single number in which case that fraction is used for all parameters. Defaults to 0.05.
        sigma_fraction (float | list[float] | None, optional): The width of the normal distribution sampled.  A list of fractions for each parameter can be provided, or, a single number in which case that width is used for all parameters. Defaults to None.
        param_pairs (list[tuple[str, str]] | None, optional): A list of parameters to vary.  Each entry just be a pair of parameters for the anode and cathode, where the strings match keys in the base design. If None are provided, the list is inferred by selecting pairs of parameters from the base design that start with anode and cathode.  Defaults to None.
        round_ndigits (int, optional): Defaults to 5.
        eps (float, optional):  Defaults to 1e-12.
        design_name_format (str, optional): A format string used to generate the design name for each sample, which must contain a single %i for the sample number (which starts from 1). Defaults to "MC Variation sample #%i" e.g. which would cause the first sample to have design name "MC Variation sample #1".

    Returns:
        design_changes (list[dict[str, float]]): List of design changes for each sample.
    """

    def _is_numeric(x: Any) -> bool:
        return isinstance(x, (int, float)) and not isinstance(x, bool)

    if seed is not None:
        random.seed(seed)

    if param_pairs is None:
        exclude = {"anode", "cathode"}
        anode_keys = [
            k for k in base_design if k.startswith("anode") and k not in exclude
        ]
        cathode_set = {
            k for k in base_design if k.startswith("cathode") and k not in exclude
        }
        inferred: list[tuple[str, str]] = []
        for ak in anode_keys:
            ck = "cathode" + ak[len("anode") :]
            if (
                ck in cathode_set
                and _is_numeric(base_design.get(ak))
                and _is_numeric(base_design.get(ck))
            ):
                inferred.append((ak, ck))
        param_pairs = inferred

    if not param_pairs:
        raise ValueError("No numeric anode/cathode parameter pairs found.")

    if isinstance(bound_range, float):
        bound_range = [bound_range] * len(param_pairs)
    elif len(bound_range) != len(param_pairs):
        raise ValueError(
            "bound_range must be a float or list of floats with the same length as param_pairs"
        )

    if sigma_fraction is None:
        sigma_fraction = [br / 3.0 for br in bound_range]
    elif isinstance(sigma_fraction, float):
        sigma_fraction = [sigma_fraction] * len(param_pairs)
    elif len(sigma_fraction) != len(param_pairs):
        raise ValueError(
            "sigma_fraction must be a float or list of floats with the same length as param_pairs"
        )

    stats: dict[str, tuple[float, float, float, float]] = {}
    for i, (an_key, ca_key) in enumerate(param_pairs):
        mean_an = float(base_design[an_key])
        mean_ca = float(base_design[ca_key])

        sigma_an = mean_an * sigma_fraction[i]
        sigma_ca = mean_ca * sigma_fraction[i]

        lo_an, hi_an = mean_an * (1 - bound_range[i]), mean_an * (1 + bound_range[i])
        lo_ca, hi_ca = mean_ca * (1 - bound_range[i]), mean_ca * (1 + bound_range[i])

        stats[an_key] = (mean_an, sigma_an, lo_an, hi_an)
        stats[ca_key] = (mean_ca, sigma_ca, lo_ca, hi_ca)

    designs_only_changes: list[dict[str, float]] = []

    for i in range(n_samples):
        changed: dict[str, Any] = {"designName": design_name_format % (i + 1)}

        for an_key, ca_key in param_pairs:
            mean_an, sigma_an, lo_an, hi_an = stats[an_key]
            mean_ca, sigma_ca, lo_ca, hi_ca = stats[ca_key]

            z_an = random.gauss(0.0, 1.0)
            z_ca = random.gauss(0.0, 1.0)

            an_val = min(max(mean_an + z_an * sigma_an, lo_an), hi_an)
            ca_val = min(max(mean_ca + z_ca * sigma_ca, lo_ca), hi_ca)

            an_rounded = round(
                an_val + (0 if abs(an_val - mean_an) > eps else 0.0), round_ndigits
            )
            ca_rounded = round(
                ca_val + (0 if abs(ca_val - mean_ca) > eps else 0.0), round_ndigits
            )

            if an_rounded != round(mean_an, round_ndigits):
                changed[an_key] = an_rounded
            if ca_rounded != round(mean_ca, round_ndigits):
                changed[ca_key] = ca_rounded

        designs_only_changes.append(changed)

    return designs_only_changes


# =====================================================================
# Plotting Utilities
# =====================================================================


# Breathe Hex Codes
hex_colors = ["#00c34e", "#9bda9e", "#ffffff", "#e0dcda", "#b8aea7"]


def _transform_key(k: str) -> str:
    """Fallback key transformer — customize if you want prettier labels."""
    return k


def plot_scatter_matrix(
    base_design: dict[str, Any],
    changes: list[dict[str, Any]],
    param_keys: list[str],
    title: str = "Manufacturing variations",
    marker_size: int = 6,
    tickangle: int | None = -45,
) -> go.Figure:
    """Create a Plotly scatter-plot matrix (SPLOM) for selected parameters.

    Args:
        base_design (dict[str, Any]): The base design dictionary, typically from 'api.get_design_parameters'.
        changes (list[dict[str, Any]]): List of the design changes generated by 'make_manufacturing_variations'.
        param_keys (list[str]): A list of parameter keys to plot.
        title (str, optional): Plot title. Defaults to "Manufacturing variations".
        tickangle (int | None, optional): Tilt labels if needed. Defaults to -45.

    Returns:
        (plotly.Figure): A Plotly figure object.
    """
    samples = []
    for ch in changes:
        d = dict(base_design)
        d.update(ch)
        samples.append(d)

    data = {k: [s.get(k, None) for s in samples] for k in param_keys}

    fig = go.Figure(
        data=go.Splom(
            dimensions=[
                dict(label=_transform_key(k), values=data[k]) for k in param_keys
            ],
            marker=dict(
                color=hex_colors[0],
                size=marker_size,
                line=dict(width=0.5, color="rgba(0,0,0,0.3)"),
            ),
            diagonal_visible=True,
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=14)),
        width=800,
        height=600,
        paper_bgcolor="rgba(240,240,240,1)",
        plot_bgcolor="rgba(240,240,240,1)",
        font=dict(size=8),
    )

    fig.update_xaxes(tickfont=dict(size=8), showgrid=True)
    fig.update_yaxes(tickfont=dict(size=8), showgrid=True)
    if tickangle is not None:
        fig.update_xaxes(tickangle=tickangle)

    fig.show()

    return fig


def plot_variation_histograms(
    base_design: dict[str, Any],
    changes: list[dict[str, Any]],
    param_keys: list[str],
    title: str = "Distribution of Manufacturing Variations",
    bins: int = 30,
) -> go.Figure:
    """Create a 2×2 subplot of histograms for selected parameters.

    Use this function to visualise the samples generated by 'make_manufacturing_variations'.

    Args:
        base_design (dict[str, Any]): The base design dictionary, typically from 'api.get_design_parameters'.
        changes (list[dict[str, Any]]): The list of design changes generated by 'make_manufacturing_variations'.
        param_keys (list[str]): A list of parameter keys to plot.
        title (str, optional): Plot title. Defaults to "Distribution of Manufacturing Variations".
        bins (int, optional): Number of bins in the histograms. Defaults to 30.

    Returns:
        (plotly.Figure): A Plotly figure object.
    """
    samples = []
    for ch in changes:
        d = dict(base_design)
        d.update(ch)
        samples.append(d)

    fig = make_subplots(
        rows=2, cols=2, subplot_titles=[_transform_key(k) for k in param_keys]
    )

    for i, key in enumerate(param_keys):
        row, col = divmod(i, 2)
        row += 1
        col += 1
        vals = [s.get(key) for s in samples if isinstance(s.get(key), (int, float))]
        fig.add_trace(
            go.Histogram(
                x=vals,
                nbinsx=bins,
                marker_color=hex_colors[i % len(hex_colors)],
                opacity=0.75,
                name=_transform_key(key),
            ),
            row=row,
            col=col,
        )

    fig.update_layout(
        title=title,
        width=900,
        height=700,
        paper_bgcolor="rgba(240,240,240,1)",
        plot_bgcolor="rgba(240,240,240,1)",
        bargap=0.05,
    )
    fig.show()

    return fig


def plot_capacity_histogram(df, title="Distribution of Capacity [Ah]", bins=20):
    """
    Plot a histogram of capacity values [Ah] across all designs.

    Args:
        df (pd.DataFrame): DataFrame with KPI names as the index (rows).
                           Must contain 'Capacity [Ah]' as a row.
        title (str): Title for the plot.
        bins (int): Number of histogram bins.

    Returns:
        (plotly.Figure): A Plotly figure object.
    """
    if "Capacity [Ah]" not in df.index:
        raise KeyError("'Capacity [Ah]' row not found in DataFrame index.")

    values = df.loc["Capacity [Ah]"].values

    fig = go.Figure(
        data=go.Histogram(
            x=values,
            nbinsx=bins,
            marker=dict(color=hex_colors[0]),
            opacity=0.75,
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Capacity [Ah]",
        yaxis_title="Count",
        bargap=0.05,
        width=800,
        height=600,
        paper_bgcolor="rgba(240,240,240,1)",
        plot_bgcolor="rgba(240,240,240,1)",
    )

    fig.show()

    return fig


def plot_dcir_histogram(
    df, title="Distribution of DCIR", bins=20, include_baseline=True
) -> go.Figure:
    """
    Plot a histogram of DCIR resistance values across all designs.

    Args:
        df (pd.DataFrame): DataFrame with at least "Resistance (Ω)" column.
                           Also should contain a "Design" column.
        title (str): Title for the plot.
        bins (int): Number of histogram bins.
        include_baseline (bool): Whether to include 'Baseline' in the histogram.

    Returns:
        (plotly.Figure): A Plotly figure object.
    """
    if "Resistance (Ω)" not in df.columns:
        raise KeyError("'Resistance (Ω)' column not found in DataFrame.")

    if not include_baseline and "Design" in df.columns:
        values = df.loc[df["Design"] != "Baseline", "Resistance (Ω)"].values
    else:
        values = df["Resistance (Ω)"].values

    fig = go.Figure(
        data=go.Histogram(
            x=values,
            nbinsx=bins,
            marker=dict(color=hex_colors[1]),
            opacity=0.75,
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title="Resistance (Ω)",
        yaxis_title="Count",
        bargap=0.05,
        width=800,
        height=600,
        paper_bgcolor="rgba(240,240,240,1)",
        plot_bgcolor="rgba(240,240,240,1)",
    )

    fig.show()

    return fig


def plot_capacity_resistance_heatmap(
    kpi_df: pd.DataFrame,
    dcir_df: pd.DataFrame,
    changes: list[dict[str, Any]],
    base_design: dict[str, Any],
    capacity_row_label: str = "Capacity [Ah]",
    resistance_col: str = "Resistance (Ω)",
    design_col: str = "Design",
    include_baseline: bool = True,
    bins: tuple[int, int] = (30, 30),
    title: str = "Capacity vs DCIR",
    marker_size: int = 8,
):
    """Heatmap-style scatter: Capacity [Ah] on x, Resistance (Ω) on y,
    hover shows the varied design parameters for each sample.

    Args:
        kpi_df (pd.DataFrame): KPIs dataframe.
        dcir_df (pd.DataFrame): DCIR dataframe.
        changes (list[dict[str, Any]]): List of design changes generated by 'make_manufacturing_variations'.
        base_design (dict[str, Any]): Base design dictionary.
        capacity_row_label (str, optional): Capacity row label. Defaults to "Capacity [Ah]".
        resistance_col (str, optional): Resistance column label. Defaults to "Resistance (Ω)".
        design_col (str, optional): Design column label. Defaults to "Design".
        include_baseline (bool, optional): Whether to include the baseline design. Defaults to True.
        bins (tuple[int, int], optional): Number of bins for the x and y axes. Defaults to (30, 30).
        title (str, optional): Plot title. Defaults to "Capacity vs DCIR".
        marker_size (int, optional): Marker size. Defaults to 8.

    Raises:
        KeyError: If the capacity row label is not found in the kpi_df index.

    Returns:
        (plotly.Figure): A Plotly figure object.
    """
    import plotly.graph_objects as go

    if capacity_row_label not in kpi_df.index:
        raise KeyError(f"'{capacity_row_label}' not found in kpi_df index.")

    cap = (
        kpi_df.loc[capacity_row_label]
        .to_frame(name=capacity_row_label)
        .reset_index()
        .rename(columns={"index": design_col})
    )

    df = cap.merge(dcir_df[[design_col, resistance_col]], on=design_col, how="inner")
    if not include_baseline:
        df = df[df[design_col] != "Baseline"]

    full_designs = []
    for i, ch in enumerate(changes, start=1):
        d = dict(base_design)
        d.update(ch)
        d["Design"] = f"MC Variation sample #{i}"
        full_designs.append(d)
    if include_baseline:
        d = dict(base_design)
        d["Design"] = "Baseline"
        full_designs.insert(0, d)

    full_designs = {d["Design"]: d for d in full_designs}

    hover_texts = []
    for _, row in df.iterrows():
        design_name = row[design_col]
        params = full_designs.get(design_name, {})
        param_str = "<br>".join(
            [f"{k}: {v}" for k, v in params.items() if isinstance(v, (int, float))]
        )
        hover_texts.append(f"Design: {design_name}<br>{param_str}")

    x = df[capacity_row_label].astype(float).to_numpy()
    y = df[resistance_col].astype(float).to_numpy()

    x_edges = np.linspace(x.min(), x.max(), bins[0] + 1)
    y_edges = np.linspace(y.min(), y.max(), bins[1] + 1)
    counts, _, _ = np.histogram2d(x, y, bins=[x_edges, y_edges])
    x_bin = np.clip(np.digitize(x, x_edges) - 1, 0, bins[0] - 1)
    y_bin = np.clip(np.digitize(y, y_edges) - 1, 0, bins[1] - 1)
    density = counts[x_bin, y_bin].astype(float)
    if density.max() > 0:
        density = density / density.max()

    fig = go.Figure(
        data=go.Scatter(
            x=x,
            y=y,
            mode="markers",
            text=hover_texts,
            hovertemplate="%{text}<extra></extra>",
            marker=dict(
                size=marker_size,
                color=hex_colors[0],
                showscale=False,
                line=dict(width=0.5, color="rgba(0,0,0,0.25)"),
            ),
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=capacity_row_label,
        yaxis_title=resistance_col,
        width=800,
        height=600,
        paper_bgcolor="rgba(240,240,240,1)",
        plot_bgcolor="rgba(240,240,240,1)",
    )

    fig.show()

    return fig
