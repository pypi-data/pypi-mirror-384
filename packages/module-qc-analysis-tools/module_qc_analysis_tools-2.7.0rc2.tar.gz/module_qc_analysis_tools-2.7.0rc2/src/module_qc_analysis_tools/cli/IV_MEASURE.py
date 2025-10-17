from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

import arrow
import matplotlib.pyplot as plt
import numpy as np
import typer
from module_qc_data_tools import (
    get_layer_from_sn,
    load_iv_alt,
    load_json,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools.analysis.iv_measure import analyse
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    print_result_summary,
)
from module_qc_analysis_tools.utils.misc import (
    JsonChecker,
    bcolors,
    convert_prefix,
    get_inputs,
    get_time_stamp,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)

TEST_TYPE = Path(__file__).stem


@app.command()
def main(
    input_meas: Path = OPTIONS["input_meas"],
    base_output_dir: Path = OPTIONS["output_dir"],
    qc_criteria_path: Path = OPTIONS["qc_criteria"],
    reference_iv_path: Path = OPTIONS["reference_iv"],
    input_layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
    site: str = OPTIONS["site"],
    input_vdepl: float = OPTIONS["depl_volt"],
):
    r"""
    Analyses sensor leakage current vs voltage measurement.

    Some relevant points for this analysis:
    - Use the leakage current to determine breakdown
    - Acceptances for leakage current and per area are defined at the operational voltage (used for $V \leq V_\mathrm{op}$)
    - Current compliance of $100 \mu A$ used (if leakage current is within $1\mu A$ with 5% tolerance)
    - If compliance is set weirdly or measurement is incomplete, then the breakdown is $V_\mathrm{max}$ if less than the breakdown threshold ($V_\mathrm{op}$ for 3D and $V_\mathrm{depl}+70$ for planar)
    - Leakage current per area not filled (`-999`) if $V_\mathrm{op}$ is not reached
    - Leakage current increase factor is in fact a "scale factor" in case the leakage current is reduced (e.g. when cold) compared with measurement on bare module
    - Breakdown reduction now includes the value `-1` for the case when breakdown observed on sensor/bare module but not on module (easy to include into the current cut range)

    This analysis produces an output file with several key parameters: breakdown voltage,
    leakage current at operation voltage (depletion voltage + 20/50V for
    3D/planar sensor), whether breakdown was observed and the absolute maximum
    measured bias voltage.  Note that raw measurement data will be plotted and
    uploaded onto the production database, which uses the absolute bias voltage
    and leakage current regardless of the polarity. All currents will be
    converted to uA.

    If the depletion voltage if the sensor is unknown, please do not supply
    anything to `--vdepl`. In this case either a value from the database or a
    default value will be used.

    Two analysis criteria are the change wrt the bare module stage
    (see module spec document [AT2- IP-ES-0009](https://edms.cern.ch/document/2019657/3).
    An additional input file is required which provides the reference bare
    module IV with up to 3 bare modules (triplets) in the format below. This is
    generated in localDB. If none is supplied, the analysis will run but the
    module will not pass.

    ??? note "Reference bare module IV format"

        ```json
        {
          'target_component' : <MODULE_SN>,
          'target_stage' : <MODULE_STAGE>,
          'reference_IVs' : [
            { 'component' : <SENSOR_TILE_SN>,
              'stage' : <bare module stage>,
              'Vbd' : <VALUE>,
              'Vfd' : <VALUE>,
              'temperature' : <VALUE>,
              'IV_ARRAY' : { "voltage" : [ array ], "current" : [array], "temperature": [array] }
            },
            { 'component' : <SENSOR_TILE_SN>,
              'stage' : <bare module stage>,
              'Vbd' : <VALUE>,
              'Vfd' : <VALUE>,
              'temperature' : <VALUE>,
              'IV_ARRAY' : { "voltage" : [ array ], "current" : [array], "temperature": [array] }
            },
            { 'component' : <SENSOR_TILE_SN>,
              'stage' : <bare module stage>,
              'Vbd' : <VALUE>,
              'Vfd' : <VALUE>,
              'temperature' : <VALUE>,
              'IV_ARRAY' : { "time": [array], "voltage" : [ array ], "current" : [array], "sigma current": [array], "temperature": [array], "humidity": [array] }
            }
          ]
        }
        ```

    For more details, see [Lingxin's slides](https://indico.cern.ch/event/1567113/contributions/6602198/) in the ITkPix Module QC Software Development meeting from Tuesday, July 8th, 2025.

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

    allinputs = get_inputs(input_meas)
    reference_iv = get_inputs(reference_iv_path) if reference_iv_path else None
    if not reference_iv_path:
        log.warning(
            bcolors.WARNING
            + " No reference bare module IV provided, analysis will fail."
            + bcolors.ENDC
        )

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming IV analysis")
    log.info(" ===============================================")
    log.info("")

    alloutput = []
    timestamps = []
    for _ifile, filename in enumerate(sorted(allinputs)):
        log.info("")
        log.info(f" Loading {filename}")
        meas_timestamp = get_time_stamp(filename)

        ### alternative input format discussed here: https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/merge_requests/109
        with Path(filename).open(encoding="utf-8") as infile:
            if "QCHELPER" in infile.read():
                infile.seek(0)
                inputDFs = load_iv_alt(filename, TEST_TYPE, input_vdepl)
            else:
                try:
                    inputDFs = load_json(filename)
                except Exception:
                    try:
                        log.warning(
                            bcolors.WARNING
                            + " Unusual file format, trying to decode."
                            + bcolors.ENDC
                        )
                        inputDFs = load_iv_alt(filename, TEST_TYPE, input_vdepl)
                    except Exception as eee:
                        log.error(
                            bcolors.ERROR
                            + f"J sonChecker check not passed. {eee}. Please provide a valid input file."
                            + bcolors.ENDC
                        )
                        raise RuntimeError from eee

        log.info(
            f" There are results from {len(inputDFs)} module(s) stored in this file"
        )

        for inputDF in inputDFs:
            # Check file integrity
            checker = JsonChecker(inputDF, TEST_TYPE)

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
            module_sn = metadata.get("ModuleSN")

            if input_layer == "Unknown":
                try:
                    layer = get_layer_from_sn(module_sn)
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

            #  Simplistic QC criteria
            meas_array = {}
            _prefix = None

            try:
                if qcframe._data["current"]["Unit"] != "uA":
                    _prefix = qcframe._data["current"]["Unit"]
            except KeyError:
                log.warning(
                    bcolors.WARNING
                    + " No unit found! Assuming default prefix uA!"
                    + bcolors.ENDC
                )

            try:
                for key in ["current", "sigma current"]:
                    qcframe._data[key]["Values"] = convert_prefix(
                        qcframe._data[key]["Values"],
                        inprefix=qcframe._data[key]["Unit"],
                        targetprefix="u",
                    )
                    qcframe._data[key]["Unit"] = "uA"
            except KeyError as kerr:
                log.warning(kerr)

            for key in qcframe._data:
                meas_array[key] = qcframe._data[key]["Values"]

            baremoduleIV = None
            if reference_iv:
                inputdata = None
                with Path(reference_iv[0]).open(encoding="utf-8") as serialized:
                    inputdata = json.load(serialized)
                if not inputdata:
                    log.warning(
                        bcolors.WARNING
                        + " No reference bare module IV provided, analysis will fail."
                        + bcolors.ENDC
                    )
                else:
                    if not isinstance(inputdata, list):
                        # Can read one IV measurement in sensor json format at a time
                        inputdata = [inputdata]
                        log.info(" Found ref data for one measurement.")
                    else:
                        log.info(f" Found ref data for {len(inputdata)} measurement.")

                    inputdata_dict = {
                        jtem["target_component"]: jtem for jtem in inputdata
                    }

                    baremoduleIV = inputdata_dict.get(module_sn)
                    if not baremoduleIV:
                        log.error(
                            bcolors.ERROR
                            + " Didn't find correct module SN in reference data."
                            + bcolors.ENDC
                        )
                        raise typer.Exit(1)

                    if "reference_IVs" not in baremoduleIV:
                        log.error(
                            bcolors.ERROR
                            + f" No reference data found for {module_sn}."
                            + bcolors.ENDC
                        )
                        raise typer.Exit(1)
            else:
                baremoduleIV = None

            results, passes_qc, summary, fig = analyse(
                meas_array,
                input_vdepl,
                module_sn,
                layer,
                baremoduleIV,
                metadata.get("AverageTemperature"),
                qc_criteria_path,
            )

            if fig:
                # save qc result figure
                plt_outfile = output_dir.joinpath(f"{module_sn}_plot.png")
                log.info(f" Saving {plt_outfile}")
                fig.savefig(plt_outfile, dpi=150)
                plt.close()
                outfile = output_dir.joinpath(f"{module_sn}.png")

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

            Vbd = results["BREAKDOWN_VOLTAGE"]
            Ilc = results["LEAK_CURRENT"]

            log.info(
                f" Module {module_sn} has breakdown voltage of {Vbd} and I(Vop) of {Ilc}."
            )

            #  Output a json file
            outputDF = outputDataFrame()
            outputDF._serialNumber = module_sn
            outputDF.set_test_type(TEST_TYPE)
            data = qcDataFrame()
            for key, result in results.items():
                data.add_parameter(key, result)
            data.add_property(
                "ANALYSIS_VERSION",
                __version__,
            )
            data.add_property("TEMP", np.mean(meas_array["temperature"]), 2)
            data.add_property(
                "HUM",
                np.mean(meas_array["humidity"])
                if len(meas_array["humidity"]) > 0
                else 0,
                2,
            )

            data._meta_data.update(metadata)

            data.add_meta_data(
                "MEASUREMENT_VERSION",
                qcframe.get_properties().get(TEST_TYPE + "_MEASUREMENT_VERSION"),
            )
            time_start = qcframe.get_meta_data()["TimeStart"]
            time_end = qcframe.get_meta_data().get("TimeEnd")
            # support for sensor-IV in their string format
            if isinstance(time_start, str):
                time_start = arrow.get(time_start, "YYYY-MM-DD_HHmmss").timestamp()

            if isinstance(time_end, str):
                time_end = arrow.get(time_end, "YYYY-MM-DD_HHmmss").timestamp()

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

            data.add_meta_data("QC_LAYER", layer)
            data.add_meta_data("INSTITUTION", institution)
            data.add_meta_data("MODULE_SN", module_sn)

            outputDF.set_results(data)
            outputDF.set_pass_flag(bool(passes_qc))

            alloutput += [outputDF.to_dict(True)]
            timestamps += [meas_timestamp]

    # Only store results from same timestamp into same file
    dfs = np.array(alloutput)
    tss = np.array(timestamps)
    for x in np.unique(tss):
        outfile = output_dir.joinpath(f"{module_sn}.json")
        log.info(f" Saving output of analysis to: {outfile}")
        save_dict_list(
            outfile,
            dfs[tss == x].tolist(),
        )


if __name__ == "__main__":
    typer.run(main)
