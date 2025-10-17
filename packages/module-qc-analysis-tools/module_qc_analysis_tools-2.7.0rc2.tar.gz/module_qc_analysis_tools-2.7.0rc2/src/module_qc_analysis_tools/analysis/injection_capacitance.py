from __future__ import annotations

import logging
from functools import partial

import matplotlib.pyplot as plt
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
    get_qc_config,
)

TEST_TYPE = "INJECTION_CAPACITANCE"

log = logging.getLogger(f"analysis.{TEST_TYPE}")


def analyze(
    input_json,
    site="",
    input_layer="Unknown",
    qc_criteria_path=None,
):
    func = partial(
        analyze_chip,
        site=site,
        input_layer=input_layer,
        qc_criteria_path=qc_criteria_path,
    )
    results = []
    for chip in input_json:
        if isinstance(chip, list):
            for item in chip:
                result = func(item)
                if result:
                    results.append(result)
        else:
            result = func(chip)
            if result:
                results.append(result)

    return zip(*results)


def analyze_chip(
    input_json,
    site="",
    input_layer="Unknown",
    qc_criteria_path=None,
):
    inputDF = outputDataFrame(_dict=input_json)

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

    qc_config = get_qc_config(qc_criteria_path, TEST_TYPE, metadata.get("ModuleSN"))

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

    #   Calculate quanties
    # Vmux conversion is embedded.
    extractor = DataExtractor(inputDF, TEST_TYPE)
    calculated_data = extractor.calculate()

    #         Plotting
    CapMeas = calculated_data.get("CapMeas").get("Values")
    CapMeasPar = calculated_data.get("CapMeasPar").get("Values")
    VDDAcapmeas = calculated_data.get("VDDAcapmeas").get("Values")
    VmuxGnds = calculated_data.get("Vmux30").get("Values")
    ImuxGnds = calculated_data.get("Imux63").get("Values")

    allCpix = []
    figs = []
    for i, value in enumerate(CapMeas):
        cmeas = abs(
            value
            / (
                (VDDAcapmeas[i] - (extractor.rImux * value + ImuxGnds[i] - VmuxGnds[i]))
                * 10000000
            )
        )
        cpar = abs(
            CapMeasPar[i]
            / (
                (
                    VDDAcapmeas[i]
                    - (extractor.rImux * CapMeasPar[i] + ImuxGnds[i] - VmuxGnds[i])
                )
                * 10000000
            )
        )
        cpix = ((cmeas - cpar) / 100) - 0.48e-15
        allCpix += [cpix * 1e15]

    avgCpix = sum(allCpix) / len(allCpix)

    fig1, ax1 = plt.subplots()
    ax1.plot(
        range(len(allCpix)),
        allCpix,
        "o",
        label="Pixel injection capacitance",
        markersize=10,
    )
    plt.axhline(
        y=avgCpix,
        color="r",
        linestyle="-",
        label="Average Cpix = " + str(round(avgCpix, 3)) + " fF",
    )
    plt.legend(bbox_to_anchor=(1.0, 1), loc="upper right")
    plt.title(chipname)
    ax1.set_xlabel("N (measurements)")
    ax1.set_ylim(min(allCpix) - 0.1, max(allCpix) + 0.1)
    ax1.set_ylabel("Pixel injection capacitance [fF]")
    plt.grid()
    figs.append(fig1)

    fig2, ax1 = plt.subplots()
    ax1.plot(
        range(len(CapMeas)),
        CapMeas,
        "o",
        label="Capmeasure current circuit",
        markersize=10,
    )
    ax1.set_xlabel("N (measurements)")
    ax1.set_ylabel("CapMeas circuit current [A]")
    plt.grid()
    plt.title(chipname)
    figs.append(fig2)

    fig3, ax1 = plt.subplots()
    ax1.plot(
        range(len(CapMeasPar)),
        CapMeasPar,
        "o",
        label="Capmeasure parasitic current circuit",
        markersize=10,
    )
    ax1.set_xlabel("N (measurements)")
    ax1.set_ylabel("CapMeas parasitic current [A]")
    plt.grid()
    plt.title(chipname)
    figs.append(fig3)

    # Load values to dictionary for QC analysis
    results = {}
    results.update({"INJ_CAPACITANCE": avgCpix})

    # Perform QC analysis
    passes_qc, summary, rounded_results = perform_qc_analysis(
        TEST_TYPE, qc_config, layer, results
    )

    # Output a json file
    outputDF = outputDataFrame()
    outputDF.set_test_type(TEST_TYPE)
    data = qcDataFrame()
    data._meta_data.update(metadata)
    data.add_property(
        "ANALYSIS_VERSION",
        __version__,
    )
    data.add_meta_data(
        "MEASUREMENT_VERSION",
        qcframe.get_properties().get(f"{TEST_TYPE}_MEASUREMENT_VERSION"),
    )
    data.add_meta_data("QC_LAYER", layer)
    data.add_meta_data("INSTITUTION", institution)
    for key, value in rounded_results.items():
        data.add_parameter(key, value)
    outputDF.set_results(data)
    outputDF.set_pass_flag(passes_qc)

    return chipname, outputDF.to_dict(True), passes_qc, summary, figs
