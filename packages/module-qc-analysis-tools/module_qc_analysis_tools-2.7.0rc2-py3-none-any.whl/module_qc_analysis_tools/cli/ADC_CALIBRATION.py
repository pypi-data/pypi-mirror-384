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

from module_qc_analysis_tools.analysis.adc_calibration import analyze
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

TEST_TYPE = "ADC_CALIBRATION"


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
    Performs the ADC calibration.

    It produces several diagnostic plots and an output file with the ADC calibration slope and offset.
    """
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
    log.info(" \tPerforming ADC calibration analysis")
    log.info(" ===============================================")
    log.info("")

    allinputs = get_inputs(input_meas)

    alloutput = []
    chip_names = []
    timestamps = []
    for filename in sorted(allinputs):
        meas_timestamp = get_time_stamp(filename)
        log.info("")
        log.info(f" Loading {filename}")
        input_jsons = json.loads(Path(filename).read_text(encoding="utf-8"))
        chipnames, outputDFs, passes_qcs, summaries, figs = analyze(
            input_jsons,
            input_layer=input_layer,
            site=site,
            fit_method=fit_method,
            qc_criteria_path=qc_criteria_path,
        )

        alloutput.extend(outputDFs)
        chip_names.extend(chipnames)
        timestamps.extend([meas_timestamp] * len(outputDFs))

        for chipname, passes_qc, summary, fig in zip(
            chipnames, passes_qcs, summaries, figs
        ):
            # save qc result figure
            outfile = output_dir.joinpath(f"{chipname}.png")
            log.info(f" Saving {outfile}")
            fig.savefig(f"{outfile}")
            plt.close(fig)
            # print qc result summary
            print_result_summary(summary, TEST_TYPE, output_dir, chipname)
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
        for outputDF, chipname in zip(alloutput, chip_names):
            outfile = output_dir.joinpath(f"{chipname}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            save_dict_list(outfile, [outputDF])


if __name__ == "__main__":
    typer.run(main)
