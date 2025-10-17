from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import arrow
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
    bcolors,
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
    log.info(" \tPerforming HV_LV_TEST analysis")
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

            results = j[0].get("results", {})
            props = results.get("property", {})
            metadata = results.get("Metadata") or results.get("metadata", {})
            measurements = results.get("Measurements", {})

            props["OPERATOR"] = props.get("OPERATOR_IDENTITY", "")

            # Extract relevant information
            serial_number = d.get("serialNumber")

            # Bypass for backward compatibility
            def _transfer_obsolete_data(
                source_dict,
                target_dict,
                key_list,
                update_action,
            ):
                if not source_dict:
                    return

                for obsolete_key in key_list:
                    if obsolete_key not in source_dict:
                        continue

                    parts = obsolete_key.split("[")
                    key = parts[0]
                    unit = parts[1].rstrip("]") if len(parts) > 1 else ""
                    value = source_dict[obsolete_key]

                    update_action(target_dict, key, value, unit)

            def _update_as_measurement(target, key, value, unit):
                """Update a dictionary for 'Measurements'"""
                inner_dict = target.setdefault(key, {})
                inner_dict.setdefault("Values", []).append(value)
                inner_dict["Unit"] = unit

            def _update_as_property(target, key, value, _unit):
                """Update a dictionary for 'property'"""
                target[key] = value

            metadata_measurements = metadata.get("Measurement")
            if metadata_measurements:
                obsolete_meas_col_names = [
                    "VIN_DROP[V]",
                    "GND_DROP[V]",
                    # "VIN_RESISTANCE[mOhm]",
                    # "GND_RESISTANCE[mOhm]",
                    "EFFECTIVE_RESISTANCE[mOhm]",
                    "HV_LEAKAGE[mV]",
                    "LEAKAGE_CURRENT[nA]",
                    "NTC_VOLTAGE[V]",
                    "NTC_VALUE[kOhm]",
                    "HUMIDITY[RH%]",
                    "TEMPERATURE",
                    "R1_HV_RESISTOR",
                ]
                _transfer_obsolete_data(
                    metadata_measurements,
                    measurements,
                    obsolete_meas_col_names,
                    _update_as_measurement,
                )
                measurements["RELATIVE_HUMIDITY"] = measurements.pop("HUMIDITY", -999)
                measurements["DAMAGE_COMMENT"] = {"Values": [""]}

                obsolete_prop_col_names = [
                    "TEST_DURATION[min]",
                ]
                _transfer_obsolete_data(
                    metadata_measurements,
                    props,
                    obsolete_prop_col_names,
                    _update_as_property,
                )

            effective_resistance = (
                measurements["EFFECTIVE_RESISTANCE"]["Values"][0]
                if measurements.get("EFFECTIVE_RESISTANCE")
                else 999
            )
            leakage_current = (
                measurements["LEAKAGE_CURRENT"]["Values"][0]
                if measurements.get("LEAKAGE_CURRENT")
                else 999
            )

            passes_qc = (
                # (vin_resistance <= 12)
                # and (gnd_resistance <= 12)
                (effective_resistance <= 12) and (leakage_current <= 20)
            )

            # Output a json file
            outputDF = outputDataFrame()
            outputDF.set_test_type(test_type)

            qc_data = qcDataFrame()
            qc_data._meta_data.update(metadata)

            # qc_data.add_property("SERIAL_NUMBER", serial_number)
            # Other properties remain the same
            # ...

            # Handle 'property' from results

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

            time_start = qc_data.get_meta_data()["TimeStart"]
            time_end = qc_data.get_meta_data().get("TimeEnd")
            duration = (
                (arrow.get(time_end) - arrow.get(time_start)).total_seconds()
                if time_end
                else -1
            )

            qc_data.add_property(
                "MEASUREMENT_DATE",
                arrow.get(time_start).isoformat(timespec="milliseconds"),
            )
            qc_data.add_property("MEASUREMENT_DURATION", int(duration))

            for key, value in results["Measurements"].items():
                try:
                    if len(value["Values"]) < 1:
                        param_value = None
                    else:
                        param_value = value["Values"][0]
                    qc_data.add_parameter(key, param_value)
                except (KeyError, IndexError, TypeError):
                    log.warning(
                        f'Skipping measurement "{key}" due to unexpected data format: {value}'
                    )
                    continue
            outputDF.set_results(qc_data)
            outputDF.set_pass_flag(passes_qc)

            log.info("")
            if passes_qc:
                log.info(
                    f" Module {serial_number} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Module {serial_number} passes QC? "
                    + bcolors.BADRED
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            log.info("")

            outfile = output_dir.joinpath(f"{serial_number}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": serial_number})
            save_dict_list(outfile, [out])


if __name__ == "__main__":
    typer.run(main)
