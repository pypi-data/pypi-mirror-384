import pytest
import os
from breathe_design.cycler import Cycler


class TestCycler:
    """Test cases for the refactored Cycler class."""

    def test_cycler_initialization_A_units(self):
        """Test Cycler initialization with Ampere units."""
        cycler = Cycler("A", 3.0)
        assert cycler._selected_unit == "A"
        assert cycler._cell_capacity == 3.0
        assert cycler._protocols is not None
        assert isinstance(cycler._protocols, dict)

    def test_cycler_initialization_C_units(self):
        """Test Cycler initialization with C-rate units."""
        cycler = Cycler("C", 2.5)
        assert cycler._selected_unit == "C"
        assert cycler._cell_capacity == 2.5

    def test_protocols_loaded_from_json(self):
        """Test that protocols are loaded from JSON file."""
        cycler = Cycler("A", 3.0)

        # Check that known protocols exist
        assert "CC_CHG" in cycler._protocols
        assert "CC_DCH" in cycler._protocols
        assert "DCIR" in cycler._protocols
        assert "CCCV" in cycler._protocols
        assert "RateCap" in cycler._protocols

        # Check protocol structure
        cc_chg = cycler._protocols["CC_CHG"]
        assert "I_chg" in cc_chg
        assert "V_max" in cc_chg
        assert isinstance(cc_chg["I_chg"], list)
        assert len(cc_chg["I_chg"]) == 2  # [min, max]

    def test_cc_chg_valid_parameters(self):
        """Test CC_CHG protocol with valid parameters."""
        cycler = Cycler("A", 3.0)
        result = cycler.cc_chg(I_chg=1.0, V_max=4.2)

        assert result["cycle_type"] == "CC_CHG"
        assert result["selected_unit"] == "A"
        assert result["control_parameters"]["I_chg"] == 1.0
        assert result["control_parameters"]["V_max"] == 4.2

    def test_cc_chg_c_rate_conversion(self):
        """Test CC_CHG protocol with C-rate units."""
        cycler = Cycler("C", 3.0)  # 3 Ah capacity
        result = cycler.cc_chg(I_chg=1.0, V_max=4.2)  # 1C = 3A

        assert result["cycle_type"] == "CC_CHG"
        assert result["selected_unit"] == "C"
        assert result["control_parameters"]["I_chg"] == 1.0  # Input value preserved
        assert result["control_parameters"]["V_max"] == 4.2

    def test_cc_chg_out_of_bounds_current(self):
        """Test CC_CHG fails with out-of-bounds current."""
        cycler = Cycler("A", 3.0)

        with pytest.raises(ValueError, match="Invalid value for I_chg"):
            cycler.cc_chg(I_chg=600.0, V_max=4.2)  # Above maximum

    def test_cc_chg_out_of_bounds_voltage(self):
        """Test CC_CHG fails with out-of-bounds voltage."""
        cycler = Cycler("A", 3.0)

        with pytest.raises(ValueError, match="Invalid value for V_max"):
            cycler.cc_chg(I_chg=1.0, V_max=5.0)  # Above maximum

    def test_cc_chg_missing_parameter(self):
        """Test CC_CHG fails with missing required parameter."""
        cycler = Cycler("A", 3.0)

        with pytest.raises(TypeError, match="missing 1 required positional argument"):
            cycler.cc_chg(I_chg=1.0)  # Missing V_max

    def test_cc_chg_none_parameter(self):
        """Test CC_CHG fails with None parameter."""
        cycler = Cycler("A", 3.0)

        with pytest.raises(ValueError, match="Missing required parameter"):
            cycler.cc_chg(I_chg=None, V_max=4.2)

    def test_cc_dch_valid_parameters(self):
        """Test CC_DCH protocol with valid parameters."""
        cycler = Cycler("A", 3.0)
        result = cycler.cc_dch(I_dch=-2.0, V_min=2.8)

        assert result["cycle_type"] == "CC_DCH"
        assert result["control_parameters"]["I_dch"] == -2.0
        assert result["control_parameters"]["V_min"] == 2.8

    def test_dcir_valid_parameters(self):
        """Test DCIR protocol with valid parameters."""
        cycler = Cycler("A", 3.0)
        result = cycler.dcir(
            I_dch=-5.0,
            t_dur=10.0,
            t_rest_before=5.0,
            t_rest_after=5.0,
            v_min=2.8,
            v_max=4.2,
        )

        assert result["cycle_type"] == "DCIR"
        assert result["control_parameters"]["I_dch"] == -5.0
        assert result["control_parameters"]["t_dur"] == 10.0
        assert result["control_parameters"]["t_rest_before"] == 5.0
        assert result["control_parameters"]["t_rest_after"] == 5.0
        assert result["control_parameters"]["v_min"] == 2.8
        assert result["control_parameters"]["v_max"] == 4.2

    def test_cccv_valid_parameters(self):
        """Test CCCV protocol with valid parameters."""
        cycler = Cycler("A", 3.0)
        result = cycler.cccv(
            I_chg=1.0,
            I_dch=-2.0,
            I_cut=0.1,
            V_max=4.2,
            V_min=2.8,
            t_restC=300.0,
            t_restD=300.0,
        )

        assert result["cycle_type"] == "CCCV"
        assert result["control_parameters"]["I_chg"] == 1.0
        assert result["control_parameters"]["I_dch"] == -2.0
        assert result["control_parameters"]["I_cut"] == 0.1

    def test_rate_cap_valid_parameters(self):
        """Test RateCap protocol with valid parameters."""
        cycler = Cycler("A", 3.0)
        result = cycler.rate_cap(
            I_chg=1.0, I_dch=-2.0, I_cut=0.1, V_max=4.2, V_min=2.8, t_restC=300.0
        )

        # rate_cap method should correctly set cycle_type to "RateCap"
        assert result["cycle_type"] == "RateCap"
        assert result["control_parameters"]["I_chg"] == 1.0

    def test_invalid_cycle_type(self):
        """Test that invalid cycle type raises error."""
        cycler = Cycler("A", 3.0)

        # Manually create invalid cycler dict to test _build_cycler_dict
        invalid_cycler = {
            "cycle_type": "INVALID_TYPE",
            "selected_unit": "A",
            "control_parameters": {},
        }

        with pytest.raises(ValueError, match="Invalid cycle type"):
            cycler._build_cycler_dict(invalid_cycler)

    def test_c_rate_bounds_checking(self):
        """Test that C-rate values are converted for bounds checking."""
        cycler = Cycler("C", 3.0)  # 3 Ah capacity

        # 200C would be 600A, which is above the 500A limit
        with pytest.raises(ValueError, match="Invalid value for I_chg"):
            cycler.cc_chg(I_chg=200.0, V_max=4.2)  # 200C = 600A > 500A max

    def test_c_rate_valid_within_bounds(self):
        """Test that valid C-rate values pass bounds checking."""
        cycler = Cycler("C", 3.0)  # 3 Ah capacity

        # 1C = 3A, which is well within bounds
        result = cycler.cc_chg(I_chg=1.0, V_max=4.2)
        assert result["control_parameters"]["I_chg"] == 1.0

    def test_protocols_structure(self):
        """Test that protocols have the expected flattened structure."""
        cycler = Cycler("A", 3.0)

        for protocol_name, protocol in cycler._protocols.items():
            assert isinstance(protocol, dict)

            # Each parameter should map to [min, max] list
            for param_name, bounds in protocol.items():
                assert isinstance(bounds, list)
                assert len(bounds) == 2
                min_val, max_val = bounds

                # min_val can be None or numeric
                if min_val is not None:
                    assert isinstance(min_val, (int, float))

                # max_val can be None or numeric
                if max_val is not None:
                    assert isinstance(max_val, (int, float))

    def test_load_protocols_file_not_found(self):
        """Test that missing protocols file raises appropriate error."""
        # This is harder to test without mocking, but we can test the error message format
        # by examining the code behavior when file doesn't exist

        # Create a temporary Cycler class that tries to load from non-existent file
        original_dirname = os.path.dirname

        def mock_dirname(path):
            return "/non/existent/path"

        # Temporarily replace os.path.dirname
        os.path.dirname = mock_dirname
        try:
            with pytest.raises(
                FileNotFoundError, match="Could not find cycling protocols file"
            ):
                Cycler("A", 3.0)
        finally:
            # Restore original function
            os.path.dirname = original_dirname

    def test_protocols_json_content_validation(self):
        """Test that protocols loaded from JSON have valid content."""
        cycler = Cycler("A", 3.0)

        # Test CC_CHG protocol specifically
        cc_chg = cycler._protocols["CC_CHG"]
        assert cc_chg["I_chg"] == [0.0, 500.0]
        assert cc_chg["V_max"] == [2.5, 4.5]

        # Test DCIR protocol has all expected parameters
        dcir = cycler._protocols["DCIR"]
        expected_dcir_params = [
            "I_dch",
            "t_dur",
            "t_rest_before",
            "t_rest_after",
            "v_min",
            "v_max",
        ]
        for param in expected_dcir_params:
            assert param in dcir
            assert isinstance(dcir[param], list)
            assert len(dcir[param]) == 2

    def test_default_cycler_structure(self):
        """Test that default cycler structure is properly initialized."""
        cycler = Cycler("A", 3.0)

        # Check default cycler structure
        default = cycler._default_cycler
        assert default["cycle_type"] is None
        assert default["selected_unit"] == "A"
        assert default["control_parameters"] == {}

    def test_parameter_validation_edge_cases(self):
        """Test edge cases in parameter validation."""
        cycler = Cycler("A", 3.0)

        # Test minimum boundary values
        result = cycler.cc_chg(I_chg=0.0, V_max=2.5)  # Minimum values
        assert result["control_parameters"]["I_chg"] == 0.0
        assert result["control_parameters"]["V_max"] == 2.5

        # Test maximum boundary values
        result = cycler.cc_chg(I_chg=500.0, V_max=4.5)  # Maximum values
        assert result["control_parameters"]["I_chg"] == 500.0
        assert result["control_parameters"]["V_max"] == 4.5

    def test_docstring_accuracy(self):
        """Test that method docstrings accurately describe the functionality."""
        cycler = Cycler("A", 3.0)

        # Check that CC_CHG method returns what docstring claims
        result = cycler.cc_chg(I_chg=1.0, V_max=4.2)
        assert isinstance(result, dict), "cc_chg should return dict as documented"

        # Check that DCIR method returns what docstring claims
        result = cycler.dcir(
            I_dch=-5.0,
            t_dur=10.0,
            t_rest_before=5.0,
            t_rest_after=5.0,
            v_min=2.8,
            v_max=4.2,
        )
        assert isinstance(result, dict), "dcir should return dict as documented"
