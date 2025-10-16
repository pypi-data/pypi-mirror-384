VALID_MATERIALS = {"steel", "aluminum", "pouch"}
VALID_ASSEMENT_TYPES = {"stacked", "wound", "zFolded"}


def validate_material(material):
    if material not in VALID_MATERIALS:
        raise ValueError(
            f"Invalid material: '{material}'. Must be one of {sorted(VALID_MATERIALS)}."
        )


def validate_assembly_type(assembly_type):
    if assembly_type not in VALID_ASSEMENT_TYPES:
        raise ValueError(
            f"Invalid assembly type: '{assembly_type}'. Must be one of {sorted(VALID_ASSEMENT_TYPES)}."
        )


def validate_format_parameter(param_name, param_value):
    """Validate a format parameter against its bounds."""
    # Import here to avoid circular imports
    from .parameter_validator import parameter_validator

    bounds = parameter_validator.get_parameter_bounds()

    if param_name not in bounds:
        return  # Skip validation for unknown parameters

    if param_value is None:
        raise ValueError(f"Format parameter '{param_name}' cannot be None")

    if not isinstance(param_value, (int, float)):
        raise ValueError(
            f"Format parameter '{param_name}' must be numeric, got {type(param_value)}"
        )

    min_val, max_val = bounds[param_name]

    if min_val is not None and param_value < min_val:
        raise ValueError(
            f"Format parameter '{param_name}' value {param_value} is below minimum allowed value {min_val}"
        )

    if max_val is not None and param_value > max_val:
        raise ValueError(
            f"Format parameter '{param_name}' value {param_value} is above maximum allowed value {max_val}"
        )


def define_cuboid_format(
    name, material, housingThickness_mm, length_mm, width_mm, thickness_mm, assemblyType
):
    """
    Defines a dictionary for a cuboid battery format.

    Parameters:
        name (str): Name of the battery format
        material (str): Material used
        housingThickness_mm (float): Housing thickness
        length_mm (float): Length of the battery
        width_mm (float): Width of the battery
        thickness_mm (float): Thickness of the battery
        assembly_type (str): Type of assembly

    Returns:
        dict: A dictionary representing the cuboid battery format
    """
    validate_material(material)
    validate_assembly_type(assemblyType)

    # Validate numeric parameters
    validate_format_parameter("housingThickness_mm", housingThickness_mm)
    validate_format_parameter("length_mm", length_mm)
    validate_format_parameter("width_mm", width_mm)
    validate_format_parameter("thickness_mm", thickness_mm)

    return {
        "shape": "cuboid",
        "name": name,
        "material": material,
        "housingThickness_mm": float(housingThickness_mm),
        "length_mm": float(length_mm),
        "width_mm": float(width_mm),
        "thickness_mm": float(thickness_mm),
        "assemblyType": assemblyType,
    }


def define_cylinder_format(
    name, material, housingThickness_mm, diameter_mm, height_mm, innerDiameter_mm
):
    """
    Defines a dictionary for a cylindrical battery format.

    Parameters:
        name (str): Name of the battery format
        material (str): Material used
        housingThickness_mm (float): Housing thickness
        diameter_mm (float): Outer diameter of the cylinder
        height_mm (float): Height of the cylinder
        innerDiameter_mm (float): Inner diameter of the cylinder

    Returns:
        dict: A dictionary representing the cylindrical battery format
    """
    validate_material(material)

    # Validate numeric parameters
    validate_format_parameter("housingThickness_mm", housingThickness_mm)
    validate_format_parameter("diameter_mm", diameter_mm)
    validate_format_parameter("height_mm", height_mm)
    validate_format_parameter("innerDiameter_mm", innerDiameter_mm)

    # Additional validation: inner diameter should be less than outer diameter
    if innerDiameter_mm >= diameter_mm:
        raise ValueError(
            f"Inner diameter ({innerDiameter_mm}) must be less than outer diameter ({diameter_mm})"
        )

    return {
        "shape": "cylinder",
        "name": name,
        "material": material,
        "housingThickness_mm": float(housingThickness_mm),
        "diameter_mm": float(diameter_mm),
        "height_mm": float(height_mm),
        "innerDiameter_mm": float(innerDiameter_mm),
    }
