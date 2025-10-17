#!/usr/bin/env python3
from __future__ import annotations

import json
import logging
from pathlib import Path

import jsonschema
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from jsonschema import validate

from module_qc_analysis_tools import data
from module_qc_analysis_tools.utils.analysis import (
    get_layer,
)
from module_qc_analysis_tools.utils.misc import bcolors

log = logging.getLogger("analysis")

# Turn off matplotlib DEBUG messages
plt.set_loglevel(level="warning")


# Pixel failure categories and corresponding bit
testbit_ordered_names = [
    "COLUMN_DISABLED",
    "DEAD_DIGITAL",
    "BAD_DIGITAL",
    "DEAD_ANALOG",
    "BAD_ANALOG",
    "THRESHOLD_FAILED_FITS",
    "TUNING_BAD",
    "HIGH_ENC",
    "HIGH_NOISE",
    "MERGED_BUMPS",
    "DISCONNECTED_BUMPS_ZERO_BIAS_SCAN",
    "DISCONNECTED_BUMPS_XTALK_SCAN",
    "DISCONNECTED_BUMPS_SOURCE_SCAN",
    "DISCONNECTED_PIXELS",
]

testbit_map = {}
for i_testbit, name_testbit in enumerate(testbit_ordered_names):
    testbit_map[name_testbit] = i_testbit

# Required scans for each test. Tests will still run without required scan, but chip will fail QC.
# The selftrigger_source scan is optional in the pixel failure analysis.
# Note that this dictionary isn't really used, its more of a reference for developers
required_tests = {
    "MIN_HEALTH_TEST": [
        "std_digitalscan",
        "std_analogscan",
        "std_thresholdscan_hr",
        "std_totscan",
    ],
    "TUNING": [
        "std_tune_globalthreshold",
        "std_thresholdscan_hr",
        "std_tune_pixelthreshold",
        "std_retune_globalthreshold",
        "std_retune_pixelthreshold",
        "std_thresholdscan_hd",
        "std_totscan",
    ],
    "PIXEL_FAILURE_ANALYSIS": [
        "std_digitalscan",
        "std_analogscan",
        "std_thresholdscan_hd",  # Two scans needed, one with HV and one without
        "std_noisescan",
        "std_discbumpscan",
        "std_mergedbumpscan",
        "selftrigger_source",
    ],
}


# Given a pixel failure category, returns corresponding bit
def get_fail_bit(name):
    if name not in testbit_map:
        log.error(
            bcolors.BADRED
            + f"Asking for bit for {name}, but {name} not present in {testbit_map} - please check!"
            + bcolors.ENDC
        )
        raise RuntimeError()
    return testbit_map.get(name)


# Given pixel failure bit, returns corresponding category name
def get_name_from_bit(bit):
    try:
        index = list(testbit_map.values()).index(bit)
        return list(testbit_map.keys())[index]
    except Exception as err:
        log.error(
            bcolors.BADRED
            + f"Problem finding test name for bit {bit}, please check test name - bit mapping"
            + bcolors.ENDC
        )
        raise RuntimeError() from err


# Sets bit as 1 in integer
def set_bit(value, bit):
    return value | (1 << bit)


# Given array of pixel indices, returns corresponding rows and columns of those pixels
def get_loc_from_index(index):
    return int(index / 400), int(index % 400)


# Given row and column of single pixel, returns corresponding index
def get_index_from_loc(row, col):
    return row * 400 + col


# Loads json file
def read_json(input_file):
    try:
        input_data = json.loads(input_file.read_text(encoding="utf-8"))
    except Exception as e:
        log.error(
            bcolors.BADRED + f"{input_file} is ill-formatted, please fix" + bcolors.ENDC
        )
        raise RuntimeError() from e
    return input_data


# Uses global chip config to create a pixel map of pixels with core columns disabled. Inputs are chip config (json), chiptype (string, e.g. "RD53B"), failbit array (array of one int) which is just the params in the classification.json file. Returns the map and the number of disabled core columns
def format_coreCol_input(input_chip_config, chiptype, failbit_arr):
    nCol = 400
    nRow = 384
    nCoreCol = 50
    failbit = failbit_arr[0]
    nCol_per_CoreCol = int(nCol / nCoreCol)
    mask = np.ones((nCol, nRow)) + failbit
    numBadCoreCols = 0

    out = {}
    registers = [
        input_chip_config[chiptype]["GlobalConfig"][f"EnCoreCol{regnum}"]
        for regnum in range(4)
    ]

    binary_bits = []
    register_lens = ["016b", "016b", "016b", "06b"]
    for reg, register_len in zip(registers, register_lens):
        binary_str = format(reg, register_len)
        reversed_binary_str = binary_str[::-1]
        binary_bits.extend(reversed_binary_str)
    bits = [int(bit) for bit in binary_bits]

    for i in range(nCoreCol):
        if bits[i] == 0:
            numBadCoreCols += 1
            for col in range(nCol_per_CoreCol):
                for row in range(nRow):
                    mask[int(i * nCol_per_CoreCol + col), row] = failbit

    out["Data"] = mask
    return out, numBadCoreCols


# Schema check for json file containing all input YARR scans
def check_input_yarr_config(input_data, path):
    info_schema_path = str(data / "schema/info_schema.json")
    with Path(info_schema_path).open(encoding="utf-8") as inFile:
        info_schema = json.load(inFile)
    try:
        validate(instance=input_data, schema=info_schema)
    except jsonschema.exceptions.ValidationError as err:
        log.error(
            bcolors.BADRED
            + "Input YARR config fails schema check with the following error:"
            + bcolors.ENDC
        )
        log.error(bcolors.BADRED + f"Input YARR config: {path}" + bcolors.ENDC)
        log.error(bcolors.BADRED + f"Json Schema: {info_schema_path}" + bcolors.ENDC)
        log.error(err.message)
        raise RuntimeError() from None


# Schema check for output data from YARR scan
def check_input_yarr_data(input_data, path, config=False):
    if config:
        input_chipconfig_schema_path = str(data / "schema/input_chipconfig_schema.json")
        with Path(input_chipconfig_schema_path).open(encoding="utf-8") as inFile:
            input_chipconfig_schema = json.load(inFile)
        try:
            validate(instance=input_data, schema=input_chipconfig_schema)
        except jsonschema.exceptions.ValidationError as err:
            log.error(
                bcolors.BADRED
                + "Input chip configuration fails schema check with the following error:"
                + bcolors.ENDC
            )
            log.error(bcolors.BADRED + f"Input chip config: {path}" + bcolors.ENDC)
            log.error(
                bcolors.BADRED
                + f"Json Schema: {input_chipconfig_schema_path}"
                + bcolors.ENDC
            )
            log.error(err.message[0:200] + " ... " + err.message[-200:])
            raise RuntimeError() from None
    else:
        input_yarr_schema_path = str(data / "schema/input_yarr_schema.json")
        with Path(input_yarr_schema_path).open(encoding="utf-8") as inFile:
            input_yarr_schema = json.load(inFile)
        try:
            validate(instance=input_data, schema=input_yarr_schema)
        except jsonschema.exceptions.ValidationError as err:
            log.error(
                bcolors.BADRED
                + "Input YARR data fails schema check with the following error:"
                + bcolors.ENDC
            )
            log.error(bcolors.BADRED + f"Input YARR data: {path}" + bcolors.ENDC)
            log.error(
                bcolors.BADRED + f"Json Schema: {input_yarr_schema_path}" + bcolors.ENDC
            )
            log.error(err.message[0:200] + " ... " + err.message[-200:])
            raise RuntimeError() from None


# Transforms pixel data into flattened array
# Pixel data is formatted so 0th column is FE pad side, and orientation is so that pads are on top (looking top-down on module)
def format_pixel_input(input_data):
    _data = input_data.get("Data")
    _data = np.array(_data).transpose()
    _data = _data[::-1, ::-1]
    return _data.flatten()


# Loads TDAC input from chip config and returns as flattened array
def format_TDAC_input(config):
    _data = np.empty(0)
    chipType = next(iter(config))
    for col in config.get(chipType).get("PixelConfig"):
        _data = np.concatenate((_data, col.get("TDAC")))
    _data = _data.reshape(400, 384).transpose()
    _data = _data[::-1, ::-1]
    return _data.flatten()


# Loads enable input from chip config returns as flattened array
def format_enable_input(config):
    _data = np.empty(0)

    chipType = next(iter(config))
    for col in config.get(chipType).get("PixelConfig"):
        _data = np.concatenate((_data, col.get("Enable")))
    _data = _data.reshape(400, 384).transpose()
    _data = _data[::-1, ::-1]
    return _data.flatten()


# Returns flattened array of pixel indices
def get_pixel_index():
    pix_index = np.empty((384, 400))
    for r in range(384):
        pix_index[r, :] = np.arange(r * 400, r * 400 + 400, dtype=int)
    return pix_index.flatten()


# Gets layer-specific selection, if necessary
def check_test_params(test_params, layer, test_name):
    if isinstance(test_params, dict):
        layer_name = get_layer(layer)
        layer_bounds = test_params.get(layer_name)
        if not layer_bounds:
            log.error(
                bcolors.ERROR
                + f" QC selections for {test_name} and {layer_name} do not exist - please check! Skipping."
                + bcolors.ENDC
            )
            return False
        return layer_bounds
    return test_params


# Checks that pixel selection make sense with specified test method
def check_test_method(test_method, test_params):
    if test_method == "MinBound":
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"MinBound cut requested, but {len(test_params)} params provided! Please only provide single lower bound"
                + bcolors.ENDC,
            )
            raise RuntimeError()
    elif test_method == "MaxBound":
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"MaxBound cut requested, but {len(test_params)} params provided! Please only provide single upper bound"
                + bcolors.ENDC,
            )
            raise RuntimeError()
    elif test_method == "MinMaxBound":
        if len(test_params) != 2:
            log.error(
                bcolors.BADRED
                + f"MinMaxBound cut requested, but {len(test_params)} params provided! Please only provide single lower and upper params"
                + bcolors.ENDC,
            )
            raise RuntimeError()
    elif test_method == "RemoveOneValue":
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"RemoveOneValue cut requested, but {len(test_params)} params provided! Please only provide single value to remove"
                + bcolors.ENDC,
            )
            raise RuntimeError()
    elif test_method == "Outlier":
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"Outlier cut requested, but {len(test_params)} params provided! Please only provide single value to determine outliers"
                + bcolors.ENDC,
            )
            raise RuntimeError()
    elif test_method == "percentile":
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"Percentile cut requested, but {len(test_params)} params provided! Please only provide single percentile"
                + bcolors.ENDC,
            )
            raise RuntimeError()
    else:
        log.error(
            bcolors.BADRED
            + f"Method {test_method} not recognized. Skipping"
            + bcolors.ENDC
        )
        return -1
    return 0


# Checks if specific pixel failure category was checked
def check_record(record_fail, test_name):
    test_bit = set_bit(0, get_fail_bit(test_name))
    return record_fail & test_bit == test_bit


# Returns list of flattened arrays, where each array indicates which pixels passed/failed each failure category
def get_result_arrays(fail, fail_record):
    # Counts pixels that have been classified
    failures_dependent = []  # List of (153600,) arrays, one for each possible failure
    failures_independent = []  # List of (153600,) arrays, one for each possible failure
    for t in testbit_map:
        fail_bit = set_bit(0, get_fail_bit(t))

        # Only store results that were recorded
        if not check_record(fail_record, t):
            failures_dependent += [np.full(shape=(153600,), fill_value=-1)]
            failures_independent += [np.full(shape=(153600,), fill_value=-1)]
            continue

        independent_mask = fail & fail_bit == fail_bit
        failures_independent += [independent_mask]

        # Count how many pixels have failed this test, and passed all previous tests
        test_bit = 0
        for i in range(get_fail_bit(t) + 1):
            if not check_record(fail_record, get_name_from_bit(i)):
                continue
            test_bit = set_bit(test_bit, i)
        dependent_mask = fail & test_bit == fail_bit
        failures_dependent += [dependent_mask]

    return failures_independent, failures_dependent


# Counts pixels failing each category (dependent / independent / integrated)
def count_pixels(fail, fail_record, test_names, ignore_bad_corecol):
    log.info("")
    log.info("Classifying pixel failures!")
    log.info("")
    # Counts pixels that have been classified
    failures = {}
    total_failures = 0
    for t in testbit_map:
        # Skip tests that do not classify pixels
        if t not in test_names:
            log.debug(
                bcolors.WARNING
                + f"count_pixels: {t} not used to classify pixels, skipping "
                + bcolors.ENDC
            )
            continue

        failures.update({t: {}})
        fail_bit = set_bit(0, get_fail_bit(t))
        ccbit = set_bit(0, get_fail_bit("COLUMN_DISABLED"))

        # Only store results that were recorded
        if not check_record(fail_record, t):
            log.debug(
                bcolors.WARNING
                + f"count_pixels: {t} not checked, skipping "
                + bcolors.ENDC
            )
            failures.get(t).update({"independent": -1})
            failures.get(t).update({"dependent": -1})
            try:
                failures.get(t).update(
                    {"integrated": list(failures.values())[-2].get("integrated")}
                )
            except Exception:
                failures.get(t).update({"integrated": -1})
            continue

        # if ignore bad corecol turned on, dont count cc pixels in other tests
        if t != "COLUMN_DISABLED" and ignore_bad_corecol:
            nfail_independent = len(
                fail[(fail & fail_bit == fail_bit) & (fail & ccbit != ccbit)]
            )
        else:
            nfail_independent = len(fail[(fail & fail_bit == fail_bit)])

        failures.get(t).update({"independent": nfail_independent})

        # Count how many pixels have failed this test, and passed all previous tests
        test_bit = 0
        max_bit = get_fail_bit(t)
        for i in range(max_bit + 1):
            if get_name_from_bit(i) not in test_names:
                continue
            if not check_record(fail_record, get_name_from_bit(i)):
                continue
            if (
                "DISCONNECTED" in t
                and "DISCONNECTED_BUMPS_" in get_name_from_bit(i)
                and t != get_name_from_bit(i)
            ):
                # Ignore data from 'DISCONNECTED_BUMPS_' categories, which are only for diagnostic purposes
                continue
            test_bit = set_bit(test_bit, i)
        nfail_dependent = len(fail[fail & test_bit == fail_bit])
        failures.get(t).update({"dependent": nfail_dependent})

        if ("DISCONNECTED_BUMPS_" not in t) and (
            ("COLUMN_DISABLED" not in t) or not ignore_bad_corecol
        ):
            total_failures += nfail_dependent

        failures.get(t).update({"integrated": total_failures})

    return failures


# Identify pixels in simple (not-custom-method) pixel failure category
def classify_pixels(_data, fail, record, test_name, test_method, test_params):
    pix_fail = np.copy(fail)
    fail_bit = get_fail_bit(test_name)

    # Check pixel classification
    error_code = check_test_method(test_method, test_params)
    if error_code:
        return error_code

    # Identify failures
    if test_method == "MinBound":
        failures = np.where(_data < test_params[0])

    elif test_method == "MaxBound":
        failures = np.where(_data > test_params[0])

    elif test_method == "MinMaxBound":
        failures = np.where((_data < test_params[0]) | (_data > test_params[1]))

    elif test_method == "RemoveOneValue":
        failures = np.where(_data == test_params[0])

    elif test_method == "Outlier":
        mean = np.mean(_data)
        failures = np.where(np.abs(_data - mean) > test_params[0])

    else:
        msg = f"Test method {test_method} is not valid"
        raise ValueError(msg)

    # Record failures
    record = set_bit(record, fail_bit)
    mask = np.zeros_like(pix_fail, dtype=bool)
    mask[failures] = True
    pix_fail[mask] = set_bit(pix_fail[mask], fail_bit)

    return pix_fail, record


# Identifies merged pixels
def identify_merged_pixels(
    _data, fail, record, test_name, test_params, outputdir, chipname
):
    pix_fail = np.copy(fail)
    fail_bit = get_fail_bit(test_name)
    pix_index = get_pixel_index()

    # Identify pixels which have occupancy > value
    occ = np.where(_data > test_params[0])
    occ_index = pix_index[occ]

    merged_paired = np.empty(0).astype(int)
    merged_unpaired = np.empty(0).astype(int)

    # Skip neighbor check if too many (10%) merged pixels
    if len(occ_index) > 15360:
        log.warning(
            bcolors.WARNING
            + f"There are too many pixels with occupancy in merged bump scan ({len(occ_index)}). Will skip neighboring pixel check and assume all merged pixels are paired. Please investigate."
            + bcolors.ENDC
        )
        merged_paired = occ_index.astype(int)
    else:
        # Identify paired pixels
        rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(occ_index)

        for r, c in zip(rows, cols):
            check = np.empty(0)

            # Find index of neighboring pixels
            if r != 0:
                check = np.append(check, get_index_from_loc(r - 1, c))
            if r != 383:
                check = np.append(check, get_index_from_loc(r + 1, c))
            if c != 0:
                check = np.append(check, get_index_from_loc(r, c - 1))
            if c != 399:
                check = np.append(check, get_index_from_loc(r, c + 1))

            # Check if any of neighboring pixels have occupancy
            if len(np.intersect1d(check, occ_index) > 0):
                merged_paired = np.append(
                    merged_paired, get_index_from_loc(r, c)
                ).astype(int)
            else:
                merged_unpaired = np.append(
                    merged_unpaired, get_index_from_loc(r, c)
                ).astype(int)

    # Record merged paired as failures
    record = set_bit(record, fail_bit)
    mask = np.zeros_like(pix_fail, dtype=bool)
    mask[merged_paired] = True
    pix_fail[mask] = set_bit(pix_fail[mask], fail_bit)

    # Plot location of merged pixels
    plt.clf()
    _fig, ax = plt.subplots()
    plt.xlabel("Row", fontsize=12)
    plt.ylabel("Column", fontsize=12)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylim((-1, 401))
    plt.xlim((-1, 385))
    plt.subplots_adjust(right=0.885)
    plt.subplots_adjust(left=0.165)
    plt.subplots_adjust(top=0.87)

    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(merged_paired)
    plt.scatter(
        rows,
        cols,
        marker="s",
        s=2,
        c="darkmagenta",
        label=f"Merged (paired): {len(merged_paired)}",
    )
    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(merged_unpaired)
    plt.scatter(
        rows,
        cols,
        marker="s",
        s=2,
        c="lightseagreen",
        label=f"Merged (unpaired): {len(merged_unpaired)}",
    )

    plt.legend(
        loc="upper left",
        bbox_to_anchor=(0.22, 1.1),
        borderaxespad=0.0,
        handlelength=0.2,
        ncol=2,
        markerscale=2,
        fontsize=11,
    )
    plt.text(
        0.0,
        1.05,
        chipname,
        fontsize=11,
        transform=ax.transAxes,
    )
    log.info("Saving " + str(outputdir.joinpath(f"{chipname}_merged.png")))
    plt.savefig(outputdir.joinpath(f"{chipname}_merged.png"))
    plt.close()

    return pix_fail, record


# Identifies pixels with low noise difference
def identify_zerobias_pixels(
    noise_hv, noise_nohv, fail, record, test_name, test_params
):
    pix_fail = np.copy(fail)
    fail_bit = get_fail_bit(test_name)
    pix_index = get_pixel_index()

    # Find pixel locations where 1) _data was present for both noHV/withHV and 2) fail selection
    noise_diff = noise_nohv - noise_hv
    noise_hv_nonzero = noise_hv != 0
    noise_nohv_nonzero = noise_nohv != 0
    fail_diff = noise_diff <= test_params[0]
    selection_mask = noise_nohv_nonzero & noise_hv_nonzero & fail_diff
    fail_zerobias = pix_index[selection_mask].astype(int)

    # Record merged paired as failures
    record = set_bit(record, fail_bit)
    mask = np.zeros_like(pix_fail, dtype=bool)
    mask[fail_zerobias] = True
    pix_fail[mask] = set_bit(pix_fail[mask], fail_bit)

    return pix_fail, record


# Identifies pixels without cross-talk in disconnected bump scan
def identify_noxtalk_pixels(_data, fail, record, test_name, test_params):
    pix_fail = np.copy(fail)
    fail_bit = get_fail_bit(test_name)
    pix_index = get_pixel_index()

    # Identify pixels which have occupancy < value
    noxtalk = np.where(_data <= test_params[0])
    noxtalk_index = pix_index[noxtalk].astype(int)

    # Record pixels with no xtalk as failures
    record = set_bit(record, fail_bit)
    mask = np.zeros_like(pix_fail, dtype=bool)
    mask[noxtalk_index] = True
    pix_fail[mask] = set_bit(pix_fail[mask], fail_bit)

    return pix_fail, record


# Identify pixels without enough hits in source scan
def identify_nosource_pixels(
    _data, enable, fail, record, test_name, test_params, outputdir, chipname
):
    pix_fail = np.copy(fail)
    fail_bit = get_fail_bit(test_name)
    pix_index = get_pixel_index()

    # Identify pixels which have occupancy > value
    nosource_mask = _data <= test_params[0]
    enable_mask = enable == 1
    combined_mask = nosource_mask & enable_mask
    nosource = np.where(combined_mask == 1)
    nosource_index = pix_index[nosource].astype(int)

    # 2D histogram of source counts
    plotdata = _data.reshape((400, 384))

    num_bins_x = plotdata.shape[1]
    num_bins_y = plotdata.shape[0]

    xvalues = np.arange(plotdata.shape[1]).repeat(plotdata.shape[0])
    yvalues = np.tile(np.arange(plotdata.shape[0]), plotdata.shape[1])

    plt.set_loglevel(level="warning")

    plt.clf()
    _h, _xedges, _yedges = np.histogram2d(
        x=xvalues, y=yvalues, bins=[num_bins_x - 1, num_bins_y - 1]
    )
    plt.hist2d(
        x=xvalues,
        y=yvalues,
        bins=[num_bins_x - 1, num_bins_y - 1],
        weights=plotdata.flatten(),
        cmap="viridis",
        norm=mcolors.LogNorm(),
    )
    plt.title(f"{chipname}", fontsize=12)

    cbar = plt.colorbar()
    cbar.set_label("Source counts")

    plt.xlabel("Rows")
    plt.ylabel("Columns")

    log.info("Saving " + str(outputdir.joinpath(f"{chipname}_source2d.png")))
    plt.savefig(outputdir.joinpath(f"{chipname}_source2d.png"))
    plt.close()

    # Record pixels without occupancy as failures
    record = set_bit(record, fail_bit)
    mask = np.zeros_like(pix_fail, dtype=bool)
    mask[nosource_index] = True
    pix_fail[mask] = set_bit(pix_fail[mask], fail_bit)

    return pix_fail, record


# Makes 1D histograms of tuning data
def plot_1d_hist(
    _data,
    test_name,
    test_method,
    test_params,
    xlabel,
    outputdir,
    chipname,
):
    plt.set_loglevel(level="warning")
    plt.clf()
    _fig, ax = plt.subplots()
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel("Number of pixels", fontsize=12)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.yscale("log")
    plt.title(f"{test_name} selection for chip {chipname}", fontsize=12)
    plt.tight_layout()
    _data = _data.flatten()
    mean = np.mean(_data)

    minRange = 0
    maxRange = int(max(_data) + max(_data) * 0.3)
    bins = range(
        minRange,
        maxRange,
        max(5, int(np.mean(_data) / 50)),
    )
    if "TDAC" in test_name:
        minRange = -15
        maxRange = 15
        bins = range(minRange, maxRange + 1, 1)
    if "TOT" in test_name:
        minRange = 0
        maxRange = 15
        bins = range(minRange, maxRange + 1, 1)

    n0, _b0, _plt0 = plt.hist(
        _data,
        bins=bins,
        linewidth=1,
        histtype="step",
        ec="black",
        fill=False,
    )
    ax.set_ylim(0.5, max(n0) + max(n0) * 100)
    ax.set_xlim(minRange, maxRange)
    plt.axvline(x=mean, ymin=0.0, ymax=0.8, color="gray", linestyle=":")
    plt.text(
        (mean - minRange) / (maxRange - minRange),
        0.82,
        round(mean, 1),
        fontsize=10,
        color="gray",
        transform=ax.transAxes,
        ha="center",
        rotation=45,
    )

    failures = -1
    # Draw selection
    if test_method in ["MinBound", "MaxBound"]:
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"MaxBound cut requested, but {len(test_params)} params provided! Please only provide single upper bound"
                + bcolors.ENDC,
            )
            raise RuntimeError()
        plt.axvline(x=test_params[0], ymin=0.0, ymax=0.8, color="red", linestyle=":")
        plt.text(
            (test_params[0] - minRange) / (maxRange - minRange),
            0.82,
            round(test_params[0], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        if test_method == "MinBound":
            failures = np.where(_data < test_params[0])
        else:
            failures = np.where(_data > test_params[0])
    elif test_method == "MinMaxBound":
        if len(test_params) != 2:
            log.error(
                bcolors.BADRED
                + f"MinMaxBound cut requested, but {len(test_params)} params provided! Please only provide single lower and upper params"
                + bcolors.ENDC,
            )
            raise RuntimeError()
        plt.axvline(x=test_params[0], ymin=0.0, ymax=0.8, color="red", linestyle=":")
        plt.axvline(x=test_params[1], ymin=0.0, ymax=0.8, color="red", linestyle=":")
        plt.text(
            (test_params[0] - minRange) / (maxRange - minRange),
            0.82,
            round(test_params[0], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        plt.text(
            (test_params[1] - minRange) / (maxRange - minRange),
            0.82,
            round(test_params[1], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        failures = np.where((_data < test_params[0]) | (_data > test_params[1]))
    elif test_method == "Outlier":
        if len(test_params) != 1:
            log.error(
                bcolors.BADRED
                + f"Outlier cut requested, but {len(test_params)} params provided! Please only provide single value to determine outliers"
                + bcolors.ENDC,
            )
            raise RuntimeError()
        plt.axvline(
            x=mean + test_params[0], ymin=0.0, ymax=0.8, color="red", linestyle=":"
        )
        plt.axvline(
            x=mean - test_params[0], ymin=0.0, ymax=0.8, color="red", linestyle=":"
        )
        plt.text(
            (mean + test_params[0] - minRange) / (maxRange - minRange),
            0.82,
            round(mean + test_params[0], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        plt.text(
            (mean - test_params[0] - minRange) / (maxRange - minRange),
            0.82,
            round(mean - test_params[0], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        failures = np.where(np.abs(_data - mean) > test_params[0])
    elif len(test_params) == 3:
        plt.axvline(x=test_params[0], ymin=0.0, ymax=0.8, color="red", linestyle=":")
        plt.axvline(x=test_params[1], ymin=0.0, ymax=0.8, color="red", linestyle=":")
        plt.text(
            (test_params[0] - minRange) / (maxRange - minRange),
            0.82,
            round(test_params[0], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        plt.text(
            (test_params[1] - minRange) / (maxRange - minRange),
            0.82,
            round(test_params[1], 1),
            fontsize=10,
            color="red",
            transform=ax.transAxes,
            ha="center",
            rotation=45,
        )
        # Assumes mean is used for selection
        if (
            np.round(mean, test_params[2]) > test_params[0]
            and np.round(mean, test_params[2]) < test_params[1]
        ):
            plt.text(
                0.02,
                0.92,
                "Passes QC selection",
                transform=ax.transAxes,
                color="green",
            )
        else:
            plt.text(
                0.02,
                0.92,
                "Fails QC selection",
                transform=ax.transAxes,
                color="red",
            )

    if failures != -1:
        plt.text(
            0.02,
            0.92,
            f"Failing pixels: {len(failures[0])}",
            transform=ax.transAxes,
            color="red",
        )

    log.info(
        "Saving "
        + str(
            outputdir.joinpath(f"{chipname}_{test_name}_{xlabel.split(' ')[0]}_1d.png")
        )
    )
    plt.savefig(
        outputdir.joinpath(f"{chipname}_{test_name}_{xlabel.split(' ')[0]}_1d.png")
    )
    plt.close()


# Makes 1D histograms comparing 0-bias & disconnected bump scan, and source & disconnected bump scan data
def plot_1d_discbumps(
    occ_sourcescan,
    en_sourcescan,
    occ_xtalk,
    noise_nohv,
    noise_hv,
    params_xtalk,
    outputdir,
    chipname,
    identifier,
):
    # Identify pixels which have occupancy > value
    enable_mask = en_sourcescan == 1
    xtalk_mask = occ_xtalk > params_xtalk[0]

    if np.any(occ_sourcescan) and np.any(en_sourcescan):
        xtalk_combined_mask = xtalk_mask & enable_mask
        noxtalk_combined_mask = ~xtalk_mask & enable_mask
        # 1D histogram of source counts, with and without x-talk
        source_withxtalk = occ_sourcescan[xtalk_combined_mask]
        source_noxtalk = occ_sourcescan[noxtalk_combined_mask]

        plt.set_loglevel(level="warning")
        plt.clf()
        _fig, ax = plt.subplots()
        plt.xlabel("Hits", fontsize=12)
        plt.ylabel("Number of enabled pixels", fontsize=12)
        plt.xticks(fontsize=13)
        plt.yticks(fontsize=13)
        plt.yscale("log")
        plt.title("Results from source scan", fontsize=12)
        plt.tight_layout()
        plt.text(
            0.02,
            0.93,
            identifier,
            fontsize=11,
            transform=ax.transAxes,
        )
        if np.any(source_withxtalk):
            mean_withxtalk = np.mean(source_withxtalk)
            std_withxtalk = np.std(source_withxtalk)
            plt.text(
                0.02,
                0.86,
                "$\\mu$ = "
                + str(round(mean_withxtalk))
                + ", $\\sigma$ = "
                + str(round(std_withxtalk))
                + " (hits)",
                fontsize=11,
                color="black",
                transform=ax.transAxes,
            )
        if np.any(source_noxtalk):
            mean_noxtalk = np.mean(source_noxtalk)
            std_noxtalk = np.std(source_noxtalk)
            plt.text(
                0.02,
                0.79,
                "$\\mu$ = "
                + str(round(mean_noxtalk))
                + ", $\\sigma$ = "
                + str(round(std_noxtalk))
                + " (hits)",
                fontsize=11,
                color="darkmagenta",
                transform=ax.transAxes,
            )

        minRange = 0
        maxRange = min(2000, int(max(occ_sourcescan[en_sourcescan == 1])))
        bins = range(
            minRange,
            maxRange,
            max(5, int(np.mean(occ_sourcescan[en_sourcescan == 1]) / 30)),
        )
        n0, _b0, plt0 = plt.hist(
            source_withxtalk,
            bins=bins,
            label=f"Occ > {params_xtalk[0]} in disc. bump scan",
            linewidth=1,
            histtype="step",
            ec="black",
            fill=False,
        )
        n1, _b1, plt1 = plt.hist(
            source_noxtalk,
            bins=bins,
            label=f"Occ <= {params_xtalk[0]} in disc. bump scan",
            linewidth=1,
            histtype="step",
            ec="darkmagenta",
            fill=False,
        )
        ax.set_ylim(
            0.5, max(np.concatenate((n0, n1))) + max(np.concatenate((n0, n1))) * 100
        )
        ax.set_xlim(minRange, maxRange)
        plt.legend(
            handles=[plt0[0], plt1[0]],
            loc="upper right",
            fontsize=10,
            title=f"{chipname}",
        )
        log.info(
            "Saving "
            + str(outputdir.joinpath(f"{chipname}_{identifier}_source1d_xtalk.png"))
        )
        plt.savefig(outputdir.joinpath(f"{chipname}_{identifier}_source1d_xtalk.png"))
        plt.close()
    else:
        log.warning(
            bcolors.WARNING
            + "Source scan data not available, skipping 1D source occupancy plot"
            + bcolors.ENDC
        )

    if np.any(noise_hv) and np.any(noise_nohv):
        # 1D histogram of noise difference, with and without x-talk
        noise_diff = noise_nohv - noise_hv
        noise_hv_nonzero = noise_hv != 0
        noise_nohv_nonzero = noise_nohv != 0
        noise_diffmask_withxtalk = noise_nohv_nonzero & noise_hv_nonzero & xtalk_mask
        noise_diffmask_noxtalk = noise_nohv_nonzero & noise_hv_nonzero & ~xtalk_mask
        noise_diff_withxtalk = noise_diff[noise_diffmask_withxtalk]
        noise_diff_noxtalk = noise_diff[noise_diffmask_noxtalk]

        plt.clf()
        _fig, ax = plt.subplots()
        plt.xlabel("Noise difference [e]", fontsize=12)
        plt.ylabel("Number of enabled pixels", fontsize=12)
        plt.xticks(fontsize=13)
        plt.yticks(fontsize=13)
        plt.yscale("log")
        plt.title("Results from zero-bias scan", fontsize=12)
        plt.tight_layout()
        plt.text(
            0.02,
            0.93,
            identifier,
            fontsize=11,
            transform=ax.transAxes,
        )
        if np.any(noise_diff_withxtalk):
            mean_diff_withxtalk = np.mean(noise_diff_withxtalk)
            std_diff_withxtalk = np.std(noise_diff_withxtalk)
            plt.text(
                0.02,
                0.86,
                "$\\mu$ = "
                + str(round(mean_diff_withxtalk, 1))
                + ", $\\sigma$ = "
                + str(round(std_diff_withxtalk, 1))
                + " (e)",
                fontsize=11,
                color="black",
                transform=ax.transAxes,
            )
        if np.any(noise_diff_noxtalk):
            mean_diff_noxtalk = np.mean(noise_diff_noxtalk)
            std_diff_noxtalk = np.std(noise_diff_noxtalk)
            plt.text(
                0.02,
                0.79,
                "$\\mu$ = "
                + str(round(mean_diff_noxtalk, 1))
                + ", $\\sigma$ = "
                + str(round(std_diff_noxtalk, 1))
                + " (e)",
                fontsize=11,
                color="red",
                transform=ax.transAxes,
            )

        minRange = -50
        maxRange = int(min(500, max(noise_diff)))
        bins = range(
            minRange,
            maxRange,
            max(5, int(np.mean(noise_diff) / 30)),
        )
        n0, _b0, plt0 = plt.hist(
            noise_diff_withxtalk,
            bins=bins,
            label=f"Occ > {params_xtalk[0]} in disc. bump scan",
            linewidth=1,
            histtype="step",
            ec="black",
            fill=False,
        )
        n1, _b1, plt1 = plt.hist(
            noise_diff_noxtalk,
            bins=bins,
            label=f"Occ <= {params_xtalk[0]} in disc. bump scan",
            linewidth=1,
            histtype="step",
            ec="red",
            fill=False,
        )
        ax.set_ylim(
            0.5, max(np.concatenate((n0, n1))) + max(np.concatenate((n0, n1))) * 100
        )
        ax.set_xlim(minRange, maxRange)
        plt.legend(
            handles=[plt0[0], plt1[0]],
            loc="upper right",
            fontsize=10,
            title=f"{chipname}",
        )
        log.info(
            "Saving "
            + str(outputdir.joinpath(f"{chipname}_{identifier}_noisediff1d_xtalk.png"))
        )
        plt.savefig(
            outputdir.joinpath(f"{chipname}_{identifier}_noisediff1d_xtalk.png")
        )
        plt.close()
    else:
        log.warning(
            bcolors.WARNING
            + "0-bias data not available, skipping 1D noise difference plot"
            + bcolors.ENDC
        )


# Makes 2D histogram of pixel map, comparing consistency of source scan and disconnected bump scan results
def plot_2d_discbumps(
    occ_sourcescan,
    en_sourcescan,
    occ_xtalk,
    params_source,
    params_xtalk,
    outputdir,
    chipname,
):
    pix_index = get_pixel_index()

    # Identify pixels which have occupancy > value
    enable_mask = en_sourcescan == 1
    xtalk_mask = occ_xtalk > params_xtalk[0]

    # 2D histogram comparing results of disc. bump scan and source scan
    source_mask = occ_sourcescan > params_source[0]
    mask_withxtalk_nosource = xtalk_mask & ~source_mask & enable_mask
    mask_noxtalk_withsource = ~xtalk_mask & source_mask & enable_mask
    mask_noxtalk_nosource = ~xtalk_mask & ~source_mask & enable_mask

    pixindex_withxtalk_nosource = pix_index[mask_withxtalk_nosource]
    pixindex_noxtalk_withsource = pix_index[mask_noxtalk_withsource]
    pixindex_noxtalk_nosource = pix_index[mask_noxtalk_nosource]
    pixindex_disabled = pix_index[~enable_mask]

    plt.clf()
    _fig, ax = plt.subplots()
    plt.xlabel("Row", fontsize=12)
    plt.ylabel("Column", fontsize=12)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylim((-1, 401))
    plt.xlim((-1, 385))
    plt.subplots_adjust(right=0.885)
    plt.subplots_adjust(left=0.165)
    plt.subplots_adjust(top=0.87)

    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(
        pixindex_noxtalk_nosource
    )
    plt.scatter(
        rows,
        cols,
        marker="s",
        s=2,
        c="teal",
        label=f"Fails disc-bump, fails source: {len(pixindex_noxtalk_nosource)}",
    )

    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(
        pixindex_withxtalk_nosource
    )
    plt.scatter(
        rows,
        cols,
        marker="o",
        s=4,
        edgecolors="darkmagenta",
        facecolors="darkmagenta",
        alpha=0.5,
        label=f"Passes disc-bump, fails source: {len(pixindex_withxtalk_nosource)}",
    )

    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(
        pixindex_noxtalk_withsource
    )
    plt.scatter(
        rows,
        cols,
        marker="v",
        s=6,
        edgecolors="dodgerblue",
        facecolors="dodgerblue",
        alpha=0.5,
        label=f"Fails disc-bump, passes source: {len(pixindex_noxtalk_withsource)}",
    )

    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(pixindex_disabled)
    plt.scatter(
        rows,
        cols,
        marker="^",
        s=4,
        edgecolors="orangered",
        facecolors="orangered",
        alpha=0.5,
        label=f"Disabled in source: {len(pixindex_disabled)}",
    )

    plt.legend(
        loc="upper left",
        bbox_to_anchor=(-0.09, 1.15),
        borderaxespad=0.0,
        handlelength=0.2,
        ncol=2,
        markerscale=2,
    )
    plt.text(
        1.02,
        0.9,
        chipname,
        fontsize=10,
        transform=ax.transAxes,
    )
    log.info("Saving " + str(outputdir.joinpath(f"{chipname}_source_vs_xtalk.png")))
    plt.savefig(outputdir.joinpath(f"{chipname}_source_vs_xtalk.png"))
    plt.close()


# Makes 2D histogram of pixel map
def plot_2d_map(
    pix_fail,
    record_fail,
    label,
    outputdir,
    chipname,
):
    pix_index = get_pixel_index()

    # 2D histogram comparing results of disc. bump scan and source scan
    failure_mask = (pix_fail & record_fail) > 0
    index_failures = pix_index[failure_mask]

    plt.clf()
    _fig, ax = plt.subplots()
    plt.xlabel("Row", fontsize=12)
    plt.ylabel("Column", fontsize=12)
    plt.xticks(fontsize=13)
    plt.yticks(fontsize=13)
    plt.ylim((-1, 401))
    plt.xlim((-1, 385))
    plt.subplots_adjust(right=0.885)
    plt.subplots_adjust(left=0.165)
    plt.subplots_adjust(top=0.87)

    rows, cols = np.vectorize(get_loc_from_index, otypes=[int, int])(index_failures)
    plt.scatter(
        rows,
        cols,
        marker="s",
        s=2,
        c="teal",
        label=f"{label}: {len(index_failures)}",
    )
    plt.legend(
        loc="upper left",
        bbox_to_anchor=(0.0, 1.1),
        borderaxespad=0.0,
        handlelength=0.2,
        ncol=2,
        markerscale=2,
        fontsize=11,
    )
    plt.text(
        0.8,
        1.05,
        chipname,
        fontsize=11,
        transform=ax.transAxes,
    )
    savelabel = label.replace(" ", "_")
    log.info("Saving " + str(outputdir.joinpath(f"{chipname}_{savelabel}.png")))
    plt.savefig(outputdir.joinpath(f"{chipname}_{savelabel}.png"))
    plt.close()


# Combines information from all disconnected bump methods to determine which pixels to count as disconnected
def identify_disc_pixels(
    occ_sourcescan,
    en_sourcescan,
    occ_xtalk,
    fail,
    record,
    test_name,
    params_source,
    params_xtalk,
):
    pix_fail = np.copy(fail)
    fail_bit = get_fail_bit(test_name)
    pix_index = get_pixel_index()

    # Identify pixels which have occupancy > value
    xtalk_mask = occ_xtalk > params_xtalk[0]

    # Use source data if present
    if np.any(occ_sourcescan) and np.any(en_sourcescan):
        enable_mask = en_sourcescan == 1
        source_mask = occ_sourcescan > params_source[0]

        # Identify disconnected bumps (require to pass both x-talk and source scan)
        fail_discbump_mask = ~xtalk_mask | (~source_mask & enable_mask)

    else:  # Otherwise only use disconnected bump scan
        fail_discbump_mask = ~xtalk_mask

    fail_discbump_index = pix_index[fail_discbump_mask].astype(int)

    # Record these pixels as failures
    record = set_bit(record, fail_bit)
    mask = np.zeros_like(pix_fail, dtype=bool)
    mask[fail_discbump_index] = True
    pix_fail[mask] = set_bit(pix_fail[mask], fail_bit)

    return pix_fail, record


# Prints summary of pixel classification to terminal
def print_pixel_classification(
    failure_summary, test_type, outputdir, chipname, ignore_dis_corecol
):
    txt = " {:^35}: {:^20}"
    log.info(txt.format("Classification", "Number of pixels (dependent)"))
    log.info("------------------------------------------------------------------")
    counts_dep = []
    counts_indep = []
    binlabels = []
    incomplete_results = False
    for criteria, failures in failure_summary.items():
        if criteria == "DISCONNECTED_BUMPS_ZERO_BIAS_SCAN":
            log.info(
                "------------------------------------------------------------------"
            )
        log.info(txt.format(criteria, failures.get("dependent")))
        counts_dep += [failures.get("dependent")]
        counts_indep += [failures.get("independent")]
        binlabels += [
            criteria.replace("DISCONNECTED_BUMPS_", "")
            .replace("_", "\n")
            .replace("DISCONNECTED", "DISC")
            .replace("SCAN", "")
            .replace("PIXELS", "PIXELS*")
        ]
        # Search for incomplete results, ignoring source scan and zero-bias scan which are not required
        if (
            failures.get("dependent") == -1
            and "SOURCE" not in criteria
            and "ZERO_BIAS" not in criteria
        ):
            incomplete_results = True
    log.info("------------------------------------------------------------------")
    log.info(
        txt.format(
            "TOTAL FAILING",
            -1
            if incomplete_results
            else list(failure_summary.values())[-1].get("integrated"),
        )
    )
    counts_dep += [list(failure_summary.values())[-1].get("integrated")]
    counts_indep += [list(failure_summary.values())[-1].get("integrated")]
    binlabels += ["TOTAL\nFAILING"]
    log.info("------------------------------------------------------------------")

    bins = range(len(counts_dep) + 1)

    # Plot dependent categorization
    fig, ax = plt.subplots()

    ax.set_title(f"{chipname} ({test_type})")
    plt.stairs(counts_dep[:-1], bins[:-1], fill=True, color="cornflowerblue")
    plt.stairs([counts_dep[-1]], bins[-2:], fill=True, color="lightcoral")
    ax.set_ylim(0, max(max(counts_dep) + max(counts_dep) / 2, 1))

    # Draw vertical lines
    plt.axvline(x=8.0, ymin=0.0, ymax=0.8, color="gray", linestyle=":")
    plt.axvline(x=13.0, ymin=0.0, ymax=0.8, color="gray", linestyle=":")
    plt.axvline(x=1.0, ymin=0.0, ymax=0.72, color="gray", linestyle=":")

    ax.set_xlim(-1.5, 14.5)

    # Label bins
    plt.xticks(
        [x + 0.5 for x in range(len(counts_dep))],
        labels=binlabels,
        rotation=40,
        fontsize=6,
    )
    ax.set_ylabel("Number of pixels")
    plt.text(0.02, 0.92, "Dependent categorization", transform=ax.transAxes)
    plt.text(
        0.02,
        0.85,
        "(Failing pixels included in single category)",
        transform=ax.transAxes,
    )
    if test_type == "PIXEL_FAILURE_ANALYSIS":
        plt.text(
            0.02,
            -0.3,
            "*DISC PIXELS uses combination of various disc. bump identificaiton methods, and is used to count the TOTAL FAILING category",
            wrap=True,
            transform=ax.transAxes,
            fontsize=9,
        )
    if ignore_dis_corecol:
        plt.text(
            0.02,
            -0.4,
            "Pixels in disabled Core Columns excluded from total failing pixels",
            wrap=True,
            transform=ax.transAxes,
            fontsize=9,
        )

    # Print bin contents
    for i, count_dep in enumerate(counts_dep):
        ypos = (
            abs(count_dep) + max(counts_dep) / 60
            if count_dep != -1
            else max(counts_dep) / 60
        )
        adj = 0
        if i == 0:
            adj = -0.05
        plt.text(i + 0.5 + adj, ypos, count_dep, ha="center", fontsize=9)
    plt.text(
        0.1,
        0.74,
        "Disabled Core\nColumn Pixels",
        color="gray",
        fontsize=9,
        transform=ax.transAxes,
        ha="center",
    )
    plt.text(
        0.30,
        0.77,
        "Electrical failures",
        color="gray",
        fontsize=9,
        transform=ax.transAxes,
    )
    plt.text(
        0.8,
        0.85,
        "Disconnected\nbumps",
        color="gray",
        fontsize=9,
        transform=ax.transAxes,
        ha="center",
    )

    fig.tight_layout()
    plt.subplots_adjust(bottom=0.3)
    plt.savefig(outputdir.joinpath(f"{chipname}_{test_type}_depclassification.png"))
    log.info(
        "Saving "
        + str(outputdir.joinpath(f"{chipname}_{test_type}_depclassification.png"))
    )
    plt.close()

    # Plot independent categorization
    fig, ax = plt.subplots()
    ax.set_title(f"{chipname} ({test_type})")
    plt.stairs(counts_indep[:-1], bins[:-1], fill=True, color="mediumseagreen")
    plt.stairs([counts_indep[-1]], bins[-2:], fill=True, color="lightcoral")
    ax.set_ylim(0, max(max(counts_indep) + max(counts_indep) / 2, 1))

    plt.axvline(x=8.0, ymin=0.0, ymax=0.8, color="gray", linestyle=":")
    plt.axvline(x=13.0, ymin=0.0, ymax=0.8, color="gray", linestyle=":")
    plt.axvline(x=1.0, ymin=0.0, ymax=0.72, color="gray", linestyle=":")

    ax.set_xlim(-1.5, 14.5)

    # Label bins
    plt.xticks(
        [x + 0.5 for x in range(len(counts_indep))],
        labels=binlabels,
        rotation=40,
        fontsize=6,
    )
    ax.set_ylabel("Number of pixels")
    plt.text(0.02, 0.92, "Independent categorization", transform=ax.transAxes)
    plt.text(
        0.02,
        0.85,
        "(Failing pixels can be included in several categories)",
        transform=ax.transAxes,
    )

    # Print bin contents
    for i, count_indep in enumerate(counts_indep):
        ypos = (
            abs(count_indep) + max(counts_indep) / 60
            if count_indep != -1
            else max(counts_indep) / 60
        )
        adj = 0
        if i == 0:
            adj -= 0.05
        plt.text(i + 0.5 + adj, ypos, count_indep, ha="center", fontsize=9)
    if test_type == "PIXEL_FAILURE_ANALYSIS":
        plt.text(
            0.02,
            -0.3,
            "*DISC PIXELS uses combination of various disc. bump identificaiton methods, and is used to count the TOTAL FAILING category",
            wrap=True,
            transform=ax.transAxes,
            fontsize=9,
        )
    if ignore_dis_corecol:
        plt.text(
            0.02,
            -0.4,
            "Pixels in disabled Core Columns excluded from independent counts and total failing pixels",
            wrap=True,
            transform=ax.transAxes,
            fontsize=9,
        )

    # Draw vertical lines
    plt.text(
        0.1,
        0.74,
        "Disabled Core\nColumn Pixels",
        color="gray",
        fontsize=9,
        transform=ax.transAxes,
        ha="center",
    )
    plt.text(
        0.30,
        0.77,
        "Electrical failures",
        color="gray",
        fontsize=9,
        transform=ax.transAxes,
    )
    plt.text(
        0.85,
        0.85,
        "Disconnected\nbumps",
        color="gray",
        fontsize=9,
        transform=ax.transAxes,
        ha="center",
    )

    fig.tight_layout()
    plt.subplots_adjust(bottom=0.3)
    plt.savefig(outputdir.joinpath(f"{chipname}_{test_type}_indepclassification.png"))
    log.info(
        "Saving "
        + str(outputdir.joinpath(f"{chipname}_{test_type}_indepclassification.png"))
    )
    plt.close()


# Split pixels based on their location in the chip
def split_pixels(_data, module_type, chip_id):
    matrix = np.empty(0)
    inneredge1 = np.empty(0)
    inneredge2 = np.empty(0)
    outeredge1 = np.empty(0)
    outeredge2 = np.empty(0)

    if not np.any(_data):
        return matrix, inneredge1, outeredge1

    # First reconstruct 2D array
    _data = _data.reshape((384, 400))

    # Then identify inner / outer edges
    if "QUAD" in module_type:
        if chip_id in [12, 14]:
            matrix = _data[2:-1, 1:-2].flatten()
            inneredge1 = _data[0:2, :].flatten()
            inneredge2 = np.concatenate(
                (_data[2:, -1].flatten(), _data[2:, -2].flatten())
            )
            outeredge1 = _data[-1, 0:-2].flatten()
            outeredge2 = _data[2:-1, 0].flatten()
        else:
            matrix = _data[2:-1, 2:-1].flatten()
            inneredge1 = _data[0:2, :].flatten()
            inneredge2 = _data[2:, 0:2].flatten()
            outeredge1 = _data[2:-1, -1].flatten()
            outeredge2 = _data[-1, 2:].flatten()

    else:
        matrix = _data[1:-1, 1:-1].flatten()
        inneredge1 = np.empty(0)
        inneredge2 = np.empty(0)
        outeredge1 = np.concatenate(
            (_data[-1, 0:-1].flatten(), _data[0:1, :].flatten())
        )
        outeredge2 = np.concatenate((_data[1:-1, 0].flatten(), _data[1:, -1].flatten()))

    inneredge = np.concatenate((inneredge1, inneredge2), axis=0)
    outeredge = np.concatenate((outeredge1, outeredge2), axis=0)

    return matrix, inneredge, outeredge
