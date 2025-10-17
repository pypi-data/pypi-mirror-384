from __future__ import annotations

import json
import logging
from functools import partial

import arrow
import matplotlib.pyplot as plt
import numpy as np
from module_qc_data_tools import (
    get_layer_from_sn,
    get_nominal_current,
    outputDataFrame,
    qcDataFrame,
)
from module_qc_data_tools.utils import (
    get_chip_type_from_serial_number,
)
from module_qc_tools import data as mqt_data
from scipy.optimize import curve_fit

from module_qc_analysis_tools import __version__
from module_qc_analysis_tools.utils.analysis import (
    check_layer,
    get_layer,
    get_n_chips,
    get_nominal_kShuntA,
    get_nominal_kShuntD,
    get_nominal_RextA,
    get_nominal_RextD,
    get_nominal_Voffs,
    perform_qc_analysis,
)
from module_qc_analysis_tools.utils.classification import (
    format_coreCol_input,
)
from module_qc_analysis_tools.utils.misc import (
    DataExtractor,
    JsonChecker,
    bcolors,
    get_BOMCode_from_metadata,
    get_cutFile_suffix,
    get_qc_config,
    linear_fit,
    linear_fit_np,
)


def linear_func(x, a, b):
    """define a linear fit function, that is used to fit the IshuntA/D
    points to find the min Iin to pass the IshuntA/D QC criteria"""
    return a * x + b


TEST_TYPE = "SLDO"


log = logging.getLogger(f"analysis.{TEST_TYPE}")


def analyze(
    input_jsons,
    site="",
    input_layer="Unknown",
    fit_method="numpy",
    qc_criteria_path=None,
    nChipsInput=0,
    lp_enable=False,
):
    func = partial(
        analyze_chip,
        site=site,
        input_layer=input_layer,
        fit_method=fit_method,
        qc_criteria_path=qc_criteria_path,
        nChipsInput=nChipsInput,
        lp_enable=lp_enable,
    )

    results = []
    for input_json in input_jsons:
        if isinstance(input_json, list):
            for chip in input_json:
                result = func(chip)
                if result:
                    results.append(result)
        else:
            result = func(input_json)
            if result:
                results.append(result)

    return zip(*results)


def analyze_chip(
    chip,
    site="",
    input_layer="Unknown",
    fit_method="numpy",
    qc_criteria_path=None,
    nChipsInput=0,
    lp_enable=False,
):
    inputDF = outputDataFrame(_dict=chip)

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
        return None

    log.debug(" JsonChecker check passed!")

    #   Get info
    qcframe = inputDF.get_results()
    metadata = qcframe.get_meta_data()

    if input_layer == "Unknown":
        try:
            layer = get_layer_from_sn(metadata.get("ModuleSN"))
        except Exception:
            log.error(bcolors.WARNING + " Something went wrong." + bcolors.ENDC)
    else:
        module_sn = metadata.get("ModuleSN")
        log.warning(
            bcolors.WARNING
            + f" Overwriting default layer config {get_layer_from_sn(module_sn)} with manual input  {input_layer}!"
            + bcolors.ENDC
        )
        layer = input_layer
    check_layer(layer)

    try:
        chip_type = get_chip_type_from_serial_number(metadata.get("ModuleSN"))
    except Exception:
        log.error(
            bcolors.WARNING + " Couldn't get chip type from module SN" + bcolors.ENDC
        )
        return None

    BOMCode = get_BOMCode_from_metadata(metadata, layer)

    qc_config = get_qc_config(
        qc_criteria_path, TEST_TYPE, metadata.get("ModuleSN"), BOMCode
    )

    # SLDO parameters
    kShuntA = get_nominal_kShuntA(chip_type)
    kShuntD = get_nominal_kShuntD(chip_type)
    RextA = get_nominal_RextA(BOMCode)
    RextD = get_nominal_RextD(BOMCode)
    if nChipsInput == 0:
        nChips = get_n_chips(layer)
    elif nChips != get_n_chips(layer):
        log.warning(
            bcolors.WARNING
            + f" Overwriting default number of chips ({get_n_chips(layer)}) with manual input       ({nChipsInput})!"
            + bcolors.ENDC
        )
        nChips = nChipsInput

    try:
        chipname = metadata.get("Name")
        log.debug(f" Found chip name = {chipname} from chip config")
    except Exception:
        log.error(
            bcolors.ERROR
            + f" Chip name not found in input from {chipname}, skipping."
            + bcolors.ENDC
        )
        return None

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
            + "No institution found. Please specify your testing site either in the measurement     data or specify with the --site option. "
            + bcolors.ENDC
        )
        return None

    R_eff = 1.0 / ((kShuntA / RextA) + (kShuntD / RextD)) / nChips

    Vofs = get_nominal_Voffs(layer, lp_enable)

    p = np.poly1d([R_eff, Vofs])
    p1 = np.poly1d([R_eff, 0])

    # calculate quanties
    extractor = DataExtractor(inputDF, TEST_TYPE)
    calculated_data = extractor.calculate()

    passes_qc = True

    # Plot parameters
    Iint_max = (
        max(
            *(calculated_data["Iref"]["Values"] * 100000),
            *(calculated_data["IcoreD"]["Values"]),
            *(calculated_data["IcoreA"]["Values"]),
            *(calculated_data["IshuntD"]["Values"]),
            *(calculated_data["IshuntA"]["Values"]),
            *(calculated_data["IinD"]["Values"]),
            *(calculated_data["IinA"]["Values"]),
        )
        + 0.5
    )
    I_max = max(calculated_data["Current"]["Values"]) + 0.5
    I_min = min(calculated_data["Current"]["Values"]) - 0.5
    V_max = (
        max(
            *(calculated_data["VrefOVP"]["Values"]),
            *(calculated_data["Vofs"]["Values"]),
            *(calculated_data["VDDD"]["Values"]),
            *(calculated_data["VDDA"]["Values"]),
            *(calculated_data["VinD"]["Values"]),
            *(calculated_data["VinA"]["Values"]),
        )
        + 2.0
    )
    T_min = min(0.0, *(calculated_data["Temperature"]["Values"]))
    T_max = max(calculated_data["Temperature"]["Values"]) + 1.0

    # set common x axis range for all plots
    x_min = 4.5
    x_max = I_max

    # Internal voltages visualization

    figs = []

    fig1, ax1 = plt.subplots()
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["VinA"]["Values"],
        marker="o",
        markersize=4,
        label="VinA",
        color="tab:red",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["VinD"]["Values"],
        marker="o",
        markersize=4,
        label="VinD",
        color="tab:red",
        linestyle="--",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["VDDA"]["Values"],
        marker="o",
        markersize=4,
        label="VDDA",
        color="tab:blue",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["VDDD"]["Values"],
        marker="o",
        markersize=4,
        label="VDDD",
        color="tab:blue",
        linestyle="--",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["Vofs"]["Values"],
        marker="o",
        markersize=4,
        label="Vofs",
        color="tab:orange",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["VrefOVP"]["Values"],
        marker="o",
        markersize=4,
        label="VrefOVP",
        color="tab:cyan",
    )

    xp = np.linspace(I_min, I_max, 1000)
    ax1.plot(
        xp,
        p(xp),
        label=f"V = {R_eff:.3f} I + {Vofs:.2f}",
        color="tab:brown",
        linestyle="dotted",
    )
    ax1.set_xlabel("I [A]")
    ax1.set_ylabel("V [V]")
    plt.title(f"VI curve for chip: {chipname}")
    plt.xlim(x_min, x_max)
    ax1.set_ylim(0.0, V_max)
    ax1.legend(loc="upper left", framealpha=0)
    plt.grid()

    ax2 = ax1.twinx()
    ax2.plot(
        calculated_data["Current"]["Values"],
        calculated_data["Temperature"]["Values"],
        marker="^",
        markersize=4,
        color="tab:green",
        label="Temperature (NTC)",
        linestyle="-.",
    )
    ax2.set_ylabel("T [C]")
    ax2.set_ylim(T_min, T_max)
    ax2.legend(loc="upper right", framealpha=0)

    fig1.tight_layout()

    figs.append(fig1)

    # safe intersection points to add them below to data
    intersections = []
    slopes = []
    offsets = []
    chi2 = []
    linestyles = []

    # x and y data for analog and digital
    # flip the arrays because SLDO measurement is taken from high to low current
    x = np.flip(np.array(calculated_data["Current"]["Values"]))
    y_digital = np.flip(np.array(calculated_data["IshuntD"]["Values"]))
    y_analog = np.flip(np.array(calculated_data["IshuntA"]["Values"]))

    # minimal I shunt to pass QC from cut file
    min_I_shunt_cut_digital = qc_config["SLDO_ISHUNTD"][get_layer(layer)]["sel"][0]
    min_I_shunt_cut_analog = qc_config["SLDO_ISHUNTA"][get_layer(layer)]["sel"][0]

    # minimal I shunt value that is trustable for the fit, here it is called threshold from which on data is taken into account
    min_I_shunt_trustable = 0.05

    # add x value range beyond the scope of the data points

    for min_I_shunt_cut, y in zip(
        [min_I_shunt_cut_digital, min_I_shunt_cut_analog], [y_digital, y_analog]
    ):
        # filter over minimal trustable I shunt values, y_ substitute
        over_threshold = np.where(y > min_I_shunt_trustable)[0]
        if min_I_shunt_cut == min_I_shunt_cut_digital:
            linestyles.append("--")
        else:
            linestyles.append("-")
        if len(over_threshold) <= 3:
            log.error(
                bcolors.ERROR
                + "Too few data point over minimal trustable I shunt. "
                + bcolors.ENDC
            )
            intersections.append(-999)  # indicate, that fit kinda went wrong
            chi2.append(-999)
            slopes.append(-999)
            offsets.append(-999)
        else:
            # only fit first 4 points
            over_threshold_y_limited = y[over_threshold][:4]
            over_threshold_x_limited = x[over_threshold][:4]
            # getting fit parameters, curve_fit also return covariance matrix thus only take first element which is slope and offset
            popt = curve_fit(
                linear_func, over_threshold_x_limited, over_threshold_y_limited
            )[0]

            intersec = (min_I_shunt_cut - popt[1]) / popt[0]
            intersections.append(intersec)

            slopes.append(popt[0])
            offsets.append(popt[1])
            # calculate the chi-square
            residuals = over_threshold_y_limited - linear_func(
                over_threshold_x_limited, *popt
            )
            chi_square = np.sum(
                (residuals**2) / linear_func(over_threshold_x_limited, *popt)
            )

            chi2.append(chi_square)

    # Internal currents visualization
    x_values = np.linspace(-1, 10, 500)
    fig2, ax1 = plt.subplots()
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["IinA"]["Values"],
        marker="o",
        markersize=4,
        label="IinA",
        color="tab:red",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["IinD"]["Values"],
        marker="o",
        markersize=4,
        label="IinD",
        color="tab:red",
        linestyle="--",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["Iref"]["Values"] * 100000,
        marker="o",
        markersize=4,
        label="Iref*100k",
        color="tab:cyan",
    )
    ax1.plot(
        x_values,
        linear_func(x_values, slopes[0], offsets[0]),
        color="tab:blue",
        linestyle=linestyles[0],
        linewidth=0.8,
    )
    ax1.plot(
        x_values,
        linear_func(x_values, slopes[1], offsets[1]),
        color="tab:blue",
        linestyle=linestyles[1],
        linewidth=0.8,
    )
    ax1.plot(
        [intersections[0], intersections[0]],
        [0, 0.8],
        color="g",
        linestyle="--",
        label=f"min Iin passing QC = {intersections[0]:.2f} A",
    )
    ax1.plot(
        [intersections[1], intersections[1]],
        [0, 0.8],
        color="b",
        linestyle="--",
        label=f"min Iin passing QC = {intersections[1]:.2f} A",
    )
    ax1.axhline(
        y=min_I_shunt_cut_digital, color="g", linestyle="--", label="min IshuntD QC_cut"
    )
    ax1.annotate(
        f"{min_I_shunt_cut_digital}",
        xy=(1, min_I_shunt_cut_digital),
        xytext=(-393, 0),
        xycoords=("axes fraction", "data"),
        textcoords="offset points",
        fontsize=8,
    )
    ax1.axhline(
        y=min_I_shunt_cut_analog, color="b", linestyle="--", label="min IshuntA QC_cut"
    )
    ax1.annotate(
        f"{min_I_shunt_cut_analog}",
        xy=(1, min_I_shunt_cut_digital),
        xytext=(-393, -18),
        xycoords=("axes fraction", "data"),
        textcoords="offset points",
        fontsize=8,
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["IshuntA"]["Values"],
        marker="o",
        markersize=4,
        label="IshuntA",
        color="tab:blue",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["IshuntD"]["Values"],
        marker="o",
        markersize=4,
        label="IshuntD",
        color="tab:blue",
        linestyle="--",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["IcoreA"]["Values"],
        marker="o",
        markersize=4,
        label="IcoreA",
        color="tab:orange",
    )
    ax1.plot(
        calculated_data["Current"]["Values"],
        calculated_data["IcoreD"]["Values"],
        marker="o",
        markersize=4,
        label="IcoreD",
        color="tab:orange",
        linestyle="--",
    )
    ax1.set_xlabel("I [A]")
    ax1.set_ylabel("I [A]")
    plt.title(f"Currents for chip: {chipname}")

    plt.xlim(x_min, x_max)
    plt.ylim(0.0, Iint_max)
    ax1.legend(loc="upper left", framealpha=0)
    plt.grid()

    ax2 = ax1.twinx()
    ax2.plot(
        calculated_data["Current"]["Values"],
        calculated_data["Temperature"]["Values"],
        marker="^",
        markersize=4,
        color="tab:green",
        label="Temperature (NTC)",
        linestyle="-.",
    )
    ax2.set_ylabel("T [C]")
    ax2.set_ylim(T_min, T_max)
    ax2.legend(loc="upper right", bbox_to_anchor=(1, 0.9), framealpha=0)

    fig2.tight_layout()

    figs.append(fig2)

    # SLDO fit
    VinAvg = (
        calculated_data["VinA"]["Values"] + calculated_data["VinD"]["Values"]
    ) / 2.0
    if fit_method.value == "root":
        slope, offset, _r1 = linear_fit(calculated_data["Current"]["Values"], VinAvg)
    else:
        slope, offset, _r1 = linear_fit_np(calculated_data["Current"]["Values"], VinAvg)
    # Residual analysis
    # for the VinA/VinD residuals, only used in plot, remove data points where communication failed (VinA/VinD=0)
    ignore_points_with_lostcom = calculated_data["VinA"]["Values"] != 0
    residual_VinA = (
        p1(calculated_data["Current"]["Values"][ignore_points_with_lostcom])
        - (
            calculated_data["VinA"]["Values"][ignore_points_with_lostcom]
            - calculated_data["Vofs"]["Values"][ignore_points_with_lostcom]
        )
    ) * 1000

    residual_VinD = (
        p1(calculated_data["Current"]["Values"][ignore_points_with_lostcom])
        - (
            calculated_data["VinD"]["Values"][ignore_points_with_lostcom]
            - calculated_data["Vofs"]["Values"][ignore_points_with_lostcom]
        )
    ) * 1000
    residual_VinA_nomVofs = (
        p(calculated_data["Current"]["Values"][ignore_points_with_lostcom])
        - calculated_data["VinA"]["Values"][ignore_points_with_lostcom]
    ) * 1000
    residual_VinD_nomVofs = (
        p(calculated_data["Current"]["Values"][ignore_points_with_lostcom])
        - calculated_data["VinD"]["Values"][ignore_points_with_lostcom]
    ) * 1000

    residual_Vin = p1(calculated_data["Current"]["Values"]) - (
        VinAvg - calculated_data["Vofs"]["Values"]
    )
    residual_Vofs = (
        Vofs - calculated_data["Vofs"]["Values"][ignore_points_with_lostcom]
    ) * 1000
    res_max = (
        max(
            *(residual_VinA_nomVofs),
            *(residual_VinD_nomVofs),
            *(residual_VinA),
            *(residual_VinD),
            *(residual_Vofs),
        )
        + 20
    )

    res_min = (
        min(
            *(residual_VinA_nomVofs),
            *(residual_VinD_nomVofs),
            *(residual_VinA),
            *(residual_VinD),
            *(residual_Vofs),
        )
        - 10
    )

    fig3, ax1 = plt.subplots()
    ax1.plot(
        calculated_data["Current"]["Values"][ignore_points_with_lostcom],
        residual_VinA_nomVofs,
        marker="o",
        markersize=4,
        label=f"{R_eff:.3f}I+{Vofs:.2f}-VinA",
        color="tab:red",
    )
    ax1.plot(
        calculated_data["Current"]["Values"][ignore_points_with_lostcom],
        residual_VinD_nomVofs,
        marker="o",
        markersize=4,
        label=f"{R_eff:.3f}I+{Vofs:.2f}-VinD",
        color="tab:red",
        linestyle="--",
    )
    ax1.plot(
        calculated_data["Current"]["Values"][ignore_points_with_lostcom],
        residual_VinA,
        marker="o",
        markersize=4,
        label=f"{R_eff:.3f}I+Vofs-VinA",
        color="tab:blue",
    )
    ax1.plot(
        calculated_data["Current"]["Values"][ignore_points_with_lostcom],
        residual_VinD,
        marker="o",
        markersize=4,
        label=f"{R_eff:.3f}I+Vofs-VinD",
        color="tab:blue",
        linestyle="--",
    )
    ax1.plot(
        calculated_data["Current"]["Values"][ignore_points_with_lostcom],
        residual_Vofs,
        marker="o",
        markersize=4,
        label=f"{Vofs}-Vofs",
        color="tab:orange",
    )
    ax1.set_xlabel("I [A]")
    ax1.set_ylabel("V [mV]")
    plt.title(f"VI curve for chip: {chipname}")
    plt.xlim(x_min, x_max)
    plt.ylim(res_min, res_max)
    ax1.legend(loc="upper right", framealpha=0)
    plt.grid()
    fig3.tight_layout()

    figs.append(fig3)

    # Find point measured closest to nominal input current
    meas_config = json.loads((mqt_data / "configs" / "meas_config.json").read_text())
    BOM_type = get_cutFile_suffix(BOMCode)
    sldo_nom_input_current = get_nominal_current(
        meas_config, layer, chip_type, BOM_type, nChips
    )
    log.debug(
        f"Retrieved nominal current from default measurement config to be: {sldo_nom_input_current}"
    )
    idx = (
        np.abs(calculated_data["Current"]["Values"] - sldo_nom_input_current)
    ).argmin()
    log.debug(
        f" Closest current measured to nominal is: {calculated_data['Current']['Values'][idx]}"
    )

    # Calculate values for QC analysis and output file
    SLDO_LINEARITY = np.sqrt(np.sum((np.array(residual_Vin)) ** 2) / len(residual_Vin))
    SLDO_VINA_VIND = (
        calculated_data["VinA"]["Values"][idx] - calculated_data["VinD"]["Values"][idx]
    )
    SLDO_VDDA = calculated_data["VDDA"]["Values"][idx]
    SLDO_VDDD = calculated_data["VDDD"]["Values"][idx]
    SLDO_VINA = calculated_data["VinA"]["Values"][idx]
    SLDO_VIND = calculated_data["VinD"]["Values"][idx]
    SLDO_VOFFS = calculated_data["Vofs"]["Values"][idx]
    SLDO_IINA = calculated_data["IinA"]["Values"][idx]
    SLDO_IIND = calculated_data["IinD"]["Values"][idx]
    SLDO_IREF = calculated_data["Iref"]["Values"][idx] * 1e6
    SLDO_ISHUNTA = calculated_data["IshuntA"]["Values"][idx]
    SLDO_ISHUNTD = calculated_data["IshuntD"]["Values"][idx]

    # Get number of disabled core columns from the metadata
    _, SLDO_CORE_COL_DISABLED = format_coreCol_input(
        metadata.get("ChipConfigs"), chip_type, [0]
    )

    # Load values to dictionary for QC analysis
    results = {}
    results.update({"SLDO_LINEARITY": SLDO_LINEARITY})
    results.update({"SLDO_VINA_VIND": SLDO_VINA_VIND})
    results.update({"SLDO_VDDA": SLDO_VDDA})
    results.update({"SLDO_VDDD": SLDO_VDDD})
    results.update({"SLDO_VINA": SLDO_VINA})
    results.update({"SLDO_VIND": SLDO_VIND})
    results.update({"SLDO_VOFFS": SLDO_VOFFS})
    results.update({"SLDO_IINA": SLDO_IINA})
    results.update({"SLDO_IIND": SLDO_IIND})
    results.update({"SLDO_IREF": SLDO_IREF})
    results.update({"SLDO_ISHUNTA": SLDO_ISHUNTA})
    results.update({"SLDO_ISHUNTD": SLDO_ISHUNTD})
    results.update({"SLDO_CORE_COL_DISABLED": SLDO_CORE_COL_DISABLED})

    # Perform QC analysis
    passes_qc, summary, rounded_results = perform_qc_analysis(
        TEST_TYPE, qc_config, layer, results
    )

    #  Output a json file
    outputDF = outputDataFrame()
    outputDF.set_test_type(TEST_TYPE)
    data = qcDataFrame()
    data._meta_data.update(metadata)
    data.add_property(
        "ANALYSIS_VERSION",
        __version__,
    )
    try:
        data.add_property(
            "YARR_VERSION",
            qcframe.get_properties().get("YARR_VERSION"),
        )
    except Exception as e:
        log.warning(f"Unable to find YARR version! Require YARR >= v1.5.2. {e}")
        data.add_property("YARR_VERSION", "")
    data.add_meta_data(
        "MEASUREMENT_VERSION",
        qcframe.get_properties().get(TEST_TYPE + "_MEASUREMENT_VERSION"),
    )
    time_start = qcframe.get_meta_data()["TimeStart"]
    time_end = qcframe.get_meta_data()["TimeEnd"]
    duration = arrow.get(time_end) - arrow.get(time_start)

    data.add_property(
        "MEASUREMENT_DATE",
        arrow.get(time_start).isoformat(timespec="milliseconds"),
    )
    data.add_property("MEASUREMENT_DURATION", int(duration.total_seconds()))

    data.add_meta_data("QC_LAYER", layer)
    data.add_meta_data("INSTITUTION", institution)
    # Add all values used in QC selection to output file
    for key, value in rounded_results.items():
        data.add_parameter(key, value)

    # Calculate additional values for output file only
    analog_overhead = calculated_data["IshuntA"]["Values"][idx] / (
        calculated_data["IinA"]["Values"][idx]
        - calculated_data["IshuntA"]["Values"][idx]
    )
    digital_overhead = calculated_data["IshuntD"]["Values"][idx] / (
        calculated_data["IinD"]["Values"][idx]
        - calculated_data["IshuntD"]["Values"][idx]
    )
    data.add_parameter("SLDO_ANALOG_OVERHEAD", analog_overhead, 3)
    data.add_parameter("SLDO_DIGITAL_OVERHEAD", digital_overhead, 3)
    data.add_parameter("SLDO_VI_SLOPE", slope, 3)
    data.add_parameter("SLDO_VI_OFFSET", offset, 3)
    data.add_parameter("SLDO_NOM_INPUT_CURRENT", sldo_nom_input_current, 3)
    data.add_parameter("SLDO_D_MIN_IIN", intersections[0], 3)
    data.add_parameter("SLDO_A_MIN_IIN", intersections[1], 3)
    data.add_parameter("SLDO_D_SLOPE", slopes[0], 3)
    data.add_parameter("SLDO_A_SLOPE", slopes[1], 3)
    data.add_parameter("SLDO_D_OFFSET", offsets[0], 3)
    data.add_parameter("SLDO_A_OFFSET", offsets[1], 3)
    data.add_parameter("SLDO_D_CHI2", chi2[0], 3)
    data.add_parameter("SLDO_A_CHI2", chi2[1], 3)
    outputDF.set_results(data)
    outputDF.set_pass_flag(passes_qc)

    return chipname, outputDF.to_dict(True), passes_qc, summary, figs
