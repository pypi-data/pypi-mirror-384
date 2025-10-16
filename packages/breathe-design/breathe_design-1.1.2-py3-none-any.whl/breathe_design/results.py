"""
Results handler classes for Breathe Design simulation outputs.

This module provides convenient interfaces for working with simulation results,
including easy access to KPIs, dynamic data, and integrated plotting capabilities.
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .plots import plot_dynamic_response, plot_kpis, radar_plot
from .plots import plot_sensitivities as plot_sensitivities_plot
from .utilities import _transform_key, normalize_results
from .dynamic_analysis import extract_dynamic_kpis


class SingleSimulationResults:
    """
    A simple results handler for a single simulation.

    This class provides easy access to KPIs, dynamic data, and plotting capabilities
    for a single simulation result.
    """

    def __init__(self, result: dict):
        """
        Initialize the SingleSimulationResults handler.

        Args:
            result: Output from run_sim function (single dict)
        """
        self._result = result
        self._input_parameters = result.get("input_parameters", {})

    def _format_kpis(self) -> pd.DataFrame:
        """Format KPIs using the same logic as the API interface."""
        kpis = self._result["KPIs"]
        if "KPInames" in self._result:
            kpi_names = [_transform_key(key) for key in self._result["KPInames"]]
            results_df = pd.DataFrame(kpis)
            results_df["KPI"] = kpi_names
            results_df = results_df[
                ["KPI"] + [col for col in results_df.columns if col != "KPI"]
            ]
            return results_df.set_index("KPI")
        else:
            return pd.DataFrame(kpis)

    @property
    def kpis(self) -> pd.DataFrame:
        """Get formatted KPIs."""
        return self._format_kpis()

    @property
    def dynamic_data(self) -> dict:
        """Get dynamic data."""
        return self._result.get("dynamicData", {})

    @property
    def design_names(self) -> list[str]:
        """Get list of design names."""
        return list(self.kpis.columns)

    @property
    def baseline(self) -> pd.Series:
        """Get KPIs for the Baseline design if it exists."""
        if "Baseline" in self.kpis.columns:
            return self.kpis["Baseline"]
        elif len(self.kpis.columns) > 0:
            # If no Baseline, return the first design
            return self.kpis.iloc[:, 0]
        else:
            return pd.Series()

    @property
    def capacity(self) -> float:
        """Get the capacity value for the Baseline design (or first design if no Baseline)."""
        baseline_kpis = self.baseline
        if "Capacity [Ah]" in baseline_kpis.index:
            return baseline_kpis["Capacity [Ah]"]
        elif "capacity_Ah" in baseline_kpis.index:
            return baseline_kpis["capacity_Ah"]
        else:
            raise ValueError("Capacity KPI not found in results")

    def get_kpis(self, design_name: str | None = None) -> pd.DataFrame:
        """Get KPIs for specific design(s)."""
        if design_name is None:
            return self.kpis
        if design_name is not None and design_name not in self.kpis.columns:
            raise ValueError(
                f"Design {design_name} not found. Cannot normalize results."
            )
        return self.kpis[design_name]

    def get_normalized_kpis(self, design_name: str = None) -> pd.DataFrame:
        """
        Get normalized KPIs relative to the Baseline design.

        Args:
            design_name (str, optional): Specific design(s) to include. If None, includes all designs.

        Returns:
            pd.DataFrame: Normalized KPIs with Baseline = 1.0 and other designs as ratios

        Raises:
            ValueError: If no Baseline design is found
        """
        kpis = self.get_kpis(design_name)

        # Check if Baseline exists
        if "Baseline" not in kpis.columns:
            raise ValueError("No Baseline design found. Cannot normalize results.")
        if design_name is not None and design_name not in kpis.columns:
            raise ValueError(
                f"Design {design_name} not found. Cannot normalize results."
            )

        return normalize_results(kpis)

    def get_dynamic_data(self, design_name: str | None = None) -> dict:
        """Get dynamic data for specific design(s)."""
        if design_name is None:
            return self.dynamic_data
        return (
            {design_name: self.dynamic_data[design_name]}
            if design_name in self.dynamic_data
            else {}
        )

    def compare_designs(
        self, plot_type: str = "relative", designs: list[str] | None = None
    ) -> go.Figure:
        """Compare designs using KPI plots."""
        kpis = self.kpis
        # Check if we only have Baseline
        if len(kpis.columns) == 1 and "Baseline" in kpis.columns:
            raise ValueError("Only Baseline design found. Cannot compare designs.")
        if designs:
            available_designs = [d for d in designs if d in kpis.columns]
            if available_designs:
                kpis = kpis[available_designs]
        if plot_type == "radar":
            return radar_plot(kpis)
        else:
            return plot_kpis(kpis, plot_type)

    def plot_voltage_response(self, design_name: str | None = None) -> go.Figure:
        """Plot voltage response for specified design."""
        return self.plot_dynamic_response("voltModel", design_name)

    def plot_dynamic_response(
        self, variable_name: str = "voltModel", design_name: str | None = None
    ) -> go.Figure:
        """Plot dynamic response for specified variable and design."""
        dynamic_data = self.get_dynamic_data(design_name)
        if not dynamic_data:
            raise ValueError("No dynamic data available for this simulation")
        return plot_dynamic_response(dynamic_data, variable_name)

    def dynamic_kpis(
        self, dynamic_kpi_type: str, design_name: str | None = None
    ) -> pd.DataFrame:
        """
        Extract dynamic KPIs for specified type and design.

        This method checks if the cycler type matches the requested KPI type
        and extracts the appropriate metrics.

        Args:
            dynamic_kpi_type (str): Type of dynamic KPI to extract ("DCIR" or "RateCap")
            design_name (str, optional): Specific design to analyze. If None, analyzes all designs.

        Returns:
            pd.DataFrame: DataFrame containing the extracted dynamic KPIs

        Raises:
            ValueError: If the cycler type doesn't match the requested KPI type
        """
        # Check dynamic data is not {}
        if not self.dynamic_data:
            raise ValueError("No dynamic data available for this simulation")
        # Check if we have cycler information to validate the request
        if hasattr(self, "_result") and "cycler" in self._result:
            cycler_type = self._result.get("cycler", {}).get("cycle_type", "")
            if dynamic_kpi_type == "DCIR" and cycler_type != "DCIR":
                raise ValueError(
                    f"Requested DCIR KPIs but cycler type is {cycler_type}"
                )
            elif dynamic_kpi_type == "RateCap" and cycler_type not in [
                "CC_CHG",
                "CC_DCH",
            ]:
                raise ValueError(
                    f"Requested RateCap KPIs but cycler type is {cycler_type}"
                )

        dynamic_data = self.get_dynamic_data(design_name)
        return extract_dynamic_kpis(dynamic_kpi_type, dynamic_data)

    def plot_sensitivities(self) -> go.Figure:
        """Plot sensitivity heatmap for the simulation."""
        if "KPInames" not in self._result or "Sensitivities" not in self._result:
            raise ValueError("Sensitivity data not available for this simulation")

        kpi_names = self._result["KPInames"]
        sensitivities = self._result["Sensitivities"]
        return plot_sensitivities_plot(kpi_names, sensitivities)

    def plot_radar(self, designs: list[str] = None) -> go.Figure:
        """
        Create a radar plot comparing designs across KPIs.

        Args:
            designs (list[str], optional): Specific designs to include. If None, includes all designs.

        Returns:
            go.Figure: Radar plot figure
        """
        # Check if we only have Baseline
        if len(self.kpis.columns) == 1 and "Baseline" in self.kpis.columns:
            raise ValueError("Only Baseline design found. Cannot compare designs.")
        kpis = self.get_normalized_kpis(designs)
        return radar_plot(kpis)

    def get_input_parameters(self) -> dict:
        """Get the original input parameters used for the simulation."""
        return self._input_parameters.copy()

    def get_summary(self) -> dict:
        """Get a summary of the simulation results."""
        return {
            "is_batch": False,
            "num_simulations": 1,
            "design_names": self.design_names,
            "num_designs": len(self.design_names),
            "input_parameters": self._input_parameters,
        }

    def print_dynamic_variables(self):
        """Print dynamic variables in the dynamic data for the specified design."""
        if not self.dynamic_data:
            raise ValueError("No dynamic data available for this simulation")
        design_name = "Baseline"
        if design_name in self.dynamic_data:
            print("Available variables:")
            for var in self.dynamic_data[design_name].keys():
                print(var)
        else:
            print(f"No dynamic data available for {design_name}")


class BatchSimulationResults:
    """
    A results handler for multiple simulations.

    This class handles a list of simulation results and provides methods
    for comparison and analysis across simulations.
    """

    def __init__(self, results: list[dict]):
        """
        Initialize the BatchSimulationResults handler.

        Args:
            results: list of outputs from run_sim function
        """
        self._results = results
        self.num_simulations = len(results)

        # Create SingleSimulationResults objects for each result
        self._simulation_results = [
            SingleSimulationResults(result) for result in results
        ]

        # Extract input parameters from each simulation
        self._input_parameters = []
        for sim_result in self._simulation_results:
            self._input_parameters.append(sim_result.get_input_parameters())

    def _calculate_subplot_layout(self) -> tuple[int, int]:
        """
        Calculate optimal rows and columns for subplot layout.

        Returns:
            tuple: (rows, cols) for optimal subplot arrangement
        """
        if self.num_simulations <= 4:
            # For small numbers, prefer horizontal layout
            return 1, self.num_simulations
        elif self.num_simulations <= 6:
            # For medium numbers, try 2 rows
            return 2, (self.num_simulations + 1) // 2
        elif self.num_simulations <= 12:
            # For larger numbers, try 3 rows
            return 3, (self.num_simulations + 2) // 3
        else:
            # For very large numbers, calculate based on square root
            cols = int(self.num_simulations**0.5) + 1
            rows = (self.num_simulations + cols - 1) // cols
            return rows, cols

    def _generate_subplot_titles(self) -> list[str]:
        """
        Generate descriptive subplot titles based on simulation conditions.

        Returns:
            List of titles for each subplot
        """
        titles = []
        for i, sim_result in enumerate(self._simulation_results):
            params = sim_result.get_input_parameters()

            # Create a descriptive title
            title_parts = [f"Sim {i + 1}"]

            # Add key parameters if they exist
            if "initialSoC" in params:
                title_parts.append(f"SOC={params['initialSoC']}")
            if "initialTemperature_degC" in params:
                title_parts.append(f"T={params['initialTemperature_degC']}°C")
            if "ambientTemperature_degC" in params:
                title_parts.append(f"T_amb={params['ambientTemperature_degC']}°C")

            # Join with line breaks for better readability
            titles.append("<br>".join(title_parts))

        return titles

    def __len__(self):
        """Return the number of simulations."""
        return self.num_simulations

    def __getitem__(self, index):
        """Access individual simulation results by index."""
        return self._simulation_results[index]

    def __iter__(self):
        """Iterate over simulation results."""
        for sim_result in self._simulation_results:
            yield sim_result

    @property
    def first(self) -> "SingleSimulationResults":
        """Get the first simulation result."""
        return self._simulation_results[0]

    @property
    def baseline(self) -> pd.Series:
        """Get KPIs for the Baseline design from the first simulation."""
        return self.first.baseline

    @property
    def capacity(self) -> float:
        """Get the capacity value for the Baseline design from the first simulation."""
        return self.first.capacity

    @property
    def design_names(self) -> list[str]:
        """Get the design names for the first simulation."""
        return self.first.design_names

    @property
    def dynamic_data(self) -> list[dict]:
        """Get dynamic data for all simulations."""
        return [sim.dynamic_data for sim in self._simulation_results]

    def get_kpis(self, designs: list[str] | None = None) -> list[pd.DataFrame]:
        """Get KPIs for all the first simulation."""
        return self.first.get_kpis(designs)

    def get_normalized_kpis(
        self, designs: list[str] | None = None
    ) -> list[pd.DataFrame]:
        """
        Get normalized KPIs for all simulations relative to their Baseline designs.

        Args:
            designs (list[str], optional): Specific design(s) to include. If None, includes all designs.

        Returns:
            pd.DataFrame: List of normalized KPIs for each simulation

        Raises:
            ValueError: If no Baseline design is found in any simulation
        """
        return self.first.get_normalized_kpis(designs)

    def get_dynamic_data(self, design_name: str | None = None) -> list[dict]:
        """Get dynamic data for all simulations."""
        return [sim.get_dynamic_data(design_name) for sim in self._simulation_results]

    def compare_designs(
        self, plot_type: str = "relative", designs: list[str] | None = None
    ) -> go.Figure:
        """Compare designs across all simulations using subplots."""
        if plot_type == "radar":
            raise ValueError("Radar plots not supported for batch simulations")

        # Calculate optimal rows and columns for better layout
        rows, cols = self._calculate_subplot_layout()

        # Get KPIs for all simulations
        kpis_list = self.get_kpis(designs)
        # Check if we only have Baseline
        if len(kpis_list[0].columns) == 1 and "Baseline" in kpis_list[0].columns:
            raise ValueError("Only Baseline design found. Cannot compare designs.")
        # Create subplots with calculated layout
        subplot_titles = self._generate_subplot_titles()
        fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles)

        for i, kpis in enumerate(kpis_list):
            if not kpis.empty:
                temp_fig = plot_kpis(kpis, plot_type)
                # Calculate row and column position
                row = (i // cols) + 1
                col = (i % cols) + 1
                for trace in temp_fig.data:
                    fig.add_trace(trace, row=row, col=col)

        fig.update_layout(
            title=f"Design Comparison - {plot_type.title()}",
            height=300 * rows,
            # Add margin to prevent title overlap
            margin=dict(t=100),
            # Reduce subtitle text size
            font=dict(size=10),
        )
        return fig

    def plot_dynamic_response(
        self, variable_name: str = "voltModel", design_name: str | None = None
    ) -> go.Figure:
        """Plot dynamic response across all simulations using subplots."""
        # Check if dynamic data is available for any simulation
        if not self._simulation_results[0].dynamic_data:
            raise ValueError("No dynamic data available.")

        # Calculate optimal rows and columns for better layout
        rows, cols = self._calculate_subplot_layout()
        subplot_titles = self._generate_subplot_titles()
        fig = make_subplots(rows=rows, cols=cols, subplot_titles=subplot_titles)

        for i, sim_result in enumerate(self._simulation_results):
            temp_fig = sim_result.plot_dynamic_response(variable_name, design_name)
            # Calculate row and column position
            row = (i // cols) + 1
            col = (i % cols) + 1
            for trace in temp_fig.data:
                fig.add_trace(trace, row=row, col=col)

        fig.update_layout(height=300 * rows)
        return fig

    def plot_voltage_response(self, design_name: str | None = None) -> go.Figure:
        """Plot voltage response across all simulations using subplots."""
        return self.plot_dynamic_response("voltModel", design_name)

    def dynamic_kpis(
        self, dynamic_kpi_type: str, design_name: str | None = None
    ) -> list[pd.DataFrame]:
        """
        Extract dynamic KPIs for all simulations.

        This method checks if the cycler type matches the requested KPI type
        and extracts the appropriate metrics for each simulation.

        Args:
            dynamic_kpi_type (str): Type of dynamic KPI to extract ("DCIR" or "RateCap")
            design_name (str, optional): Specific design to analyze. If None, analyzes all designs.

        Returns:
            list[pd.DataFrame]: list of DataFrames containing the extracted dynamic KPIs for each simulation

        Raises:
            ValueError: If the cycler type doesn't match the requested KPI type
        """
        return [
            sim.dynamic_kpis(dynamic_kpi_type, design_name)
            for sim in self._simulation_results
        ]

    def plot_sensitivities(self) -> go.Figure:
        """Plot sensitivity heatmap for the first simulation in the batch."""
        return self.first.plot_sensitivities()

    def plot_radar(self, designs: list[str] | None = None) -> go.Figure:
        """
        Create a radar plot comparing designs across KPIs for the first simulation.

        Args:
            designs (list[str], optional): Specific designs to include. If None, includes all designs.

        Returns:
            go.Figure: Radar plot figure
        """
        return self.first.plot_radar(designs)

    def get_input_parameters(self) -> list[dict]:
        """Get the input parameters for all simulations."""
        return self._input_parameters.copy()

    def get_summary(self) -> dict:
        """Get a summary of all simulation results."""
        return {
            "is_batch": True,
            "num_simulations": self.num_simulations,
            "design_names": self.first.design_names if self._simulation_results else [],
            "num_designs": len(self.first.design_names)
            if self._simulation_results
            else 0,
            "input_parameters": self._input_parameters,
        }

    def print_dynamic_variables(self):
        """Print dynamic variables in the dynamic data for the first simulation."""
        self.first.print_dynamic_variables()
