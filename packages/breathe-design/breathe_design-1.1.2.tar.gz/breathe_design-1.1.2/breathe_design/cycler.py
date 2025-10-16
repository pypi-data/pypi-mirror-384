import copy
import json
import os


class Cycler:
    """
    Represents a battery cycler protocol used in the breathe design process for dynamic analysis. Has methods to generate different battery cycler protocols in the correct format.
    """

    def __init__(self, selected_unit: str, cell_capacity: float):
        """
        Initialize a Cycler object with the selected unit and cell capacity. The default protocol is set to CC_CHG.

        Parameters:
            selected_unit (str): The unit of current (A or C) used in the cycler.
            cell_capacity (float): The capacity of the battery cell in Ah.
        """
        self._selected_unit = selected_unit
        self._cell_capacity = cell_capacity
        self._default_cycler = {
            "cycle_type": None,
            "selected_unit": selected_unit,
            "control_parameters": {},
        }
        self._protocols = self._load_protocols()

    def _load_protocols(self) -> dict:
        """
        Load cycling protocols from the JSON configuration file.

        Returns:
            dict: Dictionary containing protocol definitions with parameter limits.
        """
        # Get the directory where this module is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "cycling_protocols.json")

        try:
            with open(json_path, "r") as f:
                protocols = json.load(f)
            return protocols
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find cycling protocols file at {json_path}. "
                "Please ensure cycling_protocols.json exists in the breathe_design package directory."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in cycling protocols file: {e}")

    def cc_chg(self, I_chg: float, V_max: float) -> dict:
        """
        Create a Constant Current Charge cycler protocol.

        Parameters:
            I_chg (float): The charging current in [A || C]. Required.
            V_max (float): The maximum charging voltage in V. Required.

        Returns:
            (dict): representing the CC-CHG cycling protocol.

        """
        cycler = copy.deepcopy(self._default_cycler)
        cycler["cycle_type"] = "CC_CHG"
        cycler["control_parameters"]["I_chg"] = I_chg
        cycler["control_parameters"]["V_max"] = V_max
        return self._build_cycler_dict(cycler)

    def cc_dch(self, I_dch: float, V_min: float) -> dict:
        """
        Create a Constant Current Discharge cycler protocol.

        Args:
            I_dch (float): The discharging current in [A || C]. Required.
            V_min (float): The minimum discharging voltage in V. Required.

        Returns:
            (dict): representing the CC-DCH cycling protocol.
        """
        cycler = copy.deepcopy(self._default_cycler)
        cycler["cycle_type"] = "CC_DCH"
        cycler["control_parameters"]["I_dch"] = I_dch
        cycler["control_parameters"]["V_min"] = V_min
        return self._build_cycler_dict(cycler)

    def dcir(
        self,
        I_dch: float,
        t_dur: float,
        t_rest_before: float,
        t_rest_after: float,
        v_min: float,
        v_max: float,
    ) -> dict:
        """
        Create a Direct Current Internal Resistance (DCIR) cycler protocol.

        Parameters:
            I_dch (float): The discharging current in [A || C]. Required.
            t_dur (float): The duration of the discharge in seconds. Required.
            t_rest_before (float): The rest time before the discharge in seconds. Required.
            t_rest_after (float): The rest time after the discharge in seconds. Required.
            v_min (float): The minimum voltage in V. Required.
            v_max (float): The maximum voltage in V. Required.

        Returns:
            (dict): representing the DCIR cycling protocol.
        """
        cycler = copy.deepcopy(self._default_cycler)
        cycler["cycle_type"] = "DCIR"
        cycler["control_parameters"]["I_dch"] = I_dch
        cycler["control_parameters"]["t_dur"] = t_dur
        cycler["control_parameters"]["t_rest_before"] = t_rest_before
        cycler["control_parameters"]["t_rest_after"] = t_rest_after
        cycler["control_parameters"]["v_min"] = v_min
        cycler["control_parameters"]["v_max"] = v_max
        return self._build_cycler_dict(cycler)

    def cccv(
        self,
        I_chg: float,
        I_dch: float,
        I_cut: float,
        V_max: float,
        V_min: float,
        t_restC: float,
        t_restD: float,
    ) -> dict:
        """
        Create a Constant Current Constant Voltage (CCCV) cycler protocol.

        Parameters:
            I_chg (float): The charging current in [A || C]. Required.
            I_dch (float): The discharging current in [A || C]. Required.
            I_cut (float): The cut-off current in [A || C]. Required.
            V_max (float): The maximum charging voltage in V. Required.
            V_min (float): The minimum discharging voltage in V. Required.
            t_restC (float): The rest time (in seconds) after charging. Required.
            t_restD (float): The rest time (in seconds) after discharging. Required.

        Returns:
            (dict): representing the CCCV cycling protocol.
        """
        cycler = copy.deepcopy(self._default_cycler)
        cycler["cycle_type"] = "CCCV"
        cycler["control_parameters"]["I_chg"] = I_chg
        cycler["control_parameters"]["I_dch"] = I_dch
        cycler["control_parameters"]["I_cut"] = I_cut
        cycler["control_parameters"]["V_max"] = V_max
        cycler["control_parameters"]["V_min"] = V_min
        cycler["control_parameters"]["t_restC"] = t_restC
        cycler["control_parameters"]["t_restD"] = t_restD
        return self._build_cycler_dict(cycler)

    def rate_cap(
        self,
        I_chg: float,
        I_dch: float,
        I_cut: float,
        V_max: float,
        V_min: float,
        t_restC: float,
    ) -> dict:
        """
        Create a Rate Capacity cycler protocol.

        Parameters:
            I_chg (float): The charging current in [A || C]. Required.
            I_dch (float): The discharging current in [A || C]. Required.
            I_cut (float): The cut-off current in [A || C]. Required.
            V_max (float): The maximum charging voltage in V. Required.
            V_min (float): The minimum discharging voltage in V. Required.
            t_restC (float): The rest time (in seconds) after charging. Required.

        Returns:
            (dict): representing the RateCap cycling protocol.
        """
        cycler = copy.deepcopy(self._default_cycler)
        cycler["cycle_type"] = "RateCap"
        cycler["control_parameters"]["I_chg"] = I_chg
        cycler["control_parameters"]["I_dch"] = I_dch
        cycler["control_parameters"]["I_cut"] = I_cut
        cycler["control_parameters"]["V_max"] = V_max
        cycler["control_parameters"]["V_min"] = V_min
        cycler["control_parameters"]["t_restC"] = t_restC
        return self._build_cycler_dict(cycler)

    def _build_cycler_dict(self, cycler: dict) -> dict:
        if cycler["cycle_type"] not in self._protocols:
            raise ValueError(f"Invalid cycle type: {cycler['cycle_type']}")

        protocol_params = self._protocols[cycler["cycle_type"]]

        for param in protocol_params:
            if param not in cycler["control_parameters"]:
                raise ValueError(f"Missing required parameter: {param}")
            # copy value for checking
            value = copy.deepcopy(cycler["control_parameters"][param])
            if value is None:
                raise ValueError(f"Missing required parameter: {param}")
            if self._selected_unit == "C":
                if param in ["I_chg", "I_dch", "I_cut"]:
                    value *= (
                        self._cell_capacity
                    )  # Convert from multiples of the cell's capacity (C) to Amps

            min_val, max_val = protocol_params[param]
            if value < min_val or value > max_val:
                raise ValueError(
                    f"Invalid value for {param}. Must be between {min_val} and {max_val}."
                )

        return cycler
