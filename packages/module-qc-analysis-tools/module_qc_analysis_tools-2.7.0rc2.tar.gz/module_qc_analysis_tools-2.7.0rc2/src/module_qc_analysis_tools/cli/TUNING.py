from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import arrow
import numpy as np
import typer
from module_qc_data_tools import (
    convert_serial_to_name,
    get_layer_from_sn,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    get_bounds_and_precision,
    get_layer,
    perform_qc_analysis,
    print_result_summary,
)
from module_qc_analysis_tools.utils.classification import (
    check_input_yarr_config,
    check_input_yarr_data,
    check_test_params,
    classify_pixels,
    count_pixels,
    format_coreCol_input,
    format_pixel_input,
    format_TDAC_input,
    plot_1d_hist,
    plot_2d_map,
    read_json,
)
from module_qc_analysis_tools.utils.misc import (
    bcolors,
    get_qc_config,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    input_yarr: Path = OPTIONS["input_yarr_config"],
    qc_criteria_path: Path = OPTIONS["qc_criteria"],
    pixel_classification_path: Path = OPTIONS["pixel_classification"],
    base_output_dir: Path = OPTIONS["output_dir"],
    permodule: bool = OPTIONS["permodule"],
    input_layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
    ignore_bad_corecol: bool = OPTIONS["ignore_bad_corecol"],
):
    """
    Analyzes the tuning performance from YARR scans.

    It produces an output file with key parameters (threshold before/after tuning, ...). Note that the YARR scans to be used in the analysis should be identified with [`mqat analysis load-yarr-scans`](#mqat-config-load-yarr-scans).
    """
    test_type = Path(__file__).stem

    time_start = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    log = logging.getLogger("analysis")
    log.setLevel(verbosity.value)
    log.addHandler(logging.FileHandler(f"{output_dir}/output.log"))

    # Turn off pytest DEBUG messages
    pil_logger = logging.getLogger("PIL")
    pil_logger.setLevel(logging.INFO)

    log.info("")
    log.info(" ====================================================")
    log.info(" \tPerforming tuning analysis")
    log.info(" ====================================================")
    log.info("")

    input_data = read_json(input_yarr)
    check_input_yarr_config(input_data, path=input_yarr)
    datadir = input_data["datadir"]
    yarr_version = input_data["YARR_VERSION"]
    module_sn = input_data["module"]["serialNumber"]
    time_start = input_data["TimeStart"]
    time_duration = input_data.get("TimeDuration", -1)
    layer = get_layer_from_sn(module_sn)
    chiptype = input_data["module"]["chipType"]

    qc_config_untuned = get_qc_config(
        qc_criteria_path, test_type + "_UNTUNED", module_sn
    )
    qc_config_tuned = get_qc_config(qc_criteria_path, test_type + "_TUNED", module_sn)

    # Don't allow ignoring bad core columns unless RD53B
    if chiptype != "RD53B":
        ignore_bad_corecol = False

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

    pixel_classification = read_json(pixel_classification_path)
    if not pixel_classification.get(test_type):
        log.error(
            bcolors.BADRED
            + f"Pixel failure selection for {test_type} not found in {pixel_classification_path}! Please check. "
            + bcolors.ENDC
        )
        raise RuntimeError()

    alloutput = []
    for c in input_data["chip"]:
        chipSN = c["serialNumber"]
        chipName = convert_serial_to_name(chipSN)
        filepaths = c["filepaths"]
        results_tuned = {}
        results_untuned = {}

        # Initialize array to track pixel failures
        pix_fail_tuned = np.zeros(153600, dtype=np.uint16)
        pix_fail_untuned = np.zeros(153600, dtype=np.uint16)

        # Initialize int to track which classifications have been checked
        record_fail_tuned = 0
        record_fail_untuned = 0

        log.debug(f"Performing tuning test analysis on chip {c['serialNumber']}")

        # Loop through pixel failure tests from config file
        for test_name, params in pixel_classification.get(test_type).items():
            log.debug(f"Performing {test_name}")

            test_input = params.get("input")
            test_method = params.get("method")
            test_params = params.get("params")

            # Get layer-specific params if necessary
            test_params = check_test_params(test_params, layer, test_name)
            if not test_params:
                continue

            # Check if we have data for that test
            if test_input not in filepaths:
                log.info(
                    bcolors.WARNING
                    + f"YARR data for {test_name} not found in {input_yarr} ({test_input}). TUNING will fail due to incomplete data."
                    + bcolors.ENDC
                )
                which_results = (
                    results_untuned if "UNTUNED" in test_name else results_tuned
                )
                names = (
                    [f"{test_name}_LOW", f"{test_name}_HIGH"]
                    if test_method == "percentile"
                    else [test_name]
                )
                for name in names:
                    which_results.update({"TUNING_" + name: -999.0})
                continue

            # Read input YARR scan
            if datadir != "":
                input_data_path = datadir + "/" + filepaths[test_input]
            else:
                input_data_path = filepaths[test_input]

            input_data = read_json(Path(input_data_path))

            if "TDAC" in test_name:
                check_input_yarr_data(input_data, input_data_path, config=True)
                pix_data = format_TDAC_input(input_data)
            else:
                if test_name == "COLUMN_DISABLED":
                    check_input_yarr_data(input_data, path=input_data_path, config=True)
                    input_data, numBadCoreCols = format_coreCol_input(
                        input_data, chiptype, test_params
                    )
                    log.debug(
                        f"There are {numBadCoreCols} disabled core columns in this chip config"
                    )
                else:
                    check_input_yarr_data(input_data, path=input_data_path)
                pix_data = format_pixel_input(input_data)

            # Calculate relevant quantities
            if test_method == "mean":
                if "TDAC" not in test_name and "TOT" not in test_name:
                    pix_data = pix_data[pix_data > 0]
                if "UNTUNED" in test_name:
                    results_untuned.update({"TUNING_" + test_name: np.mean(pix_data)})
                else:
                    results_tuned.update({"TUNING_" + test_name: np.mean(pix_data)})

            elif test_method == "rms":
                if "TDAC" not in test_name and "TOT" not in test_name:
                    pix_data = pix_data[pix_data > 0]
                if "UNTUNED" in test_name:
                    results_untuned.update({"TUNING_" + test_name: np.std(pix_data)})
                else:
                    results_tuned.update({"TUNING_" + test_name: np.std(pix_data)})

            elif test_method == "percentile":
                if "TDAC" not in test_name and "TOT" not in test_name:
                    pix_data = pix_data[pix_data > 0]
                bound = (100 - test_params[0]) / 2.0
                lower, upper = np.percentile(pix_data, [bound, 100 - bound])
                if "UNTUNED" in test_name:
                    results_untuned.update({"TUNING_" + test_name + "_LOW": lower})
                    results_untuned.update({"TUNING_" + test_name + "_HIGH": upper})
                else:
                    results_tuned.update({"TUNING_" + test_name + "_LOW": lower})
                    results_tuned.update({"TUNING_" + test_name + "_HIGH": upper})
            else:
                log.debug(f"Classifying pixels failing {test_name}")
                if test_name == "TUNED_THRESHOLD_FAILED_FITS":
                    pix_fail_tuned, record_fail_tuned = classify_pixels(
                        pix_data,
                        pix_fail_tuned,
                        record_fail_tuned,
                        "THRESHOLD_FAILED_FITS",
                        test_method,
                        test_params,
                    )
                    if np.isscalar(pix_fail_tuned):
                        continue
                elif test_name == "UNTUNED_THRESHOLD_FAILED_FITS":
                    pix_fail_untuned, record_fail_untuned = classify_pixels(
                        pix_data,
                        pix_fail_untuned,
                        record_fail_untuned,
                        "THRESHOLD_FAILED_FITS",
                        test_method,
                        test_params,
                    )
                    if np.isscalar(pix_fail_untuned):
                        continue
                else:
                    log.error("TUNING not equipped to test for {test_name}. Please fix")
                    raise RuntimeError()

            test_params_plot = test_params
            if test_params_plot == "null" and test_name in qc_config_untuned:
                lower_bound, upper_bound, precision = get_bounds_and_precision(
                    qc_config_untuned, test_name, get_layer(layer)
                )
                test_params_plot = [lower_bound, upper_bound, precision]
            elif test_params_plot == "null" and test_name in qc_config_tuned:
                lower_bound, upper_bound, precision = get_bounds_and_precision(
                    qc_config_tuned, test_name, get_layer(layer)
                )
                test_params_plot = [lower_bound, upper_bound, precision]

            try:
                if test_name in ["UNTUNED_THRESHOLD_MEAN", "TUNED_THRESHOLD_MEAN"]:
                    plot_1d_hist(
                        pix_data,
                        test_name,
                        test_method,
                        test_params_plot,
                        "Threshold (e)",
                        output_dir,
                        chipName,
                    )
                elif test_name in ["UNTUNED_NOISE_MEAN", "TUNED_NOISE_MEAN"]:
                    plot_1d_hist(
                        pix_data,
                        test_name,
                        test_method,
                        test_params_plot,
                        "Noise (e)",
                        output_dir,
                        chipName,
                    )
                elif test_name in ["UNTUNED_TDAC_MEAN", "TUNED_TDAC_MEAN"]:
                    plot_1d_hist(
                        pix_data,
                        test_name,
                        test_method,
                        test_params_plot,
                        "TDAC",
                        output_dir,
                        chipName,
                    )
                elif test_name == "TUNED_TOT_MEAN":
                    plot_1d_hist(
                        pix_data,
                        test_name,
                        test_method,
                        test_params_plot,
                        "TOT",
                        output_dir,
                        chipName,
                    )
            except Exception as e:
                log.warning(
                    bcolors.WARNING
                    + f"Problem plotting 1d histogram of {test_name} results: {e}"
                    + bcolors.ENDC
                )

        chiplog = logging.FileHandler(f"{output_dir}/{chipName}.log")
        log.addHandler(chiplog)
        failure_summary_tuned = count_pixels(
            pix_fail_tuned,
            record_fail_tuned,
            ["THRESHOLD_FAILED_FITS"],
            ignore_bad_corecol,
        )
        results_tuned.update(
            {
                "TUNING_TUNED_THRESHOLD_FAILED_FITS": failure_summary_tuned.get(
                    "THRESHOLD_FAILED_FITS"
                ).get("independent")
            }
        )
        # Plot electrical failures
        try:
            plot_2d_map(
                pix_fail_tuned,
                record_fail_tuned,
                "Tuned failures",
                output_dir,
                chipName,
            )
        except Exception as e:
            log.warning(
                bcolors.WARNING
                + f"Problem plotting 2d map of tuned-pixel failures: {e}"
                + bcolors.ENDC
            )

        failure_summary_untuned = count_pixels(
            pix_fail_untuned,
            record_fail_untuned,
            ["THRESHOLD_FAILED_FITS"],
            ignore_bad_corecol,
        )
        results_untuned.update(
            {
                "TUNING_UNTUNED_THRESHOLD_FAILED_FITS": failure_summary_untuned.get(
                    "THRESHOLD_FAILED_FITS"
                ).get("independent")
            }
        )
        # Plot electrical failures
        try:
            plot_2d_map(
                pix_fail_untuned,
                record_fail_untuned,
                "Untuned failures",
                output_dir,
                chipName,
            )
        except Exception as e:
            log.warning(
                bcolors.WARNING
                + f"Problem plotting 2d map of untuned-pixel failures: {e}"
                + bcolors.ENDC
            )

        (
            passes_qc_untuned,
            summary_untuned,
            rounded_results_untuned,
        ) = perform_qc_analysis(test_type, qc_config_untuned, layer, results_untuned)
        passes_qc_tuned, summary_tuned, rounded_results_tuned = perform_qc_analysis(
            test_type, qc_config_tuned, layer, results_tuned
        )
        print_result_summary(
            summary_untuned, test_type, output_dir, chipName, "untuned"
        )
        print_result_summary(summary_tuned, test_type, output_dir, chipName, "tuned")

        passes_qc = passes_qc_untuned and passes_qc_tuned

        if passes_qc == -1:
            log.error(
                bcolors.ERROR
                + f" QC analysis for {chipName} was NOT successful. Please fix and re-run. Continuing to next chip.."
                + bcolors.ENDC
            )
            continue
        log.info("")
        if passes_qc:
            log.info(
                f" Chip {chipName} passes QC? "
                + bcolors.OKGREEN
                + f"{passes_qc}"
                + bcolors.ENDC
            )
        else:
            log.info(
                f" Chip {chipName} passes QC? "
                + bcolors.BADRED
                + f"{passes_qc}"
                + bcolors.ENDC
            )
        log.info("")
        log.removeHandler(chiplog)
        chiplog.close()

        #  Output a json file
        outputDF = outputDataFrame()
        outputDF.set_test_type(test_type)
        outputDF.set_serial_num(chipSN)
        data = qcDataFrame()
        data.add_property("ANALYSIS_VERSION", __version__)
        data.add_property("YARR_VERSION", yarr_version)
        data.add_meta_data("QC_LAYER", layer)

        data.add_property(
            "MEASUREMENT_DATE",
            arrow.get(time_start).isoformat(timespec="milliseconds"),
        )
        data.add_property("MEASUREMENT_DURATION", int(time_duration))
        rounded_results_combined = rounded_results_untuned.copy()
        rounded_results_combined.update(rounded_results_tuned)
        # Add all parameters used in QC selection
        for key, value in rounded_results_combined.items():
            if key not in qc_config_tuned and key not in qc_config_untuned:
                data.add_parameter(key, value, 3)
            else:
                data.add_parameter(key, value)

        outputDF.set_results(data)
        outputDF.set_pass_flag(passes_qc)

        if permodule:
            alloutput += [outputDF.to_dict(True)]
        else:
            outfile = output_dir.joinpath(f"{chipName}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            save_dict_list(outfile, [outputDF.to_dict(True)])

    if permodule:
        outfile = output_dir.joinpath("module.json")
        log.info(f" Saving output of analysis to: {outfile}")
        save_dict_list(
            outfile,
            alloutput,
        )


if __name__ == "__main__":
    typer.run(main)
