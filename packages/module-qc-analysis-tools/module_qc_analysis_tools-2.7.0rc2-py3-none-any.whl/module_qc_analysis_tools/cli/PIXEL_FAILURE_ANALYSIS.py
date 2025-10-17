from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path

import arrow
import numpy as np
import typer
from module_qc_data_tools import (
    convert_serial_to_name,
    get_layer_from_sn,
    get_type_from_sn,
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
    format_enable_input,
    format_pixel_input,
    get_fail_bit,
    get_result_arrays,
    identify_disc_pixels,
    identify_merged_pixels,
    identify_nosource_pixels,
    identify_noxtalk_pixels,
    identify_zerobias_pixels,
    plot_1d_discbumps,
    plot_1d_hist,
    plot_2d_discbumps,
    plot_2d_map,
    print_pixel_classification,
    read_json,
    split_pixels,
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
    Classifies pixel failures and performs the pixel failure analysis.

    It produces an output file with several key parameters (number of pixels failing each category, total failing pixels, ...). Note that the YARR scans to be used in the analysis should be identified with [`mqat analysis load-yarr-scans`](#mqat-config-load-yarr-scans).

    ---

    General idea of how this analysis works:

    - Pixels are flagged as either passing or failing a range of selections.
    - This information is stored in a flat numpy array of 153600 16-bit integers, called 'pix_fail'
    - Each bit corresponds to a single pixel failure category (i.e. DIGITAL_DEAD)
    - A separate 16-bit integer, called 'record_fail' keeps track of which pixel failure categories\
      were checked (so we can distinguish cases where all pixels pass a category, or if that selection\
      wasn't applied.
    - At the end of the analysis, a function is called ('count_pixels') which summarizes the number of pixels\
      failing each category.
    - All of the pixel failure categories are treated the same, except for: DISCONNECTED_BUMPS_ZERO_BIAS_SCAN, \
      DISCONNECTED_BUMPS_XTALK_SCAN, and DISCONNECTED_BUMPS_SOURCE_SCAN. These categories are simply used for \
      diagnostic purposes, but pixels failing them do not count towards the total number of failed pixels. \
      Instead, a combined algorithm (DISCONNECTED_PIXELS) is used instead.
    - Electrical pixel failures and disconnected failures are treated somewhat separately until the end of \
      the analysis, where they are combined into a single 'FAILING_PIXELS' category

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
    log.info(" \tPerforming pixel failure analysis")
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
    module_type = get_type_from_sn(module_sn)
    chip_id = 0
    layer = get_layer_from_sn(module_sn)

    # Find module layer
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

    # Find json file with pixel classification selection
    pixel_classification = read_json(pixel_classification_path)
    if not pixel_classification.get(
        test_type + "_ELECTRICAL"
    ) or not pixel_classification.get(test_type + "_DISCONNECTED"):
        log.error(
            bcolors.BADRED
            + f"Pixel failure selection for {test_type}_ELECTRICAL or {test_type}_DISCONNECTED not found in {pixel_classification_path}! Please check. "
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

        chiplog = logging.FileHandler(f"{output_dir}/{chipName}.log")
        log.addHandler(chiplog)

        log.debug(f"Performing pixel failure analysis on chip {c['serialNumber']}")

        # Prepare output json file
        outputDF = outputDataFrame()
        outputDF.set_test_type(test_type)
        outputDF.set_serial_num(chipSN)
        data = qcDataFrame()
        data.add_property("ANALYSIS_VERSION", __version__)
        data.add_property("YARR_VERSION", yarr_version)
        data.add_meta_data("QC_LAYER", layer)
        data.add_property(
            "MEASUREMENT_DATE", arrow.get(time_start).isoformat(timespec="milliseconds")
        )

        data.add_property("MEASUREMENT_DURATION", int(time_duration))

        test_names_elec = pixel_classification.get(test_type + "_ELECTRICAL").keys()
        test_names_disc = pixel_classification.get(test_type + "_DISCONNECTED").keys()
        test_names_all = list(test_names_elec) + list(test_names_disc)

        ##############################################################
        # Loop through electrical pixel failure tests from config file
        ##############################################################

        for test_name, params in pixel_classification.get(
            test_type + "_ELECTRICAL"
        ).items():
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
                    + f"YARR data for {test_name} not found in {input_yarr} ({test_input}). PIXEL_FAILURE_ANALYSIS will fail due to incomplete data."
                    + bcolors.ENDC
                )
                results.update({f"PIXEL_FAILURE_{test_name}": -999.0})
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
                results.update({"PIXEL_FAILURE_" + test_name: np.mean(pix_data)})
            elif test_method == "rms":
                if "TDAC" not in test_name and "TOT" not in test_name:
                    pix_data = pix_data[pix_data > 0]
                results.update({"PIXEL_FAILURE_" + test_name: np.std(pix_data)})
            elif test_method == "custom":
                pass
            else:
                log.debug(f"Classifying pixels failing {test_name}")
                pix_fail, record_fail = classify_pixels(
                    pix_data, pix_fail, record_fail, test_name, test_method, test_params
                )
                if np.isscalar(pix_fail):
                    continue

            # Make diagnostic plots
            try:
                if test_name == "TUNING_BAD":
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
                    + f"Problem plotting 1d {test_name} histograms: {e}"
                    + bcolors.ENDC
                )

        # Count pixels failing each category
        failure_summary_elec = count_pixels(
            pix_fail, record_fail, test_names_elec, ignore_bad_corecol
        )

        # Plot electrical failures
        try:
            plot_2d_map(
                pix_fail, record_fail, "PFA electrical failures", output_dir, chipName
            )
        except Exception as e:
            log.warning(
                bcolors.WARNING
                + f"Problem plotting 2d map of electrical failures: {e}"
                + bcolors.ENDC
            )

        # Prepare data for combined analysis
        occ_sourcescan = np.empty(0)
        en_sourcescan = np.empty(0)
        occ_xtalk = np.empty(0)
        noise_nohv = np.empty(0)
        noise_hv = np.empty(0)

        ###########################
        # Merged bump analysis
        ###########################

        params_merged = pixel_classification.get(test_type + "_DISCONNECTED").get(
            "MERGED_BUMPS"
        )
        if params_merged.get("input") in filepaths:
            if datadir != "":
                input_data_path = datadir + "/" + filepaths[params_merged.get("input")]
            else:
                input_data_path = filepaths[params_merged.get("input")]
            input_data = read_json(Path(input_data_path))
            check_input_yarr_data(input_data, path=input_data_path)
            occ_merged = format_pixel_input(input_data)

            test_params = params_merged.get("params")
            if len(test_params) != 1:
                log.error(
                    bcolors.BADRED
                    + f"There should be 1 param provided for MERGED_BUMPS analysis, but {len(test_params)} were provided. Please fix."
                    + bcolors.ENDC
                )
                raise RuntimeError()

            pix_fail, record_fail = identify_merged_pixels(
                occ_merged,
                pix_fail,
                record_fail,
                "MERGED_BUMPS",
                test_params,
                output_dir,
                chipName,
            )

        else:
            log.warning(
                bcolors.WARNING
                + "Data is not present to perform merged bump analysis"
                + bcolors.ENDC
            )

        ###############################################
        # Disconnected bump analysis: zero-bias scan
        ###############################################

        params_0bias = pixel_classification.get(test_type + "_DISCONNECTED").get(
            "DISCONNECTED_BUMPS_ZERO_BIAS_SCAN"
        )
        if (
            params_0bias.get("input")[0] in filepaths
            and params_0bias.get("input")[1] in filepaths
        ):
            log.debug("Performing DISCONNECTED_BUMPS_ZERO_BIAS_SCAN")

            if datadir != "":
                input_data_path = (
                    datadir + "/" + filepaths[params_0bias.get("input")[0]]
                )
            else:
                input_data_path = filepaths[params_0bias.get("input")[0]]
            input_data = read_json(Path(input_data_path))
            check_input_yarr_data(input_data, path=input_data_path)
            noise_hv = format_pixel_input(input_data)

            if datadir != "":
                input_data_path = (
                    datadir + "/" + filepaths[params_0bias.get("input")[1]]
                )
            else:
                input_data_path = filepaths[params_0bias.get("input")[1]]
            input_data = read_json(Path(input_data_path))
            check_input_yarr_data(input_data, path=input_data_path)
            noise_nohv = format_pixel_input(input_data)

            test_params = params_0bias.get("params")
            if len(test_params) != 1:
                log.error(
                    bcolors.BADRED
                    + f"There should be 1 param provided for DISCONNECTED_BUMPS_ZERO_BIAS_SCAN analysis, but {len(test_params)} were provided. Please fix."
                    + bcolors.ENDC
                )
                raise RuntimeError()

            pix_fail, record_fail = identify_zerobias_pixels(
                noise_hv,
                noise_nohv,
                pix_fail,
                record_fail,
                "DISCONNECTED_BUMPS_ZERO_BIAS_SCAN",
                test_params,
            )

        else:
            log.warning(
                bcolors.WARNING
                + "Data is not present to perform zero-bias disconnected bump scan analysis"
                + bcolors.ENDC
            )

        ###############################################
        # Disconnected bump analysis: cross-talk scan
        ###############################################

        params_xtalk = pixel_classification.get(test_type + "_DISCONNECTED").get(
            "DISCONNECTED_BUMPS_XTALK_SCAN"
        )
        if params_xtalk.get("input")[0] in filepaths:
            if datadir != "":
                input_data_path = (
                    datadir + "/" + filepaths[params_xtalk.get("input")[0]]
                )
            else:
                input_data_path = filepaths[params_xtalk.get("input")[0]]
            input_data = read_json(Path(input_data_path))
            check_input_yarr_data(input_data, path=input_data_path)
            occ_xtalk = format_pixel_input(input_data)

            chip_id = 0
            try:
                if datadir != "":
                    input_data_path = (
                        datadir + "/" + filepaths[params_xtalk.get("config")[0]]
                    )
                else:
                    input_data_path = filepaths[params_xtalk.get("config")[0]]
                input_data = read_json(Path(input_data_path))
                check_input_yarr_data(input_data, path=input_data_path, config=True)
                chipname_str = next(iter(input_data))
                chip_id = input_data.get(chipname_str).get("Parameter").get("ChipId")
                if "QUAD" in module_type and chip_id not in [12, 13, 14, 15]:
                    log.warning(
                        bcolors.WARNING
                        + "Module was identified as quad but ChipId ({chip_id}) not recognized. Should be 12-15. Will not identify inner/outer edge pixels correctly."
                        + bcolors.ENDC
                    )
                    module_type = "unknown"
            except Exception:
                log.warning(
                    bcolors.BADRED
                    + "No ChipId found in config. This is needed to analyze disconnected bump data. Please fix."
                    + bcolors.ENDC
                )

            test_params = params_xtalk.get("params")
            if len(test_params) != 1:
                log.error(
                    bcolors.BADRED
                    + f"There should be 1 param provided for DISCONNECTED_BUMPS_XTALK_SCAN analysis, but {len(test_params)} were provided. Please fix."
                    + bcolors.ENDC
                )
                raise RuntimeError()

            pix_fail, record_fail = identify_noxtalk_pixels(
                occ_xtalk,
                pix_fail,
                record_fail,
                "DISCONNECTED_BUMPS_XTALK_SCAN",
                test_params,
            )

        else:
            log.warning(
                bcolors.WARNING
                + "Data is not present to perform cross-talk disconnected bump scan analysis"
                + bcolors.ENDC
            )

        ###############################################
        # Disconnected bump analysis: source scan
        ###############################################

        params_source = pixel_classification.get(test_type + "_DISCONNECTED").get(
            "DISCONNECTED_BUMPS_SOURCE_SCAN"
        )
        if (
            params_source.get("input")[0] in filepaths
            and params_source.get("config")[0] in filepaths
        ):
            data.add_parameter("PIXEL_FAILURE_SOURCE_SCAN_DONE", True)

            if datadir != "":
                input_data_path = (
                    datadir + "/" + filepaths[params_source.get("input")[0]]
                )
            else:
                input_data_path = filepaths[params_source.get("input")[0]]
            input_data = read_json(Path(input_data_path))
            check_input_yarr_data(input_data, path=input_data_path)
            occ_sourcescan = format_pixel_input(input_data)

            if datadir != "":
                input_data_path = (
                    datadir + "/" + filepaths[params_source.get("config")[0]]
                )
            else:
                input_data_path = filepaths[params_source.get("config")[0]]
            input_data = read_json(Path(input_data_path))
            check_input_yarr_data(input_data, path=input_data_path, config=True)
            en_sourcescan = format_enable_input(input_data)

            # Check that mask applied during source scan corresponds to pixels that fail electrically
            result_array_indep, result_array_dep = get_result_arrays(
                pix_fail, record_fail
            )
            try:
                test = result_array_dep[get_fail_bit("HIGH_NOISE")]
                enabled = en_sourcescan == 1
                passelec = test == 0
                if len(en_sourcescan[~enabled & passelec]) > 0:
                    log.warning(
                        bcolors.WARNING
                        + f"There are {len(en_sourcescan[~enabled & passelec])} pixels that were disabled during source scan but pass electrically. Please check."
                        + bcolors.ENDC
                    )
            except Exception:
                log.warning(
                    bcolors.WARNING
                    + "Unable to check if mask during noise scan corresponds to electrically failing pixels. Please contact developer."
                    + bcolors.ENDC
                )

            test_params = params_source.get("params")
            if len(test_params) != 1:
                log.error(
                    bcolors.BADRED
                    + f"There should be 1 param provided for DISCONNECTED_BUMPS_SOURCE_SCAN analysis, but {len(test_params)} were provided. Please fix."
                    + bcolors.ENDC
                )
                raise RuntimeError()

            pix_fail, record_fail = identify_nosource_pixels(
                occ_sourcescan,
                en_sourcescan,
                pix_fail,
                record_fail,
                "DISCONNECTED_BUMPS_SOURCE_SCAN",
                test_params,
                output_dir,
                chipName,
            )

        else:
            log.warning(
                bcolors.WARNING
                + "Data is not present to perform source-scan disconnected bump scan analysis"
                + bcolors.ENDC
            )
            data.add_parameter("PIXEL_FAILURE_SOURCE_SCAN_DONE", False)

        ###############################################
        # Disconnected bump analysis: combined results
        ###############################################

        # If disconnected bump scan is present, make diagnostic plots
        if np.any(occ_xtalk):
            # Split pixels into inner edge / outer edge / matrix pixels
            occ_sourcescan_loc = split_pixels(occ_sourcescan, module_type, chip_id)
            en_sourcescan_loc = split_pixels(en_sourcescan, module_type, chip_id)
            occ_xtalk_loc = split_pixels(occ_xtalk, module_type, chip_id)
            noise_nohv_loc = split_pixels(noise_nohv, module_type, chip_id)
            noise_hv_loc = split_pixels(noise_hv, module_type, chip_id)
            loc_labels = ["matrix", "inneredge", "outeredge"]

            for (
                tmpocc_sourcescan,
                tmpen_sourcescan,
                tmpocc_xtalk,
                tmpnoise_hv,
                tmpnoise_nohv,
                label,
            ) in zip(
                occ_sourcescan_loc,
                en_sourcescan_loc,
                occ_xtalk_loc,
                noise_hv_loc,
                noise_nohv_loc,
                loc_labels,
            ):
                if "QUAD" not in module_type and label == "inneredge":
                    continue

                try:
                    plot_1d_discbumps(
                        tmpocc_sourcescan,
                        tmpen_sourcescan,
                        tmpocc_xtalk,
                        tmpnoise_nohv,
                        tmpnoise_hv,
                        params_xtalk.get("params"),
                        output_dir,
                        chipName,
                        label + "_pixels",
                    )
                except Exception as e:
                    log.warning(
                        bcolors.WARNING
                        + f"Problem plotting 1d disconnected bump histograms: {e}"
                        + bcolors.ENDC
                    )

            try:
                plot_1d_discbumps(
                    occ_sourcescan,
                    en_sourcescan,
                    occ_xtalk,
                    noise_nohv,
                    noise_hv,
                    params_xtalk.get("params"),
                    output_dir,
                    chipName,
                    "all_pixels",
                )
            except Exception as e:
                log.warning(
                    bcolors.WARNING
                    + f"Problem plotting 1d disconnected bump histograms: {e}"
                    + bcolors.ENDC
                )

            # Identify disconnected bumps using combination of results
            pix_fail, record_fail = identify_disc_pixels(
                occ_sourcescan,
                en_sourcescan,
                occ_xtalk,
                pix_fail,
                record_fail,
                "DISCONNECTED_PIXELS",
                params_source.get("params"),
                params_xtalk.get("params"),
            )
        else:
            log.warning(
                bcolors.WARNING
                + "No disconnected bump scan available; unable to perform combined disconnected bump analysis"
                + bcolors.ENDC
            )

        # If disconnected bump scan and source scan are present, make 2D plot comparing results of each pixel
        try:
            if np.any(occ_xtalk) and np.any(occ_sourcescan) and np.any(en_sourcescan):
                plot_2d_discbumps(
                    occ_sourcescan,
                    en_sourcescan,
                    occ_xtalk,
                    params_source.get("params"),
                    params_xtalk.get("params"),
                    output_dir,
                    chipName,
                )
        except Exception as e:
            log.warning(
                bcolors.WARNING
                + f"Problem plotting 2d map of disconnected bumps: {e}"
                + bcolors.ENDC
            )

        # Count pixels failing individiaul tests
        failure_summary_disc = count_pixels(
            pix_fail, record_fail, test_names_disc, ignore_bad_corecol
        )

        ###############################################
        # Perform QC selection and save output
        ###############################################

        # Dump pickle file with the full pixel map for each pixel failure
        result_array_indep, result_array_dep = get_result_arrays(pix_fail, record_fail)
        if len(test_names_all) > len(result_array_indep):
            log.error(
                bcolors.BADRED
                + f"Length of output arrays {len(result_array_indep)} does not include results from all tests ({len(test_names_all)}) - please fix!"
                + bcolors.ENDC
            )
            raise RuntimeError()
        with output_dir.joinpath(f"{chipName}_results_all.pickle").open(
            "wb"
        ) as outpickle:
            outputArrays = {}
            for test in test_names_all:
                try:
                    outputArrays.update(
                        {
                            test + "_indep": result_array_indep[get_fail_bit(test)]
                            .reshape((384, 400))
                            .transpose()
                        }
                    )
                    outputArrays.update(
                        {
                            test + "_dep": result_array_indep[get_fail_bit(test)]
                            .reshape((384, 400))
                            .transpose()
                        }
                    )
                except Exception:
                    log.error(
                        bcolors.BADRED
                        + "Unable to dump results to pickle file. Please contact developer"
                        + bcolors.ENDC
                    )
            pickle.dump(outputArrays, outpickle)

        # Count pixels in each failing category
        failure_summary_all = count_pixels(
            pix_fail, record_fail, test_names_all, ignore_bad_corecol
        )

        for fname, nfail in failure_summary_all.items():
            if fname == "DISCONNECTED_PIXELS":
                # Will fill this later, see below
                continue
            data.add_parameter("PIXEL_FAILURE_" + fname, nfail.get("dependent"))

        # Get total electrical and disconnected failures, separately.

        total_elec_failing = list(failure_summary_elec.values())[-1].get("integrated")
        # Search for any incomplete results
        for eresult in list(failure_summary_elec.values()):
            if eresult.get("dependent") == -1:
                total_elec_failing = -1
        results.update({"PIXEL_FAILURE_ELECTRICALLY_FAILED": total_elec_failing})
        data.add_parameter("PIXEL_FAILURE_ELECTRICALLY_FAILED", total_elec_failing)

        # Count number of pixels classified as disconnected and electrically passing (for QC selection)
        # AND count number of pixels classified as disconnected, regardless of electrical results
        total_disc_failing = list(failure_summary_disc.values())[-1].get("integrated")
        # Search for any incomplete results, ignoring source scan and zero-bias scan, which are not required
        for etest, eresult in list(failure_summary_disc.items()):
            if (
                eresult.get("dependent") == -1
                and "SOURCE" not in etest
                and "ZERO_BIAS" not in etest
            ):
                total_disc_failing = -1
        total_disc_failing_elec_pass = (
            failure_summary_all.get("DISCONNECTED_PIXELS").get("dependent")
            if list(failure_summary_elec.values())[-1].get("dependent") != -1
            else -1
        )
        results.update(
            {"PIXEL_FAILURE_DISCONNECTED_PIXELS": total_disc_failing_elec_pass}
        )
        data.add_parameter(
            "PIXEL_FAILURE_DISCONNECTED_PIXELS", total_disc_failing_elec_pass
        )
        data.add_parameter("PIXEL_FAILURE_DISC_PIXEL_ALL_ELEC", total_disc_failing)

        total_failing = list(failure_summary_all.values())[-1].get("integrated")
        # Search for any incomplete results, ignoring source scan and zero-bias scan, which are not required
        for etest, eresult in list(failure_summary_all.items()):
            if (
                eresult.get("dependent") == -1
                and "SOURCE" not in etest
                and "ZERO_BIAS" not in etest
            ):
                total_failing = -1
        results.update({"PIXEL_FAILURE_FAILING_PIXELS": total_failing})
        data.add_parameter("PIXEL_FAILURE_FAILING_PIXELS", total_failing)

        # Print summary of analysis
        print_pixel_classification(
            failure_summary_all, test_type, output_dir, chipName, ignore_bad_corecol
        )

        # Perform chip-level QC analysis
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
