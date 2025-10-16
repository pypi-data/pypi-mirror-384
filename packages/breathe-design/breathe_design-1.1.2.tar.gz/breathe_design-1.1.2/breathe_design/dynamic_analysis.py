from typing import Literal
import numpy as np
import pandas as pd
from .api_utils import BreatheException


def extract_dynamic_kpis(
    dynamic_kpi: Literal["DCIR", "RateCap"], data: dict
) -> pd.DataFrame:
    """
    Extract KPIs from the given data and return them in a pandas DataFrame.

    Args:
        data (dict): Dictionary containing time series data for each design. Expected format: {design_name: {'Time': [...], 'voltModel': [...], 'currentModel': [...]}, ...}

    Returns:
        (pandas.DataFrame): DataFrame with columns ['Design', 'Resistance', 'Capacity'] containing the KPIs for each design
    """
    if dynamic_kpi not in ["DCIR", "RateCap"]:
        raise BreatheException(f"Invalid dynamic KPI type: {dynamic_kpi}")

    # Initialize lists to store results
    designs = []
    resistances = []
    capacities = []

    # Process each design
    for design_name in data.keys():
        t = np.asarray(data[design_name]["Time"])
        v = np.asarray(data[design_name]["voltModel"])
        i = np.asarray(data[design_name]["currModel"])

        # Find the last point before current goes negative (discharge starts)
        discharge_start_idx = np.where(i < 0)[0]
        if len(discharge_start_idx) > 0:
            # Get the voltage just before discharge starts
            v_before_discharge = (
                v[discharge_start_idx[0] - 1] if discharge_start_idx[0] > 0 else v[0]
            )
        else:
            # If no discharge found, use first voltage
            v_before_discharge = v[0]

        i_map = i < 0
        t = t[i_map]
        v = v[i_map]
        i = i[i_map]
        # Calculate resistance and capacity
        resistance = np.abs((v_before_discharge - v[-1]) / np.mean(i))
        capacity = np.abs(np.trapezoid(i, t) / 3600)

        # Store results
        designs.append(design_name)
        resistances.append(resistance)
        capacities.append(capacity)

    # Create DataFrame
    if dynamic_kpi == "DCIR":
        results_df = pd.DataFrame({"Design": designs, "Resistance (Ω)": resistances})
    elif dynamic_kpi == "RateCap":
        results_df = pd.DataFrame({"Design": designs, "Capacity (Ah)": capacities})

    return results_df
