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
    load_json,
    outputDataFrame,
    qcDataFrame,
    save_dict_list,
)
from module_qc_data_tools.utils import MyEncoder

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    FitMethod,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    get_bounds_and_precision,
    get_layer,
    perform_qc_analysis,
    print_result_summary,
)
from module_qc_analysis_tools.utils.misc import (
    DataExtractor,
    JsonChecker,
    bcolors,
    get_inputs,
    get_qc_config,
    get_time_stamp,
    getImuxMap,
    getVmuxMap,
    linear_fit,
    linear_fit_np,
)

app = typer.Typer(context_settings=CONTEXT_SETTINGS)

log = logging.getLogger("analysis")

EMPTY_VAL = -999


def get_NtcCalPar(metadata):
    # Read NTC parameters from metadata in the chip config.
    if "NtcCalPar" in metadata:
        NtcCalPar = metadata.get("NtcCalPar")
    else:
        NtcCalPar = [
            0.0007488999981433153,
            0.0002769000129774213,
            7.059500006789676e-08,
        ]
        log.warning(
            bcolors.WARNING
            + " No NtcCalPar found in the input config file! Using the default NTC parameters."
            + bcolors.ENDC
        )
    return NtcCalPar


def get_NfPar(metadata):
    # Read Nf parameters from metadata in the chip config.
    NfPar = {}
    if "NfASLDO" in metadata:
        NfPar["NfASLDO"] = metadata.get("NfASLDO")
    else:
        NfPar["NfASLDO"] = 1.264
        log.warning(
            bcolors.WARNING
            + " No NfASLDO found in the input config file! Using the default Nf parameter value 1.264."
            + bcolors.ENDC
        )
    if "NfDSLDO" in metadata:
        NfPar["NfDSLDO"] = metadata.get("NfDSLDO")
    else:
        NfPar["NfDSLDO"] = 1.264
        log.warning(
            bcolors.WARNING
            + " No NfASLDO found in the input config file! Using the default Nf parametervalue 1.264."
            + bcolors.ENDC
        )
    if "NfACB" in metadata:
        NfPar["NfACB"] = metadata.get("NfACB")
    else:
        NfPar["NfACB"] = 1.264
        log.warning(
            bcolors.WARNING
            + " No Nfacb found in the input config file! Using the default Nf parameter value 1.264."
            + bcolors.ENDC
        )

    return NfPar


def calculate_T(calculated_data, NtcCalPar, NfPar):
    # Calculate T External NTC
    Vntc = np.array(calculated_data["Vntc"]["Values"])
    Intc = np.array(calculated_data["Intc"]["Values"])

    Rntc = np.mean(Vntc / Intc)
    A = NtcCalPar[0]
    B = NtcCalPar[1]
    C = NtcCalPar[2]
    AR_TEMP_NTC = 1 / (A + B * np.log(Rntc) + C * ((np.log(Rntc)) ** 3)) - 273.15

    log.debug(f" T Ext NTC: {AR_TEMP_NTC} C")

    # Calculate T External External NTC
    AR_TEMP_EXT = np.mean(np.array(calculated_data["TExtExtNTC"]["Values"]))

    log.debug(f" T Ext Ext NTC: {AR_TEMP_EXT} C")

    # Calculate T MOS sensors
    Vmux14 = np.array(calculated_data["VMonSensAna"]["Values"])
    Vmux16 = np.array(calculated_data["VMonSensDig"]["Values"])
    Vmux18 = np.array(calculated_data["VMonSensAcb"]["Values"])

    def calc_temp_sens(Vmux, Nf):
        V_Bias0 = np.mean(Vmux[:16])
        V_Bias1 = np.mean(Vmux[-16:])
        q = 1.602e-19
        kB = 1.38064852e-23
        dV = V_Bias1 - V_Bias0
        return dV * q / (Nf * kB * np.log(15)) - 273.15

    AR_TEMP_ASLDO = calc_temp_sens(Vmux14, NfPar["NfASLDO"])
    AR_TEMP_DSLDO = calc_temp_sens(Vmux16, NfPar["NfDSLDO"])
    AR_TEMP_ACB = calc_temp_sens(Vmux18, NfPar["NfACB"])

    log.debug(f" T MonSensAna: {AR_TEMP_ASLDO} C")
    log.debug(f" T MonSensDig: {AR_TEMP_DSLDO} C")
    log.debug(f" T MonSensAcb: {AR_TEMP_ACB} C")

    return (
        AR_TEMP_NTC,
        AR_TEMP_EXT,
        AR_TEMP_ASLDO,
        AR_TEMP_DSLDO,
        AR_TEMP_ACB,
    )


def check_vdd_trim_saturation(vdd):
    """
    Look for vdd trim saturation by comparing minimum votage step-size to
    average step-size. If saturation occurs very early, this will not catch it.
    """
    dV_frac = 0.1  # arbitrarily chosen scale factor
    VDD_dV_list = np.diff(vdd)

    dV_mean = np.mean(VDD_dV_list[:10])  # Use first 10 trims to calculate avg
    min_stepsize = dV_frac * dV_mean

    trimSaturated = -1
    for i, dV in enumerate(VDD_dV_list):
        isSaturated = bool(dV < min_stepsize)
        if isSaturated:
            if i < len(VDD_dV_list) - 1 and VDD_dV_list[i + 1] > min_stepsize:
                isSaturated = False
                continue
            trimSaturated = i
            break

    return float(trimSaturated)


def plot_vdd_vs_trim(trim, vdd, vdd_name, output_name, chipname, fit_method):
    fig, ax1 = plt.subplots()
    ax1.plot(trim, vdd, "o", label=f"{vdd_name} vs trim")
    if fit_method == "root":
        p1, p0, _r1 = linear_fit(trim, vdd)
    else:
        p1, p0, _r1 = linear_fit_np(trim, vdd)
    ax1.axhline(y=1.2, color="r", linestyle="--", label=f"Nominal {vdd_name} value")
    x_line = np.linspace(trim[0], trim[-1], 100)
    ax1.plot(
        x_line,
        p1 * x_line + p0,
        "g-",
        alpha=0.5,
        label=f"Fitted line y = {p1:.3e} * x + {p0:.3e}",
    )
    ax1.set_title(f"{vdd_name} vs Trim Chip {chipname}")
    ax1.set_xlabel("Trim")
    ax1.set_ylabel(f"{vdd_name} (V)")
    ax1.legend()
    log.info(f" Saving {output_name}")
    fig.savefig(output_name)
    plt.close(fig)


## plot anything else against trim, no fit or target value
def plot_stuff_vs_trim(
    trim, stuff, stuff_name, output_name, chipname, unit="V", domain="A"
):
    fig, ax1 = plt.subplots()
    ax1.plot(trim, stuff, "o", label=f"{stuff_name} vs trim{domain}")
    ax1.set_title(f"{stuff_name} vs Trim{domain} Chip {chipname}")
    ax1.set_xlabel(f"Trim{domain}")
    ax1.set_ylabel(f"{stuff_name} ({unit})")
    ax1.legend()
    log.info(f" Saving {output_name}")
    fig.savefig(output_name)
    plt.close(fig)


def plot_bank_vddd(rosc, vdd, rosc_name, p1, p0, bank_name, chipname, output_dir):
    fig, ax1 = plt.subplots()
    x_line = np.linspace(vdd[0], vdd[-1], 100)
    for i, rosc_i in enumerate(rosc):
        ax1.plot(vdd, rosc_i, "o", markersize=1)
        ax1.plot(
            x_line,
            p1[i] * x_line + p0[i],
            alpha=0.5,
            label=f"{rosc_name[i]} ({p1[i]:.3e}, {p0[i]:.3e})",
        )
    ax1.set(
        title=f"ROSC {bank_name} vs VDD Chip {chipname}",
        xlabel="VDDD (V)",
        ylabel="ROSC (MHz)",
    )
    ax1.legend()
    plot_name = bank_name.replace(" ", "_")
    log.info(f" Saving {chipname}_ROSC_vs_VDDD_{plot_name}.png")
    fig.savefig(output_dir.joinpath(f"{chipname}_ROSC_vs_VDDD_{plot_name}.png"))
    plt.close(fig)


def plot_rosc_vs_vddd(rosc, vdd, chipname, output_dir, fit_method):
    p1_list = []
    p0_list = []
    maxres_list = []

    # Get SLOP and OFFSET
    for _i, rosc_i in enumerate(rosc):
        if fit_method == "root":
            p1, p0, linearity = linear_fit(vdd, rosc_i)
        elif fit_method == "numpy":
            p1, p0, linearity = linear_fit_np(vdd, rosc_i)
        else:
            msg = f"Fit method {fit_method} is not valid."
            raise ValueError(msg)

        maxres_list.append(linearity)
        p1_list.append(p1)
        p0_list.append(p0)

    # Define names
    bank_AB_name = [
        "CLK 0",
        "CLK 4",
        "Inv 0",
        "Inv 4",
        "NAND 0",
        "NAND 4",
        "NOR 0",
        "NOR 4",
    ]
    bank_B_FF_name = [
        "Scan D FF 0",
        "Scan D FF 0",
        "D FF 0",
        "D FF 0",
        "Neg Edge D FF 1",
        "Neg Edge D FF 1",
    ]
    bank_B_IVT_name = [
        "LVT Inv 0",
        "LVT Inv 4",
        "LVT 4-input NAND 0",
        "LVT 4-input NAND 4",
    ]
    bank_B_CAPA_name = [
        "CAPA0",
        "CAPA1",
        "CAPA2",
        "CAPA3",
        "CAPA4",
        "CAPA5",
        "CAPA6",
        "CAPA7",
    ]

    # Plot Bank A and Bank B
    plot_bank_vddd(
        rosc[:8],
        vdd,
        bank_AB_name,
        p1_list[:8],
        p0_list[:8],
        "Bank A",
        chipname,
        output_dir,
    )
    plot_bank_vddd(
        rosc[8:24:2],
        vdd,
        bank_AB_name,
        p1_list[8:24:2],
        p0_list[8:24:2],
        "Bank B left",
        chipname,
        output_dir,
    )
    plot_bank_vddd(
        rosc[9:24:2],
        vdd,
        bank_AB_name,
        p1_list[9:24:2],
        p0_list[9:24:2],
        "Bank B right",
        chipname,
        output_dir,
    )
    plot_bank_vddd(
        rosc[24:30],
        vdd,
        bank_B_FF_name,
        p1_list[24:30],
        p0_list[24:30],
        "Bank B FF",
        chipname,
        output_dir,
    )
    plot_bank_vddd(
        rosc[30:34],
        vdd,
        bank_B_IVT_name,
        p1_list[30:34],
        p0_list[30:34],
        "Bank B LVT",
        chipname,
        output_dir,
    )
    plot_bank_vddd(
        rosc[34:],
        vdd,
        bank_B_CAPA_name,
        p1_list[34:],
        p0_list[34:],
        "Bank B Inj-cap-loaded 4-input NAND 4",
        chipname,
        output_dir,
    )

    return p1_list, p0_list, maxres_list


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
    Performs the Analog Readback.

    It produces an output file with the calculated internal biases, temperature from the internal and external temperature sensor, and VDDA/VDDD vs Trim, including diagnostic plots with slope and offset.
    """
    test_type = Path(__file__).stem
    time_start = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    output_dir = base_output_dir.joinpath(test_type).joinpath(f"{time_start}")
    output_dir.mkdir(parents=True, exist_ok=False)

    log.setLevel(verbosity.value)
    log.addHandler(logging.FileHandler(f"{output_dir}/output.log"))

    # Turn off matplotlib DEBUG messages
    plt.set_loglevel(level="warning")
    # Turn off pytest DEBUG messages
    pil_logger = logging.getLogger("PIL")
    pil_logger.setLevel(logging.INFO)

    log.info("")
    log.info(" ===============================================")
    log.info(" \tPerforming Analog Readback analysis")
    log.info(" ===============================================")
    log.info("")

    allinputs = get_inputs(input_meas)

    alloutput = []
    timestamps = []

    alloutput_int_biases = []
    timestamps_int_biases = []

    for filename in sorted(allinputs):
        log.info("")
        log.info(f" Loading {filename}")
        meas_timestamp = get_time_stamp(filename)
        inputDFs = load_json(filename)
        log.debug(
            f" There are results from {len(inputDFs)} measuremnet(s) stored in this file"
        )

        chipnames = []
        results = {}
        data = {}
        int_biases = {}
        for inputDF in inputDFs:
            # Check file integrity
            checker = JsonChecker(inputDF, test_type)

            try:
                checker.check()
            except BaseException as exc:
                log.exception(exc)
                log.warning(
                    bcolors.WARNING
                    + " JsonChecker check not passed, skipping this input."
                    + bcolors.ENDC
                )
                continue
            else:
                log.debug(" JsonChecker check passed!")

            #  Get info
            qcframe = inputDF.get_results()
            metadata = qcframe.get_meta_data()

            qc_config = get_qc_config(
                qc_criteria_path, test_type, metadata.get("ModuleSN")
            )

            if input_layer == "Unknown":
                try:
                    layer = get_layer_from_sn(metadata.get("ModuleSN"))
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

            # Read chipname from input DF
            try:
                chipname = metadata.get("Name")
                chipnames.append(chipname)
                log.debug(f" Found chip name = {chipname} from chip config")
            except Exception:
                log.warning(
                    bcolors.WARNING
                    + "Chip name not found in input from {filename}, skipping."
                    + bcolors.ENDC
                )
                continue

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

            if institution == "":
                log.error(
                    bcolors.ERROR
                    + "No institution found. Please specify your testing site either in the measurement data or specify with the --site option. "
                    + bcolors.ENDC
                )
                return

            # Create an output DF for each chip
            if chipname not in data:
                data[chipname] = qcDataFrame()
                data[chipname].add_property(
                    "ANALYSIS_VERSION",
                    __version__,
                )
                try:
                    data[chipname].add_property(
                        "YARR_VERSION",
                        qcframe.get_properties().get("YARR_VERSION"),
                    )
                except Exception as e:
                    log.warning(
                        f"Unable to find YARR version! Require YARR >= v1.5.2. {e}"
                    )
                    data[chipname].add_property("YARR_VERSION", "")
                data[chipname].add_meta_data(
                    "MEASUREMENT_VERSION",
                    qcframe.get_properties().get(test_type + "_MEASUREMENT_VERSION"),
                )
                time_start = qcframe.get_meta_data()["TimeStart"]
                time_end = qcframe.get_meta_data()["TimeEnd"]
                duration = arrow.get(time_end) - arrow.get(time_start)

                data[chipname].add_property(
                    "MEASUREMENT_DATE",
                    arrow.get(time_start).isoformat(timespec="milliseconds"),
                )
                data[chipname].add_property(
                    "MEASUREMENT_DURATION", int(duration.total_seconds())
                )

                data[chipname].add_meta_data("QC_LAYER", layer)
                data[chipname].add_meta_data("INSTITUTION", institution)
                data[chipname]._meta_data.update(metadata)
                int_biases[chipname] = {}

            #   Calculate quanties
            # Vmux conversion is embedded.
            extractor = DataExtractor(inputDF, test_type)
            calculated_data = extractor.calculate()
            Vmux_map = getVmuxMap()
            Imux_map = getImuxMap()

            AR_values_names = []
            for imux in range(32):
                AR_values_names.append(Imux_map[imux])
            for vmux in range(40):
                AR_values_names.append(Vmux_map[vmux])

            tmpresults = {}
            if inputDF._subtestType == "AR_VMEAS":
                for key in calculated_data:
                    int_biases[chipname][key] = calculated_data[key]["Values"][0]
                AR_values = []
                NOT_MEASURED = -999
                for name in AR_values_names:
                    if name in int_biases[chipname]:
                        AR_values.append(round(int_biases[chipname][name], 7))
                        proddb_name = f"AR_{name.upper()}"
                        if proddb_name in qc_config:
                            (
                                _lower_unused,
                                _upper_unused,
                                precision,
                            ) = get_bounds_and_precision(
                                qc_config, proddb_name, get_layer(layer)
                            )
                            tmpresults.update(
                                {
                                    proddb_name: round(
                                        int_biases[chipname][name], precision
                                    )
                                }
                            )
                    else:
                        AR_values.append(NOT_MEASURED)

                tmpresults.update({"AR_NOMINAL_SETTINGS": AR_values})

            elif inputDF._subtestType == "AR_TEMP":
                chipname_str = next(iter(metadata.get("ChipConfigs")))
                NtcCalPar = get_NtcCalPar(
                    metadata["ChipConfigs"][chipname_str]["Parameter"]
                )
                NfPar = get_NfPar(metadata["ChipConfigs"][chipname_str]["Parameter"])
                (
                    AR_TEMP_NTC,
                    AR_TEMP_EXT,
                    AR_TEMP_ASLDO,
                    AR_TEMP_DSLDO,
                    AR_TEMP_ACB,
                ) = calculate_T(calculated_data, NtcCalPar, NfPar)
                # Add parameters for output file
                round_value = 3
                data[chipname].add_parameter("AR_TEMP_NTC", AR_TEMP_NTC, round_value)
                data[chipname].add_parameter("AR_TEMP_EXT", AR_TEMP_EXT, round_value)
                data[chipname].add_parameter(
                    "AR_TEMP_ASLDO", AR_TEMP_ASLDO, round_value
                )
                data[chipname].add_parameter(
                    "AR_TEMP_DSLDO", AR_TEMP_DSLDO, round_value
                )
                data[chipname].add_parameter("AR_TEMP_ACB", AR_TEMP_ACB, round_value)
                data[chipname].add_parameter(
                    "AR_TEMP_NF_ASLDO", NfPar["NfASLDO"], round_value
                )
                data[chipname].add_parameter(
                    "AR_TEMP_NF_DSLDO", NfPar["NfDSLDO"], round_value
                )
                data[chipname].add_parameter(
                    "AR_TEMP_NF_ACB", NfPar["NfACB"], round_value
                )
                data[chipname].add_parameter("AR_TEMP_POLY_TOP", EMPTY_VAL, round_value)
                data[chipname].add_parameter(
                    "AR_TEMP_POLY_BOTTOM", EMPTY_VAL, round_value
                )
                data[chipname].add_parameter("AR_TEMP_NF_TOP", EMPTY_VAL, round_value)
                data[chipname].add_parameter(
                    "AR_TEMP_NF_BOTTOM", EMPTY_VAL, round_value
                )
                # Load values to dictionary for QC analysis
                tmpresults.update({"ChipNTC_vs_ExtExt": AR_TEMP_NTC - AR_TEMP_EXT})

            elif inputDF._subtestType == "AR_VDD":
                vdda = calculated_data["VDDA"]["Values"].tolist()
                vddd = calculated_data["VDDD"]["Values"].tolist()
                trimA = calculated_data["SldoTrimA"]["Values"].tolist()
                trimD = calculated_data["SldoTrimD"]["Values"].tolist()
                output_name_vdda = output_dir.joinpath(f"{chipname}_VDDA_TRIM.png")
                output_name_vddd = output_dir.joinpath(f"{chipname}_VDDD_TRIM.png")

                # Plot VDDA/VDDD vs Trim
                plot_vdd_vs_trim(
                    trimA, vdda, "VDDA", output_name_vdda, chipname, fit_method.value
                )
                plot_vdd_vs_trim(
                    trimD, vddd, "VDDD", output_name_vddd, chipname, fit_method.value
                )

                # Check where vdd vs trim saturates. -1 if no saturation
                vddd_trimsat = check_vdd_trim_saturation(vddd)
                vdda_trimsat = check_vdd_trim_saturation(vdda)

                stuffs = ["IshuntA", "IshuntD", "IinA", "IinD", "VinA", "VinD"]
                stuff_dict = {}
                output_name_dict = {}

                try:
                    for stuff in stuffs:
                        stuff_dict[stuff] = calculated_data[stuff]["Values"].tolist()

                    ## plots stuff vs trim
                    for stuff in stuffs:
                        unit = "A" if stuff.startswith("I") else "V"
                        domain = "A" if stuff.endswith("A") else "D"
                        # Plot stuffA/D vs Trim
                        if stuff.endswith("A"):
                            output_name_dict[stuff] = output_dir.joinpath(
                                f"{chipname}_{stuff}_Trim{domain}.png"
                            )
                            plot_stuff_vs_trim(
                                trimA,
                                stuff_dict[stuff],
                                stuff,
                                output_name_dict[stuff],
                                chipname,
                                unit,
                                domain,
                            )
                        elif stuff.endswith("D"):
                            output_name_dict[stuff] = output_dir.joinpath(
                                f"{chipname}_{stuff}_Trim{domain}.png"
                            )
                            plot_stuff_vs_trim(
                                trimD,
                                stuff_dict[stuff],
                                stuff,
                                output_name_dict[stuff],
                                chipname,
                                unit,
                                domain,
                            )
                except Exception:
                    log.warning(
                        "No Ishunt measurement found - data taken with module-qc-tools < v2.2.7 ?"
                    )

                # Plot ROSC vs VDDD
                rosc_list = [
                    calculated_data[f"ROSC{i}"]["Values"].tolist() for i in range(42)
                ]
                p1_list, p0_list, maxres_list = plot_rosc_vs_vddd(
                    rosc_list,
                    vddd,
                    chipname,
                    output_dir,
                    fit_method.value,
                )

                # Load values to dictionary for QC analysis
                tmpresults.update(
                    {"AR_VDDA_VS_TRIM": [round(elem, 3) for elem in vdda]}
                )
                tmpresults.update(
                    {"AR_VDDD_VS_TRIM": [round(elem, 3) for elem in vddd]}
                )
                tmpresults.update({"AR_VDDA_TRIM": vdda})
                tmpresults.update({"AR_VDDD_TRIM": vddd})
                tmpresults.update({"AR_ROSC_SLOPE": p1_list})
                tmpresults.update({"AR_ROSC_OFFSET": p0_list})
                tmpresults.update({"AR_ROSC_MAX_RESIDUAL": maxres_list})
                tmpresults.update({"AR_VDDD_SATURATION": vddd_trimsat})
                tmpresults.update({"AR_VDDA_SATURATION": vdda_trimsat})

            elif inputDF._subtestType == "AR_REGISTER":
                tmpresults.update(
                    {"AR_IREF_TRIM": int(calculated_data["IrefTrimSense"]["Values"][0])}
                )

            else:
                log.warning(
                    bcolors.WARNING
                    + f"{filename}.json does not have any required subtestType. Skipping."
                    + bcolors.ENDC
                )
                continue

            if results.get(chipname):
                results[chipname].update(tmpresults)
            else:
                results[chipname] = tmpresults

        log.debug(
            f" There are results from {len(chipnames)} chip(s) stored in this file"
        )

        #  Output a json file
        for key, df in data.items():
            outputDF = outputDataFrame()
            outputDF.set_test_type(test_type)

            # Perform QC analysis
            chiplog = logging.FileHandler(f"{output_dir}/{chipname}.log")
            log.addHandler(chiplog)
            passes_qc, summary, rounded_results = perform_qc_analysis(
                test_type,
                qc_config,
                layer,
                results.get(key),
            )

            for result, value in rounded_results.items():
                if "_vs_" in result:
                    continue  # Skip adding temperature differences
                df.add_parameter(result, value)
            outputDF.set_results(df)
            print_result_summary(summary, test_type, output_dir, key)
            if passes_qc == -1:
                log.error(
                    bcolors.ERROR
                    + f" QC analysis for {key} was NOT successful. Please fix and re-run. Continuing to next chip.."
                    + bcolors.ENDC
                )
                continue
            log.info("")
            if passes_qc:
                log.info(
                    f" Chip {key} passes QC? "
                    + bcolors.OKGREEN
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            else:
                log.info(
                    f" Chip {key} passes QC? "
                    + bcolors.BADRED
                    + f"{passes_qc}"
                    + bcolors.ENDC
                )
            log.info("")
            log.removeHandler(chiplog)
            chiplog.close()

            outputDF.set_pass_flag(passes_qc)

            if permodule:
                alloutput += [outputDF.to_dict(True)]
                timestamps += [meas_timestamp]
            else:
                outfile = output_dir.joinpath(f"{key}.json")
                log.info(f" Saving output of analysis to: {outfile}")
                save_dict_list(outfile, [outputDF.to_dict(True)])

        if verbosity.value == "DEBUG":
            # Save an output file for only internal biases
            for key, int_bias in int_biases.items():
                if permodule:
                    alloutput_int_biases += [int_bias]
                    timestamps_int_biases += [meas_timestamp]
                else:
                    outfile = output_dir.joinpath(f"{key}_internal_biases.json")
                    log.info(f" Saving DEBUG file with internal biases to: {outfile}")
                    outfile.write_text(json.dumps([int_bias], cls=MyEncoder, indent=4))
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
        if verbosity.value == "DEBUG":
            # Save an output file for only internal biases
            dfs = np.array(alloutput_int_biases)
            tss = np.array(timestamps_int_biases)
            for x in np.unique(tss):
                outfile = output_dir.joinpath(f"internal_biases_{x}.json")
                log.info(f" Saving DEBUG file with internal biases to: {outfile}")
                save_dict_list(
                    outfile,
                    dfs[tss == x].tolist(),
                )


if __name__ == "__main__":
    typer.run(main)
