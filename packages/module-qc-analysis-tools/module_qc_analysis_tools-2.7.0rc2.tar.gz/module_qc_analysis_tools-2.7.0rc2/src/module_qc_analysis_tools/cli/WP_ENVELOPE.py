from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import numpy as np
import typer
from module_qc_data_tools import (
    save_dict_list,
)

from module_qc_analysis_tools.analysis.wp_envelope import analyze
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import print_result_summary
from module_qc_analysis_tools.utils.misc import (
    bcolors,
    get_inputs,
    get_time_stamp,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)

TEST_TYPE = "WP_ENVELOPE"


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    qc_criteria_path: Path = OPTIONS["qc_criteria"],
    input_layer: str = OPTIONS["layer"],
    # _permodule: bool = OPTIONS["permodule"],
    site: str = OPTIONS["site"],
    # _fit_method: FitMethod = OPTIONS["fit_method"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    """
    Performs analysis of wire bonding protection roof envelope.
    The QC procedure is described in the following documentations:
    - https://edms.cern.ch/ui/file/2648149/1/OB_WBMP_Assembly_Procedure.pdf
    - https://edms.cern.ch/file/2648149/1/SQ_OBWBP_v8.pptx
    Tests are implemented in test_cli.py with a command "wp-envelope"
    Presentation; https://indico.cern.ch/event/1529894/
    """

    log = logging.getLogger("analysis")
    log.setLevel(verbosity.value)
    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming WP_ENVELOPE analysis")
    log.info(" ===============================================")
    log.info("")

    time_start = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_dir = base_output_dir.joinpath(TEST_TYPE).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    allinputs = get_inputs(input_meas)

    alloutput = []
    timestamps = []
    for filename in sorted(allinputs):
        meas_timestamp = get_time_stamp(filename)
        log.info("")
        log.info(f" Loading {filename}")
        input_jsons = json.loads(Path(filename).read_text(encoding="utf-8"))
        modulenames, outputDFs, passes_qcs, summaries, figs = analyze(
            input_jsons,
            input_layer=input_layer,
            site=site,
            qc_criteria_path=qc_criteria_path,
        )

        alloutput.extend(outputDFs)
        timestamps.extend([meas_timestamp] * len(outputDFs))

        for modulename, passes_qc, summary, fig in zip(
            modulenames, passes_qcs, summaries, figs
        ):
            if fig:
                # save qc result figure
                outfile = output_dir.joinpath(f"{modulename}.png")
                log.info(f" Saving {outfile}")
                fig.savefig(f"{outfile}")
            # print qc result summary
            print_result_summary(summary, TEST_TYPE, output_dir, modulename)
            if passes_qc == -1:
                log.error(
                    bcolors.ERROR
                    + f" QC analysis for {modulename} was NOT successful. Please fix and re-run. Continuing to next module.."
                    + bcolors.ENDC
                )
                continue

            log.info("")
            if passes_qc:
                log.info(
                    f" Module {modulename} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Module {modulename} passes QC? "
                    + bcolors.BADRED
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            log.info("")

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
