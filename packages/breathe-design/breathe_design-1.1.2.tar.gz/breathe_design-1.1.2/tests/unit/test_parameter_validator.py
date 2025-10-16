import pytest
import copy
from breathe_design.parameter_validator import ParameterValidator, parameter_validator


class TestParameterValidator:
    """Test cases for the unified ParameterValidator class."""

    def test_validator_initialization(self):
        """Test that the validator initializes correctly."""
        validator = ParameterValidator()
        assert validator._parameter_bounds is not None
        assert isinstance(validator._parameter_bounds, dict)
        assert len(validator._parameter_bounds) > 0

    def test_singleton_instance(self):
        """Test that the singleton instance is properly created."""
        assert parameter_validator is not None
        assert isinstance(parameter_validator, ParameterValidator)

    def test_get_parameter_bounds_all(self):
        """Test getting all parameter bounds."""
        bounds = parameter_validator.get_parameter_bounds()
        assert isinstance(bounds, dict)
        assert len(bounds) > 0

        # Check some known parameters
        assert "NPratio" in bounds
        assert "housingThickness_mm" in bounds
        assert "length_mm" in bounds

        # Check bounds format
        assert bounds["NPratio"] == [0.7, 3]
        assert bounds["housingThickness_mm"] == [0.1, 10.0]

    def test_get_parameter_bounds_specific(self):
        """Test getting bounds for a specific parameter."""
        bounds = parameter_validator.get_parameter_bounds("NPratio")
        assert bounds == {"NPratio": [0.7, 3]}

    def test_get_parameter_bounds_unknown(self):
        """Test getting bounds for an unknown parameter raises error."""
        with pytest.raises(ValueError, match="Unknown parameter"):
            parameter_validator.get_parameter_bounds("unknown_parameter")

    def test_validate_design_valid(self):
        """Test validation of a valid design."""
        design = {
            "designName": "Test Design",
            "NPratio": 1.5,
            "Vmin_V": 3.0,
            "Vmax_V": 4.2,
            "cathodePorosity": 0.4,
            "anodePorosity": 0.3,
        }

        result = parameter_validator.validate_design(design)
        assert result["designName"] == "Test Design"
        assert result["NPratio"] == 1.5
        assert result["Vmin_V"] == 3.0

    def test_validate_design_out_of_bounds_high(self):
        """Test validation fails for parameter above maximum."""
        design = {
            "designName": "Invalid Design",
            "NPratio": 5.0,  # Above maximum of 3.0
            "Vmin_V": 3.0,
        }

        with pytest.raises(ValueError, match="above maximum allowed value"):
            parameter_validator.validate_design(design)

    def test_validate_design_out_of_bounds_low(self):
        """Test validation fails for parameter below minimum."""
        design = {
            "designName": "Invalid Design",
            "NPratio": 0.5,  # Below minimum of 0.7
            "Vmin_V": 3.0,
        }

        with pytest.raises(ValueError, match="below minimum allowed value"):
            parameter_validator.validate_design(design)

    def test_validate_design_none_value(self):
        """Test validation fails for None parameter value."""
        design = {"designName": "Invalid Design", "NPratio": None, "Vmin_V": 3.0}

        with pytest.raises(ValueError, match="cannot be None"):
            parameter_validator.validate_design(design)

    def test_validate_design_non_numeric(self):
        """Test validation fails for non-numeric parameter."""
        design = {
            "designName": "Invalid Design",
            "NPratio": "not_a_number",
            "Vmin_V": 3.0,
        }

        with pytest.raises(ValueError, match="must be numeric"):
            parameter_validator.validate_design(design)

    def test_validate_design_unknown_parameter_allowed(self):
        """Test that unknown parameters are allowed (for future extensibility)."""
        design = {
            "designName": "Test Design",
            "NPratio": 1.5,
            "unknown_future_parameter": 42.0,
        }

        # Should not raise an error
        result = parameter_validator.validate_design(design)
        assert result["designName"] == "Test Design"
        assert result["NPratio"] == 1.5
        assert result["unknown_future_parameter"] == 42.0

    def test_validate_designs_list(self):
        """Test validation of a list of designs."""
        designs = [
            {"designName": "Design 1", "NPratio": 1.0, "Vmin_V": 3.0},
            {"designName": "Design 2", "NPratio": 2.0, "Vmin_V": 2.8},
        ]

        result = parameter_validator.validate_designs(designs)
        assert len(result) == 2
        assert result[0]["designName"] == "Design 1"
        assert result[1]["designName"] == "Design 2"

    def test_validate_designs_list_with_error(self):
        """Test validation of design list fails on invalid design."""
        designs = [
            {"designName": "Valid Design", "NPratio": 1.0, "Vmin_V": 3.0},
            {
                "designName": "Invalid Design",
                "NPratio": 5.0,
                "Vmin_V": 2.8,
            },  # NPratio too high
        ]

        with pytest.raises(ValueError, match="Design 1 validation failed"):
            parameter_validator.validate_designs(designs)

    def test_validate_designs_not_list(self):
        """Test that validation fails if designs is not a list."""
        with pytest.raises(ValueError, match="must be a list"):
            parameter_validator.validate_designs({"not": "a_list"})

    def test_validate_format_valid_cuboid(self):
        """Test validation of a valid cuboid format."""
        format_dict = {
            "shape": "cuboid",
            "name": "Test Cuboid",
            "material": "aluminum",
            "housingThickness_mm": 1.0,
            "length_mm": 100.0,
            "width_mm": 50.0,
            "thickness_mm": 10.0,
            "assemblyType": "stacked",
        }

        result = parameter_validator.validate_format(format_dict)
        assert result["shape"] == "cuboid"
        assert result["material"] == "aluminum"
        assert result["housingThickness_mm"] == 1.0

    def test_validate_format_valid_cylinder(self):
        """Test validation of a valid cylinder format."""
        format_dict = {
            "shape": "cylinder",
            "name": "Test Cylinder",
            "material": "steel",
            "housingThickness_mm": 0.5,
            "diameter_mm": 18.0,
            "height_mm": 65.0,
            "innerDiameter_mm": 17.0,
        }

        result = parameter_validator.validate_format(format_dict)
        assert result["shape"] == "cylinder"
        assert result["material"] == "steel"

    def test_validate_format_missing_shape(self):
        """Test validation fails when shape is missing."""
        format_dict = {
            "name": "No Shape",
            "material": "aluminum",
            "housingThickness_mm": 1.0,
        }

        with pytest.raises(ValueError, match="must specify a 'shape' field"):
            parameter_validator.validate_format(format_dict)

    def test_validate_format_missing_material(self):
        """Test validation fails when material is missing."""
        format_dict = {
            "shape": "cuboid",
            "name": "No Material",
            "housingThickness_mm": 1.0,
        }

        with pytest.raises(ValueError, match="must specify a 'material' field"):
            parameter_validator.validate_format(format_dict)

    def test_validate_format_invalid_material(self):
        """Test validation fails for invalid material."""
        format_dict = {
            "shape": "cuboid",
            "name": "Invalid Material",
            "material": "plastic",  # Not in valid materials
            "housingThickness_mm": 1.0,
        }

        with pytest.raises(ValueError, match="Invalid material"):
            parameter_validator.validate_format(format_dict)

    def test_validate_format_invalid_assembly_type(self):
        """Test validation fails for invalid assembly type."""
        format_dict = {
            "shape": "cuboid",
            "name": "Invalid Assembly",
            "material": "aluminum",
            "housingThickness_mm": 1.0,
            "assemblyType": "invalid_type",
        }

        with pytest.raises(ValueError, match="Invalid assembly type"):
            parameter_validator.validate_format(format_dict)

    def test_validate_format_cylinder_constraints(self):
        """Test cylinder-specific constraint validation."""
        format_dict = {
            "shape": "cylinder",
            "name": "Invalid Cylinder",
            "material": "steel",
            "housingThickness_mm": 0.5,
            "diameter_mm": 18.0,
            "height_mm": 65.0,
            "innerDiameter_mm": 18.0,  # Equal to outer diameter - should fail
        }

        with pytest.raises(ValueError, match="must be less than outer diameter"):
            parameter_validator.validate_format(format_dict)

    def test_validate_format_parameter_out_of_bounds(self):
        """Test format validation fails for out-of-bounds parameter."""
        format_dict = {
            "shape": "cuboid",
            "name": "Too Thick",
            "material": "aluminum",
            "housingThickness_mm": 15.0,  # Above maximum of 10.0
            "length_mm": 100.0,
        }

        with pytest.raises(ValueError, match="above maximum allowed value"):
            parameter_validator.validate_format(format_dict)

    def test_validate_formats_list(self):
        """Test validation of a list of formats."""
        formats = [
            {
                "shape": "cuboid",
                "name": "Format 1",
                "material": "aluminum",
                "housingThickness_mm": 1.0,
                "length_mm": 100.0,
            },
            {
                "shape": "cylinder",
                "name": "Format 2",
                "material": "steel",
                "housingThickness_mm": 0.5,
                "diameter_mm": 18.0,
                "height_mm": 65.0,
                "innerDiameter_mm": 17.0,
            },
        ]

        result = parameter_validator.validate_formats(formats)
        assert len(result) == 2
        assert result[0]["shape"] == "cuboid"
        assert result[1]["shape"] == "cylinder"

    def test_format_parameters(self):
        """Test parameter formatting (type conversion)."""
        params = {
            "designName": "Test",
            "NPratio": 1,  # Integer
            "housingThickness_mm": 2,  # Integer
            "material": "aluminum",  # String - should not be converted
        }

        result = parameter_validator.format_parameters(params)
        assert result["designName"] == "Test"  # String unchanged
        assert result["NPratio"] == 1.0  # Converted to float
        assert result["housingThickness_mm"] == 2.0  # Converted to float
        assert result["material"] == "aluminum"  # String unchanged

    def test_validate_and_format_designs(self):
        """Test combined validation and formatting of designs."""
        designs = [
            {"designName": "Test", "NPratio": 1, "Vmin_V": 3}  # Integers
        ]

        result = parameter_validator.validate_and_format_designs(designs)
        assert len(result) == 1
        assert isinstance(result[0]["NPratio"], float)
        assert isinstance(result[0]["Vmin_V"], float)

    def test_validate_and_format_formats(self):
        """Test combined validation and formatting of formats."""
        formats = [
            {
                "shape": "cuboid",
                "material": "aluminum",
                "housingThickness_mm": 1,  # Integer
                "length_mm": 100,  # Integer
            }
        ]

        result = parameter_validator.validate_and_format_formats(formats)
        assert len(result) == 1
        assert isinstance(result[0]["housingThickness_mm"], float)
        assert isinstance(result[0]["length_mm"], float)

    def test_validate_design_not_dict(self):
        """Test validation fails if design is not a dictionary."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            parameter_validator.validate_design("not_a_dict")

    def test_validate_format_not_dict(self):
        """Test validation fails if format is not a dictionary."""
        with pytest.raises(ValueError, match="must be a dictionary"):
            parameter_validator.validate_format("not_a_dict")

    def test_parameter_bounds_immutability(self):
        """Test that returned bounds are deep copies and don't affect internal state."""
        bounds1 = parameter_validator.get_parameter_bounds()
        bounds2 = parameter_validator.get_parameter_bounds()

        # Modify one copy
        bounds1["NPratio"] = [999, 999]

        # Other copy should be unchanged
        assert bounds2["NPratio"] == [0.7, 3]

        # Original validator should be unchanged
        bounds3 = parameter_validator.get_parameter_bounds()
        assert bounds3["NPratio"] == [0.7, 3]

    def test_design_immutability(self):
        """Test that validation doesn't modify the original design."""
        original_design = {"designName": "Test", "NPratio": 1.5}
        design_copy = copy.deepcopy(original_design)

        parameter_validator.validate_design(design_copy)

        # Original should be unchanged
        assert original_design == design_copy

    def test_format_immutability(self):
        """Test that validation doesn't modify the original format."""
        original_format = {
            "shape": "cuboid",
            "material": "aluminum",
            "housingThickness_mm": 1.0,
        }
        format_copy = copy.deepcopy(original_format)

        parameter_validator.validate_format(format_copy)

        # Original should be unchanged
        assert original_format == format_copy
