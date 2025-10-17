from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import arrow
import matplotlib.pyplot as plt
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
from module_qc_analysis_tools.utils.analysis import normalise_current
from module_qc_analysis_tools.utils.misc import (
    get_inputs,
)

log = logging.getLogger(__name__)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    input_aux: Path = OPTIONS["qc_criteria"],
    # qc_criteria_path: Path = OPTIONS["qc_criteria"],
    # layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    log.setLevel(verbosity.value)

    log.info(input_aux)
    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming IV_MEASURE analysis")
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

            module_name = d.get("serialNumber")

            #  Simplistic QC criteria
            meas_array = results.get("IV_ARRAY")
            voltage = meas_array.get("voltage")
            current = meas_array.get("current")
            sigma_current = meas_array.get("sigma current")
            temperature = meas_array.get("temperature")
            humidity = meas_array.get("humidity")

            Vbd0 = results.get("Vbd0")
            Ilc0 = results.get("Ilc")

            is3Dmodule = False

            Vdepl = 5.0 if is3Dmodule else 50.0
            Vdepl_flag = True

            leak_current_voltage = Vdepl + 20.0 if is3Dmodule else Vdepl + 50.0
            breakdown_threshold = Vdepl + 20.0 if is3Dmodule else Vdepl + 70.0
            current_threshold = 2.5 if is3Dmodule else 0.75

            area = 4.25 if is3Dmodule else 15.92  # [cm^2]
            # 15.76 for inner quad, to be implemented

            Vbd0_flag = None
            if Vbd0:
                Vbd0_flag = Vbd0 > breakdown_threshold

            Ilc0_flag = None
            if Ilc0:
                Ilc0_flag = (Ilc0 / (area + 1.0e-9)) < current_threshold

            Vbd = 0
            Ilc = 0

            fig, ax = plt.subplots(1, 2, figsize=(14.2, 4.0))

            fig.subplots_adjust(wspace=0.82)

            if input_aux is not None:
                reference_sensor_IV = None

                reference_IV = get_inputs(input_aux)
                for file in sorted(reference_IV):
                    with Path(file).open(encoding="utf-8") as f:
                        reference_dict = json.load(f)
                    reference = reference_dict.get("reference_IVs")
                    if reference:
                        reference_sensor_IV = reference[0] if reference else None

                if reference_sensor_IV:
                    sensor_V = reference_sensor_IV.get("IV_ARRAY").get("voltage")
                    sensor_I = reference_sensor_IV.get("IV_ARRAY").get("current")

                    tmp = reference_sensor_IV.get("temperature", 25)
                    tmp = 25 if tmp == 20 else tmp  # support for HPK measurement
                    temp = [tmp] * len(sensor_I)

                    normalised_current = normalise_current(
                        sensor_I, len(sensor_I) * temp
                    )
                    calib_normalised_current = [
                        element - normalised_current[0]
                        for element in normalised_current
                    ]
                    normalised_current = [
                        element - normalised_current[0]
                        for element in normalised_current
                    ]
                    idx = len([v for v in sensor_V if v < 200])

                    ps = ax[0].plot(
                        sensor_V[1:idx],
                        sensor_I[1:idx],
                        "o",
                        label="sensor_current(raw)",
                        markersize=3,
                    )
                    sensor_legend = plt.legend(
                        handles=ps, loc="lower center", bbox_to_anchor=(-1.39, -0.33)
                    )
                    plt.gca().add_artist(sensor_legend)

                    ps1 = ax[1].plot(
                        sensor_V[1:idx],
                        calib_normalised_current[1:idx],
                        "x",
                        label="sensor_current(norm)",
                        markersize=3,
                    )
                    sensor_legend1 = plt.legend(
                        handles=ps1, loc="lower center", bbox_to_anchor=(0.39, -0.33)
                    )
                    plt.gca().add_artist(sensor_legend1)

            # Finding leakage current at threshold voltage
            else:
                fig, ax = plt.subplots(1, figsize=(7.2, 4.0))
            for idx, V in enumerate(voltage):
                if Vdepl > V:
                    continue

                if leak_current_voltage >= V:
                    Ilc = current[idx]

                # Finding breakdown voltage for 3D
                if is3Dmodule:
                    if current[idx] > current[idx - 5] * 2 and voltage[idx - 5] > Vdepl:
                        Vbd = voltage[idx - 5]
                        log.info(f"Breakdown at {Vbd:.1f} V for 3D sensor")
                        ax[0].axvline(
                            Vbd,
                            linewidth=4,
                            color="r",
                            label=f"Bd @ {Vbd:.0f}V",
                        )
                        break

                # Finding breakdown voltage for Planar
                else:
                    if current[idx] > current[idx - 1] * 1.2 and voltage[idx - 1] != 0:
                        Vbd = V
                        log.info(f"Breakdown at {Vbd:.1f} V for planar sensor")
                        ax[0].axvline(
                            Vbd,
                            linewidth=4,
                            color="r",
                            label=f"Bd @ {Vbd:.0f}V",
                        )
                        break

            # Plotting options
            if len(sigma_current) == 0:
                p1 = ax[0].plot(voltage[1:], current[1:], label="current", markersize=2)
                first_legend = plt.legend(
                    handles=p1, loc="lower center", bbox_to_anchor=(0.5, -0.33)
                )
                p2 = ax[1].plot(voltage[1:], current[1:], label="current", markersize=2)
            else:
                p1 = ax[0].errorbar(
                    voltage[1:],
                    current[1:],
                    yerr=sigma_current[1:],
                    fmt="ko",
                    label="current",
                    markersize=2,
                )
                first_legend = plt.legend(
                    handles=[p1], loc="lower center", bbox_to_anchor=(-0.92, -0.33)
                )
                plt.gca().add_artist(first_legend)

                p2 = ax[1].errorbar(
                    voltage[1:],
                    current[1:],
                    yerr=sigma_current[1:],
                    fmt="ko",
                    label="current",
                    markersize=2,
                )

            if len(temperature) == 0:
                log.warning("No temperature array given")
            elif len(voltage[1:]) == len(temperature[1:]):
                ax1 = ax[0].twinx()
                (p2,) = ax1.plot(
                    voltage[1:], temperature[1:], color="C1", label="temperature"
                )
                ax1.set_ylabel("T [degC]", color="C1", fontsize="large")
                second_legend = plt.legend(
                    handles=[p2], loc="lower center", bbox_to_anchor=(1.3, -0.33)
                )
                plt.gca().add_artist(second_legend)

                ax2 = ax[1].twinx()
                (p3,) = ax2.plot(
                    voltage[1:], temperature[1:], color="C1", label="temperature"
                )
                ax2.set_ylabel("T [degC]", color="C1", fontsize="large")

            if len(humidity) == 0:
                log.warning("No humidity array given")
            elif len(voltage[1:]) == len(humidity[1:]):
                ax2 = ax[0].twinx()
                (p3,) = ax2.plot(
                    voltage[1:], humidity[1:], color="C2", label="humidity"
                )
                ax2.set_ylabel("RH [%]", color="C2", fontsize="large")
                ax2.spines["right"].set_position(("outward", 60))
                third_legend = plt.legend(
                    handles=[p3], loc="lower center", bbox_to_anchor=(1.7, -0.33)
                )
                plt.gca().add_artist(third_legend)

                ax2 = ax[1].twinx()
                (p3,) = ax2.plot(
                    voltage[1:], humidity[1:], color="C2", label="humidity"
                )
                ax2.set_ylabel("RH [%]", color="C2", fontsize="large")
                ax2.spines["right"].set_position(("outward", 60))

            ax[0].set_title(f'raw IV for"{module_name}"', fontsize="large")
            ax[0].set_xlabel(
                "Negative Voltage [V]", ha="right", va="top", x=1.0, fontsize="large"
            )
            ax[0].set_ylabel(
                "Negative Current [uA]",
                ha="right",
                va="bottom",
                y=1.0,
                fontsize="large",
            )

            ax[1].set_title(f'normalized IV for"{module_name}"', fontsize="large")
            ax[1].set_xlabel(
                "Negative Voltage [V]", ha="right", va="top", x=1.0, fontsize="large"
            )
            ax[1].set_ylabel(
                "Negative Current [uA]",
                ha="right",
                va="bottom",
                y=1.0,
                fontsize="large",
            )

            ax[0].grid()

            ax[1].grid()
            left_y_ticks = ax[0].get_yticks()

            ax[1].set_yticks(left_y_ticks)
            ax[0].set_ylim(float(left_y_ticks[0]), float(left_y_ticks[-1]))
            ax[1].set_ylim(float(left_y_ticks[0]), float(left_y_ticks[-1]))

            fig.subplots_adjust(bottom=0.25)
            fig.subplots_adjust(right=0.75)

            # ---------------------------------------------------------------
            # Flagging

            Ilc_flag = False

            # Pass or fail on leakaged current
            Ilc_flag = Ilc / (area + 1.0e-9) < current_threshold

            # Pass or fail on leakaged current
            Vbd_flag = (Vbd > breakdown_threshold) or (
                voltage[-1] > breakdown_threshold
            )

            results["LEAK_CURRENT"] = Ilc
            if Vbd == 0:
                results["BREAKDOWN_VOLTAGE"] = -999
                results["NO_BREAKDOWN_VOLTAGE_OBSERVED"] = True
            else:
                results["BREAKDOWN_VOLTAGE"] = Vbd
                results["NO_BREAKDOWN_VOLTAGE_OBSERVED"] = False
            results["MAXIMUM_VOLTAGE"] = voltage[-1]
            results["property"]["TEMP"] = sum(temperature) / len(temperature)
            results["property"]["HUM"] = sum(humidity) / len(humidity)

            passes_qc = (
                (Vbd_flag or Vbd0_flag) and (Ilc_flag or Ilc0_flag) and Vdepl_flag
            )

            log.info(
                f"Ilc_flag: {Ilc_flag}, Vbd_flag: {Vbd_flag}, passes_qc: {passes_qc}"
            )

            #  Output a json file
            outputDF = outputDataFrame()
            outputDF.set_test_type(test_type)
            data = qcDataFrame()
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
            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)

            outfile = output_dir.joinpath(f"{module_name}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": module_name})
            save_dict_list(outfile, [out])

            plt_outfile = output_dir.joinpath(f"{module_name}_plot.png")
            fig.savefig(plt_outfile, dpi=150)


if __name__ == "__main__":
    typer.run(main)
