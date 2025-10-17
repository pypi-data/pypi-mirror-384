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
    plot_1d_hist,
    plot_2d_map,
    print_pixel_classification,
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
    Performs the minimum health analysis of YARR Scans.

    It produces an output file with key parameters (number of dead/bad pixels, ...).  Note that the YARR scans to be used in the analysis should be identified with [`mqat analysis load-yarr-scans`](#mqat-config-load-yarr-scans).
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
    log.info(" \tPerforming minimum health test analysis")
    log.info(" ====================================================")
    log.info("")

    input_data = read_json(input_yarr)
    check_input_yarr_config(input_data, path=input_yarr)
    datadir = input_data["datadir"]
    yarr_version = input_data["YARR_VERSION"]
    module_sn = input_data["module"]["serialNumber"]
    chiptype = input_data["module"]["chipType"]

    qc_config = get_qc_config(qc_criteria_path, test_type, module_sn)

    # Don't allow ignoring bad core columns unless RD53B
    if chiptype != "RD53B":
        ignore_bad_corecol = False

    time_start = input_data["TimeStart"]
    time_duration = input_data.get("TimeDuration", -1)

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
        results = {}

        # Initialize array to track pixel failures
        pix_fail = np.zeros(153600, dtype=np.uint16)

        # Initialize int to track which classifications have been checked
        record_fail = 0

        log.debug(
            f"Performing minimum health test analysis on chip {c['serialNumber']}"
        )

        #  Prepare output json file
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

        # Loop through pixel failure tests from config file
        for test_name, params in pixel_classification.get(test_type).items():
            log.debug(f"Counting pixels that fail {test_name}")

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
                    + f"YARR data for {test_name} not found in {input_yarr} ({test_input}). MIN_HEALTH_TEST will fail due to incomplete data."
                    + bcolors.ENDC
                )
                results.update({f"MIN_HEALTH_{test_name}": -999.0})
                data.add_parameter(f"MIN_HEALTH_{test_name}", -999.0)
                continue

            # Read input YARR scan
            if datadir != "":
                input_data_path = datadir + "/" + filepaths[test_input]
            else:
                input_data_path = filepaths[test_input]
            input_data = read_json(Path(input_data_path))

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
                mean = np.mean(pix_data)
                results.update({"MIN_HEALTH_" + test_name: mean})
                data.add_parameter("MIN_HEALTH_" + test_name, mean, 2)
            elif test_method == "rms":
                if "TDAC" not in test_name and "TOT" not in test_name:
                    pix_data = pix_data[pix_data > 0]
                rms = np.std(pix_data)
                results.update({"MIN_HEALTH_" + test_name: rms})
                data.add_parameter("MIN_HEALTH_" + test_name, rms, 2)
            else:
                # Count passing pixels
                pix_fail, record_fail = classify_pixels(
                    pix_data, pix_fail, record_fail, test_name, test_method, test_params
                )
                if np.isscalar(pix_fail):
                    continue

            # Make diagnostic plots
            try:
                if test_name == "THRESHOLD_MEAN":
                    plot_1d_hist(
                        pix_data,
                        test_name,
                        test_method,
                        test_params,
                        "Threshold (e)",
                        output_dir,
                        chipName,
                    )
                elif test_name == "HIGH_ENC":
                    plot_1d_hist(
                        pix_data,
                        test_name,
                        test_method,
                        test_params,
                        "Noise (e)",
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
        test_names = pixel_classification.get(test_type).keys()
        failure_summary = count_pixels(
            pix_fail, record_fail, test_names, ignore_bad_corecol
        )
        for fname, nfail in failure_summary.items():
            data.add_parameter("MIN_HEALTH_" + fname, nfail.get("dependent"))

        print_pixel_classification(
            failure_summary, test_type, output_dir, chipName, ignore_bad_corecol
        )
        # Plot electrical failures
        try:
            plot_2d_map(
                pix_fail, record_fail, "MHT electrical failures", output_dir, chipName
            )
        except Exception as e:
            log.warning(
                bcolors.WARNING
                + f"Problem plotting 2d map of MHT electrical failures: {e}"
                + bcolors.ENDC
            )

        try:
            bad_analog_integrated = failure_summary.get("BAD_ANALOG").get("integrated")
            results.update({"MIN_HEALTH_BAD_ANALOG_INTEGRATED": bad_analog_integrated})
            data.add_parameter(
                "MIN_HEALTH_BAD_ANALOG_INTEGRATED", bad_analog_integrated
            )
        except Exception:
            log.warning(
                bcolors.WARNING
                + "Problem getting BAD_ANALOG results from failure summary"
                + bcolors.ENDC
            )

        try:
            threshold_failed_fits_independent = failure_summary.get(
                "THRESHOLD_FAILED_FITS"
            ).get("independent")
            results.update(
                {
                    "MIN_HEALTH_THRESHOLD_FAILED_FITS_INDEPENDENT": threshold_failed_fits_independent
                }
            )
            data.add_parameter(
                "MIN_HEALTH_THRESHOLD_FAILED_FITS_INDEPENDENT",
                threshold_failed_fits_independent,
            )
        except Exception:
            log.warning(
                bcolors.WARNING
                + "Problem getting THRESHOLD_FAILED_FITS results from failure summary"
                + bcolors.ENDC
            )

        try:
            high_enc_independent = failure_summary.get("HIGH_ENC").get("independent")
            results.update({"MIN_HEALTH_HIGH_ENC_INDEPENDENT": high_enc_independent})
            data.add_parameter("MIN_HEALTH_HIGH_ENC_INDEPENDENT", high_enc_independent)
        except Exception:
            log.warning(
                bcolors.WARNING
                + "Problem getting HIGH_ENC results from failure summary"
                + bcolors.ENDC
            )

        passes_qc, summary, _rounded_results = perform_qc_analysis(
            test_type, qc_config, layer, results
        )
        print_result_summary(summary, test_type, output_dir, chipName)
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
