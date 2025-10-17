from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import arrow
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
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    """
    Performs the Undershunt protection analysis.

    It produces an output file with the measured internal voltages and currents in when the undershunt protection mechanism is activated.
    """
    test_type = Path(__file__).stem

    allinputs = get_inputs(input_meas)

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
    log.info(" =======================================")
    log.info(" \tPerforming UNDERSHUNT PROTECTION analysis")
    log.info(" =======================================")
    log.info("")

    alloutput = []
    timestamps = []
    for filename in sorted(allinputs):
        log.info("")
        log.info(f" Loading {filename}")
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
                log.error(
                    bcolors.ERROR
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
            extractor = DataExtractor(inputDF, test_type)
            calculated_data = extractor.calculate()

            passes_qc = True

            # Load values to dictionary for QC analysis
            USP_VREFA_NOM = calculated_data["VrefA"]["Values"][0]
            USP_VREFD_NOM = calculated_data["VrefD"]["Values"][0]
            USP_VINA_NOM = calculated_data["VinA"]["Values"][0]
            USP_VIND_NOM = calculated_data["VinD"]["Values"][0]
            USP_VDDA_NOM = calculated_data["VDDA"]["Values"][0]
            USP_VDDD_NOM = calculated_data["VDDD"]["Values"][0]
            USP_IINA_NOM = calculated_data["IinA"]["Values"][0]
            USP_IIND_NOM = calculated_data["IinD"]["Values"][0]
            USP_ISHUNTA_NOM = calculated_data["IshuntA"]["Values"][0]
            USP_ISHUNTD_NOM = calculated_data["IshuntD"]["Values"][0]
            USP_VREFA_ANA = calculated_data["VrefA"]["Values"][1]
            USP_VREFD_ANA = calculated_data["VrefD"]["Values"][1]
            USP_VINA_ANA = calculated_data["VinA"]["Values"][1]
            USP_VIND_ANA = calculated_data["VinD"]["Values"][1]
            USP_VDDA_ANA = calculated_data["VDDA"]["Values"][1]
            USP_VDDD_ANA = calculated_data["VDDD"]["Values"][1]
            USP_IINA_ANA = calculated_data["IinA"]["Values"][1]
            USP_IIND_ANA = calculated_data["IinD"]["Values"][1]
            USP_ISHUNTA_ANA = calculated_data["IshuntA"]["Values"][1]
            USP_ISHUNTD_ANA = calculated_data["IshuntD"]["Values"][1]
            USP_VREFD_DIG = calculated_data["VrefD"]["Values"][2]
            USP_VREFA_DIG = calculated_data["VrefA"]["Values"][2]
            USP_VIND_DIG = calculated_data["VinD"]["Values"][2]
            USP_VINA_DIG = calculated_data["VinA"]["Values"][2]
            USP_VDDD_DIG = calculated_data["VDDD"]["Values"][2]
            USP_VDDA_DIG = calculated_data["VDDA"]["Values"][2]
            USP_IIND_DIG = calculated_data["IinD"]["Values"][2]
            USP_IINA_DIG = calculated_data["IinA"]["Values"][2]
            USP_ISHUNTD_DIG = calculated_data["IshuntD"]["Values"][2]
            USP_ISHUNTA_DIG = calculated_data["IshuntA"]["Values"][2]

            results = {}
            results.update({"USP_VREFA_NOM": USP_VREFA_NOM})
            results.update({"USP_VREFD_NOM": USP_VREFD_NOM})
            results.update({"USP_VINA_NOM": USP_VINA_NOM})
            results.update({"USP_VIND_NOM": USP_VIND_NOM})
            results.update({"USP_VDDA_NOM": USP_VDDA_NOM})
            results.update({"USP_VDDD_NOM": USP_VDDD_NOM})
            results.update({"USP_IINA_NOM": USP_IINA_NOM})
            results.update({"USP_IIND_NOM": USP_IIND_NOM})
            results.update({"USP_ISHUNTA_NOM": USP_ISHUNTA_NOM})
            results.update({"USP_ISHUNTD_NOM": USP_ISHUNTD_NOM})
            results.update({"USP_VREFA_DIG": USP_VREFA_DIG})
            results.update({"USP_VREFD_DIG": USP_VREFD_DIG})
            results.update({"USP_VINA_DIG": USP_VINA_DIG})
            results.update({"USP_VIND_DIG": USP_VIND_DIG})
            results.update({"USP_VDDA_DIG": USP_VDDA_DIG})
            results.update({"USP_VDDD_DIG": USP_VDDD_DIG})
            results.update({"USP_IINA_DIG": USP_IINA_DIG})
            results.update({"USP_IIND_DIG": USP_IIND_DIG})
            results.update({"USP_ISHUNTA_DIG": USP_ISHUNTA_DIG})
            results.update({"USP_ISHUNTD_DIG": USP_ISHUNTD_DIG})
            results.update({"USP_VREFA_ANA": USP_VREFA_ANA})
            results.update({"USP_VREFD_ANA": USP_VREFD_ANA})
            results.update({"USP_VINA_ANA": USP_VINA_ANA})
            results.update({"USP_VIND_ANA": USP_VIND_ANA})
            results.update({"USP_VDDA_ANA": USP_VDDA_ANA})
            results.update({"USP_VDDD_ANA": USP_VDDD_ANA})
            results.update({"USP_IINA_ANA": USP_IINA_ANA})
            results.update({"USP_IIND_ANA": USP_IIND_ANA})
            results.update({"USP_ISHUNTA_ANA": USP_ISHUNTA_ANA})
            results.update({"USP_ISHUNTD_ANA": USP_ISHUNTD_ANA})
            results.update({"USP_VREFA_DIFF": USP_VREFA_NOM - USP_VREFA_ANA})
            results.update({"USP_VREFD_DIFF": USP_VREFD_NOM - USP_VREFD_DIG})
            results.update({"USP_VINA_DIFF": USP_VINA_NOM - USP_VINA_ANA})
            results.update({"USP_VIND_DIFF": USP_VIND_NOM - USP_VIND_DIG})
            results.update({"USP_VDDA_DIFF": USP_VDDA_NOM - USP_VDDA_ANA})
            results.update({"USP_VDDD_DIFF": USP_VDDD_NOM - USP_VDDD_DIG})
            results.update({"USP_IINA_DIFF": USP_IINA_NOM - USP_IINA_ANA})
            results.update({"USP_IIND_DIFF": USP_IIND_NOM - USP_IIND_DIG})
            results.update({"USP_ISHUNTA_DIFF": USP_ISHUNTA_NOM - USP_ISHUNTA_ANA})
            results.update({"USP_ISHUNTD_DIFF": USP_ISHUNTD_NOM - USP_ISHUNTD_DIG})

            # Perform QC analysis
            chiplog = logging.FileHandler(f"{output_dir}/{chipname}.log")
            log.addHandler(chiplog)
            passes_qc, summary, rounded_results = perform_qc_analysis(
                test_type, qc_config, layer, results
            )
            print_result_summary(summary, test_type, output_dir, chipname)
            if passes_qc == -1:
                log.error(
                    bcolors.ERROR
                    + f" QC analysis for {chipname} was NOT successful. Please fix and re-run. Continuing to next chip.."
                    + bcolors.ENDC
                )
                continue
            log.info("")
            if passes_qc:
                log.info(
                    f" Chip {chipname} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Chip {chipname} passes QC? "
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
                qcframe.get_properties().get(test_type + "_MEASUREMENT_VERSION"),
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
            # Load values to store in output file
            for key, value in rounded_results.items():
                if "ANA" in key or "DIG" in key:
                    continue
                if key not in qc_config:
                    data.add_parameter(key, value, 4)
                else:
                    data.add_parameter(key, value)

            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)
            if permodule:
                alloutput += [outputDF.to_dict(True)]
                timestamps += [meas_timestamp]
            else:
                outfile = output_dir.joinpath(f"{chipname}.json")
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
