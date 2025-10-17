from __future__ import annotations

import contextlib
import json
import logging
from datetime import datetime
from pathlib import Path

import arrow
import typer
from module_qc_data_tools import (
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
from module_qc_analysis_tools.utils.misc import (
    get_inputs,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    reference_iv_path: Path = OPTIONS["reference_iv"],
    base_output_dir: Path = OPTIONS["output_dir"],
    # layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    log = logging.getLogger(__name__)
    log.setLevel(verbosity.value)

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming BARE_MODULE_SENSOR_IV analysis")
    log.info(" ===============================================")
    log.info("")

    test_type = Path(__file__).stem

    time_start = round(datetime.timestamp(datetime.now()))
    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    allinputs = get_inputs(input_meas)
    reference_iv = get_inputs(reference_iv_path) if reference_iv_path else []

    # qc_config = get_qc_config(qc_criteria_path, test_type)

    # alloutput = []
    # timestamps = []

    reference_sensor_IV = None
    reference_bare_IV = None
    with Path(reference_iv[0]).open(encoding="utf-8") as f:
        reference_dict = json.load(f)
    reference = reference_dict.get("reference_IVs")
    with contextlib.suppress(IndexError):
        reference_sensor_IV = reference[0]

    with contextlib.suppress(IndexError):
        reference_bare_IV = reference[1]

    if not reference_sensor_IV:
        log.warning("reference_sensor_IV is missing")

    if not reference_bare_IV:
        log.warning("reference_bare_IV is missing")

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

            module_name = d.get("serialNumber")

            # ------------------------------------------------------------------
            # Flagging
            if reference_sensor_IV and reference_bare_IV:
                Ilc_pre = reference_sensor_IV.get("Ilc")
                Ilc_now = reference_bare_IV.get("Ilc")
                Ilc_flag = Ilc_pre * 2 > Ilc_now
                result_pass_sen = reference_sensor_IV.get("qc_passed")
                result_pass_bare = reference_bare_IV.get("qc_passed")

                passes_qc = Ilc_flag and result_pass_bare and result_pass_sen

                log.info(
                    f"Ilc_flag: {Ilc_flag}, result_pass: {result_pass_bare}, result_pass_sen: {result_pass_sen}, passes_qc: {passes_qc}"
                )
            else:
                log.warning("passes_qc is forced to fail due to missing references")
                passes_qc = False

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
            # support for sensor-IV in their string format
            if isinstance(time_start, str):
                time_start = arrow.get(time_start, "YYYY-MM-DD_HHmmss").timestamp()
            time_end = qcframe.get_meta_data()["TimeEnd"]
            duration = arrow.get(time_end) - arrow.get(time_start)

            data.add_property(
                "MEASUREMENT_DATE",
                arrow.get(time_start).isoformat(timespec="milliseconds"),
            )
            data.add_property("MEASUREMENT_DURATION", int(duration.total_seconds()))

            for key, value in results["Measurements"].items():
                data.add_parameter(key, value)
            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)

            outfile = output_dir.joinpath(f"{module_name}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": module_name})
            save_dict_list(outfile, [out])


if __name__ == "__main__":
    typer.run(main)
