from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import typer
from module_qc_data_tools import (
    __version__,
    load_json,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)

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
    base_output_dir: Path = OPTIONS["output_dir"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    log = logging.getLogger(__name__)
    log.setLevel(verbosity.value)

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming LAYER_THICKNESS analysis")
    log.info(" ===============================================")
    log.info("")

    test_type = Path(__file__).stem

    time_start = round(datetime.timestamp(datetime.now()))
    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    allinputs = get_inputs(input_meas)

    for filename in sorted(allinputs):
        log.info("")
        log.info(f" Loading {filename}")

        inputDFs = load_json(filename)
        log.info(
            f" There are results from {len(inputDFs)} module(s) stored in this file"
        )

        with Path(filename).open(encoding="utf-8") as f:
            jsonData = json.load(f)

        for j, inputDF in zip(jsonData, inputDFs):
            d = inputDF.to_dict()

            results = j[0].get("results")
            props = results.get("property")
            metadata = results.get("metadata")
            # measurement = metadata.get("Measurement")

            operator = ""
            props["OPERATOR"] = operator  # operator!

            if metadata is None:
                metadata = results.get("Metadata")

            # Extract relevant information
            serial_number = d.get("serialNumber")

            # results = data["results"]
            # metadata = results["metadata"]

            # Additional parameters from the new JSON structure
            bottom_thickness = metadata.get("Measurement", {}).get(
                "BOTTOM_LAYER_THICKNESS"
            )
            coverlay = metadata.get("Measurement", {}).get(
                "COVERLAY_WITH_ADHESIVE_THICKNESS"
            )
            dielectric = metadata.get("Measurement", {}).get("DIELECTRIC_THICKNESS")
            inner_thickness = metadata.get("Measurement", {}).get(
                "INNER_LAYER_THICKNESS"
            )
            # solder_mask = metadata.get("Measurement", {}).get("SOLDERMASK_THICKNESS")
            thickness = metadata.get("Measurement", {}).get("THICKNESS")
            top_thickness = metadata.get("Measurement", {}).get("TOP_LAYER_THICKNESS")

            # Fill values from metadatas
            results["BOTTOM_LAYER_THICKNESS"] = bottom_thickness
            results["COVERLAY_WITH_ADHESIVE_THICKNESS"] = coverlay
            results["DIELECTRIC_THICKNESS"] = dielectric
            results["INNER_LAYER_THICKNESS"] = inner_thickness
            # results["SOLDERMASK_THICKNESS"] = solder_mask
            results["THICKNESS"] = thickness
            results["TOP_LAYER_THICKNESS"] = top_thickness

            # passes_qc = True
            passes_qc = (
                (188.8 <= thickness <= 283.2)
                and (23 <= top_thickness <= 38)
                and (9 <= inner_thickness <= 13.5)
                and (23 <= bottom_thickness <= 38)
            )

            # Output a json file
            outputDF = outputDataFrame()
            outputDF.set_test_type(test_type)

            qc_data = qcDataFrame()
            qc_data._meta_data.update(metadata)

            # Pass-through properties in input
            for key, value in props.items():
                qc_data.add_property(key, value)

            # Add analysis version
            qc_data.add_property(
                "ANALYSIS_VERSION",
                __version__,
            )

            # Pass-through measurement parameters
            for key, value in results.items():
                if key in [
                    "property",
                    "metadata",
                    "Metadata",
                    "Measurements",
                    "comment",
                ]:
                    continue

                qc_data.add_parameter(key, value)

            results_property = results.get("property", {})
            for key, value in results_property.items():
                qc_data.add_property(key, value)

            outputDF.set_results(qc_data)
            outputDF.set_pass_flag(passes_qc)

            outfile = output_dir.joinpath(f"{serial_number}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": serial_number})
            save_dict_list(outfile, [out])


if __name__ == "__main__":
    typer.run(main)
