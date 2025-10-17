from __future__ import annotations

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
    base_output_dir: Path = OPTIONS["output_dir"],
    # qc_criteria_path: Path = OPTIONS["qc_criteria"],
    # layer: str = OPTIONS["layer"],
    verbosity: LogLevel = OPTIONS["verbosity"],
):
    log = logging.getLogger(__name__)
    log.setLevel(verbosity.value)

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming VISUAL_INSPECTION analysis")
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

            # stage = j[0].get("stage")
            results = j[0].get("results")
            props = results.get("property")
            metadata = results.get("Metadata") or results.get("metadata")

            module_name = d.get("serialNumber")
            # alternatively, props.get("MODULE_SN")

            # Check component type
            is_pcb = module_name.startswith("20UPGPQ")

            if is_pcb:
                qc = {
                    "WIREBOND_PADS_CONTAMINATION_GRADE": 1,
                    "PARTICULATE_CONTAMINATION_GRADE": 1,
                    "WATERMARKS_GRADE": 1,
                    "SCRATCHES_GRADE": 1,
                    "SOLDERMASK_IRREGULARITIES_GRADE": 1,
                    "HV_LV_CONNECTOR_ASSEMBLY_GRADE": 1,
                    "DATA_CONNECTOR_ASSEMBLY_GRADE": 1,
                    "SOLDER_SPILLS_GRADE": 1,
                    "COMPONENT_MISALIGNMENT_GRADE": 1,
                    "SHORTS_OR_CLOSE_PROXIMITY_GRADE": 1,
                }
            else:
                qc = {
                    "SMD_COMPONENTS_PASSED_QC": 1,
                    "SENSOR_CONDITION_PASSED_QC": 1,
                    "FE_CHIP_CONDITION_PASSED_QC": 1,
                    "GLUE_DISTRIBUTION_PASSED_QC": 1,
                    "WIREBONDING_PASSED_QC": 1,
                    "PARYLENE_COATING_PASSED_QC": 1,
                }

            front_defects = metadata.get("front_defects")
            back_defects = metadata.get("back_defects")

            for defect_results in [front_defects, back_defects]:
                if defect_results is None:
                    continue

                critic_prob = False
                for _tile, defects in defect_results.items():
                    for defect in defects:
                        if is_pcb:
                            keymap = {
                                "contamination_wirebonding": "WIREBOND_PADS_CONTAMINATION_GRADE",
                                "dusts": "PARTICULATE_CONTAMINATION_GRADE",
                                "none": "WATERMARKS_GRADE",  # TODO verify this
                                "scratches": "SCRATCHES_GRADE",
                                "irregularities": "SOLDERMASK_IRREGULARITIES_GRADE",
                                "power_connector": "HV_LV_CONNECTOR_ASSEMBLY_GRADE",
                                "data_connector": "DATA_CONNECTOR_ASSEMBLY_GRADE",
                                "solder_overflow": "SOLDER_SPILLS_GRADE",
                                "misalignment": "COMPONENT_MISALIGNMENT_GRADE",
                                "close_proximity": "SHORTS_OR_CLOSE_PROXIMITY_GRADE",
                            }
                        else:
                            keymap = {
                                "glue": "GLUE_DISTRIBUTION_PASSED_QC",
                                "wire": "WIREBONDING_PASSED_QC",
                                "_sensor": "SENSOR_CONDITION_PASSED_QC",
                                "_fe": "FE_CHIP_CONDITION_PASSED_QC",
                                "_pcb": "SMD_COMPONENTS_PASSED_QC",
                                "parylene": "PARYLENE_COATING_PASSED_QC",
                            }

                        defect_level = 1

                        if defect.lower().find("yellow") >= 0:
                            defect_level = 2
                        elif defect.lower().find("red") >= 0:
                            defect_level = 3

                        # Check for other rejection criteria that are not defined in ProdDB
                        # if is_pcb:
                        #     for _key, _dtype in keymap.items():
                        #         if (
                        #             defect.lower().find("missing") > 0
                        #             or defect.lower().find("critical") > 0
                        #         ):
                        #             critic_prob = True
                        #             break

                        for key, dtype in keymap.items():
                            if defect.lower().find(key) >= 0:
                                qc[dtype] = max(qc[dtype], defect_level)
                                break

            #  Simplistic QC criteria
            passes_qc = True

            # Usual criteria
            for value in qc.values():
                if value >= 3:
                    passes_qc = False
                    break

            # Additional criteria for PCB
            if is_pcb and critic_prob:
                passes_qc = False

            # Overall grade for PCB
            if is_pcb:
                qc["OVERALL_GRADE"] = 1
                for _key, value in qc.items():
                    if value == 2:
                        qc["OVERALL_GRADE"] = 2
                        break
                if not passes_qc:
                    qc["OVERALL_GRADE"] = 5
                log.info(f"OVERALL={qc['OVERALL_GRADE']}")

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

            #  Pass-through measurement parameters
            for key, value in qc.items():
                data.add_parameter(key, value)

            att = {}
            if metadata.get("front_defect_images") is not None:
                for tile, img_id in metadata.get("front_defect_images").items():
                    name = f"front_tile{tile}.jpg"
                    att[name] = img_id
            if metadata.get("back_defect_images") is not None:
                for tile, img_id in metadata.get("back_defect_images").items():
                    name = f"back_tile{tile}.jpg"
                    att[name] = img_id

            outputDF.set_results(data)
            outputDF.set_pass_flag(passes_qc)

            outfile = output_dir.joinpath(f"{module_name}.json")
            log.info(f" Saving output of analysis to: {outfile}")
            out = outputDF.to_dict(True)
            out.update({"serialNumber": module_name})
            out.update({"gridfs_attachments": att})

            save_dict_list(outfile, [out])


if __name__ == "__main__":
    typer.run(main)
