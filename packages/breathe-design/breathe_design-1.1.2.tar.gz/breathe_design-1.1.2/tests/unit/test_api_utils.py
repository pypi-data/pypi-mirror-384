from breathe_design.api_utils import (
    map_fields_in_place,
    make_design_names_map,
    map_design_names__human_to_machine,
)


def test__make_design_names_map():
    map_h2m, map_m2h = make_design_names_map([{"designName": "Unsafe Name %!?"}])

    assert map_h2m == {"Unsafe Name %!?": "design_0"}
    assert map_m2h == {"design_0": "Unsafe Name %!?"}


def test__map_fields_in_place():
    """Test the inverse mapping from safe machine names to the human unsafe ones.

    This is the mpapping that is done on the results from the server
    """
    unsafe_name = "Unsafe Name %!?"
    map_h2m, map_m2h = make_design_names_map([{"designName": unsafe_name}])

    results = {}
    results["KPIs"] = {"Baseline": 0, unsafe_name: (1, 2, 3)}

    # map fowards to the safe names
    map_fields_in_place(results, "KPIs", map_h2m)
    assert results["KPIs"] == {"Baseline": 0, "design_0": (1, 2, 3)}

    # map back (as if they came back from the server)
    map_fields_in_place(results, "KPIs", map_m2h)
    assert results["KPIs"] == {"Baseline": 0, unsafe_name: (1, 2, 3)}


def test__map_design_names__human_to_machine():
    """Test the mapping from unsafe designNames to safe ones.

    This is the mapping that is performed on the designs before sending to the server
    """
    unsafe_name = "Unsafe Name %!?"
    designs = [{"designName": unsafe_name}]
    map_h2m, map_m2h = make_design_names_map(designs)

    # map fowards to the safe names
    designs_machine = map_design_names__human_to_machine(designs, map_h2m)
    assert designs_machine == [{"designName": "design_0"}]
