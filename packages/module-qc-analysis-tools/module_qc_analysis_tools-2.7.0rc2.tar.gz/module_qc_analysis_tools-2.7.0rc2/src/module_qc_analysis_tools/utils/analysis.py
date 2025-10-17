#!/usr/bin/env python3
from __future__ import annotations

import copy
import logging
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from module_qc_data_tools import get_sensor_type_from_layer
from module_qc_database_tools.utils import get_nominal_Rext

from module_qc_analysis_tools.utils.misc import (
    bcolors,
)

log = logging.getLogger("analysis")


def format_text():
    return " {:^30}: {:^20}: {:^20}: {:^5}"


def print_output_pass(key, results, lower_bound, upper_bound):
    txt = format_text()
    log.info(
        bcolors.OKGREEN
        + txt.format(
            key,
            results,
            f"[{lower_bound}, {upper_bound}]",
            "PASS",
        )
        + bcolors.ENDC
    )


def print_output_fail(key, results, lower_bound, upper_bound):
    txt = format_text()
    log.info(
        bcolors.BADRED
        + txt.format(
            key,
            results,
            f"[{lower_bound}, {upper_bound}]",
            "FAIL",
        )
        + bcolors.ENDC
    )


def print_output_neutral(key, results, lower_bound=None, upper_bound=None):
    if "IV_ARRAY" in key:
        return
    if not lower_bound and not upper_bound:
        txt = format_text()

        if isinstance(results, list):
            with np.printoptions(threshold=4, edgeitems=1):
                results_str = str(np.round(np.array(results), 2))
        elif isinstance(results, float):
            results_str = str(np.round(results, 2).item())
        else:
            results_str = results

        log.info(
            bcolors.WARNING + txt.format(key, results_str, "-", "-") + bcolors.ENDC
        )
    else:
        txt = format_text()
        log.info(
            bcolors.WARNING
            + txt.format(
                key,
                results,
                f"[{lower_bound}, {upper_bound}]",
                "FAIL",
            )
            + bcolors.ENDC
        )


def get_layer(layer):
    layers = {"L0": "LZero", "L1": "LOne", "L2": "LTwo"}
    return layers.get(layer)


def check_layer(layer):
    possible_layers = ["L0", "L1", "L2"]
    if layer not in possible_layers:
        msg = f"[red] Layer '{layer}' not recognized or not provided. Provide the layer with the --layer [L0, L1, or L2] option.[/]"
        raise ValueError(msg)


def get_n_chips(layer):
    check_layer(layer)
    chips_per_layer = {"L0": 3, "L1": 4, "L2": 4}
    return chips_per_layer.get(layer)


# # # begin IV stuff
# # # numbers from specification documents:
# # # - 3D sensor QA/QC document: AT2-IP-QC-0003
# # # - Planar sensor QC/QC document: AT2-IP-QC-0004
# # # - Module spec: AT2-IP-ES-0009


def coth(x):
    intype = type(x)
    if intype in [float, int] and x == 0:
        return np.nan
    if intype in [list, np.ndarray]:
        result = [np.cosh(item) / np.sinh(item) if item != 0 else np.nan for item in x]
        return result if intype is list else np.array(result)
    return np.cosh(x) / np.sinh(x)


def normalise_current(current, orig_temp, target_temp=20):
    """
    Function to convert leakage current measured at one temperature (deg C) to leakage current at a target temperature (deg C).
    Note that this function only scales the bulk current and does not take any surface or edge effect into account. Thus in order to maintain accuracy, the input temperature should be similar to the target temperature.

    current: can be a number or a list
    orig_temp: can be a number or a list
    """

    if current is None:
        msg = "Must specify current as a number or list of numbers."
        raise ValueError(msg)

    if orig_temp is None:
        msg = "Must specify original temperature as a number or list of numbers."
        raise ValueError(msg)

    intype = type(current)

    current = np.array(current)
    orig_temp = np.array(orig_temp)

    if current.size >= 1 and orig_temp.size >= 1:
        if current.size == 1 or current.size != orig_temp.size:
            orig_temp = np.mean(orig_temp)

        T1 = orig_temp + 273.15  ## measurement temperature
        T2 = target_temp + 273.15  ## temperature to be normalised to

        Eg0 = 1.17  ## eV, Eg(0K)
        S = 1.49  ## parameter, unitless
        Eph = 25.5e-3  ## eV, average phonon energy
        kboltzmann = 8.617333262e-05  # in eV/K

        ## eV, Silicon bandgap energy dependence on T, O'Donnel and Chen
        Eg = Eg0 - S * Eph * (np.array(coth(Eph / (2.0 * kboltzmann * T1))) - 1)
        # Eg = 1.124 ##eV, PhD thesis

        # if current is an np.array with size 1, it becomes a 'numpy.float64' here
        current = (
            current
            * ((T2 / T1) ** 2)
            * np.exp(-(Eg / (2 * kboltzmann)) * (1 / T2 - 1 / T1))
        )
        if intype is list:
            return current.tolist()
        if intype is float and current.size == 1:
            return float(current)
        return current

    log.warning(bcolors.WARNING + " Current cannot be normalised!" + bcolors.ENDC)
    if intype is list:
        return current.tolist()
    if intype is float and current.size == 1:
        return float(current)
    return current


def module_sensor_area(layer):
    """
    Function to return sensor area in a module (cm^2) depending on the layer
    """
    sensor_type = get_sensor_type_from_layer(layer)
    area = sensor_tile_area(sensor_type)
    if "3D" in sensor_type:
        area = 3 * area
    return area


def sensor_tile_area(sensor_type):
    """
    Function to return sensor tile area (cm^2) depending on the sensor type
    """

    if "3D" in sensor_type:
        sensor_type = "3D"
    area = {
        "3D": 4.25,
        "L1_INNER_PIXEL_QUAD_SENSOR_TILE": 15.76,
        "OUTER_PIXEL_QUAD_SENSOR_TILE": 15.92,
    }
    try:
        return area[sensor_type]
    except Exception as e:
        log.error(e)
        return None


def depletion_voltage_threshold(sensor_type):
    """
    Function to return the min depletion voltage (V) depending on the sensor type, same for sensor tile, bare module and module
    """
    ## thresholds AT2-IP-ES-0009 (module), AT2-IP-QC-0004 (planar), AT2-IP-QC-0003 (3D)
    if "3D" in sensor_type:
        return 10
    if "L1" in sensor_type:
        return 60
    return 100


def depletion_voltage_default(is3D=False):
    """
    Function to return the default depletion voltage (V) of a sensor type
    """
    return 5 if is3D else 50


def operation_voltage(depletion_voltage, is3D=False):
    """
    Function to return the operation voltage (V) depending on the depletion voltage
    """
    return depletion_voltage + 20.0 if is3D else depletion_voltage + 50.0


def breakdown_threshold(depletion_voltage, is3D=False):
    return depletion_voltage + 20 if is3D else depletion_voltage + 70


def breakdown_reduction_threshold(previous_breakdown):
    return 10 if previous_breakdown != -999 else 0


def find_breakdown_and_current(
    voltage, current, Vdepl, Vop, is3D=False, Ilim=0, Icompl=0, iv_array=None
):
    Vdb, Ilc = find_breakdown_and_current_simple(
        voltage, current, Vdepl, Vop, is3D, Ilim, Icompl, iv_array
    )
    log.debug(f" Simple values for breakdown voltage and current are: {Vdb} and {Ilc}.")

    return Vdb, Ilc


## input voltage array, (normalised) abs. current (uA) array, Vdepl (V), Vop (V)
## requires also the original IV array in case temperature very different from 20 degrees
def find_breakdown_and_current_simple(
    voltage, current, Vdepl, Vop, is3D=False, Ilim=0, Icompl=100, iv_array=None
):
    """
    Function to return the breakdown voltage (V) and leakage current (uA) at operational voltage Vop
    By comparing with
    - Ilim (leakage current per area * sensor area, defined at Vop) for 0<=V<=Vop
    - Icompl (current compliance) for Vop<V
    """
    ## use absolute values in case this function is used standalone
    voltage = np.abs(voltage)
    current = np.abs(current)

    Vbd = -999
    Ilc = -999

    for idx, V in enumerate(voltage):
        ## TODO: check if max(voltage) is => breakdown_threshold/depletion voltage?
        ## fill leakage current first in case breakdown is > Vop
        log.debug(f"V {V} Vop {Vop}, current {current[idx]}")

        if Ilc == -999 and Vop <= V:
            log.debug(f"Found Ilc at {V} V with current {current[idx]} uA")
            Ilc = current[idx]

        ## for np.isclose: rtol in fraction; atol is 1uA (current is in units of uA)
        rel_tolerance = 0.05
        abs_tolerance = 1

        log.debug(
            f"Vop {Vop} >= V {V} {Vop >= V}, current[idx] {current[idx]} >= Ilim {Ilim} {current[idx] >= Ilim}, Vop < V {Vop < V}, np.isclose {np.isclose(current[idx], Icompl, rtol=rel_tolerance, atol=abs_tolerance)}  current {current[idx]}"
        )

        measured_current = 0
        if iv_array:
            measured_current = abs(iv_array["current"][idx])

        if (Vbd == -999) and (
            (Vop >= V and current[idx] >= Ilim)
            or (
                Vop < V
                and (
                    any(
                        np.isclose(
                            [current[idx], measured_current],
                            [Icompl, Icompl],
                            rtol=rel_tolerance,
                            atol=abs_tolerance,
                        )
                    )
                    or any(item > Icompl for item in [current[idx], measured_current])
                )
            )
        ):
            Vbd = V

    ## make sure the measurement is complete
    if Vbd == -999 and max(voltage) < breakdown_threshold(Vdepl, is3D):
        Vbd = max(voltage)
        return Vbd, Ilc

    return Vbd, Ilc


def find_breakdown_and_current_robust(voltage, current, Vdepl, Vop, is3D=False):
    if isinstance(voltage, list):
        voltage = np.array(voltage)
    if isinstance(current, list):
        current = np.array(current)

    voltage = np.abs(voltage)
    current = np.abs(current)

    if (
        np.average(current) > 1e3
    ):  # crasy bare measurement in nA instead of uA: 20UPGB43000013
        current /= 1e3

    for idx, (Volt, Curr) in enumerate(zip(voltage, current)):
        log.debug(f" Value {idx} for Voltage {Volt} and Current {Curr}.")

    if (
        Vdepl < 0 or Vdepl > 150
    ):  # Bad CV analysis in several cases using default. E.g.:
        # https://itkpd.unicornuniversity.net/testRunView?id=64ba5625433ed900423787f8
        Vdepl = depletion_voltage_default(is3D)
        Vop = operation_voltage(Vdepl, is3D)

    Vbd = -999

    count_V_under_Vdepl = np.sum(voltage < Vdepl)

    # Create a mask for the condition: idx > 2 and current < 0.0001
    mask = ~((np.arange(len(current)) > 2) & (current < 0.0001))

    # Additional condition: Check if the last element of `current` is less than the second-to-last element
    if len(current) > 1 and current[-1] < current[-2]:
        mask[-1] = False  # Exclude the last element from the mask

    # Apply the mask to both current and voltage
    current = current[mask]
    voltage = voltage[mask]
    # This should remove points with less than 0.1nA

    steps_of_V = None
    ratioThr = None
    maxV = None
    if is3D:
        # Step 1: Interpolate the current using numpy
        steps_of_V = np.arange(0, max(voltage) + 1)  # Voltages at steps of 1V
        ratioThr = 2.0
        maxV = 79  # +1
        # There were several sites that stop the IV for 3D sensors at 80 V instead of 100V.
        # If the value of default maxV is set to 100V, several cases the breakdown voltage will be set to 80V, instead of -999.
        # This will not affect yields as the Vop is 25V.
    else:
        steps_of_V = np.arange(0, max(voltage) + 1, 5)  # Voltages at steps of 5V
        ratioThr = 1.5  # 1.2 #
        maxV = 195  # +5
    interpolated_current = np.interp(steps_of_V, voltage, current)

    # At this stage, we have the "correct" voltage (steps_of_V) and (interpolated_) current.

    count_V_under_Vdepl = np.sum(steps_of_V < Vdepl)

    for idv in range(2, len(steps_of_V)):  # Ensure we stay within range
        vstep = steps_of_V[idv]
        if vstep < Vdepl:  # Below depletion voltage.
            if (
                np.average(interpolated_current[:count_V_under_Vdepl]) > 10
                and np.interp(Vdepl, voltage, current) > 50
            ):
                # Low breakdown if average is below 10uA and if the current at depletion voltage above 50
                # Currents of 10uA at operation voltage is the maximum allowed so I am addressing 10uA current below depletion voltage as "early breakdown".
                return (
                    0,
                    100,
                )  # returning breakdown of 0 and a current set to the compliance (change to 100uA?)
            continue

        i_vp5V = -1
        i_v0 = interpolated_current[idv - 0]  # I(V- 0)

        ratio1 = -1
        ratio2 = -1

        ###########################
        # handling planar sensors #
        ###########################
        if not is3D:
            i_v1 = interpolated_current[idv - 1]  # I(V- 5) for planar and I(V-1) for 3D
            i_v2 = interpolated_current[idv - 2]  # I(V-10) for planar and I(V-2) for 3D
            if i_v1 == 0 or i_v2 == 0:
                msg = f"Found a voltage above {vstep} V with null current: {i_v1}, {i_v2}."
                log.error(msg)
                continue
            ratio1 = i_v0 / i_v1
            ratio2 = i_v1 / i_v2

            if idv < len(steps_of_V) - 1:
                i_vp5V = interpolated_current[idv + 1]  # Check I@V+5

        ###########################
        # handling   3D   sensors #
        ###########################
        else:
            if idv < len(steps_of_V) - 6:
                i_v0 = interpolated_current[idv + 0]  # I(V+ 0)
                i_v1 = interpolated_current[idv + 5]  # I(V+ 5)
                i_v2 = interpolated_current[idv + 1]  # I(V+ 1)
                i_v3 = interpolated_current[idv + 6]  # I(V+ 6)
                if i_v0 == 0 or i_v2 == 0:
                    msg = f"Found a voltage above {vstep} V with null current: {i_v0}, {i_v2}."
                    raise ZeroDivisionError(msg)
                ratio1 = i_v1 / i_v0  # I(V+5) / I(V+0)
                ratio2 = i_v3 / i_v2  # I(V+6) / I(V+1)
                i_vp5V = i_v1

        if (
            ratio1 > ratioThr and ratio2 > ratioThr
        ):  # Two consecutive ratios trigger the breakdown
            Vbd = steps_of_V[idv - 1]
            break
        if (
            ratio1 > ratioThr and i_vp5V > 20
        ):  # One ratio and a current larger than 20uA at V+5V (maximum allowed is 10uA).
            Vbd = steps_of_V[idv - 1]
            break

    # Current at operation voltage given by interpolation
    Ilc = np.interp(Vop, voltage, current)

    # If no breakdown is found with the previous method, this does mean there was no breakdown.
    if Vbd == -999:
        if (
            max(voltage) <= maxV
        ):  # If measurement stopped before default maxV, it will be consider as the breakdown.
            Vbd = max(voltage)
            if Vbd < Vdepl:  # Second confirmation if stop before depletion voltage.
                return 0, 100

            return Vbd, Ilc

        # if current reaches 99 (~ compliance) with a fast rise, there will be no second ratio and this sets the Vbd to that value.
        indices = np.where(current > 99)[0]
        if indices.size > 0:
            Vbd = voltage[indices[0]]

    # Final checks:
    if (Vbd >= 80 and is3D) or Vbd >= 200:
        Vbd = -999.0  # Irrefutable

    # Off set required because we are checking forward in 3D instead of backward in planar.
    if Vbd != -999 and is3D and Vbd > 5:
        Vbd += 5

    # float conversion required as values are np.float64
    return float(Vbd), float(Ilc)


## input voltage array, (normalised) abs. current array, Vdepl
def find_breakdown_and_current_spec(voltage, current, Vdepl, Vop, is3D=False):
    """
    Function to return the breakdown voltage (V) and leakage current (uA) at operational voltage Vop
    Defined as per sensor QA/QC document
    - 3D sensor QA/QC document: AT2-IP-QC-0003
    - Planar sensor QC/QC document: AT2-IP-QC-0004
    - Module spec: AT2-IP-ES-0009
    """
    ## use absolute values in case this function is used standalone
    voltage = np.abs(voltage)
    current = np.abs(current)

    Vbd = -999
    Ilc = -999

    for idx, V in enumerate(voltage):
        ## TODO: check if max(voltage) is => breakdown_threshold/depletion voltage?
        ## TODO: set upper limit if V < Vdepl and current[idx] < ilim: ## ilim to be determined
        if Vdepl > V:
            continue

        if Ilc == -999 and Vop <= V:
            Ilc = current[idx]

        # Finding breakdown voltage for 3D using temperature-normalised current
        # 3D IV is measured in 1V steps
        if (
            Vbd == -999
            and is3D
            and current[idx] > current[idx - 5] * 2
            and voltage[idx - 5] > Vdepl
        ):
            Vbd = V
            log.debug(
                f"Breakdown at {Vbd:.1f} V for 3D sensor according to spec'ed analysis"
            )

        # Finding breakdown voltage for Planar using temperature-normalised current
        # planar IV is measured in 5V steps
        if (
            Vbd == -999
            and (not is3D)
            and current[idx] > current[idx - 1] * 1.2
            and current[idx - 1] != 0
        ):
            Vbd = V
            log.debug(
                f"Breakdown at {Vbd:.1f} V for planar sensor according to spec'ed analysis"
            )

    return Vbd, Ilc


def current_compliance():
    """
    Function to return the current compliance (100 uA)
    Defined as per sensor QA/QC document
    - 3D sensor QA/QC document: AT2-IP-QC-0003
    - Planar sensor QC/QC document: AT2-IP-QC-0004
    - Module spec: AT2-IP-ES-0009
    """
    return 100.0


def current_threshold(is3D=False, isBare=False, isModule=False):
    """
    Function to return maximum allowed leakage current (uA) per area (cm^2)
    """
    ## uA/cm^2; module criteria is 2x sensor criteria
    if isBare or isModule:
        return 2.5 * 2 if is3D else 0.75 * 2
    return 2.5 if is3D else 0.75


def current_increase_threshold(previous_current):
    """
    Function to return the maximum allowed leakage current given the leakage current of the previous stage
    """
    return previous_current * 2


def update_iv_cuts(
    qc_selections,
    layer,
    Vdepl,
):
    """
    Function to update the QC cuts on the breakdown voltage depending on the depletion voltage
    """
    iv_cuts = copy.deepcopy(qc_selections)  ## make copy because will have to modify
    qc_layer = get_layer(layer)
    # is3D = layer in ["R0", "R0.5", "L0"]

    iv_cuts["BREAKDOWN_VOLTAGE"][qc_layer]["sel"][0] += round(Vdepl, 1)

    return iv_cuts


def make_iv_plots(
    module_sn: str,
    iv_array,
    normalised_current,
    Vbd: float,
    temp: float | None = None,
    cold: bool = False,
    ref: dict | None = None,
    Vop: float | None = None,
    Vbdthres: float | None = None,
    Ithres: float | None = None,
    Icompl: float | None = None,
):
    """
    Function to plot make IV plots.

    `module_sn`: module serial number in the production database starting with "20UP";
    `iv_array`:  IV dictionary from the production database;
    `normalised_current`: current array that has been normalised to 20 degrees Celsius;
    `Vbd`: breakdown voltage determined from data;
    `temp`: in case the `temperature` array is unsuitable, a fixed value can be used;
    `cold`: whether this measurement is done cold;
    `ref`: reference IV from bare module stage;
    `Vop`: operational voltage (V);
    `Vbdthres`: breakdown voltage threshold (V);
    `Ithres`: max. allowed current (uA) at operational voltage;
    `Icompl`: abs. current compliance (uA).
    """
    fig, ax = plt.subplots(1, figsize=(7.2, 4.0))

    # plot breakdown
    if Vbd > 0:
        ax.axvline(
            Vbd,
            linewidth=4,
            color="r",
            label=f"Bd @ {Vbd:.0f}V",
        )

    #  plot IV, temperature and humidity
    style_data = "ko"
    style_normdata = "*k"
    p1, p11 = None, None
    if len(iv_array["sigma current"]) == 0:
        (p1,) = ax.plot(
            iv_array["voltage"][1:],
            iv_array["current"][1:],
            style_data,
            label="current (raw)",
            markersize=3,
        )
        if not cold:
            (p11,) = ax.plot(
                iv_array["voltage"][1:],
                normalised_current[1:],
                style_normdata,
                label="current (norm. 20$^\\circ$C)",
                markersize=5,
            )
    else:
        p1 = ax.errorbar(
            iv_array["voltage"][1:],
            iv_array["current"][1:],
            yerr=iv_array["sigma current"][1:],
            fmt=style_data,
            elinewidth=1,
            label="current (raw)",
            markersize=3,
        )

        if not cold:
            p11 = ax.errorbar(
                iv_array["voltage"][1:],
                normalised_current[1:],
                yerr=iv_array["sigma current"][1:],
                fmt=style_normdata,
                elinewidth=1,
                label="current (norm. 20$^\\circ$C)",
                markersize=5,
            )
    if not cold:
        first_legend = plt.legend(
            handles=[p1, p11], loc="lower center", bbox_to_anchor=(0.15, -0.33)
        )
    else:
        first_legend = plt.legend(
            handles=[p1], loc="lower center", bbox_to_anchor=(0.15, -0.33)
        )
    plt.gca().add_artist(first_legend)

    if len(iv_array["temperature"]) == 0 and temp is None:
        log.warning(bcolors.WARNING + "No temperature to plot!" + bcolors.ENDC)
    else:
        ax1 = ax.twinx()
        if len(iv_array["voltage"][1:]) == len(iv_array["temperature"][1:]):
            temps = iv_array["temperature"][1:]
            (p2,) = ax1.plot(
                iv_array["voltage"][1:],
                temps,
                color="C1",
                linewidth=1,
                label="temperature",
            )

        elif len(iv_array["temperature"]) > 0:
            temps = iv_array["temperature"][1:]
            (p2,) = ax1.axhline(
                np.average(temps),
                color="C1",
                linewidth=1,
                label="temperature",
            )
        else:
            temps = [temp]
            (p2,) = ax1.axhline(
                temp,
                color="C1",
                linewidth=1,
                label="temperature",
            )

        # Ensure y-axis has at least ±0.5°C around mean
        mean_temp = np.mean(temps)
        temp_range = max(np.max(temps) - np.min(temps), 1.0)  # ensure at least 1°C span
        lower = mean_temp - temp_range / 2.0
        upper = mean_temp + temp_range / 2.0
        ax1.set_ylim(lower, upper)

        ax1.set_ylabel("T ($^\\circ$C)", color="C1", fontsize="large")
        second_legend = plt.legend(
            handles=[p2], loc="lower center", bbox_to_anchor=(0.55, -0.33)
        )
        plt.gca().add_artist(second_legend)

    if len(iv_array["humidity"]) == 0:
        log.warning(bcolors.WARNING + " No humidity array to plot" + bcolors.ENDC)
    else:
        ax2 = ax.twinx()
        if len(iv_array["voltage"][1:]) == len(iv_array["humidity"][1:]):
            hums = iv_array["humidity"][1:]
            (p3,) = ax2.plot(
                iv_array["voltage"][1:],
                hums,
                color="C2",
                linewidth=1,
                label="humidity",
            )
        else:
            hums = iv_array["humidity"][1:]
            # # if len(iv_array["humidity"]) > 0:
            (p3,) = ax2.axhline(
                np.average(hums),
                color="C2",
                linewidth=1,
                label="humidity",
            )

        # Ensure y-axis has at least ±0.5% around mean
        mean_hum = np.mean(hums)
        hum_range = max(np.max(hums) - np.min(hums), 1.0)  # ensure at least 1% RH span
        lower = mean_hum - hum_range / 2.0
        upper = mean_hum + hum_range / 2.0
        ax2.set_ylim(lower, upper)

        ax2.set_ylabel("RH (%)", color="C2", fontsize="large")
        ax2.spines["right"].set_position(("outward", 60))
        third_legend = plt.legend(
            handles=[p3], loc="lower center", bbox_to_anchor=(0.85, -0.33)
        )
        plt.gca().add_artist(third_legend)

    legend = []

    #  plot normalised reference bare module IV
    if ref is not None:
        ref_plots = []
        ref_voltage = []

        for iv in ref["reference_IVs"]:
            iv["IV_ARRAY"]["voltage"] = [abs(v) for v in iv["IV_ARRAY"]["voltage"]]
            iv["IV_ARRAY"]["current"] = [abs(c) for c in iv["IV_ARRAY"]["current"]]
            voltage_step = np.average(
                [
                    j - i
                    for i, j in zip(
                        iv["IV_ARRAY"]["voltage"][:-1], iv["IV_ARRAY"]["voltage"][1:]
                    )
                ]
            )
            try:
                iv["IV_ARRAY"]["current"] = normalise_current(
                    iv["IV_ARRAY"]["current"], iv["IV_ARRAY"]["temperature"]
                )
                ref_plots.append(
                    ax.plot(
                        iv["IV_ARRAY"]["voltage"],
                        iv["IV_ARRAY"]["current"],
                        linestyle="dotted",
                        label=iv["component_sn"] + " norm.",
                    )[0]
                )
            except KeyError:
                iv["IV_ARRAY"]["current"] = normalise_current(
                    iv["IV_ARRAY"]["current"], iv["temperature"]
                )
                ref_plots.append(
                    ax.plot(
                        iv["IV_ARRAY"]["voltage"],
                        iv["IV_ARRAY"]["current"],
                        linestyle="dotted",
                        label=iv["component_sn"] + " norm.",
                    )[0]
                )
            except Exception as e:
                log.warning(f"Can't normalise bare module IV: {e}")
                ref_plots.append(
                    ax.plot(
                        iv["IV_ARRAY"]["voltage"],
                        iv["IV_ARRAY"]["current"],
                        linestyle="dotted",
                        label=iv["component_sn"],
                    )[0]
                )
            if voltage_step < 1:
                ref_voltage.append([float(v) for v in iv["IV_ARRAY"]["voltage"]])
            else:
                ref_voltage.append([int(v) for v in iv["IV_ARRAY"]["voltage"]])

        if len(ref["reference_IVs"]) > 1:
            ## check if all measurements have the same length
            if all(i == ref_voltage[0] for i in ref_voltage):
                sum_array = {}
                sum_array["voltage"] = [abs(item) for item in ref_voltage[0]]
                sum_array["current"] = len(sum_array["voltage"]) * [0]
                for iv in ref["reference_IVs"]:
                    sum_array["current"] = [
                        sum(x)
                        for x in zip(
                            sum_array["current"],
                            iv["IV_ARRAY"]["current"],
                        )
                    ]

                ref_plots.append(
                    ax.plot(
                        sum_array["voltage"],
                        sum_array["current"],
                        linestyle="dashed",
                        label="sum(bare modules)",
                    )[0]
                )
            else:
                log.warning(
                    bcolors.WARNING
                    + f"Bare IVs have different lengths {[len(iv['IV_ARRAY']['voltage']) for iv in ref['reference_IVs']]}, trying to sum up the currents."
                    + bcolors.ENDC
                )
                sum_array = {}
                length = min(len(_l) for _l in ref_voltage)
                sum_array["voltage"] = ref_voltage[0][:length]
                sum_array["current"] = length * [0]
                for iv in ref["reference_IVs"]:
                    sum_array["current"] = [
                        sum(x)
                        for x in zip(
                            sum_array["current"],
                            iv["IV_ARRAY"]["current"][:length],
                        )
                    ]

                ref_plots.append(
                    ax.plot(
                        sum_array["voltage"],
                        sum_array["current"],
                        linestyle="dashed",
                        label="sum(bare modules)*",
                    )[0]
                )

        # ax.legend(handles=ref_plots, loc="best", fontsize=8)
        legend.extend(ref_plots)

    # plot limits
    Imax = max(iv_array["current"] + normalised_current)
    if Vbdthres:
        legend.append(
            ax.axvline(
                Vbdthres,
                linewidth=1,
                linestyle="dashed",
                color="r",
                label=f"Breakdown Threshold @ {Vbdthres:.0f}V",
            )
        )
    if Vop:
        legend.append(
            ax.axvline(
                Vop,
                linewidth=1,
                linestyle="dashed",
                color="g",
                label=f"Operational Voltage @ {Vop:.0f}V",
            )
        )
    if Vop and Ithres and (np.isclose(Imax, Ithres, rtol=0.1) or Imax > Ithres):
        legend.append(
            ax.plot(
                (0, Vop),
                (Ithres, Ithres),
                linewidth=1,
                linestyle="dashed",
                color="b",
                label=f"Leakage Current Threshold @ {Ithres:.0f}uA",
            )[0]
        )

    if Vop and Icompl and (np.isclose(Imax, Icompl, rtol=0.1) or Imax > Icompl):
        legend.append(
            ax.plot(
                (Vop, ax.get_xlim()[1]),
                (Icompl, Icompl),
                linewidth=1,
                linestyle="dashed",
                color="b",
                label=f"Leakage Current Compliance @ {Icompl:.0f}uA",
            )[0]
        )

    ax.legend(handles=legend, loc="best", fontsize=8)
    ax.set_title(f'IV for module "{module_sn}"', fontsize="large")
    ax.set_xlabel("Bias Voltage [V]", ha="right", va="top", x=1.0, fontsize="large")
    ax.set_ylabel(
        "Leakage Current ($\\mathrm{\\mu}$A)",
        ha="right",
        va="bottom",
        y=1.0,
        fontsize="large",
    )

    fig.subplots_adjust(bottom=0.25)
    fig.subplots_adjust(right=0.75)

    ax.grid()

    return fig


#### end IV stuff


def get_nominal_Voffs(layer, lp_mode=False):
    check_layer(layer)
    Voffs = {
        "L0": 1.1,
        "L1": 1.0,
        "L2": 1.0,
    }
    Voffs_lp = {
        "L0": 1.38,
        "L1": 1.33,
        "L2": 1.33,
    }
    if lp_mode:
        return Voffs_lp.get(layer)

    return Voffs.get(layer)


def get_nominal_kShuntA(chip_type):
    kShuntA = {"RD53B": 1040, "ITKPIXV2": 1000}
    return kShuntA.get(chip_type)


def get_nominal_kShuntD(chip_type):
    kShuntD = {"RD53B": 1040, "ITKPIXV2": 1000}
    return kShuntD.get(chip_type)


def get_nominal_RextA(BOM_code):
    return get_nominal_Rext("A", BOM_code)


def get_nominal_RextD(BOM_code):
    return get_nominal_Rext("D", BOM_code)


# Function to get key from value in muxMaps
def get_key(mydict, val):
    for key, value in mydict.items():
        if val == value:
            return key
    return -1


def get_bounds_and_precision(qc_selections, key, layer):
    lower_bound, upper_bound, precision = None, None, None
    if isinstance(qc_selections.get(key).get("sel"), list):
        if len(qc_selections.get(key).get("sel")) != 2:
            log.error(
                bcolors.ERROR
                + f" QC selections for {key} are ill-formatted, should be list of length 2! Please fix: {qc_selections.get(key).get('sel')} . Skipping."
                + bcolors.ENDC
            )
            raise RuntimeError()
        lower_bound = qc_selections.get(key).get("sel")[0]
        upper_bound = qc_selections.get(key).get("sel")[1]
        precision = qc_selections.get(key).get("precision")
    elif qc_selections.get(key).get("LZero"):
        layer_bounds = qc_selections.get(key).get(layer).get("sel")
        if not layer_bounds:
            log.error(
                bcolors.ERROR
                + f" QC selections for {key} and {layer} do not exist - please check! Skipping."
                + bcolors.ENDC
            )
            raise RuntimeError()
        lower_bound = layer_bounds[0]
        upper_bound = layer_bounds[1]
        precision = qc_selections.get(key).get(layer).get("precision")
    return lower_bound, upper_bound, precision


def perform_qc_analysis_AR_VDD_Trim(_test_type, qc_config, _layer, results, key):
    # QC analysis for VDDA_VS_TRIM and VDDD_VS_TRIM
    pass_vdd_vs_trim_test = True

    cell_text = np.empty(0)
    # Check that nominal VDD value is between 2nd and 13th trim value
    lower_bound_vdd = qc_config.get("sel")[0]
    upper_bound_vdd = qc_config.get("sel")[1]

    vdd = np.array(results)
    Trim = int(np.absolute(vdd - 1.2).argmin())

    if (Trim < lower_bound_vdd) or (Trim > upper_bound_vdd):
        pass_vdd_vs_trim_test = False
    if pass_vdd_vs_trim_test:
        print_output_pass(f"{key}", Trim, lower_bound_vdd, upper_bound_vdd)
    else:
        print_output_fail(f"{key}", Trim, lower_bound_vdd, upper_bound_vdd)
    cell_text = np.append(
        cell_text,
        [
            f"{key}",
            Trim,
            f"[{lower_bound_vdd}, {upper_bound_vdd}]",
            pass_vdd_vs_trim_test,
        ],
    )

    rounded_results = Trim

    return pass_vdd_vs_trim_test, cell_text, rounded_results


def perform_qc_analysis_AR_ROSC(_test_type, qc_config, _layer, results, key):
    # QC analysis for ROSC_VS_VDDD
    pass_rosc_vs_vddd_test = True

    rounded_results_list = results.copy()
    cell_text = np.empty(0)

    # Count fraction of ROSC selections passing, fail module if > X% fail
    nPass = 0
    nTotal = 0
    for i, result in enumerate(results):
        tmp_pass_qc = True
        lower_bound = (
            qc_config.get("sel")[0]
            if "RESIDUAL" in key
            else qc_config.get(f"ROSC{i}").get("sel")[0]
        )
        upper_bound = (
            qc_config.get("sel")[1]
            if "RESIDUAL" in key
            else qc_config.get(f"ROSC{i}").get("sel")[1]
        )
        precision = (
            qc_config.get("precision")
            if "RESIDUAL" in key
            else qc_config.get(f"ROSC{i}").get("precision")
        )
        rounded_results = round(result, precision)
        rounded_results_list[i] = rounded_results

        nTotal += 1
        if (rounded_results < lower_bound) or (rounded_results > upper_bound):
            tmp_pass_qc = False
        else:
            nPass += 1

        if log.getEffectiveLevel() <= logging.DEBUG:
            if tmp_pass_qc:
                print_output_pass(
                    f"{key}_{i}", rounded_results, lower_bound, upper_bound
                )
            else:
                print_output_neutral(
                    f"{key}_{i}", rounded_results, lower_bound, upper_bound
                )
        cell_text = np.append(
            cell_text,
            [
                f"{key}_{i}",
                rounded_results,
                f"[{lower_bound}, {upper_bound}]",
                tmp_pass_qc,
            ],
        )

    # Apply selection on fraction of ROSC passing selection
    lower_bound = qc_config.get("FRACPASS").get("sel")[0]
    upper_bound = qc_config.get("FRACPASS").get("sel")[1]
    precision = qc_config.get("FRACPASS").get("precision")
    fracPass = nPass / nTotal
    rounded_results = round(fracPass, precision)

    if (rounded_results < lower_bound) or (rounded_results > upper_bound):
        pass_rosc_vs_vddd_test = False
    if pass_rosc_vs_vddd_test:
        print_output_pass(f"{key}_FRACPASS", rounded_results, lower_bound, upper_bound)
    else:
        print_output_fail(f"{key}_FRACPASS", rounded_results, lower_bound, upper_bound)
    cell_text = np.append(
        cell_text,
        [
            f"{key}_FRACPASS",
            rounded_results,
            f"[{lower_bound}, {upper_bound}]",
            pass_rosc_vs_vddd_test,
        ],
    )

    return pass_rosc_vs_vddd_test, cell_text, rounded_results_list


# Function takes as input test type (i.e. ADC_CALIBRATION), file containing QC selections,
# and dictionary with results. Returns QC result (true/false), a numpy array of text to
# be printed later into a table, and the same result dictionary it was passed, but with
# the values rounded to the same precision as the QC selection they are compared to.


# The "check" keyword is to make sure all keys in qc_selection have been used.
# Can be set to "False" to suppress errors in case not all keys are used.
# E.g. in data transmission (to be backward compatible when adding data merging).
def perform_qc_analysis(test_type, qc_selections, layer_name, results, check=True):
    log.info("")
    log.info(" Performing QC analysis!")
    log.info("")

    check_qc_selections = qc_selections.copy()

    check_layer(layer_name)
    layer = get_layer(layer_name)

    passes_qc_overall = True
    txt = format_text()
    log.info(txt.format("Parameter", "Analysis result", "QC criteria", "Pass"))
    log.info(
        "--------------------------------------------------------------------------------------"
    )

    # Setup arrays for plotting
    cell_text = np.empty(0)

    # Setup rounded result dictionary
    rounded_results_dict = results.copy()

    for key in results:
        if "IV_ARRAY" in key:
            continue
        if not qc_selections.get(key):
            log.debug(
                bcolors.WARNING
                + f" Selection for {key} not found in QC file! Skipping."
                + bcolors.ENDC
            )
            print_output_neutral(key, results.get(key))

            if isinstance(results.get(key), list):
                rounded_results = np.round(results.get(key), 2)
            elif isinstance(results.get(key), float):
                rounded_results = np.round(results.get(key), 2).item()
            elif isinstance(results.get(key), int):
                rounded_results = results.get(key)
            else:  ## just in case there is a dict or so
                continue

            with np.printoptions(threshold=4, edgeitems=1):
                cell_text = np.append(
                    cell_text,
                    [
                        key,
                        str(rounded_results),
                        None,
                        None,
                    ],
                )
            continue
        check_qc_selections.pop(key)

        # Handle AR_VDDA_VS_TRIM and AR_VDD_VS_TRIM separately
        if ("AR_VDDA_TRIM" in key) or ("AR_VDDD_TRIM" in key):
            (
                passes_qc_test,
                new_cell_text,
                rounded_list,
            ) = perform_qc_analysis_AR_VDD_Trim(
                test_type,
                qc_selections.get(key),
                layer,
                results.get(key),
                key,
            )
            rounded_results_dict.update({key: rounded_list})
            cell_text = np.append(cell_text, new_cell_text)
            passes_qc_overall = passes_qc_overall and passes_qc_test
            continue

        # Handle AR_ROSC_SLOPE and AR_ROSC_OFFSET separately
        if "AR_ROSC" in key:
            passes_qc_test, new_cell_text, rounded_list = perform_qc_analysis_AR_ROSC(
                test_type,
                qc_selections.get(key),
                layer,
                results.get(key),
                key,
            )
            rounded_results_dict.update({key: rounded_list})
            cell_text = np.append(cell_text, new_cell_text)
            passes_qc_overall = passes_qc_overall and passes_qc_test
            continue

        # Breakdown not observed
        if (
            "BREAKDOWN_VOLTAGE" in key
            and results["BREAKDOWN_VOLTAGE"] == -999
            and results["NO_BREAKDOWN_VOLTAGE_OBSERVED"]
        ):
            lower_bound, upper_bound, precision = get_bounds_and_precision(
                qc_selections, key, layer
            )
            rounded_results = round(results.get(key), precision)
            rounded_results_dict.update({key: rounded_results})
            passes_qc_test = True
            print_output_pass(key, rounded_results, lower_bound, upper_bound)

            cell_text = np.append(
                cell_text,
                [
                    key,
                    rounded_results,
                    f"[{lower_bound}, {upper_bound}]",
                    passes_qc_test,
                ],
            )
            passes_qc_overall = passes_qc_overall and passes_qc_test
            continue

        log.debug(f"QC selections for {key}: {qc_selections.get(key).get('sel')}")

        lower_bound, upper_bound, precision = get_bounds_and_precision(
            qc_selections, key, layer
        )

        if isinstance(lower_bound, list) and isinstance(upper_bound, list):
            rounded_results = []
            for results_entry in results.get(key):
                rounded_results_entry = round(results_entry, precision)
                rounded_results.append(rounded_results_entry)
            rounded_results_dict.update({key: rounded_results})
            passes_qc_test = True
            rounded_results_output_format = ""
            lower_bound_output_format = ""
            upper_bound_output_format = ""
            for rounded_results_entry_i in rounded_results:
                if (
                    rounded_results_entry_i
                    < lower_bound[rounded_results.index(rounded_results_entry_i)]
                    or rounded_results_entry_i
                    > upper_bound[rounded_results.index(rounded_results_entry_i)]
                ):
                    passes_qc_test = False
                rounded_results_output_format = rounded_results_output_format + (
                    str(rounded_results_entry_i) + ", "
                )
                lower_bound_output_format = (
                    lower_bound_output_format
                    + str(lower_bound[rounded_results.index(rounded_results_entry_i)])
                    + ", "
                )
                upper_bound_output_format = (
                    upper_bound_output_format
                    + str(upper_bound[rounded_results.index(rounded_results_entry_i)])
                    + ", "
                )
            rounded_results_output_format = rounded_results_output_format[:-2]
            lower_bound_output_format = lower_bound_output_format[:-2]
            upper_bound_output_format = upper_bound_output_format[:-2]
            if passes_qc_test:
                print_output_pass(
                    key,
                    rounded_results_output_format,
                    lower_bound_output_format,
                    upper_bound_output_format,
                )
            else:
                print_output_fail(
                    key,
                    rounded_results_output_format,
                    lower_bound_output_format,
                    upper_bound_output_format,
                )
            passes_qc_overall = passes_qc_overall and passes_qc_test

            cell_text = np.append(
                cell_text,
                [
                    key,
                    rounded_results_output_format,
                    f"[{lower_bound_output_format}, {upper_bound_output_format}]",
                    passes_qc_test,
                ],
            )
            continue
        rounded_results = round(results.get(key), precision)
        rounded_results_dict.update({key: rounded_results})
        passes_qc_test = True
        if rounded_results < lower_bound or rounded_results > upper_bound:
            passes_qc_test = False
        if passes_qc_test:
            print_output_pass(key, rounded_results, lower_bound, upper_bound)
        else:
            print_output_fail(key, rounded_results, lower_bound, upper_bound)
        passes_qc_overall = passes_qc_overall and passes_qc_test

        cell_text = np.append(
            cell_text,
            [
                key,
                rounded_results,
                f"[{lower_bound}, {upper_bound}]",
                passes_qc_test,
            ],
        )
    if check and len(check_qc_selections) > 0:
        for key in check_qc_selections:
            log.error(
                bcolors.ERROR
                + f" Parameter from chip for QC selection of {key} was not passed to analysis - please fix!"
                + bcolors.ENDC
            )
        passes_qc_overall = False
    log.info(
        "--------------------------------------------------------------------------------------"
    )

    return passes_qc_overall, cell_text, rounded_results_dict


def print_result_summary(cell_text, test_type, outputdir, chipname, label=""):
    # Turn off matplotlib DEBUG messages
    plt.set_loglevel(level="warning")

    cell_text = cell_text.reshape(-1, 4)
    nrows, _ncols = cell_text.shape
    cellColours = np.empty(0)
    for r in range(nrows):
        if cell_text[r][3] is None:
            cellColours = np.append(cellColours, ["white"] * 4)
        elif cell_text[r][3] == "True":
            cellColours = np.append(cellColours, ["lightgreen"] * 4)
        else:
            cellColours = np.append(cellColours, ["lightcoral"] * 4)
    cellColours = cellColours.reshape(-1, 4)
    colLabels = np.array(["Parameter", "Analysis result", "QC criteria", "Pass"])
    colWidths = [1.2, 0.4, 0.5, 0.3]

    cell_text[np.where(cell_text == None)] = "-"  # noqa: E711 # pylint: disable=singleton-comparison

    if test_type == "ANALOG_READBACK":
        nRowsPrinted = 0
        nRowsPerPlot = [31, 34, 43, 43, 43, 43, 100]
        nPlot = 0
        while nRowsPrinted < len(cell_text):
            if nRowsPrinted + nRowsPerPlot[nPlot] > len(cell_text):
                maxRow = len(cell_text)
            else:
                maxRow = nRowsPrinted + nRowsPerPlot[nPlot]

            cell_text1 = cell_text[nRowsPrinted:maxRow, :]
            cellColours1 = cellColours[nRowsPrinted:maxRow, :]
            nrows, _ncols = cell_text1.shape
            fig, ax = plt.subplots(figsize=(6.4, 1.5 + nrows * 0.5))
            table = ax.table(
                cellText=cell_text1,
                colLabels=colLabels,
                loc="upper center",
                cellLoc="center",
                colWidths=colWidths,
                cellColours=cellColours1,
            )
            format_result_summary(
                fig, ax, table, chipname, test_type, outputdir, f"{label}{nPlot}"
            )
            nRowsPrinted += nRowsPerPlot[nPlot]
            nPlot += 1

    else:
        fig, ax = plt.subplots(figsize=(6.4, 1.5 + nrows * 0.5))
        table = ax.table(
            cellText=cell_text,
            colLabels=colLabels,
            loc="upper center",
            cellLoc="center",
            colWidths=colWidths,
            cellColours=cellColours,
        )
        format_result_summary(fig, ax, table, chipname, test_type, outputdir, label)


def format_result_summary(fig, ax, table, chipname, test_type, outputdir, label=""):
    fig.patch.set_visible(False)
    if label:
        label = f"_{label}"
    ax.axis("off")
    ax.axis("tight")
    table.scale(1, 3)
    ax.set_title(f"{test_type} for {chipname}", fontsize=15)
    table.auto_set_font_size(False)
    table.set_fontsize(15)
    plt.savefig(
        outputdir.joinpath(f"{chipname}_summary{label}.png"),
        bbox_inches="tight",
        dpi=100,
        transparent=False,
        edgecolor="white",
    )
    log.info(" Saving " + str(outputdir.joinpath(f"{chipname}_summary{label}.png")))
    plt.close()


def submit_results(
    outputDF, timestamp, site="Unspecified", outputfile="submit.txt", layer="Unknown"
):
    results = outputDF.get("results")

    # Temporary solution to avoid error when indexing array that doesn't exist
    if not results.get("AR_VDDA_VS_TRIM"):
        results.update({"AR_VDDA_VS_TRIM": [-1] * 16})
    if not results.get("AR_VDDD_VS_TRIM"):
        results.update({"AR_VDDD_VS_TRIM": [-1] * 16})
    if not results.get("AR_ROSC_SLOPE"):
        results.update({"AR_ROSC_SLOPE": [-1] * 42})
    if not results.get("AR_ROSC_OFFSET"):
        results.update({"AR_ROSC_OFFSET": [-1] * 42})
    if not results.get("AR_NOMINAL_SETTINGS"):
        results.update({"AR_NOMINAL_SETTINGS": [-1] * 72})
    analysis_version = results.get("property").get("ANALYSIS_VERSION")
    meas_version = results.get("Metadata").get("MEASUREMENT_VERSION")

    url = {
        "ADC_CALIBRATION": f"https://docs.google.com/forms/d/e/1FAIpQLSegDYRQ1Foe5eTuSOVZUXe0d1f_Bh5v3rhsffCnu9DUDFR69A/formResponse?usp=pp_url\
	&entry.1920584355={timestamp}\
	&entry.1282466276={outputDF.get('passed')}\
	&entry.141409196={analysis_version}\
	&entry.1579707472={meas_version}\
	&entry.913205750={layer}\
	&entry.104853658={outputDF.get('serialNumber')}\
	&entry.802167553={site}\
	&entry.1592726943={results.get('ADC_CALIBRATION_SLOPE')}\
	&entry.422835427={results.get('ADC_CALIBRATION_OFFSET')}",
        "VCAL_CALIBRATION": f"https://docs.google.com/forms/d/e/1FAIpQLSenLUdLpaHLssp-jdUf1YvqiWvR8WOAkhrpQgfBlZYTWWRNog/formResponse?usp=pp_url\
	&entry.1920584355={timestamp}\
	&entry.796846737={outputDF.get('passed')}\
	&entry.1436190418={analysis_version}\
	&entry.463035701={meas_version}\
	&entry.74191116={layer}\
	&entry.104853658={outputDF.get('serialNumber')}\
	&entry.802167553={site}\
	&entry.1592726943={results.get('VCAL_MED_SLOPE')}\
	&entry.422835427={results.get('VCAL_MED_OFFSET')}\
	&entry.424316677={results.get('VCAL_MED_SLOPE_SMALL_RANGE')}\
	&entry.2055663117={results.get('VCAL_MED_OFFSET_SMALL_RANGE')}\
	&entry.1630084203={results.get('VCAL_HIGH_SLOPE')}\
	&entry.1107555352={results.get('VCAL_HIGH_OFFSET')}\
	&entry.1994936328={results.get('VCAL_HIGH_SLOPE_SMALL_RANGE')}\
	&entry.524584120={results.get('VCAL_HIGH_OFFSET_SMALL_RANGE')}",
        "INJECTION_CAPACITANCE": f"https://docs.google.com/forms/d/e/1FAIpQLSfHpq9pjuzgYvjUU8ZHapzCOrIHzyJx3xirJunGEtBO2COYGw/formResponse?usp=pp_url\
	&entry.1920584355={timestamp}\
	&entry.346685867={outputDF.get('passed')}\
	&entry.2076657244={analysis_version}\
	&entry.2143111336={meas_version}\
	&entry.1736672890={layer}\
	&entry.104853658={outputDF.get('serialNumber')}\
	&entry.802167553={site}\
	&entry.1714546984={results.get('INJ_CAPACITANCE')}",
        "LP_MODE": f"https://docs.google.com/forms/d/e/1FAIpQLSdVBudYiVFG9ts_0y6bQ4xhGJ-mIJNM-N1Hcs7jgPhiYVNAwA/formResponse?usp=pp_url\
	&entry.1920584355={timestamp}\
	&entry.104853658={outputDF.get('serialNumber')}\
	&entry.1282466276={outputDF.get('passed')}\
	&entry.141409196={analysis_version}\
	&entry.1579707472={meas_version}\
	&entry.913205750={layer}\
	&entry.802167553={site}\
	&entry.1592726943={results.get('LP_VINA')}\
	&entry.422835427={results.get('LP_VIND')}\
	&entry.1218296463={results.get('LP_VOFFS')}\
	&entry.1682731027={results.get('LP_IINA')}\
	&entry.784021623={results.get('LP_IIND')}\
	&entry.1188204940={results.get('LP_ISHUNTA')}\
	&entry.1456818826={results.get('LP_ISHUNTD')}\
	&entry.1355617557={results.get('LP_DIGITAL_FAIL')}",
        "OVERVOLTAGE_PROTECTION": f"https://docs.google.com/forms/d/e/1FAIpQLSc0lwqev5Yyozmnn3gkdnTOoH9BbSdjOuL7CAbhQOZ2rTJINg/formResponse?usp=pp_url\
	&entry.1920584355={timestamp}\
	&entry.104853658={outputDF.get('serialNumber')}\
	&entry.1282466276={outputDF.get('passed')}\
	&entry.141409196={analysis_version}\
	&entry.1579707472={meas_version}\
	&entry.913205750={layer}\
	&entry.802167553={site}\
	&entry.1592726943={results.get('OVP_VINA')}\
	&entry.422835427={results.get('OVP_VIND')}\
	&entry.1218296463={results.get('OVP_VREFOVP')}\
	&entry.1682731027={results.get('OVP_IINA')}\
	&entry.784021623={results.get('OVP_IIND')}",
        "SLDO": f"https://docs.google.com/forms/d/e/1FAIpQLSf3NC84OaYYjJ-DgQ29RvMV2dDQnUI0nxBFdnCUVMby7RXOFQ/formResponse?usp=pp_url\
	&entry.910646842={outputDF.get('serialNumber')}\
	&entry.1225658339={outputDF.get('passed')}\
	&entry.2052956027={analysis_version}\
	&entry.314862968={meas_version}\
	&entry.137143573={layer}\
	&entry.507508481={site}\
	&entry.1425106615={timestamp}\
	&entry.613380586={results.get('SLDO_VI_SLOPE')}\
	&entry.2009791679={results.get('SLDO_VI_OFFSET')}\
	&entry.1877869140={results.get('SLDO_NOM_INPUT_CURRENT')}\
	&entry.1380637801={results.get('SLDO_VDDA')}\
	&entry.959013471={results.get('SLDO_VDDD')}\
	&entry.427742248={results.get('SLDO_VINA')}\
	&entry.1100117192={results.get('SLDO_VIND')}\
	&entry.411324334={results.get('SLDO_VOFFS')}\
	&entry.257023545={results.get('SLDO_IINA')}\
	&entry.172777573={results.get('SLDO_IIND')}\
	&entry.2138863081={results.get('SLDO_IREF')}\
	&entry.1216431295={results.get('SLDO_ISHUNTA')}\
	&entry.825886502={results.get('SLDO_ISHUNTD')}\
	&entry.298426805={results.get('SLDO_ANALOG_OVERHEAD')}\
	&entry.187142037={results.get('SLDO_DIGITAL_OVERHEAD')}\
	&entry.844801892={results.get('SLDO_LINEARITY')}\
	&entry.812048396={results.get('SLDO_VINA_VIND')}",
        "ANALOG_READBACK": f"https://docs.google.com/forms/d/e/1FAIpQLScsfVAnZokYd-CDef1WZGgdNEY-AdqeS3erRF1mzy6Bl37eYg/formResponse?usp=pp_url\
	&entry.910646842={outputDF.get('serialNumber')}\
	&entry.351877676={outputDF.get('passed')}\
	&entry.2065736414={analysis_version}\
	&entry.1608510255={meas_version}\
	&entry.1353243899={layer}\
	&entry.507508481={site}\
	&entry.1425106615={timestamp}\
	&entry.613380586={results.get('AR_NOMINAL_SETTINGS')[0]}\
	&entry.2091108240={results.get('AR_NOMINAL_SETTINGS')[1]}\
	&entry.1308096676={results.get('AR_NOMINAL_SETTINGS')[2]}\
	&entry.1616657488={results.get('AR_NOMINAL_SETTINGS')[3]}\
	&entry.303689355={results.get('AR_NOMINAL_SETTINGS')[4]}\
	&entry.1299197252={results.get('AR_NOMINAL_SETTINGS')[5]}\
	&entry.337124367={results.get('AR_NOMINAL_SETTINGS')[6]}\
	&entry.539725220={results.get('AR_NOMINAL_SETTINGS')[7]}\
	&entry.174520567={results.get('AR_NOMINAL_SETTINGS')[8]}\
	&entry.2077557631={results.get('AR_NOMINAL_SETTINGS')[9]}\
	&entry.1152177529={results.get('AR_NOMINAL_SETTINGS')[10]}\
	&entry.1170074988={results.get('AR_NOMINAL_SETTINGS')[11]}\
	&entry.1695410680={results.get('AR_NOMINAL_SETTINGS')[12]}\
	&entry.1683989630={results.get('AR_NOMINAL_SETTINGS')[13]}\
	&entry.637795568={results.get('AR_NOMINAL_SETTINGS')[14]}\
	&entry.1796334891={results.get('AR_NOMINAL_SETTINGS')[15]}\
	&entry.1192471500={results.get('AR_NOMINAL_SETTINGS')[16]}\
	&entry.1037413000={results.get('AR_NOMINAL_SETTINGS')[17]}\
	&entry.1731827348={results.get('AR_NOMINAL_SETTINGS')[18]}\
	&entry.1788264831={results.get('AR_NOMINAL_SETTINGS')[19]}\
	&entry.1271298835={results.get('AR_NOMINAL_SETTINGS')[20]}\
	&entry.294928269={results.get('AR_NOMINAL_SETTINGS')[21]}\
	&entry.1752002697={results.get('AR_NOMINAL_SETTINGS')[22]}\
	&entry.1789768564={results.get('AR_NOMINAL_SETTINGS')[23]}\
	&entry.19338211={results.get('AR_NOMINAL_SETTINGS')[24]}\
	&entry.1373225730={results.get('AR_NOMINAL_SETTINGS')[25]}\
	&entry.1288561285={results.get('AR_NOMINAL_SETTINGS')[26]}\
	&entry.993587744={results.get('AR_NOMINAL_SETTINGS')[27]}\
	&entry.1225105463={results.get('AR_NOMINAL_SETTINGS')[28]}\
	&entry.2014795413={results.get('AR_NOMINAL_SETTINGS')[29]}\
	&entry.814046228={results.get('AR_NOMINAL_SETTINGS')[30]}\
	&entry.1206599091={results.get('AR_NOMINAL_SETTINGS')[31]}\
	&entry.1046023025={results.get('AR_NOMINAL_SETTINGS')[32]}\
	&entry.125849508={results.get('AR_NOMINAL_SETTINGS')[33]}\
	&entry.278665318={results.get('AR_NOMINAL_SETTINGS')[34]}\
	&entry.1317511634={results.get('AR_NOMINAL_SETTINGS')[35]}\
	&entry.799431715={results.get('AR_NOMINAL_SETTINGS')[36]}\
	&entry.1032356051={results.get('AR_NOMINAL_SETTINGS')[37]}\
	&entry.206739602={results.get('AR_NOMINAL_SETTINGS')[38]}\
	&entry.47441728={results.get('AR_NOMINAL_SETTINGS')[39]}\
	&entry.887166253={results.get('AR_NOMINAL_SETTINGS')[40]}\
	&entry.290527652={results.get('AR_NOMINAL_SETTINGS')[41]}\
	&entry.1481344879={results.get('AR_NOMINAL_SETTINGS')[42]}\
	&entry.155322339={results.get('AR_NOMINAL_SETTINGS')[43]}\
	&entry.556597681={results.get('AR_NOMINAL_SETTINGS')[44]}\
	&entry.1293797041={results.get('AR_NOMINAL_SETTINGS')[45]}\
	&entry.1984481605={results.get('AR_NOMINAL_SETTINGS')[46]}\
	&entry.1633430606={results.get('AR_NOMINAL_SETTINGS')[47]}\
	&entry.1430993123={results.get('AR_NOMINAL_SETTINGS')[48]}\
	&entry.526213623={results.get('AR_NOMINAL_SETTINGS')[49]}\
	&entry.1631275305={results.get('AR_NOMINAL_SETTINGS')[50]}\
	&entry.975590254={results.get('AR_NOMINAL_SETTINGS')[51]}\
	&entry.1474828103={results.get('AR_NOMINAL_SETTINGS')[52]}\
	&entry.1495459865={results.get('AR_NOMINAL_SETTINGS')[53]}\
	&entry.1128496051={results.get('AR_NOMINAL_SETTINGS')[54]}\
	&entry.367477458={results.get('AR_NOMINAL_SETTINGS')[55]}\
	&entry.1466626922={results.get('AR_NOMINAL_SETTINGS')[56]}\
	&entry.631124052={results.get('AR_NOMINAL_SETTINGS')[57]}\
	&entry.946981503={results.get('AR_NOMINAL_SETTINGS')[58]}\
	&entry.571213202={results.get('AR_NOMINAL_SETTINGS')[59]}\
	&entry.688702844={results.get('AR_NOMINAL_SETTINGS')[60]}\
	&entry.431853336={results.get('AR_NOMINAL_SETTINGS')[61]}\
	&entry.1724286670={results.get('AR_NOMINAL_SETTINGS')[62]}\
	&entry.2112361286={results.get('AR_NOMINAL_SETTINGS')[63]}\
	&entry.1689766951={results.get('AR_NOMINAL_SETTINGS')[64]}\
	&entry.2142543004={results.get('AR_NOMINAL_SETTINGS')[65]}\
	&entry.1946421005={results.get('AR_NOMINAL_SETTINGS')[66]}\
	&entry.707341702={results.get('AR_NOMINAL_SETTINGS')[67]}\
	&entry.1328302698={results.get('AR_NOMINAL_SETTINGS')[68]}\
	&entry.1022788500={results.get('AR_NOMINAL_SETTINGS')[69]}\
	&entry.973739200={results.get('AR_NOMINAL_SETTINGS')[70]}\
	&entry.1279705270={results.get('AR_NOMINAL_SETTINGS')[71]}\
	&entry.1637225517={results.get('AR_TEMP_NTC')}\
	&entry.1793217377={results.get('AR_TEMP_EXT')}\
	&entry.2135558015={results.get('AR_TEMP_ASLDO')}\
	&entry.1505388309={results.get('AR_TEMP_DSLDO')}\
	&entry.363112736={results.get('AR_TEMP_ACB')}\
	&entry.1942035528={results.get('AR_TEMP_ACB')}\
	&entry.1251896209={results.get('AR_VDDA_VS_TRIM')[0]}\
	&entry.896618670={results.get('AR_VDDA_VS_TRIM')[1]}\
	&entry.60914654={results.get('AR_VDDA_VS_TRIM')[2]}\
	&entry.961303064={results.get('AR_VDDA_VS_TRIM')[3]}\
	&entry.448329889={results.get('AR_VDDA_VS_TRIM')[4]}\
	&entry.1155979196={results.get('AR_VDDA_VS_TRIM')[5]}\
	&entry.412804010={results.get('AR_VDDA_VS_TRIM')[6]}\
	&entry.949350985={results.get('AR_VDDA_VS_TRIM')[7]}\
	&entry.307370261={results.get('AR_VDDA_VS_TRIM')[8]}\
	&entry.409514081={results.get('AR_VDDA_VS_TRIM')[9]}\
	&entry.2001782359={results.get('AR_VDDA_VS_TRIM')[10]}\
	&entry.10329903={results.get('AR_VDDA_VS_TRIM')[11]}\
	&entry.1636667111={results.get('AR_VDDA_VS_TRIM')[12]}\
	&entry.685698936={results.get('AR_VDDA_VS_TRIM')[13]}\
	&entry.537201174={results.get('AR_VDDA_VS_TRIM')[14]}\
	&entry.1053736177={results.get('AR_VDDA_VS_TRIM')[15]}\
	&entry.1435921809={results.get('AR_VDDD_VS_TRIM')[0]}\
	&entry.1499425666={results.get('AR_VDDD_VS_TRIM')[1]}\
	&entry.1890145904={results.get('AR_VDDD_VS_TRIM')[2]}\
	&entry.383115039={results.get('AR_VDDD_VS_TRIM')[3]}\
	&entry.398663489={results.get('AR_VDDD_VS_TRIM')[4]}\
	&entry.1566918433={results.get('AR_VDDD_VS_TRIM')[5]}\
	&entry.1555345873={results.get('AR_VDDD_VS_TRIM')[6]}\
	&entry.1092876262={results.get('AR_VDDD_VS_TRIM')[7]}\
	&entry.1293594936={results.get('AR_VDDD_VS_TRIM')[8]}\
	&entry.2099215210={results.get('AR_VDDD_VS_TRIM')[9]}\
	&entry.413539179={results.get('AR_VDDD_VS_TRIM')[10]}\
	&entry.1080321692={results.get('AR_VDDD_VS_TRIM')[11]}\
	&entry.259801418={results.get('AR_VDDD_VS_TRIM')[12]}\
	&entry.2100743637={results.get('AR_VDDD_VS_TRIM')[13]}\
	&entry.1600042255={results.get('AR_VDDD_VS_TRIM')[14]}\
	&entry.50695564={results.get('AR_VDDD_VS_TRIM')[15]}\
	&entry.1267721453={results.get('AR_ROSC_SLOPE')[0]}\
	&entry.1108238171={results.get('AR_ROSC_SLOPE')[1]}\
	&entry.405342661={results.get('AR_ROSC_SLOPE')[2]}\
	&entry.2036291468={results.get('AR_ROSC_SLOPE')[3]}\
	&entry.1125126277={results.get('AR_ROSC_SLOPE')[4]}\
	&entry.509984940={results.get('AR_ROSC_SLOPE')[5]}\
	&entry.1518471801={results.get('AR_ROSC_SLOPE')[6]}\
	&entry.1010295649={results.get('AR_ROSC_SLOPE')[7]}\
	&entry.1658294866={results.get('AR_ROSC_SLOPE')[8]}\
	&entry.1700088219={results.get('AR_ROSC_SLOPE')[9]}\
	&entry.1990240042={results.get('AR_ROSC_SLOPE')[10]}\
	&entry.1994855141={results.get('AR_ROSC_SLOPE')[11]}\
	&entry.2004501020={results.get('AR_ROSC_SLOPE')[12]}\
	&entry.619680759={results.get('AR_ROSC_SLOPE')[13]}\
	&entry.1547920247={results.get('AR_ROSC_SLOPE')[14]}\
	&entry.112225409={results.get('AR_ROSC_SLOPE')[15]}\
	&entry.8615499={results.get('AR_ROSC_SLOPE')[16]}\
	&entry.447685801={results.get('AR_ROSC_SLOPE')[17]}\
	&entry.948996117={results.get('AR_ROSC_SLOPE')[18]}\
	&entry.549701779={results.get('AR_ROSC_SLOPE')[19]}\
	&entry.2034139644={results.get('AR_ROSC_SLOPE')[20]}\
	&entry.1738370945={results.get('AR_ROSC_SLOPE')[21]}\
	&entry.680984854={results.get('AR_ROSC_SLOPE')[22]}\
	&entry.380214201={results.get('AR_ROSC_SLOPE')[23]}\
	&entry.1949714184={results.get('AR_ROSC_SLOPE')[24]}\
	&entry.2080061991={results.get('AR_ROSC_SLOPE')[25]}\
	&entry.1355093371={results.get('AR_ROSC_SLOPE')[26]}\
	&entry.983676271={results.get('AR_ROSC_SLOPE')[27]}\
	&entry.1022530148={results.get('AR_ROSC_SLOPE')[28]}\
	&entry.2066074162={results.get('AR_ROSC_SLOPE')[29]}\
	&entry.1683950787={results.get('AR_ROSC_SLOPE')[30]}\
	&entry.1799042116={results.get('AR_ROSC_SLOPE')[31]}\
	&entry.352512380={results.get('AR_ROSC_SLOPE')[32]}\
	&entry.953608394={results.get('AR_ROSC_SLOPE')[33]}\
	&entry.1335702676={results.get('AR_ROSC_SLOPE')[34]}\
	&entry.1182244852={results.get('AR_ROSC_SLOPE')[35]}\
	&entry.869372092={results.get('AR_ROSC_SLOPE')[36]}\
	&entry.1109476155={results.get('AR_ROSC_SLOPE')[37]}\
	&entry.696844799={results.get('AR_ROSC_SLOPE')[38]}\
	&entry.881044474={results.get('AR_ROSC_SLOPE')[39]}\
	&entry.210472674={results.get('AR_ROSC_SLOPE')[40]}\
	&entry.1561547505={results.get('AR_ROSC_SLOPE')[41]}\
	&entry.294359514={results.get('AR_ROSC_OFFSET')[0]}\
	&entry.218278347={results.get('AR_ROSC_OFFSET')[1]}\
	&entry.1296340612={results.get('AR_ROSC_OFFSET')[2]}\
	&entry.325246147={results.get('AR_ROSC_OFFSET')[3]}\
	&entry.1461792727={results.get('AR_ROSC_OFFSET')[4]}\
	&entry.147717067={results.get('AR_ROSC_OFFSET')[5]}\
	&entry.308162325={results.get('AR_ROSC_OFFSET')[6]}\
	&entry.340294729={results.get('AR_ROSC_OFFSET')[7]}\
	&entry.1216091165={results.get('AR_ROSC_OFFSET')[8]}\
	&entry.1537892680={results.get('AR_ROSC_OFFSET')[9]}\
	&entry.651177331={results.get('AR_ROSC_OFFSET')[10]}\
	&entry.346475768={results.get('AR_ROSC_OFFSET')[11]}\
	&entry.1035896081={results.get('AR_ROSC_OFFSET')[12]}\
	&entry.2143379250={results.get('AR_ROSC_OFFSET')[13]}\
	&entry.923945135={results.get('AR_ROSC_OFFSET')[14]}\
	&entry.989723257={results.get('AR_ROSC_OFFSET')[15]}\
	&entry.971816065={results.get('AR_ROSC_OFFSET')[16]}\
	&entry.552958174={results.get('AR_ROSC_OFFSET')[17]}\
	&entry.739541542={results.get('AR_ROSC_OFFSET')[18]}\
	&entry.186269499={results.get('AR_ROSC_OFFSET')[19]}\
	&entry.502633129={results.get('AR_ROSC_OFFSET')[20]}\
	&entry.1532319666={results.get('AR_ROSC_OFFSET')[21]}\
	&entry.1786481368={results.get('AR_ROSC_OFFSET')[22]}\
	&entry.921537910={results.get('AR_ROSC_OFFSET')[23]}\
	&entry.91112264={results.get('AR_ROSC_OFFSET')[24]}\
	&entry.1403783859={results.get('AR_ROSC_OFFSET')[25]}\
	&entry.880466574={results.get('AR_ROSC_OFFSET')[26]}\
	&entry.255500529={results.get('AR_ROSC_OFFSET')[27]}\
	&entry.406968658={results.get('AR_ROSC_OFFSET')[28]}\
	&entry.252699286={results.get('AR_ROSC_OFFSET')[29]}\
	&entry.73007307={results.get('AR_ROSC_OFFSET')[30]}\
	&entry.22088182={results.get('AR_ROSC_OFFSET')[31]}\
	&entry.460622752={results.get('AR_ROSC_OFFSET')[32]}\
	&entry.987149730={results.get('AR_ROSC_OFFSET')[33]}\
	&entry.1559814776={results.get('AR_ROSC_OFFSET')[34]}\
	&entry.1700713522={results.get('AR_ROSC_OFFSET')[35]}\
	&entry.417646576={results.get('AR_ROSC_OFFSET')[36]}\
	&entry.1968942403={results.get('AR_ROSC_OFFSET')[37]}\
	&entry.1596668024={results.get('AR_ROSC_OFFSET')[38]}\
	&entry.2058648829={results.get('AR_ROSC_OFFSET')[39]}\
	&entry.1785914={results.get('AR_ROSC_OFFSET')[40]}\
	&entry.1316032248={results.get('AR_ROSC_OFFSET')[41]}",
    }
    log.info(
        bcolors.WARNING
        + "Copy the following URL into a browser to submit these results: \n"
        + url.get(outputDF.get("testType")).replace("\t", "")
        + "\n"
        + "View submitted results at: https://docs.google.com/spreadsheets/d/1pw_07F94fg2GJQr8wlvhaRUV63uhsAuBt_S1FEFBzBU/view"
        + bcolors.ENDC
    )
    with Path(outputfile).open("a", encoding="utf-8") as fpointer:
        fpointer.writelines(url.get(outputDF.get("testType")).replace("\t", "") + "\n")
