import copy
import json
import os
from typing import Dict, List, Any, Optional


class ParameterValidator:
    """
    Unified validator for design and format parameters used in the breathe design process.
    Ensures parameters are within acceptable bounds before API calls to prevent errors.
    """

    def __init__(self):
        """
        Initialize the ParameterValidator with parameter bounds from JSON file.
        """
        self._parameter_bounds = self._load_parameter_bounds()

    def _load_parameter_bounds(self) -> dict:
        """
        Load parameter bounds from the unified JSON configuration file.

        Returns:
            dict: Dictionary containing parameter bounds with [min, max] values.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "parameter_bounds.json")

        try:
            with open(json_path, "r") as f:
                bounds = json.load(f)
            return bounds
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Could not find parameter bounds file at {json_path}. "
                "Please ensure parameter_bounds.json exists in the breathe_design package directory."
            )
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in parameter bounds file: {e}")

    def validate_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single design dictionary against parameter bounds.

        Args:
            design (Dict[str, Any]): Dictionary containing design parameters.

        Returns:
            Dict[str, Any]: The validated design dictionary.

        Raises:
            ValueError: If any parameter is out of bounds or invalid.
        """
        return self._validate_parameters(
            design, self._parameter_bounds, "design", ["designName"]
        )

    def validate_designs(self, designs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a list of design dictionaries.

        Args:
            designs (List[Dict[str, Any]]): List of design dictionaries.

        Returns:
            List[Dict[str, Any]]: List of validated design dictionaries.

        Raises:
            ValueError: If any design contains invalid parameters.
        """
        return self._validate_parameters_list(designs, self.validate_design, "Design")

    def validate_format(self, format_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single format dictionary against parameter bounds and constraints.

        Args:
            format_dict (Dict[str, Any]): Dictionary containing format parameters.

        Returns:
            Dict[str, Any]: The validated format dictionary.

        Raises:
            ValueError: If any parameter is out of bounds or invalid.
        """
        # Import here to avoid circular imports
        from .format import validate_material, validate_assembly_type

        if not isinstance(format_dict, dict):
            raise ValueError("Format must be a dictionary")

        # Make a copy to avoid modifying the original
        validated_format = copy.deepcopy(format_dict)

        # Validate required fields
        if "shape" not in validated_format:
            raise ValueError("Format must specify a 'shape' field")

        if "material" not in validated_format:
            raise ValueError("Format must specify a 'material' field")

        # Validate material and assembly type
        validate_material(validated_format["material"])
        if "assemblyType" in validated_format:
            validate_assembly_type(validated_format["assemblyType"])

        # Skip format-specific fields during parameter validation
        skip_fields = ["shape", "name", "material", "assemblyType"]

        # Validate numeric parameters
        validated_format = self._validate_parameters(
            validated_format, self._parameter_bounds, "format", skip_fields
        )

        # Shape-specific validations
        if validated_format["shape"] == "cylinder":
            self._validate_cylinder_constraints(validated_format)
        elif validated_format["shape"] == "cuboid":
            self._validate_cuboid_constraints(validated_format)

        return validated_format

    def validate_formats(self, formats: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate a list of format dictionaries.

        Args:
            formats (List[Dict[str, Any]]): List of format dictionaries.

        Returns:
            List[Dict[str, Any]]: List of validated format dictionaries.

        Raises:
            ValueError: If any format contains invalid parameters.
        """
        return self._validate_parameters_list(formats, self.validate_format, "Format")

    def _validate_parameters(
        self,
        param_dict: Dict[str, Any],
        bounds: Dict[str, List],
        param_type: str,
        skip_fields: List[str],
    ) -> Dict[str, Any]:
        """
        Core parameter validation logic.

        Args:
            param_dict (Dict[str, Any]): Dictionary containing parameters to validate.
            bounds (Dict[str, List]): Parameter bounds to validate against.
            param_type (str): Type of parameters for error messages ("design" or "format").
            skip_fields (List[str]): Field names to skip during validation.

        Returns:
            Dict[str, Any]: The validated parameter dictionary.
        """
        if not isinstance(param_dict, dict):
            raise ValueError(f"{param_type.capitalize()} must be a dictionary")

        # Make a copy to avoid modifying the original
        validated_params = copy.deepcopy(param_dict)

        # Check each parameter
        for param_name, param_value in validated_params.items():
            # Skip non-parameter fields
            if param_name in skip_fields:
                continue

            if param_name in bounds:
                self._validate_single_parameter(
                    param_name, param_value, bounds[param_name], param_type
                )
            # Allow unknown parameters for future extensibility

        return validated_params

    def _validate_parameters_list(
        self, param_list: List[Dict[str, Any]], validator_func, param_type_name: str
    ) -> List[Dict[str, Any]]:
        """
        Validate a list of parameter dictionaries.

        Args:
            param_list (List[Dict[str, Any]]): List of parameter dictionaries.
            validator_func: Function to validate individual dictionaries.
            param_type_name (str): Name for error messages.

        Returns:
            List[Dict[str, Any]]: List of validated parameter dictionaries.
        """
        if not isinstance(param_list, list):
            raise ValueError(f"{param_type_name}s must be a list")

        validated_list = []
        for i, param_dict in enumerate(param_list):
            try:
                validated_param = validator_func(param_dict)
                validated_list.append(validated_param)
            except ValueError as e:
                raise ValueError(f"{param_type_name} {i} validation failed: {e}")

        return validated_list

    def _validate_single_parameter(
        self, param_name: str, param_value: Any, bounds: List, param_type: str
    ) -> None:
        """
        Validate a single parameter against its bounds.

        Args:
            param_name (str): Name of the parameter.
            param_value (Any): Value of the parameter.
            bounds (List): [min, max] bounds for the parameter.
            param_type (str): Type of parameter for error messages.

        Raises:
            ValueError: If the parameter value is invalid or out of bounds.
        """
        if param_value is None:
            raise ValueError(
                f"{param_type.capitalize()} parameter '{param_name}' cannot be None"
            )

        # Check if parameter is numeric
        if not isinstance(param_value, (int, float)):
            raise ValueError(
                f"{param_type.capitalize()} parameter '{param_name}' must be numeric, got {type(param_value)}"
            )

        min_val, max_val = bounds

        # Check minimum bound (if not None)
        if min_val is not None and param_value < min_val:
            raise ValueError(
                f"{param_type.capitalize()} parameter '{param_name}' value {param_value} is below minimum allowed value {min_val}"
            )

        # Check maximum bound (if not None)
        if max_val is not None and param_value > max_val:
            raise ValueError(
                f"{param_type.capitalize()} parameter '{param_name}' value {param_value} is above maximum allowed value {max_val}"
            )

    def _validate_cylinder_constraints(self, format_dict: Dict[str, Any]) -> None:
        """
        Validate cylinder-specific constraints.

        Args:
            format_dict (Dict[str, Any]): Cylinder format dictionary.
        """
        if "diameter_mm" in format_dict and "innerDiameter_mm" in format_dict:
            diameter = format_dict["diameter_mm"]
            inner_diameter = format_dict["innerDiameter_mm"]

            if inner_diameter >= diameter:
                raise ValueError(
                    f"Inner diameter ({inner_diameter}) must be less than outer diameter ({diameter})"
                )

    def _validate_cuboid_constraints(self, format_dict: Dict[str, Any]) -> None:
        """
        Validate cuboid-specific constraints.

        Args:
            format_dict (Dict[str, Any]): Cuboid format dictionary.
        """
        # Add any cuboid-specific validation logic here if needed
        pass

    def format_parameters(self, param_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format parameters for API consistency (e.g., ensuring proper types).

        Args:
            param_dict (Dict[str, Any]): Dictionary containing parameters.

        Returns:
            Dict[str, Any]: Formatted parameter dictionary.
        """
        formatted_params = copy.deepcopy(param_dict)

        # Use the unified bounds

        # Ensure numeric parameters are float type for API consistency
        for param_name, param_value in formatted_params.items():
            if param_name in [
                "designName",
                "shape",
                "name",
                "material",
                "assemblyType",
            ]:
                continue

            if param_name in self._parameter_bounds and param_value is not None:
                if isinstance(param_value, (int, float)):
                    formatted_params[param_name] = float(param_value)

        return formatted_params

    def validate_and_format_designs(
        self, designs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate and format a list of designs in one step.

        Args:
            designs (List[Dict[str, Any]]): List of design dictionaries.

        Returns:
            List[Dict[str, Any]]: List of validated and formatted design dictionaries.
        """
        validated_designs = self.validate_designs(designs)
        formatted_designs = [
            self.format_parameters(design) for design in validated_designs
        ]
        return formatted_designs

    def validate_and_format_formats(
        self, formats: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Validate and format a list of formats in one step.

        Args:
            formats (List[Dict[str, Any]]): List of format dictionaries.

        Returns:
            List[Dict[str, Any]]: List of validated and formatted format dictionaries.
        """
        validated_formats = self.validate_formats(formats)
        formatted_formats = [
            self.format_parameters(format_dict) for format_dict in validated_formats
        ]
        return formatted_formats

    def get_parameter_bounds(self, param_name: Optional[str] = None) -> Dict[str, List]:
        """
        Get parameter bounds for specific parameters or all parameters.

        Args:
            param_name (Optional[str]): Name of specific parameter, or None for all parameters.

        Returns:
            Dict[str, List]: Parameter bounds as {parameter_name: [min, max]}.
        """
        if param_name is None:
            return copy.deepcopy(self._parameter_bounds)

        if param_name not in self._parameter_bounds:
            raise ValueError(f"Unknown parameter: {param_name}")

        return {param_name: copy.deepcopy(self._parameter_bounds[param_name])}


# Create singleton instance for convenience
parameter_validator = ParameterValidator()
