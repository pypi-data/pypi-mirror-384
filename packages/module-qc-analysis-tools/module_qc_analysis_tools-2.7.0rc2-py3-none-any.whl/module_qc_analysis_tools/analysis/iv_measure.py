from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
from module_qc_data_tools import (
    get_sensor_type_from_layer,
)

from module_qc_analysis_tools import data as data_path
from module_qc_analysis_tools.utils.analysis import (
    breakdown_threshold,
    current_compliance,
    current_threshold,
    depletion_voltage_default,
    find_breakdown_and_current,
    make_iv_plots,
    module_sensor_area,
    normalise_current,
    operation_voltage,
    perform_qc_analysis,
    update_iv_cuts,
)
from module_qc_analysis_tools.utils.misc import (
    bcolors,
    get_qc_config,
)

TEST_TYPE = Path(__file__).stem.upper()

log = logging.getLogger("analysis")


def analyse(
    iv_array,
    depl_volt,
    module_sn,
    layer,
    ref=None,
    temp=None,
    qc_criteria_path=None,
):
    sensor_type = get_sensor_type_from_layer(layer)
    is3Dmodule = "3D" in sensor_type
    cold = False
    # # qc_criteria_path is normally a path in mqat
    # # but can be (miss)used to enter an actual qc_criteria json for reporting
    # # see if it's a json, if not, it's a path or None
    try:
        qc_config = json.loads(qc_criteria_path)
    except (ValueError, TypeError, json.decoder.JSONDecodeError):
        qc_config = get_qc_config(
            qc_criteria_path or data_path / "analysis_cuts.json", TEST_TYPE
        )

    #  check input IV array
    for key in ["voltage", "current", "sigma current"]:
        iv_array[key] = [abs(value) for value in iv_array[key]]

    normalised_current = []

    if len(iv_array["voltage"]) == len(iv_array["temperature"]):
        normalised_current = normalise_current(
            iv_array["current"], iv_array["temperature"]
        )
        cold = np.average(iv_array["temperature"]) < 0
    elif len(iv_array["temperature"]) > 0:
        normalised_current = normalise_current(
            iv_array["current"],
            len(iv_array["current"]) * [np.average(iv_array["temperature"])],
        )
        cold = np.average(iv_array["temperature"]) < 0
    elif temp is not None:
        log.warning(
            bcolors.WARNING
            + f" No temperature array recorded, using {temp}degC."
            + bcolors.ENDC
        )
        normalised_current = normalise_current(
            iv_array["current"], len(iv_array["current"]) * [temp]
        )
        cold = temp < 0
    else:
        log.warning(
            bcolors.WARNING
            + " No temperature recorded, cannot normalise to 20 degC."
            + bcolors.ENDC
        )

    if cold:
        normalised_current = iv_array["current"]

    #  check reference IV data
    if ref is not None:
        try:
            ref["reference_IVs"]
        except Exception as fail:
            log.warning(
                bcolors.WARNING + f" No reference IVs found: {fail}" + bcolors.ENDC
            )

            if is3Dmodule and len(ref["reference_IVs"]) == 3:
                log.debug(" Found 3 bare single IVs for triplet.")
            elif not is3Dmodule and len(ref["reference_IVs"]) == 1:
                log.debug(" Found one bare quad IV.")
            else:
                log.error(
                    bcolors.ERROR
                    + " Incorrect number of reference IVs found \U0001f937"
                    + bcolors.ENDC
                )

            for item in ref["reference_IVs"]:
                if not (
                    item["Vbd"]
                    and item["Vfd"]
                    and item["temperature"]
                    and item["IV_ARRAY"]
                ):
                    log.error(
                        bcolors.ERROR
                        + ' Key(s) missing in "reference_IVs"'
                        + bcolors.ENDC
                    )

    #  get values
    area = module_sensor_area(layer)
    current_at_vop = (
        current_threshold(is3D=is3Dmodule, isBare=False, isModule=True) * area
    )
    current_compl = current_compliance()

    # # depletion voltage, operation voltage
    # # sensor measurement range is 0V to 200V (planar)
    Vdepl = 0
    if depl_volt is not None and abs(depl_volt) > 0 and abs(depl_volt) < 200:
        Vdepl = abs(depl_volt)
        log.info(f" Using manual input depletion voltage {Vdepl}V.")
    elif ref is not None:
        for v in ref["reference_IVs"]:
            if v["Vfd"] in [-999, 0, None]:
                log.warning(
                    bcolors.WARNING
                    + f" Depletion voltage provided in the bare module IV is not valid: {v['Vfd']}V for component {v['component_sn']}!"
                    + bcolors.ENDC
                )
        try:
            tmp_vfd = max(
                abs(v["Vfd"]) for v in ref["reference_IVs"] if v["Vfd"] != -999
            )
            if 0 < tmp_vfd < 200:
                Vdepl = tmp_vfd
                log.info(f" Found depletion voltage from sensor data: {Vdepl}V.")
            else:
                log.warning(
                    bcolors.WARNING
                    + f" Depletion voltage provided in the bare module IV is not valid: {tmp_vfd}V. Proceed using default value!"
                    + bcolors.ENDC
                )
        except (KeyError, ValueError):
            depl_volt = None
            log.warning(
                bcolors.WARNING
                + " No depletion voltage found in bare module IV."
                + bcolors.ENDC
            )

    if Vdepl == 0:
        Vdepl = depletion_voltage_default(is3Dmodule)
        log.warning(
            bcolors.WARNING
            + f" No valid depletion voltage provided, proceed using default value of {Vdepl}V."
            + bcolors.ENDC
        )

    # # same for sensor and module
    Vop = operation_voltage(Vdepl, is3Dmodule)

    # # breakdown voltage and leakage current at operation voltage from previous stage
    # # *0 values are from previous stage (bare module reception)
    Vbd0 = None  # # get from bare module stage below
    Ilc0 = 0  # # initial value has to be 0 because currents will be added below

    if ref is not None:
        # # check if any of the bare modules have a breakdown
        # # for triplets get the lowest breakdown voltage
        try:
            Vbd0 = min(
                (v["Vbd"] for v in ref["reference_IVs"] if v["Vbd"] > -999),
                default=-999,
            )
        except Exception:
            _missing = {v["component_sn"]: v["Vbd"] for v in ref["reference_IVs"]}
            log.error(
                f"Missing breakdown voltage on sensor tile(s), please fix it in the production database! {_missing}"
            )

        for iv in ref["reference_IVs"]:
            if (
                np.average(iv["IV_ARRAY"]["voltage"]) < 0
                or np.average(iv["IV_ARRAY"]["current"]) < 0
            ):
                log.warning(
                    f"The bare module IV of {iv['component_sn']} has negative polarity! Data in the PDB should store absolute values - please fix!"
                )
                for key in ["voltage", "current"]:
                    try:
                        iv["IV_ARRAY"][key] = np.abs(iv["IV_ARRAY"][key])
                    except KeyError as kerr:
                        log.warning(kerr)
            for index, v in enumerate(iv["IV_ARRAY"]["voltage"]):
                # # only need V>=Vop to determine leakage current at Vop
                if v >= Vop:
                    temperatures = iv["IV_ARRAY"]["temperature"] or []
                    voltages = iv["IV_ARRAY"]["voltage"]
                    _temp = 23
                    if not temperatures:
                        log.warning(
                            f" No temperature array found for bare module {iv['component_sn']}"
                        )
                        try:
                            _temp: float = (
                                temperatures[index]
                                if len(temperatures) == len(voltages)
                                else iv["temperature"]
                            )
                        except Exception:
                            _temp: float = iv["temperature"]

                    Ilc0 += normalise_current(
                        iv["IV_ARRAY"]["current"][index], _temp
                    )  # # += for triplets

                    break

        log.debug(f"Ilc0: {Ilc0}uA at {Vop}V")

    #  breakdown voltage and leakage current at operation voltage
    Vbd = -999  # # -999V if no breakdown occurred during the measurement
    Ilc = -999
    # Finding breakdown voltage and leakage current at operation voltage
    Vbd, Ilc = find_breakdown_and_current(
        iv_array["voltage"],
        normalised_current,
        Vdepl,
        Vop,
        is3Dmodule,
        current_at_vop,
        current_compl,
        iv_array,
    )

    fig = make_iv_plots(
        module_sn,
        iv_array,
        normalised_current,
        Vbd,
        temp,
        cold,
        ref,
        Vop,
        breakdown_threshold(Vdepl, is3Dmodule),
        current_at_vop,
        current_compl,
    )

    qc_config = update_iv_cuts(qc_config, layer, Vdepl)

    # # "IV_ARRAY", "IV_IMG", "BREAKDOWN_VOLTAGE", "LEAK_CURRENT", "MAXIMUM_VOLTAGE", "NO_BREAKDOWN_VOLTAGE_OBSERVED"
    results = {}
    results["IV_ARRAY"] = iv_array
    results["BREAKDOWN_VOLTAGE"] = Vbd

    # check for the case that breakdown was observed in the previous stage but not in the current stage
    # solves https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/issues/144
    if Vbd0 and Vbd0 > -999 and (Vbd == -999 or Vbd > Vbd0):
        results["BREAKDOWN_REDUCTION"] = -1
    else:
        results["BREAKDOWN_REDUCTION"] = Vbd0 - Vbd if Vbd0 else -999

    results["NO_BREAKDOWN_VOLTAGE_OBSERVED"] = True
    if Vbd != -999:
        results["NO_BREAKDOWN_VOLTAGE_OBSERVED"] = False
    results["MAXIMUM_VOLTAGE"] = max(iv_array["voltage"])
    results["LEAK_CURRENT"] = Ilc
    results["LEAK_INCREASE_FACTOR"] = Ilc / Ilc0 if (Ilc0 and (Ilc != -999)) else -999
    results["LEAK_PER_AREA"] = Ilc / area if Ilc != -999 else -999

    passes_qc, summary, rounded_results = perform_qc_analysis(
        TEST_TYPE, qc_config, layer, results
    )

    return rounded_results, passes_qc, summary, fig
