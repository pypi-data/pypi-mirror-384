import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from .utilities import _transform_key, normalize_results

# Breathe Hex Codes
hex_colors = ["#00c34e", "#9bda9e", "#ffffff", "#e0dcda", "#b8aea7"]


def plot_sensitivities(kpi_names, sensitivities):
    """
    Create a heatmap plot of sensitivities for different KPIs and parameters.

    This function generates a heatmap visualization of the sensitivity values
    for various Key Performance Indicators (KPIs) with respect to different parameters.
    The heatmap is normalized for each KPI to enhance visual comparison.

    Args:
        kpi_names (list): A list of strings representing the names of the KPIs.
        sensitivities (dict): A dictionary where keys are parameter names and values are lists of sensitivity values corresponding to each KPI.

    Returns:
        (plotly.Figure): A Plotly Figure object representing the sensitivity heatmap, which can be displayed or further modified.
    """
    kpi_names = [_transform_key(key) for key in kpi_names]
    param_names = [_transform_key(key) for key in sensitivities.keys()]
    sensitivity_values = list(sensitivities.values())

    heatmap_data = np.array(sensitivity_values)
    for k in range(len(kpi_names)):
        normalizer = np.max(np.abs(heatmap_data[:, k]))
        if normalizer > 0:
            heatmap_data[:, k] *= 1 / normalizer

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data,
            x=kpi_names,
            y=param_names,
            colorscale=hex_colors,
            reversescale=True,
            text=[[f"{val:.2f}" for val in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont={"size": 10},
        )
    )

    fig.update_layout(
        title="Sensitivity Heatmap",
        xaxis_title="KPIs",
        yaxis_title="Parameters",
        xaxis_tickangle=-45,
        width=800,
        height=600,
        paper_bgcolor="rgba(240, 240, 240, 1)",
        plot_bgcolor="rgba(240, 240, 240, 1)",
    )

    return fig


def plot_kpis(results, plot_type):
    """
    Create a horizontal bar plot comparing KPI values of different designs to a baseline.

    This function generates a plotly figure that visualizes the performance
    of various design alternatives compared to a baseline design for different Key
    Performance Indicators (KPIs).

    Args:
        results (pandas.DataFrame): A DataFrame containing KPI values for different designs. It should have columns for 'KPI', 'Baseline', and other design alternatives.
        plot_type (str): A string indicating the type of plot to generate. It can be either "relative" or "delta".

    Returns:
        (plotly.Figure): A Plotly Figure object representing the horizontal bar chart of KPI values, which can be displayed or further modified.
    """
    test_designs = [col for col in results.columns if col != "Baseline"]
    normalized_df = results.copy()

    if plot_type == "relative":
        for test in test_designs:
            normalized_df[test] = normalized_df[test] / normalized_df["Baseline"]
        title = "Relative Value of Designs Compared to Baseline"
        xaxis_title = "Relative Value"
    elif plot_type == "delta":
        for test in test_designs:
            normalized_df[test] = (
                normalized_df[test] - normalized_df["Baseline"]
            ) / normalized_df["Baseline"]
        title = "Delta Value of Designs Compared to Baseline"
        xaxis_title = "Delta Value"
    else:
        raise ValueError(
            "Invalid plot_type. It should be either 'relative' or 'delta'."
        )

    fig = go.Figure()

    for i, test in enumerate(test_designs):
        fig.add_trace(
            go.Bar(
                y=normalized_df.index,
                x=normalized_df[test],
                name=test,
                orientation="h",
                marker_color=hex_colors[i % len(hex_colors)],
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title="KPI",
        barmode="group",
        legend_title="Design",
        width=800,
        height=600,
        paper_bgcolor="rgba(240, 240, 240, 1)",
        plot_bgcolor="rgba(240, 240, 240, 1)",
    )

    return fig


def plot_voltage_response(data):
    """
    Create a line plot of voltage response for multiple designs.

    This function generates a Plotly figure that visualizes the voltage response
    of various designs over time, specifically focusing on voltage models.

    Args:
        data (dict): A dictionary where keys are design names and values are dictionaries containing 'Time' and 'voltModel' data for each design. The structure should be: {design_name: {'Time': [...], 'voltModel': [...]}, ...}

    Returns:
        (plotly.Figure): A Plotly Figure object representing the line plot of dynamic KPI performance, which can be displayed or further modified.
    """
    return plot_dynamic_response(data, "voltModel")


def plot_dynamic_response(data, variable_name="voltModel"):
    """
    Create a line plot of dynamic response for multiple designs.

    This function generates a Plotly figure that visualizes the dynamic response given the variable name.

    Args:
        data (dict): A dictionary where keys are design names and values are dictionaries containing 'Time' and 'voltModel' data for each design. The structure should be: {design_name: {'Time': [...], 'voltModel': [...]}, ...}
        variable_name (str): The name of the variable to plot. variable_name can be one of the following: Time, voltModel, voltAnode, voltCathode, ocvModel, ocvAnode, ocvCathode, tempSurfaceModel, socModel, socAnode, socCathode, currModel, heatFluxModel.


    Returns:
        (plotly.Figure): A Plotly Figure object representing the line plot of dynamic KPI performance, which can be displayed or further modified.
    """
    fig = go.Figure()

    designs = list(data.keys())
    designs = [design for design in designs if data[design] is not None]
    num_designs = len(designs)

    for i, design in enumerate(designs):
        color = px.colors.sample_colorscale(
            hex_colors, [i / (num_designs - 1) if num_designs > 1 else 0.0]
        )[0]
        fig.add_trace(
            go.Scatter(
                x=data[design]["Time"],
                y=data[design][variable_name],
                mode="lines",
                name=design,
                line=dict(color=color, width=2),
            )
        )

    fig.update_layout(
        title="Dynamic KPI Performance",
        xaxis_title="Time [s]",
        yaxis_title=_transform_key(variable_name),
        legend_title="Designs",
        width=800,
        height=600,
        paper_bgcolor="rgba(240, 240, 240, 1)",
        plot_bgcolor="rgba(240, 240, 240, 1)",
    )

    return fig


def plot_ocv(battery):
    """
    Create a scatter plot of OCV data for a battery.
    This function generates a plotly figure that visualizes the OCV data for a battery.

    Args:
        battery (dict): A dictionary containing OCV data for a battery. The structure should be: {
            "SoC": [...],
            "ChargeVoltage_V_": [...],
            "DischargeVoltage_V_": [...],
            "AnodeChargeVoltage_V_": [...]

    Returns:
        (plotly.Figure): A Plotly Figure object representing the scatter plot of OCV data, which can be displayed or further modified.
    """
    fig = go.Figure()
    x_data = battery["SoC_SoH"]
    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=battery["ChargeVoltage_V_"],
            mode="lines",
            name="Charge Voltage",
            line=dict(color=hex_colors[0], width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=battery["DischargeVoltage_V_"],
            mode="lines",
            name="Discharge Voltage",
            line=dict(color=hex_colors[0], width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=battery["AnodeChargeVoltage_V_"],
            mode="lines",
            name="Anode Charge Voltage",
            line=dict(color=hex_colors[1], width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=battery["AnodeDischargeVoltage_V_"],
            mode="lines",
            name="Anode Discharge Voltage",
            line=dict(color=hex_colors[1], width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=battery["SoC"],
            y=battery["CathodeChargeVoltage_V_"],
            mode="lines",
            name="Cathode Charge Voltage",
            line=dict(color=hex_colors[2], width=2),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=x_data,
            y=battery["CathodeDischargeVoltage_V_"],
            mode="lines",
            name="Cathode Discharge Voltage",
            line=dict(color=hex_colors[2], width=2),
        )
    )

    fig.update_layout(
        title="Open-Circuit Voltage (OCV) vs SoC",
        xaxis_title="SoC * SoH",
        yaxis_title="Voltage [V]",
        legend_title="Voltage Type",
        width=800,
        height=600,
        paper_bgcolor="rgba(240, 240, 240, 1)",
        plot_bgcolor="rgba(240, 240, 240, 1)",
    )

    return fig


def radar_plot(results):
    """
    Create a radar plot to visualize the performance of various designs.

    Args:
        results (pandas.DataFrame): A DataFrame containing the performance metrics of various designs.

    Returns:
        (plotly.Figure): A radar plot representing the performance of various designs.
    """
    # Define the labels for each axis
    labels = results.index  # Use the index names as labels
    results = normalize_results(results)
    # Create the radar plot
    fig = go.Figure()
    c = 0
    for i in range(len(results.columns)):
        column = results.columns[i]
        if c == len(hex_colors):
            c = 0
        fig.add_trace(
            go.Scatterpolar(
                r=results.iloc[:, i].tolist()
                + [results.iloc[0, i]],  # Add the first value to close the shape
                theta=labels.tolist() + [labels[0]],
                fill=None,
                name=column,
                line={"color": hex_colors[c]},
            )
        )
        c += 1

    # Update the layout
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 2])), showlegend=True
    )

    return fig
