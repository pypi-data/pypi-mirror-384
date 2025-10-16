from breathe_design.montecarlo_utils import make_manufacturing_variations


def test_make_manufacturing_variations():
    base_design = {
        "anodePorosity": 0.5,
        "cathodePorosity": 0.5,
        "anodeThickness_um": 10,
        "cathodeThickness_um": 10,
    }
    bound_range = 0.05
    changes = make_manufacturing_variations(
        base_design, n_samples=10, bound_range=bound_range, seed=42
    )
    assert len(changes) == 10
    assert all(isinstance(change, dict) for change in changes)
    assert all(change["designName"] for change in changes)
    assert [c["designName"] for c in changes] == [
        f"MC Variation sample #{i}" for i in range(1, 11)
    ]


def test_make_manufacturing_variations__bound_range_list():
    base_design = {
        "anodePorosity": 0.5,
        "cathodePorosity": 0.5,
        "anodeThickness_um": 10,
        "cathodeThickness_um": 10,
    }
    n_samples = 10
    bound_range = [0.04, 0.06]
    changes = make_manufacturing_variations(
        base_design, n_samples=n_samples, bound_range=list(bound_range), seed=42
    )
    assert len(changes) == 10
    assert all(isinstance(change, dict) for change in changes)
    assert all(change["designName"] for change in changes)
