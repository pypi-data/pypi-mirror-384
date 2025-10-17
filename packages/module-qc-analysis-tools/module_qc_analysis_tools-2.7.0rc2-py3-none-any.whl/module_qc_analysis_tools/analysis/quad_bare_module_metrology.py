from __future__ import annotations

import logging
from functools import partial

import arrow
import numpy as np
from module_qc_data_tools import (
    get_layer_from_sn,
    outputDataFrame,
    qcDataFrame,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools import data as data_path
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    perform_qc_analysis,
)
from module_qc_analysis_tools.utils.misc import (
    JsonChecker,
    bcolors,
    get_qc_config,
)

TEST_TYPE = "QUAD_BARE_MODULE_METROLOGY"

log = logging.getLogger(f"analysis.{TEST_TYPE}")


def analyze(
    input_jsons,
    site="",
    input_layer="Unknown",
    qc_criteria_path=None,
):
    func = partial(
        analyze_module,
        site=site,
        input_layer=input_layer,
        qc_criteria_path=qc_criteria_path,
    )

    results = []
    for input_json in input_jsons:
        if isinstance(input_json, list) and len(input_json) > 1:
            msg = "Must provide a single measurement per module."
            raise RuntimeError(msg)
        result = func(input_json)
        if result:
            results.append(result)

    return zip(*results)


def analyze_module(
    input_json,
    site="",
    input_layer="Unknown",
    qc_criteria_path=None,
):
    inputDF = outputDataFrame(_dict=input_json[0])

    qc_config = get_qc_config(
        qc_criteria_path or data_path / "analysis_cuts.json", TEST_TYPE
    )

    # Check file integrity
    checker = JsonChecker(inputDF, TEST_TYPE)

    try:
        # NB: flatness and angles are independent measurements and don't correspond to each other
        checker.check(keywords_length=False)
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

    module_sn = metadata.get("ModuleSN")
    if input_layer == "Unknown":
        try:
            layer = get_layer_from_sn(module_sn)
        except Exception:
            log.error(bcolors.WARNING + " Something went wrong." + bcolors.ENDC)
    else:
        log.warning(
            bcolors.WARNING
            + f" Overwriting default layer config {get_layer_from_sn(module_sn)} with manual input {input_layer}!"
            + bcolors.ENDC
        )
        layer = input_layer
    check_layer(layer)

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

    df = inputDF.get_results()._data

    results = {key: np.average(value["Values"]) for key, value in df.items()}

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
    data.add_meta_data(
        "MEASUREMENT_VERSION",
        qcframe.get_properties().get(f"{TEST_TYPE}_MEASUREMENT_VERSION"),
    )
    time_start = qcframe.get_meta_data()["TimeStart"]
    time_end = qcframe.get_meta_data().get("TimeEnd")
    duration = (
        (arrow.get(time_end) - arrow.get(time_start)).total_seconds()
        if time_end
        else -1
    )

    data.add_property(
        "MEASUREMENT_DATE",
        arrow.get(time_start).isoformat(timespec="milliseconds"),
    )
    data.add_property("MEASUREMENT_DURATION", int(duration))
    data.add_meta_data("QC_LAYER", layer)
    data.add_meta_data("INSTITUTION", institution)
    for key, value in rounded_results.items():
        data.add_parameter(key, value)
    outputDF.set_results(data)
    outputDF.set_pass_flag(passes_qc)

    return module_sn, outputDF.to_dict(True), passes_qc, summary, None
