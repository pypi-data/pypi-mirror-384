from __future__ import annotations

import logging
from functools import partial

import arrow
import matplotlib.pyplot as plt
import numpy as np
from module_qc_data_tools import (
    get_layer_from_sn,
    get_nlanes_from_sn,
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

TEST_TYPE = "DATA_TRANSMISSION"

log = logging.getLogger(f"analysis.{TEST_TYPE}")


def merge_dicts(d1, d2, keep_latest_keys=None):
    """Recursively merge two dictionaries, keeping the latest values for specific keys
    and applying logical AND for the 'passed' field."""
    if keep_latest_keys is None:
        keep_latest_keys = {"runNumber", "MEASUREMENT_DATE", "MEASUREMENT_DURATION"}

    merged = dict(d1)  # Start with d1's keys and values
    for key, value in d2.items():
        if key in keep_latest_keys:
            merged[key] = value  # Always take the latest value from d2
        elif key == "passed":
            merged[key] = merged[key] and value  # Apply AND operation
        elif key in merged:
            if isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = merge_dicts(
                    merged[key], value, keep_latest_keys
                )  # Recursive merge
            elif isinstance(merged[key], list) and isinstance(value, list):
                merged[key] += value  # Concatenate lists
            elif isinstance(merged[key], set) and isinstance(value, set):
                merged[key] |= value  # Union of sets
            elif merged[key] != value:
                merged[key] = [merged[key], value]  # Store differing values in a list
        else:
            merged[key] = value
    return merged


def analyze(
    input_jsons,
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

    tempresults = []
    for input_json in input_jsons:
        if isinstance(input_json, list):
            for chip in input_json:
                result = func(chip)
                if result:
                    tempresults.append(result)
        else:
            result = func(input_json)
            if result:
                tempresults.append(result)

    results = {}
    for chipname, data, passes_qc, summary, fig in tempresults:
        if chipname in results:  # do merge
            otherdata, other_passes_qc, other_summary, other_figs = results[chipname]
            results[chipname] = (
                merge_dicts(otherdata, data),
                passes_qc & other_passes_qc,
                np.array([*other_summary.tolist(), *summary.tolist()]),
                [*other_figs, fig],
            )
        else:
            results[chipname] = (data, passes_qc, summary, [fig])

    results = [(chipname, *result) for chipname, result in results.items()]
    return zip(*results)


def analyze_chip(
    input_json,
    site="",
    input_layer="Unknown",
    qc_criteria_path=None,
):
    ## will be returned
    chipname = None
    data = qcDataFrame()  ## to output data frame
    summary = np.empty((0, 4), str)
    passes_qc = True
    fig = None

    ## used only here
    n_lanes_per_chip = None
    results_eye = {}  ## has only "EYE_WIDTH" for analysis
    results_merge = {}  ##
    summary_merge = np.empty((0, 4), str)
    inputDFs = []

    if isinstance(input_json, list):
        for item in input_json:
            inputDFs.append(outputDataFrame(_dict=item))
    else:
        inputDFs.append(outputDataFrame(_dict=input_json))

    ## inputDFs contain subtest results for each chip
    ## each inputDF is one subtest
    ## want to have a combined summary per chip of all subtests
    for inputDF in inputDFs:
        # Check file integrity
        checker = JsonChecker(inputDF, TEST_TYPE)
        try:
            checker.check()
        except KeyError as kerr:
            log.warning(bcolors.WARNING + f"KeyError {kerr}" + bcolors.ENDC)
            log.warning(
                bcolors.WARNING
                + "This might be OK due to backward compatibility."
                + bcolors.ENDC
            )
        except BaseException as exc:
            log.exception(exc)
            log.error(
                bcolors.ERROR
                + " JsonChecker check not passed, skipping this input."
                + bcolors.ENDC
            )
            return None

        log.debug(" JsonChecker check passed!")

        # Get info
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

        try:
            chipname = metadata.get("Name")
            log.debug(f" Found chip name = {chipname} from chip config")
        except Exception:
            log.error(
                bcolors.ERROR
                + f" Chip name not found in input from {input_json}, skipping."
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
            qcframe.get_properties().get(TEST_TYPE + "_MEASUREMENT_VERSION"),
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

        #  Output a json file
        outputDF = outputDataFrame()
        outputDF.set_test_type(TEST_TYPE)

        #   Calculate quanties
        extractor = DataExtractor(inputDF, TEST_TYPE)
        calculated_data = extractor.calculate()
        qc_config = get_qc_config(qc_criteria_path, TEST_TYPE, module_sn)

        log.debug(f" calculated_data:\n{calculated_data}")
        log.debug(f"---------------{inputDF._subtestType}----------------")
        ### subtesttype
        if inputDF._subtestType == "DT_MERGE":
            for key in calculated_data:
                # Load values to dictionary for QC analysis
                results_merge.update(
                    {
                        key.upper().replace("-", "_"): int(
                            calculated_data[key]["Values"][0]
                        )
                    }
                )
                # Add data merging to output file
                data.add_parameter(
                    key.upper().replace("-", "_"),
                    int(calculated_data[key]["Values"][0]),
                )
            passes_qc, summary_merge, _rounded_results = perform_qc_analysis(
                TEST_TYPE, qc_config, layer, results_merge, check=False
            )
            summary_merge = summary_merge.reshape(-1, 4)
        elif inputDF._subtestType == "DT_DIGITALSCAN":
            pass
        else:
            n_lanes_per_chip = get_nlanes_from_sn(module_sn)
            passes_qc_per_lane = n_lanes_per_chip * [True]
            linestyles = ["solid", "dotted", "dashed", "dashdot"]
            markerstyles = ["*", "o", "v", "s"]
            colours = ["C0", "C1", "C2", "C3"]

            DELAY = calculated_data["Delay"]["Values"]
            EYE_OPENING = []
            EYE_WIDTH = []
            DELAY_SETTING = []

            fig, ax = plt.subplots()

            ## calculated_data.keys() are e.g. ["Delay", "EyeOpening0"]
            for lane in range(len(calculated_data.keys()) - 1):
                log.debug(
                    f"{lane} / len(calculated_data.keys()) {calculated_data.keys()}"
                )
                EYE_OPENING.append(calculated_data[f"EyeOpening{lane}"]["Values"])

                start_val = 0
                width = 0
                last_width = 0
                best_val = 0
                best_width = 0
                best_delay = 0

                for j in DELAY:
                    if EYE_OPENING[-1][j] == 1:
                        if width == 0:
                            start_val = j
                        width += 1
                        if j == DELAY[-1] and width > last_width:
                            best_val = start_val
                            best_width = width
                    else:
                        if width > last_width:
                            best_val = start_val
                            best_width = width
                        last_width = best_width
                        width = 0

                if best_width != 0:
                    best_delay = int(best_val + (best_width / 2))
                    log.info(
                        f"Delay setting for lane {lane} with eye width {best_width}: {best_delay}"
                    )
                else:
                    log.info(f"No good delay setting for lane {lane}")

                EYE_WIDTH.append(best_width)
                DELAY_SETTING.append(best_delay)

                # Load values to dictionary for QC analysis
                results_eye.update({"EYE_WIDTH": best_width})

                # Perform QC analysis
                (
                    passes_qc_per_lane[lane],
                    summary_per_lane,
                    _rounded_results,
                ) = perform_qc_analysis(
                    TEST_TYPE, qc_config, layer, results_eye, check=False
                )
                summary_per_lane[0] = summary_per_lane[0] + str(lane)
                summary = np.append(summary, [summary_per_lane], axis=0)
                summary.reshape(-1, 4)

                # Add eye widths to output file
                data.add_parameter(f"EYE_WIDTH{lane}", EYE_WIDTH[lane], 0)
                log.debug(f"EYE_WIDTH {EYE_WIDTH}")

                # # Internal eye diagram visualisation
                ax.step(
                    calculated_data["Delay"]["Values"],
                    calculated_data[f"EyeOpening{lane}"]["Values"],
                    linestyle=linestyles[lane],
                    color=colours[lane],
                    label=f"Eye Opening [{lane}]: {best_width}",
                )
                ax.plot(
                    best_delay,
                    1,
                    linestyle="None",
                    marker=markerstyles[lane],
                    markersize=10,
                    color=colours[lane],
                    label=f"Best Delay [{lane}]: {best_delay}",
                )

                ax.legend()

            passes_qc = all(passes_qc_per_lane)

            ax.set_xlabel("Delay")
            ax.set_ylabel("Eye Opening")
            ax.set_title(f"{module_sn} {chipname}")
            plt.grid()
            plt.tight_layout()

    summary = np.append(summary, summary_merge, axis=0)
    log.debug(f" fig {fig}")

    outputDF.set_results(data)
    outputDF.set_pass_flag(passes_qc)
    return chipname, outputDF.to_dict(True), passes_qc, summary, fig
