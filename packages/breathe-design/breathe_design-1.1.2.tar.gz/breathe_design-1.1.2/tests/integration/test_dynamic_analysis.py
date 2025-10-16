from breathe_design import api_interface as api, Cycler
from breathe_design import SingleSimulationResults, BatchSimulationResults


def test__show_service_version(use_m2m_auth):
    version = api.get_service_version()
    print(f"Service version is {version}")


def test__dynamic_analysis_I(use_m2m_auth):
    base_params = api.get_design_parameters("Molicel P45B")
    eqm_kpis = api.get_eqm_kpis("Molicel P45B")
    designs = [{"designName": "Lower NP", "NPratio": base_params["NPratio"] * 0.95}]
    baseline_capacity = eqm_kpis.capacity
    cycler = Cycler(selected_unit="C", cell_capacity=baseline_capacity)
    cycler_input = cycler.cccv(1.0, -1.0, 0.01, 4.2, 2.6, 60.0, 60.0)

    # run a single simulation
    output = api.run_sim(
        base_battery="Molicel P45B",
        cycler=cycler_input,
        designs=designs,
        initialSoC=0.5,
        initialTemperature_degC=21.0,
    )
    assert isinstance(output, SingleSimulationResults)


def test__dynamic_analysis_II(use_m2m_auth):
    design_name = "Lower NP"
    base_params = api.get_design_parameters("Molicel P45B")
    eqm_kpis = api.get_eqm_kpis("Molicel P45B")
    designs = [{"designName": "Lower NP", "NPratio": base_params["NPratio"] * 0.95}]
    baseline_capacity = eqm_kpis.capacity
    cycler = Cycler(selected_unit="C", cell_capacity=baseline_capacity)

    # define some SOC breakpoints we want to simulate
    soc_bps = [0.25, 0.5, 0.75]
    # run a batch of simulations for different SOC breakpoints
    output = api.run_sim(
        base_battery="Molicel P45B",
        cycler=cycler.cc_chg(1.0, 4.2),
        designs=designs,
        initialSoC=soc_bps,
        initialTemperature_degC=21.0,
    )

    assert isinstance(output, BatchSimulationResults)
    assert len(output) == len(soc_bps)
    # Test indexing access
    for i in range(len(soc_bps)):
        assert design_name in output.design_names
        assert output.get_dynamic_data(design_name)[0] != {}

    # Test the simulation_results_list property
    assert len(output._simulation_results) == len(soc_bps)
    for sim_result in output._simulation_results:
        assert design_name in sim_result.design_names
        assert design_name in sim_result.dynamic_data
    cycler_dict = cycler.dcir(
        I_dch=-1.0,
        t_dur=60.0,
        t_rest_before=3.0,
        t_rest_after=200.0,
        v_min=2.5,
        v_max=4.2,
    )
    # DCIR
    output = api.run_sim(
        base_battery="Molicel P45B",
        cycler=cycler_dict,
        designs=designs,
        initialSoC=0.5,
        initialTemperature_degC=21.0,
    )

    # only one initial SOC and temperature, so we expect a SingleSimulationResults back
    assert isinstance(output, SingleSimulationResults)
    assert design_name in output.design_names
    assert design_name in output.dynamic_data

    # Test the dynamic_kpis method from the results handler
    dynamic_kpis = output.dynamic_kpis("DCIR")
    assert dynamic_kpis is not None
