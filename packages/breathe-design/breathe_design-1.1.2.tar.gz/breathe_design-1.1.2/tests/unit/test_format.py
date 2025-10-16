import pytest
from breathe_design.format import (
    validate_material,
    validate_assembly_type,
    validate_format_parameter,
    define_cuboid_format,
    define_cylinder_format,
    VALID_MATERIALS,
    VALID_ASSEMENT_TYPES,
)
from breathe_design.parameter_validator import parameter_validator


class TestFormatValidation:
    """Test cases for format validation functions."""

    def test_valid_materials_constant(self):
        """Test that VALID_MATERIALS contains expected materials."""
        assert "steel" in VALID_MATERIALS
        assert "aluminum" in VALID_MATERIALS
        assert "pouch" in VALID_MATERIALS
        assert len(VALID_MATERIALS) == 3

    def test_valid_assembly_types_constant(self):
        """Test that VALID_ASSEMENT_TYPES contains expected types."""
        assert "stacked" in VALID_ASSEMENT_TYPES
        assert "wound" in VALID_ASSEMENT_TYPES
        assert "zFolded" in VALID_ASSEMENT_TYPES
        assert len(VALID_ASSEMENT_TYPES) == 3

    def test_validate_material_valid(self):
        """Test validation of valid materials."""
        for material in VALID_MATERIALS:
            # Should not raise an exception
            validate_material(material)

    def test_validate_material_invalid(self):
        """Test validation fails for invalid materials."""
        invalid_materials = ["plastic", "wood", "ceramic", "invalid"]

        for material in invalid_materials:
            with pytest.raises(ValueError, match="Invalid material"):
                validate_material(material)

    def test_validate_assembly_type_valid(self):
        """Test validation of valid assembly types."""
        for assembly_type in VALID_ASSEMENT_TYPES:
            # Should not raise an exception
            validate_assembly_type(assembly_type)

    def test_validate_assembly_type_invalid(self):
        """Test validation fails for invalid assembly types."""
        invalid_types = ["rolled", "folded", "twisted", "invalid"]

        for assembly_type in invalid_types:
            with pytest.raises(ValueError, match="Invalid assembly type"):
                validate_assembly_type(assembly_type)

    def test_validate_format_parameter_valid(self):
        """Test validation of valid format parameters."""
        # Should not raise exceptions
        validate_format_parameter("housingThickness_mm", 1.0)
        validate_format_parameter("length_mm", 100.0)
        validate_format_parameter("diameter_mm", 18.0)

    def test_validate_format_parameter_out_of_bounds_high(self):
        """Test format parameter validation fails for values above maximum."""
        with pytest.raises(ValueError, match="above maximum allowed value"):
            validate_format_parameter("housingThickness_mm", 15.0)  # Max is 10.0

    def test_validate_format_parameter_out_of_bounds_low(self):
        """Test format parameter validation fails for values below minimum."""
        with pytest.raises(ValueError, match="below minimum allowed value"):
            validate_format_parameter("housingThickness_mm", 0.05)  # Min is 0.1

    def test_validate_format_parameter_none(self):
        """Test format parameter validation fails for None values."""
        with pytest.raises(ValueError, match="cannot be None"):
            validate_format_parameter("housingThickness_mm", None)

    def test_validate_format_parameter_non_numeric(self):
        """Test format parameter validation fails for non-numeric values."""
        with pytest.raises(ValueError, match="must be numeric"):
            validate_format_parameter("housingThickness_mm", "not_a_number")

    def test_validate_format_parameter_unknown_parameter(self):
        """Test that unknown parameters are silently skipped."""
        # Should not raise an exception
        validate_format_parameter("unknown_parameter", 42.0)

    def test_define_cuboid_format_valid(self):
        """Test creation of valid cuboid format."""
        result = define_cuboid_format(
            name="Test Cuboid",
            material="aluminum",
            housingThickness_mm=1.0,
            length_mm=100.0,
            width_mm=50.0,
            thickness_mm=10.0,
            assemblyType="stacked",
        )

        assert result["shape"] == "cuboid"
        assert result["name"] == "Test Cuboid"
        assert result["material"] == "aluminum"
        assert result["housingThickness_mm"] == 1.0
        assert result["length_mm"] == 100.0
        assert result["width_mm"] == 50.0
        assert result["thickness_mm"] == 10.0
        assert result["assemblyType"] == "stacked"

        # Check that numeric values are converted to float
        assert isinstance(result["housingThickness_mm"], float)
        assert isinstance(result["length_mm"], float)

    def test_define_cuboid_format_invalid_material(self):
        """Test cuboid creation fails with invalid material."""
        with pytest.raises(ValueError, match="Invalid material"):
            define_cuboid_format(
                name="Invalid Material",
                material="plastic",
                housingThickness_mm=1.0,
                length_mm=100.0,
                width_mm=50.0,
                thickness_mm=10.0,
                assemblyType="stacked",
            )

    def test_define_cuboid_format_invalid_assembly_type(self):
        """Test cuboid creation fails with invalid assembly type."""
        with pytest.raises(ValueError, match="Invalid assembly type"):
            define_cuboid_format(
                name="Invalid Assembly",
                material="aluminum",
                housingThickness_mm=1.0,
                length_mm=100.0,
                width_mm=50.0,
                thickness_mm=10.0,
                assemblyType="invalid_type",
            )

    def test_define_cuboid_format_out_of_bounds_parameter(self):
        """Test cuboid creation fails with out-of-bounds parameter."""
        with pytest.raises(ValueError, match="above maximum allowed value"):
            define_cuboid_format(
                name="Too Thick",
                material="aluminum",
                housingThickness_mm=15.0,  # Above maximum
                length_mm=100.0,
                width_mm=50.0,
                thickness_mm=10.0,
                assemblyType="stacked",
            )

    def test_define_cylinder_format_valid(self):
        """Test creation of valid cylinder format."""
        result = define_cylinder_format(
            name="Test Cylinder",
            material="steel",
            housingThickness_mm=0.5,
            diameter_mm=18.0,
            height_mm=65.0,
            innerDiameter_mm=17.0,
        )

        assert result["shape"] == "cylinder"
        assert result["name"] == "Test Cylinder"
        assert result["material"] == "steel"
        assert result["housingThickness_mm"] == 0.5
        assert result["diameter_mm"] == 18.0
        assert result["height_mm"] == 65.0
        assert result["innerDiameter_mm"] == 17.0

        # Check that numeric values are converted to float
        assert isinstance(result["housingThickness_mm"], float)
        assert isinstance(result["diameter_mm"], float)

    def test_define_cylinder_format_invalid_material(self):
        """Test cylinder creation fails with invalid material."""
        with pytest.raises(ValueError, match="Invalid material"):
            define_cylinder_format(
                name="Invalid Material",
                material="plastic",
                housingThickness_mm=0.5,
                diameter_mm=18.0,
                height_mm=65.0,
                innerDiameter_mm=17.0,
            )

    def test_define_cylinder_format_invalid_constraints(self):
        """Test cylinder creation fails when inner diameter >= outer diameter."""
        with pytest.raises(ValueError, match="must be less than outer diameter"):
            define_cylinder_format(
                name="Invalid Cylinder",
                material="steel",
                housingThickness_mm=0.5,
                diameter_mm=18.0,
                height_mm=65.0,
                innerDiameter_mm=18.0,  # Equal to outer diameter
            )

        with pytest.raises(ValueError, match="must be less than outer diameter"):
            define_cylinder_format(
                name="Invalid Cylinder 2",
                material="steel",
                housingThickness_mm=0.5,
                diameter_mm=18.0,
                height_mm=65.0,
                innerDiameter_mm=19.0,  # Greater than outer diameter
            )

    def test_define_cylinder_format_out_of_bounds_parameter(self):
        """Test cylinder creation fails with out-of-bounds parameter."""
        with pytest.raises(ValueError, match="above maximum allowed value"):
            define_cylinder_format(
                name="Too Thick",
                material="steel",
                housingThickness_mm=15.0,  # Above maximum
                diameter_mm=18.0,
                height_mm=65.0,
                innerDiameter_mm=17.0,
            )

    def test_parameter_validator_format_validation(self):
        """Test that the unified parameter validator can validate formats."""
        # parameter_validator should be the unified parameter validator
        assert parameter_validator is not None

        # Test that it has the expected methods
        assert hasattr(parameter_validator, "validate_format")
        assert hasattr(parameter_validator, "validate_formats")
        assert hasattr(parameter_validator, "validate_design")
        assert hasattr(parameter_validator, "validate_designs")

    def test_unified_validator_integration(self):
        """Test integration with the unified parameter validator."""
        # Create a format and validate it using the unified validator
        format_dict = {
            "shape": "cuboid",
            "name": "Integration Test",
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

    def test_numeric_parameter_type_conversion(self):
        """Test that define functions convert integers to floats."""
        # Test with integer inputs
        cuboid = define_cuboid_format(
            name="Integer Test",
            material="aluminum",
            housingThickness_mm=1,  # Integer
            length_mm=100,  # Integer
            width_mm=50,  # Integer
            thickness_mm=10,  # Integer
            assemblyType="stacked",
        )

        # All numeric parameters should be floats
        assert isinstance(cuboid["housingThickness_mm"], float)
        assert isinstance(cuboid["length_mm"], float)
        assert isinstance(cuboid["width_mm"], float)
        assert isinstance(cuboid["thickness_mm"], float)

        # Values should be preserved
        assert cuboid["housingThickness_mm"] == 1.0
        assert cuboid["length_mm"] == 100.0

    def test_boundary_values(self):
        """Test format validation with boundary values."""
        # Test minimum boundary values
        min_cuboid = define_cuboid_format(
            name="Min Values",
            material="aluminum",
            housingThickness_mm=0.1,  # Minimum
            length_mm=1.0,  # Minimum
            width_mm=1.0,  # Minimum
            thickness_mm=1.0,  # Minimum
            assemblyType="stacked",
        )
        assert min_cuboid["housingThickness_mm"] == 0.1

        # Test maximum boundary values
        max_cuboid = define_cuboid_format(
            name="Max Values",
            material="aluminum",
            housingThickness_mm=10.0,  # Maximum
            length_mm=1000.0,  # Maximum
            width_mm=1000.0,  # Maximum
            thickness_mm=100.0,  # Maximum
            assemblyType="stacked",
        )
        assert max_cuboid["housingThickness_mm"] == 10.0

    def test_error_message_specificity(self):
        """Test that error messages are specific and helpful."""
        # Test specific parameter name in error message
        with pytest.raises(ValueError) as exc_info:
            validate_format_parameter("housingThickness_mm", 15.0)

        assert "housingThickness_mm" in str(exc_info.value)
        assert "15.0" in str(exc_info.value)
        assert "10.0" in str(exc_info.value)  # Maximum value

        # Test material error message
        with pytest.raises(ValueError) as exc_info:
            validate_material("plastic")

        assert "plastic" in str(exc_info.value)
        assert "aluminum" in str(exc_info.value) or "steel" in str(
            exc_info.value
        )  # Valid options shown

    def test_unified_validator_format_list_validation(self):
        """Test that the unified validator can validate lists of formats."""
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

    def test_unified_validator_format_parameter_bounds(self):
        """Test that the unified validator uses the same parameter bounds as format functions."""
        # Get bounds from unified validator
        bounds = parameter_validator.get_parameter_bounds()

        # Test that format-specific parameters exist
        assert "housingThickness_mm" in bounds
        assert "length_mm" in bounds
        assert "diameter_mm" in bounds

        # Test that bounds match expected values
        assert bounds["housingThickness_mm"] == [0.1, 10.0]
        assert bounds["length_mm"] == [1.0, 1000.0]

    def test_unified_validator_format_validation_consistency(self):
        """Test that unified validator and format functions give consistent results."""
        # Test a format that should pass both validations
        valid_format = {
            "shape": "cuboid",
            "name": "Consistency Test",
            "material": "aluminum",
            "housingThickness_mm": 2.0,
            "length_mm": 150.0,
            "width_mm": 75.0,
            "thickness_mm": 15.0,
            "assemblyType": "stacked",
        }

        # Both should succeed
        unified_result = parameter_validator.validate_format(valid_format)
        format_function_result = define_cuboid_format(
            name="Consistency Test",
            material="aluminum",
            housingThickness_mm=2.0,
            length_mm=150.0,
            width_mm=75.0,
            thickness_mm=15.0,
            assemblyType="stacked",
        )

        # Key fields should match
        assert unified_result["material"] == format_function_result["material"]
        assert (
            unified_result["housingThickness_mm"]
            == format_function_result["housingThickness_mm"]
        )

    def test_unified_validator_format_error_consistency(self):
        """Test that unified validator and format functions give consistent errors."""
        # Test a parameter that should fail in both
        invalid_thickness = 15.0  # Above maximum of 10.0

        # Both should fail with similar error messages
        with pytest.raises(ValueError, match="above maximum allowed value"):
            parameter_validator.validate_format(
                {
                    "shape": "cuboid",
                    "material": "aluminum",
                    "housingThickness_mm": invalid_thickness,
                }
            )

        with pytest.raises(ValueError, match="above maximum allowed value"):
            define_cuboid_format(
                name="Error Test",
                material="aluminum",
                housingThickness_mm=invalid_thickness,
                length_mm=100.0,
                width_mm=50.0,
                thickness_mm=10.0,
                assemblyType="stacked",
            )
