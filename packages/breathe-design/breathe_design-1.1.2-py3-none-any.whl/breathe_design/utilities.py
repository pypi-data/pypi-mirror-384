def _transform_key(key):
    """
    Transforms the key to match the desired format.
    """
    transformations = {
        "anode": "Anode",
        "cathode": "Cathode",
        "electrolyte": "Electrolyte",
        "format": "Format",
        "NPratio": "NP Ratio",
        "Vmin_V": "Vmin [V]",
        "Vmax_V": "Vmax [V]",
        "cathodePorosity": "Cathode Porosity",
        "anodePorosity": "Anode Porosity",
        "cathodeThickness_um": "Cathode Thickness [um]",
        "anodeThickness_um": "Anode Thickness [um]",
        "copperThickness_um": "Copper Thickness [um]",
        "aluminumThickness_um": "Aluminum Thickness [um]",
        "separatorThickness_um": "Separator Thickness [um]",
        "electrolyteBuffer_rel": "Electrolyte Buffer",
        "capacity_Ah": "Capacity [Ah]",
        "nominalVoltage_V": "Nominal Voltage [V]",
        "energy_Wh": "Energy [Wh]",
        "gravEnergyDensity_Whkg": "Gravimetric Energy Density [Wh/kg]",
        "minimumAnodeVoltage_mV": "Minimum Anode Voltage [mV]",
        "weight_g": "Weight [g]",
        "heatCapacity_kJK": "Heat Capacity [kJ/K]",
        "volume_l": "Volume [l]",
        "volEnergyDensity_Whl": "Volumetric Energy Density [Wh/l]",
        "voltModel": "Voltage [V]",
    }
    return transformations.get(key, key)


def normalize_results(results):
    """
    Normalizes the results based on the baseline design.

    Args:
        results (pd.DataFrame): The equilibirum kpi results DataFrame.

    Returns:
        (pd.DataFrame): A normalized DataFrame containing the normalized results.
    """
    normalized_df = results.copy()
    test_designs = [col for col in results.columns if col != "Baseline"]
    for test in test_designs:
        normalized_df[test] = normalized_df[test] / normalized_df["Baseline"]
    normalized_df["Baseline"] = 1.0
    return normalized_df


def enable_notebook_plotly():
    import plotly.io as pio

    pio.renderers.default = "notebook"
