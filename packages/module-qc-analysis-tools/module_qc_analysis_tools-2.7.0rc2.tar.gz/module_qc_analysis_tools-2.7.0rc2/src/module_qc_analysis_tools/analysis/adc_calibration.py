from __future__ import annotations

import logging
from functools import partial

import arrow
import matplotlib.pyplot as plt
import numpy as np
from module_qc_data_tools import (
    get_layer_from_sn,
    outputDataFrame,
    qcDataFrame,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    perform_qc_analysis,
)
from module_qc_analysis_tools.utils.misc import (
    DataExtractor,
    JsonChecker,
    bcolors,
    get_BOMCode_from_metadata,
    get_qc_config,
    linear_fit,
    linear_fit_np,
)

TEST_TYPE = "ADC_CALIBRATION"

log = logging.getLogger(f"analysis.{TEST_TYPE}")


def analyze(
    input_jsons,
    site="",
    input_layer="Unknown",
    fit_method="numpy",
    qc_criteria_path=None,
):
    func = partial(
        analyze_chip,
        site=site,
        input_layer=input_layer,
        fit_method=fit_method,
        qc_criteria_path=qc_criteria_path,
    )

    results = []
    for input_json in input_jsons:
        if isinstance(input_json, list):
            for chip in input_json:
                result = func(chip)
                if result:
                    results.append(result)
        else:
            result = func(input_json)
            if result:
                results.append(result)

    return zip(*results)


def analyze_chip(
    chip,
    site="",
    input_layer="Unknown",
    fit_method="numpy",
    qc_criteria_path=None,
):
    inputDF = outputDataFrame(_dict=chip)

    # Check file integrity
    checker = JsonChecker(inputDF, TEST_TYPE)

    try:
        checker.check()
    except BaseException as exc:
        log.exception(exc)
        log.warning(
            bcolors.WARNING
            + " JsonChecker check not passed, skipping this input."
            + bcolors.ENDC
        )
        return None

    log.debug(" JsonChecker check passed!")

    #   Get info
    qcframe = inputDF.get_results()
    metadata = qcframe.get_meta_data()

    if input_layer == "Unknown":
        try:
            layer = get_layer_from_sn(metadata.get("ModuleSN"))
        except Exception:
            log.error(bcolors.WARNING + " Something went wrong." + bcolors.ENDC)
    else:
        module_sn = metadata.get("ModuleSN")
        log.warning(
            bcolors.WARNING
            + f" Overwriting default layer config {get_layer_from_sn(module_sn)} with manual input {input_layer}!"
            + bcolors.ENDC
        )
        layer = input_layer
    check_layer(layer)

    try:
        chipname = metadata.get("Name")
        log.debug(f" Found chip name = {chipname} from chip config")
    except Exception:
        log.warning(
            bcolors.WARNING
            + "Chip name not found in input from {filename}, skipping."
            + bcolors.ENDC
        )
        return None

    institution = metadata.get("Institution")
    if site != "" and institution != "":
        log.warning(
            bcolors.WARNING
            + f" Overwriting default institution {institution} with manual input {site}!"
            + bcolors.ENDC
        )
        institution = site
    elif site != "":
        institution = site

    if institution == "":
        log.error(
            bcolors.ERROR
            + "No institution found. Please specify your testing site either in the measurement data or specify with the --site option. "
            + bcolors.ENDC
        )
        return None

    BOMCode = get_BOMCode_from_metadata(metadata, layer)

    qc_config = get_qc_config(
        qc_criteria_path, TEST_TYPE, metadata.get("ModuleSN"), BOMCode
    )

    #   Calculate quanties
    # Vmux conversion is embedded.
    extractor = DataExtractor(inputDF, TEST_TYPE)
    calculated_data = extractor.calculate()

    # extract analog ground measurement
    AnaGND30_measurements = calculated_data.pop("AnaGND30")["Values"]
    AnaGND30_mean = np.mean(AnaGND30_measurements)
    AnaGND30_std = np.std(AnaGND30_measurements)

    #         Plotting
    x_key = "ADC_Vmux8"
    x = calculated_data.pop(x_key)
    y_key = "VcalMed"

    value = calculated_data.get(y_key)
    if fit_method.value == "root":
        p1, p0, linearity = linear_fit(x["Values"], value["Values"])
    else:
        p1, p0, linearity = linear_fit_np(x["Values"], value["Values"])

    # Convert from V to mV
    p1mv = p1 * 1000
    p0mv = p0 * 1000
    linearity = linearity * 1000.0

    fig, ax1 = plt.subplots()
    ax1.plot(
        x["Values"],
        value["Values"],
        "o",
        label="Measured data",
        markersize=10,
    )
    x_line = np.linspace(x["Values"][0], x["Values"][-1], 100)
    ax1.plot(x_line, p1 * x_line + p0, "r--", label="Fitted line")
    ax1.text(
        x["Values"][0],
        0.75 * value["Values"][-1],
        f"y = {p1:.4e} * x + {p0:.4e}",
    )
    ax1.set_xlabel(f"{x_key}[{x['Unit']}]")
    ax1.set_ylabel(f"{y_key}[{value['Unit']}]")
    ax1.set_title(chipname)
    ax1.legend()

    # Load values to dictionary for QC analysis
    results = {}
    results.update({"ADC_CALIBRATION_SLOPE": p1mv})
    results.update({"ADC_CALIBRATION_OFFSET": p0mv})
    results.update({"ADC_CALIBRATION_LINEARITY": linearity})
    results.update({"ADC_ANAGND30_MEAN": AnaGND30_mean})
    results.update({"ADC_ANAGND30_STD": AnaGND30_std})

    # Perform QC analysis
    passes_qc, summary, rounded_results = perform_qc_analysis(
        TEST_TYPE, qc_config, layer, results
    )

    #  Output a json file
    outputDF = outputDataFrame()
    outputDF.set_test_type(TEST_TYPE)
    data = qcDataFrame()
    data._meta_data.update(metadata)
    data.add_property(
        "ANALYSIS_VERSION",
        __version__,
    )
    try:
        data.add_property(
            "YARR_VERSION",
            qcframe.get_properties().get("YARR_VERSION"),
        )
    except Exception as e:
        log.warning(f"Unable to find YARR version! Require YARR >= v1.5.2. {e}")
        data.add_property("YARR_VERSION", "")
    data.add_meta_data(
        "MEASUREMENT_VERSION",
        qcframe.get_properties().get(f"{TEST_TYPE}_MEASUREMENT_VERSION"),
    )
    time_start = qcframe.get_meta_data()["TimeStart"]
    time_end = qcframe.get_meta_data()["TimeEnd"]
    duration = arrow.get(time_end) - arrow.get(time_start)

    data.add_property(
        "MEASUREMENT_DATE",
        arrow.get(time_start).isoformat(timespec="milliseconds"),
    )
    data.add_property("MEASUREMENT_DURATION", int(duration.total_seconds()))
    data.add_meta_data("QC_LAYER", layer)
    data.add_meta_data("INSTITUTION", institution)
    for key, value in rounded_results.items():
        data.add_parameter(key, value)
    outputDF.set_results(data)
    outputDF.set_pass_flag(passes_qc)
    return chipname, outputDF.to_dict(True), passes_qc, summary, fig
