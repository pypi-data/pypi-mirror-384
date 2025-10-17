from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import arrow
import typer
from module_qc_data_tools import (
    get_layer_from_sn,
    load_json,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools import data as data_path
from module_qc_analysis_tools.analysis.wirebond_pull_test import process_pull_data
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import perform_qc_analysis
from module_qc_analysis_tools.utils.misc import (
    bcolors,
    get_inputs,
    get_qc_config,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    # qc_criteria_path: Path = OPTIONS["qc_criteria"],
    # layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    """
    Classifies pulls and performs the pulltest statistics.

    It produces an output file with several key parameters (pull strength min, % of wires with lift-off associated with pull strength < 7g...).

    ---

    General idea of how this analysis works:

    - For each pull, define location 'à priori', then extract 'break mode' and 'pull strength'
    - If an error occurred during the pulltest session, 'break mode' is used to show this error. Only, wires without errors are used to compute 'mean' pull strength (Option1 according to https://indico.cern.ch/event/1529894/contributions/6440914/attachments/3037883/5365239/ATLAS-ITk_MQAT_Pulltest_Analysis_MR277_JGIRAUD_2025-03-25.pdf)
    - Location is defined by the position in the list: position 1 to 10 <=> GA1, position 11 to 15 <=> GA2, position 16 to 25 <=> GA3
    - With this information, statistics are made.
    - Analysis in done comparing criterion defined for "PULL_STRENGTH", "PULL_STRENGTH_MIN" and "LIFT_OFFS_LESS_THAN_7G" according to Module Yield Taskforce report (https://indico.cern.ch/event/1533105/contributions/6451232/attachments/3043014/5376048/ModuleYield_GeneralReco_Updated.pdf)

    """
    log = logging.getLogger(__name__)
    log.setLevel(verbosity.value)

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming WIREBOND_PULL_TEST analysis")
    log.info(" ===============================================")
    log.info("")

    test_type = Path(__file__).stem

    time_start = round(datetime.timestamp(datetime.now()))
    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    allinputs = get_inputs(input_meas)
    # qc_config = get_qc_config(qc_criteria_path, test_type)

    # alloutput = []
    # timestamps = []
    for filename in sorted(allinputs):
        log.info("")
        log.info(f" Loading {filename}")
        # meas_timestamp = get_time_stamp(filename)

        inputDFs = load_json(filename)
        log.info(
            f" There are results from {len(inputDFs)} module(s) stored in this file"
        )

        with Path(filename).open(encoding="utf-8") as f:
            jsonData = json.load(f)

        for j, inputDF in zip(jsonData, inputDFs):
            d = inputDF.to_dict()
            qcframe = inputDF.get_results()

            results = j[0].get("results")
            props = results.get("property")
            metadata = results.get("Metadata") or results.get("metadata")

            pull_data = metadata.pop("pull_data", None)
            if pull_data:
                log.info("Preprocessing pull data")
                results_pull_data = process_pull_data(pull_data)

                bad_keys = []
                for key in results_pull_data:
                    if results.get(key) is not None:
                        bad_keys.append(key)
                        continue

                if bad_keys:
                    msg = f"The following measurements were provided, but will be overridden by the calculated pull data: {', '.join(bad_keys)}. Please check your input file."
                    raise ValueError(msg)

                results["Measurements"] = results_pull_data

            module_sn = d.get("serialNumber")

            qc_config = get_qc_config(data_path / "analysis_cuts.json", test_type)

            layer = get_layer_from_sn(module_sn)

            result_values = {}
            for qc_variable in [
                "PULL_STRENGTH",
                "PULL_STRENGTH_MIN",
                "LIFT_OFFS_LESS_THAN_7G",
            ]:
                result_values[qc_variable] = (
                    results.get("Measurements").get(qc_variable).get("Values")[0]
                )

            passes_qc, _, _ = perform_qc_analysis(
                test_type, qc_config, layer, result_values
            )

            log.info("")
            if passes_qc:
                log.info(
                    f" Module {module_sn} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Module {module_sn} passes QC? "
                    + bcolors.BADRED
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            log.info("")

            #  Output a json file
            outputDF = outputDataFrame()
            outputDF.set_test_type(test_type)
            data = qcDataFrame()

            if metadata is not None:
                data._meta_data.update(metadata)

            #  Pass-through properties in input
            for key, value in props.items():
                data.add_property(key, value)

            #  Add analysis version
            data.add_property(
                "ANALYSIS_VERSION",
                __version__,
            )
            time_start = qcframe.get_meta_data().get("TimeStart")
            time_end = qcframe.get_meta_data().get("TimeEnd")
            duration = (
                (arrow.get(time_end) - arrow.get(time_start)).total_seconds()
                if time_start and time_end
                else -1
            )

            data.add_property(
                "MEASUREMENT_DATE",
                arrow.get(time_start).isoformat(timespec="milliseconds"),
            )
            data.add_property("MEASUREMENT_DURATION", int(duration))

            #  Pass-through measurement parameters
            for key, value in results.items():
                if key in [
                    "property",
                    "metadata",
                    "Metadata",
                    "Measurements",
                    "comment",
                ]:
                    continue

                data.add_parameter(key, value)

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

            for key, value in results["Measurements"].items():
                data.add_parameter(key, value["Values"][0])

            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)

            outfile = output_dir.joinpath(f"{module_sn}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": module_sn})
            save_dict_list(outfile, [out])


#            plt_outfile = output_dir.joinpath(f"{module_sn}_plot.png")
#           fig.savefig(plt_outfile, dpi=150)


if __name__ == "__main__":
    typer.run(main)
