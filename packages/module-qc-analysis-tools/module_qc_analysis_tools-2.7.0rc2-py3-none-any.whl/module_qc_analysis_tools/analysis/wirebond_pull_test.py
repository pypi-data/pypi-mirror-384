from __future__ import annotations

from statistics import stdev
from typing import Literal, TypedDict

TBreakMode = Literal[
    "Midspan break",
    "Heel break on hybrid",
    "Heel break on chip",
    "Bond peel on hybrid",
    "Bond peel on chip",
    "Pull failure",
    "Operator error",
    "other error",
]


class WirebondPulLData(TypedDict):
    """
    Wirebond Pull Data entry
    """

    strength: float
    break_mode: TBreakMode


def process_pull_data(
    meas_array: list[dict[str, str | float]],
) -> dict[str, float | bool | list]:
    WIRE_PULLS = len(meas_array)
    strength = []
    wire_break_code = None
    counter_of_wires_without_error = 0
    counter_of_wires_with_error = 0
    counter_of_weak_wire = 0
    counter_of_liftoff_below_7g = 0
    counter_of_FE = 0
    counter_of_PCB = 0
    counter_of_peel_on_FE = 0
    counter_of_peel_on_PCB = 0
    counter_of_bond_peel = 0
    counter_of_midspan = 0

    data = []

    y_code_map: dict[TBreakMode, int] = {
        "Midspan break": 0,
        "Heel break on hybrid": 1,
        "Heel break on chip": 2,
        "Bond peel on hybrid": 3,
        "Bond peel on chip": 4,
        "Pull failure": 5,
        "Operator error": 5,
        "other error": 5,
    }

    for i in range(WIRE_PULLS):
        each_wire_strength = meas_array[i].get("strength")
        type_of_break = meas_array[i].get("break_mode")

        if meas_array[i].get("location"):
            location = int(meas_array[i].get("location"))
        else:
            if i < 10:
                location = 1
            elif i < 15:
                location = 2
            elif i < 25:
                location = 3
            else:
                location = 4

        wire_break_code = y_code_map.get(type_of_break)

        data.append([[each_wire_strength, wire_break_code, location]])
        # or
        # data.append([[each_wire_strength], [wire_break_code], [location]])

        if wire_break_code in [5, None]:  # Wires with errors or undefined
            counter_of_wires_with_error += 1
        else:
            counter_of_wires_without_error += 1
            if each_wire_strength < 5.0:
                counter_of_weak_wire += 1
            if type_of_break == "Heel break on chip":
                counter_of_FE += 1
            elif type_of_break == "Heel break on hybrid":
                counter_of_PCB += 1
            elif type_of_break == "Bond peel on chip":
                counter_of_peel_on_FE += 1
                if each_wire_strength < 7.0:
                    counter_of_liftoff_below_7g += 1
            elif type_of_break == "Bond peel on hybrid":
                counter_of_peel_on_PCB += 1
                if each_wire_strength < 7.0:
                    counter_of_liftoff_below_7g += 1
            elif type_of_break == "Midspan break":
                counter_of_midspan += 1
            strength.append(each_wire_strength)

        counter_of_bond_peel = counter_of_peel_on_FE + counter_of_peel_on_PCB

    return {
        "WIRE_PULLS": {"X": True, "Unit": "", "Values": [WIRE_PULLS]},
        "PULL_STRENGTH": {
            "X": True,
            "Unit": "",
            "Values": [sum(strength) / counter_of_wires_without_error],
        },
        "PULL_STRENGTH_ERROR": {"X": True, "Unit": "", "Values": [stdev(strength)]},
        "WIRE_BREAKS_5G": {"X": True, "Unit": "", "Values": [counter_of_weak_wire]},
        "PULL_STRENGTH_MIN": {"X": True, "Unit": "", "Values": [min(strength)]},
        "PULL_STRENGTH_MAX": {"X": True, "Unit": "", "Values": [max(strength)]},
        "HEEL_BREAKS_ON_FE_CHIP": {
            "X": True,
            "Unit": "",
            "Values": [counter_of_FE / WIRE_PULLS * 100],
        },
        "HEEL_BREAKS_ON_PCB": {
            "X": True,
            "Unit": "",
            "Values": [counter_of_PCB / WIRE_PULLS * 100],
        },
        "BOND_PEEL": {
            "X": True,
            "Unit": "",
            "Values": [counter_of_bond_peel / WIRE_PULLS * 100],
        },
        "LIFT_OFFS_LESS_THAN_7G": {
            "X": True,
            "Unit": "",
            "Values": [counter_of_liftoff_below_7g / WIRE_PULLS * 100],
        },
        "DATA_UNAVAILABLE": {"X": True, "Unit": "", "Values": [WIRE_PULLS == 0]},
        "PULL_STRENGTH_DATA": {"X": True, "Unit": "", "Values": [data]},
        # "WIRE_PULLS_WITHOUT_ERROR": {
        #     "X": True,
        #     "Unit": "",
        #     "Values": [counter_of_wires_without_error],
        # },
        # "BOND_PEEL_ON_FE_CHIP": {
        #     "X": True,
        #     "Unit": "",
        #     "Values": [counter_of_peel_on_FE / WIRE_PULLS * 100],
        # },
        # "BOND_PEEL_ON_PCB": {
        #     "X": True,
        #     "Unit": "",
        #     "Values": [counter_of_peel_on_PCB / WIRE_PULLS * 100],
        # },
        # "MIDSPAN": {
        #     "X": True,
        #     "Unit": "",
        #     "Values": [counter_of_midspan / WIRE_PULLS * 100],
        # },
        # "WITH_ERROR": {
        #     "X": True,
        #     "Unit": "",
        #     "Values": [counter_of_wires_with_error / WIRE_PULLS * 100],
        # },
    }
