from breathe_design import api_interface as api
import breathe_design as bd
import numpy
from tests.utils import get_temp_dir


def test_large_number_of_designs(use_m2m_auth, num_designs=1000):
    # get base design parameters
    base_battery = "Molicel P45B"
    base_params = api.get_design_parameters(base_battery)

    # make a large number of designs to test
    # scan a few parameters
    designs = []
    for i, fraction in enumerate(numpy.linspace(0.85, 1.15, num_designs)):
        designs.append(
            {
                "designName": f"Design {i}",
                "NPratio": base_params["NPratio"] * fraction,
                "cathodeThickness_um": base_params["cathodeThickness_um"] * fraction,
            }
        )

    # get equilibrium kpis first
    results = api.get_eqm_kpis("Molicel P45B", designs)
    var_kpis = results.get_kpis()
    # there should be one KPI for each design + one baseline
    assert len(var_kpis.columns) == num_designs + 1, "Wrong number of KPIs"
    assert results.design_names[0] == "Baseline"
    for i in range(len(designs)):
        assert results.design_names[i + 1] == designs[i]["designName"]

    # DCIR simulation
    cycler = bd.Cycler("C", 4.5)
    results = api.run_sim(
        base_battery=base_battery,
        cycler=cycler.dcir(-1, 30, 5, 5, 2.5, 4.2),
        designs=designs,
        initialSoC=0.7,
        initialTemperature_degC=25,
        ambientTemperature_degC=25,
    )

    # there should be one Result for each design + one baseline
    assert len(results.design_names) == num_designs + 1, "Wrong number of designs"
    assert results.design_names[0] == "Baseline"
    for i in range(len(designs)):
        assert results.design_names[i + 1] == designs[i]["designName"]

    # download designs
    folder = get_temp_dir("test_large_number_of_designs")
    files = api.download_designs(base_battery, designs=designs, folder=folder)
    # there should be one File for each design + one baseline (which is the first)
    assert len(files) == num_designs + 1, "Wrong number of files saved"
