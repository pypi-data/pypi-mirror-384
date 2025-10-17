from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import arrow
import matplotlib.pyplot as plt
import numpy as np
import typer
from module_qc_data_tools import (
    get_layer_from_sn,
    load_json,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    FitMethod,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    perform_qc_analysis,
    print_result_summary,
)
from module_qc_analysis_tools.utils.misc import (
    DataExtractor,
    JsonChecker,
    bcolors,
    get_inputs,
    get_qc_config,
    get_time_stamp,
    linear_fit,
    linear_fit_np,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    qc_criteria_path: Path = OPTIONS["qc_criteria"],
    input_layer: str = OPTIONS["layer"],
    permodule: bool = OPTIONS["permodule"],
    site: str = OPTIONS["site"],
    fit_method: FitMethod = OPTIONS["fit_method"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    """
    Performs the VCal calibration.

    It produces several diagnostic plots and an output file with the VCal calibration slope and offset.
    """
    test_type = Path(__file__).stem

    time_start = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    log = logging.getLogger("analysis")
    log.setLevel(verbosity.value)
    log.addHandler(logging.FileHandler(f"{output_dir}/output.log"))

    # Turn off matplotlib DEBUG messages
    plt.set_loglevel(level="warning")
    # Turn off pytest DEBUG messages
    pil_logger = logging.getLogger("PIL")
    pil_logger.setLevel(logging.INFO)

    log.info("")
    log.info(" ==========================================")
    log.info(" \tPerforming VCAL calibration analysis")
    log.info(" ==========================================")
    log.info("")

    allinputs = get_inputs(input_meas)

    alloutput = []
    timestamps = []
    for filename in allinputs:
        log.info("")
        log.info(f" Loading {filename}")
        output = {}
        results = {}
        meas_timestamp = get_time_stamp(filename)
        inputDFs = load_json(filename)

        log.debug(
            f" There are results from {len(inputDFs)} chip(s) stored in this file"
        )
        for inputDF in inputDFs:
            # Check file integrity
            checker = JsonChecker(inputDF, test_type)

            try:
                checker.check()
            except BaseException as exc:
                log.exception(exc)
                log.warning(
                    bcolors.WARNING
                    + " JsonChecker check not passed, skipping this input."
                    + bcolors.ENDC
                )
                continue
            else:
                log.debug(" JsonChecker check passed!")

            #   Get info
            qcframe = inputDF.get_results()
            metadata = qcframe.get_meta_data()

            qc_config = get_qc_config(
                qc_criteria_path, test_type, metadata.get("ModuleSN")
            )

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

            #  Determine test type
            try:
                testname = inputDF._subtestType
                testprefix = testname.split("_")[0] + "_" + testname.split("_")[1]
                testsuffix = testname.split(testprefix)[1]
            except Exception:
                log.error(
                    bcolors.ERROR
                    + f" {filename}.json does not have subtestType, which is needed for VCAL_CALIBRATION analysis, skipping!"
                    + bcolors.ENDC
                )
                continue

            try:
                chipname = metadata.get("Name")
                log.debug(f" Found chip name = {chipname} from chip config")
            except Exception:
                log.warning(
                    bcolors.WARNING
                    + "Chip name not found in input from {filename}, skipping."
                    + bcolors.ENDC
                )
                continue

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
                return

            #   Calculate quanties
            # Vmux conversion is embedded.
            extractor = DataExtractor(inputDF, test_type)
            calculated_data = extractor.calculate()

            #         Plotting
            # task specific - for Vcal Calibration x and y needs to be determined for plotting.
            x_key = None
            for key, value in calculated_data.items():
                if value["X"] is True:
                    x_key = key

            x = calculated_data.pop(x_key)

            y_values = ["VcalHi", "VcalMed"]
            for key in y_values:
                value = calculated_data.get(key)
                if not value:
                    # Note: This prevents from entering loop more than once
                    continue
                if fit_method.value == "root":
                    p1, p0, linearity = linear_fit(x["Values"], value["Values"])
                elif fit_method.value == "numpy":
                    p1, p0, linearity = linear_fit_np(x["Values"], value["Values"])
                else:
                    msg = f"Fit method {fit_method.value} unknown"
                    raise ValueError(msg)
                # Convert from V to mV
                p1mv = p1 * 1000
                p0mv = p0 * 1000
                linearity = linearity * 1000.0

                _fig, ax1 = plt.subplots()
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
                ax1.set_ylabel(f"{key}[{value['Unit']}]")
                ax1.set_title(chipname)
                ax1.legend()
                outfile = output_dir.joinpath(f"{chipname}_{testname}.png")
                log.info(f" Saving {outfile}")
                plt.savefig(outfile)
                plt.close()

            # Load values to dictionary for QC analysis (later)
            tmpresults = {}
            tmpresults.update({f"{testprefix}_SLOPE{testsuffix}": p1mv})
            tmpresults.update({f"{testprefix}_OFFSET{testsuffix}": p0mv})
            tmpresults.update({f"{testprefix}_LINEARITY{testsuffix}": linearity})

            #  Information for output json file
            tmpoutput = {}

            tmpoutput[f"{testprefix}_SLOPE{testsuffix}"] = p1mv
            tmpoutput[f"{testprefix}_OFFSET{testsuffix}"] = p0mv
            tmpoutput[f"{testprefix}_LINEARITY{testsuffix}"] = linearity
            tmpoutput["Metadata"] = metadata
            tmpoutput["MEASUREMENT_VERSION"] = qcframe.get_properties().get(
                test_type + "_MEASUREMENT_VERSION"
            )
            if output.get(chipname):
                output[chipname].update(tmpoutput)
                results[chipname].update(tmpresults)
            else:
                output[chipname] = tmpoutput
                results[chipname] = tmpresults

        # Perform QC analysis and make one output file per chip
        for key, chip in output.items():
            for subtest in ["HIGH", "MED"]:
                if results.get(key).get(
                    f"VCAL_{subtest}_SLOPE_SMALL_RANGE"
                ) and results.get(key).get(f"VCAL_{subtest}_SLOPE"):
                    results.get(key).update(
                        {
                            f"VCAL_{subtest}_SLOPE_SMALL_RANGE_RATIO": results.get(
                                key
                            ).get(f"VCAL_{subtest}_SLOPE_SMALL_RANGE")
                            / results.get(key).get(f"VCAL_{subtest}_SLOPE")
                        }
                    )
                    results.get(key).pop(f"VCAL_{subtest}_SLOPE_SMALL_RANGE")

                elif results.get(key).get(
                    f"VCAL_{subtest}_SLOPE_SMALL_RANGE"
                ) and not results.get(key).get(f"VCAL_{subtest}_SLOPE"):
                    log.warning(
                        bcolors.WARNING
                        + f" Results from VCAL_{subtest}_SLOPE test not found. Unable to perform QC analysis on VCAL_{subtest}_SLOPE_SMALL_RANGE"
                        + bcolors.ENDC
                    )
                    results.get(key).pop(f"VCAL_{subtest}_SLOPE_SMALL_RANGE")

                results.get(key).pop(f"VCAL_{subtest}_OFFSET_SMALL_RANGE", "")

            chiplog = logging.FileHandler(f"{output_dir}/{key}.log")
            log.addHandler(chiplog)
            passes_qc, summary, rounded_results = perform_qc_analysis(
                test_type,
                qc_config,
                layer,
                results.get(key),
            )
            print_result_summary(summary, test_type, output_dir, key)
            if passes_qc == -1:
                log.error(
                    bcolors.ERROR
                    + f" QC analysis for {key} was NOT successful. Please fix and re-run. Continuing to next chip.."
                    + bcolors.ENDC
                )
                continue
            log.info("")
            if passes_qc:
                log.info(
                    f" Chip {key} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Chip {key} passes QC? "
                    + bcolors.BADRED
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            log.info("")
            log.removeHandler(chiplog)
            chiplog.close()

            outputDF = outputDataFrame()
            test_type = Path(__file__).stem
            outputDF.set_test_type(test_type)
            data = qcDataFrame()
            data.add_property(
                "ANALYSIS_VERSION",
                __version__,
            )
            try:
                data.add_property(
                    "YARR_VERSION",
                    chip.get("YARR_VERSION"),
                )
                chip.pop("YARR_VERSION")
            except Exception as e:
                log.warning(f"Unable to find YARR version! Require YARR >= v1.5.2. {e}")
                data.add_property("YARR_VERSION", "")
            data.add_meta_data("MEASUREMENT_VERSION", chip["MEASUREMENT_VERSION"])
            time_start = qcframe.get_meta_data()["TimeStart"]
            time_end = qcframe.get_meta_data()["TimeEnd"]
            duration = arrow.get(time_end) - arrow.get(time_start)

            data.add_property(
                "MEASUREMENT_DATE",
                arrow.get(time_start).isoformat(timespec="milliseconds"),
            )
            data.add_property("MEASUREMENT_DURATION", int(duration.total_seconds()))
            chip.pop("MEASUREMENT_VERSION")
            data.add_meta_data("QC_LAYER", layer)
            data.add_meta_data("INSTITUTION", institution)
            data._meta_data.update(chip["Metadata"])
            chip.pop("Metadata")
            chip.update(rounded_results)  # Update with rounded results
            for param in chip:
                if param not in qc_config:
                    data.add_parameter(
                        param, chip[param], 2
                    )  # round values not used in QC
                else:
                    data.add_parameter(param, chip[param])
            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)
            if permodule:
                alloutput += [outputDF.to_dict(True)]
                timestamps += [meas_timestamp]
            else:
                outfile = output_dir.joinpath(f"{key}.json")
                log.info(f" Saving output of analysis to: {outfile}")
                save_dict_list(outfile, [outputDF.to_dict(True)])
    if permodule:
        # Only store results from same timestamp into same file
        dfs = np.array(alloutput)
        tss = np.array(timestamps)
        for x in np.unique(tss):
            outfile = output_dir.joinpath("module.json")
            log.info(f" Saving output of analysis to: {outfile}")
            save_dict_list(
                outfile,
                dfs[tss == x].tolist(),
            )


if __name__ == "__main__":
    typer.run(main)
