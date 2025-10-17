from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import typer
from module_qc_data_tools import (
    save_dict_list,
)

from module_qc_analysis_tools.analysis.long_term_stability_dcs import analyze
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    FitMethod,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import print_result_summary
from module_qc_analysis_tools.utils.misc import (
    bcolors,
    get_inputs,
    get_time_stamp,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)

TEST_TYPE = "LONGTERM_STABILITY_DCS"


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    qc_criteria_path: Path = OPTIONS["qc_criteria"],
    input_layer: str = OPTIONS["layer"],
    permodule: bool = OPTIONS["permodule"],
    site: str = OPTIONS["site"],
    _fit_method: FitMethod = OPTIONS["fit_method"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    time_start = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = base_output_dir.joinpath(TEST_TYPE).joinpath(f"{time_start}")
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
    log.info(" ===============================================")
    log.info(" \tPerforming Long-term stability DCS analysis")
    log.info(" ===============================================")
    log.info("")

    allinputs = get_inputs(input_meas)

    alloutput = []
    timestamps = []
    for filename in sorted(allinputs):
        meas_timestamp = get_time_stamp(filename)
        log.info("")
        log.info(f" Loading {filename}")
        input_jsons = json.loads(Path(filename).read_text(encoding="utf-8"))
        module_sns, outputDFs, passes_qcs, summaries, _ = analyze(
            input_jsons,
            input_layer=input_layer,
            site=site,
            qc_criteria_path=qc_criteria_path,
        )

        alloutput.extend(outputDFs)
        timestamps.extend([meas_timestamp] * len(outputDFs))

        for module_sn, passes_qc, summary in zip(module_sns, passes_qcs, summaries):
            # print qc result summary
            print_result_summary(summary, TEST_TYPE, output_dir, module_sn)
            if passes_qc == -1:
                log.error(
                    bcolors.ERROR
                    + f" QC analysis for {module_sn} was NOT successful. Please fix and re-run. Continuing to next chip.."
                    + bcolors.ENDC
                )
                continue

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
    else:
        for outputDF, module_sn in zip(alloutput, module_sns):
            outfile = output_dir.joinpath(f"{module_sn}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            save_dict_list(outfile, [outputDF])


if __name__ == "__main__":
    typer.run(main)
