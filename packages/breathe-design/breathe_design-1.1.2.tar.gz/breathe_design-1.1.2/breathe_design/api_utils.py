from typing import Any
from copy import deepcopy


class BreatheException(Exception):
    """An exception from the BreatheDesignModel API

    Args:
        Exception (_type_): _description_
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


def make_design_names_map(
    designs: list[dict[str, Any]],
) -> tuple[dict[str, str], dict[str, str]]:
    """Return new 'safe' design names that can be used to replace the
    "designName" key in the designs.

    Returns
     - a map from the existing 'human' design name, to the safe 'machine' ones - to be used for the initial mapping
     - a map from the safe 'machine' design name, back to the old 'human' one- to be used for "undoing" the mapping

    Args:
        designs (_type_): _description_

    Returns:
        tuple[list[str], dict[str, str]]: _description_
    """

    map_human_to_machine = {}
    map_machine_to_human = {}
    for i, design in enumerate(designs):
        design_name_human = design["designName"]
        design_name_machine = f"design_{i}"
        map_human_to_machine[design_name_human] = design_name_machine
        map_machine_to_human[design_name_machine] = design_name_human
    return map_human_to_machine, map_machine_to_human


def map_design_names__human_to_machine(
    designs: list[dict], map_human_to_machine: dict[str, str]
):
    designs_mapped = deepcopy(designs)
    for i, design in enumerate(designs_mapped):
        design_name_orig = design["designName"]
        designs_mapped[i]["designName"] = map_human_to_machine[design_name_orig]
    return designs_mapped


def map_design_names__machine_to_human(
    designs_mapped: list[dict], map_machine_to_human: dict[str, str]
):
    designs = deepcopy(designs_mapped)
    for i, design in enumerate(designs):
        design_name_orig = design["designName"]
        designs[i]["designName"] = map_machine_to_human[design_name_orig]
    return designs


def convert_none_strings_to_none(data: Any) -> Any:
    """
    Recursively convert "none" strings to Python None in nested data structures.

    This function handles dictionaries, lists, and other data types, converting
    any occurrence of the string "none" to Python None.

    Args:
        data: The data structure to process (dict, list, or any other type)

    Returns:
        The processed data structure with "none" strings converted to None
    """
    if isinstance(data, dict):
        return {k: convert_none_strings_to_none(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_none_strings_to_none(item) for item in data]
    elif isinstance(data, str) and data == "none":
        return None
    else:
        return data


def map_fields_in_place(container: dict, key: str, key_map: dict[str, str]):
    """Swap the keys in the element in the [container] with key [key]
    If the sub-key name exists in [map_machine_to_human] then replace it with the mapped string
    Otherwise leave the key as it is

    Example:

    if results["KPIs"] = {"Baseline": <A>, "design_0": <B>}

    then after running:
        map_fields_in_place(results, "KPIs", {"design_0": "Design Zero"})

    results["KPIs"] = {"Baseline": <A>, "Design Zero": <B>}

    Args:
        container (dict): _description_
        key (str): _description_
        map_machine_to_human (dict[str, str]): _description_
    """
    container_orig = deepcopy(container[key])
    container[key] = {}
    for k, v in container_orig.items():
        orig_key = key_map.get(k, k)
        container[key][orig_key] = v
