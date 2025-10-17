from __future__ import annotations

import json
import logging
from pathlib import Path

import typer
from module_qc_data_tools import (
    check_sn_format,
    convert_name_to_serial,
    get_layer_from_sn,
)

from module_qc_analysis_tools.cli.globals import (
    CONTEXT_SETTINGS,
    OPTIONS,
    LogLevel,
)
from module_qc_analysis_tools.utils.analysis import (
    get_n_chips,
)
from module_qc_analysis_tools.utils.classification import (
    required_tests,
)
from module_qc_analysis_tools.utils.misc import (
    bcolors,
)

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

results_from_scans = {
    "std_digitalscan": ["OccupancyMap"],
    "std_analogscan": ["OccupancyMap", "MeanTotMap"],
    "std_thresholdscan_hr": ["Chi2Map", "ThresholdMap", "NoiseMap", "Config"],
    "std_thresholdscan_hd": ["Chi2Map", "ThresholdMap", "NoiseMap", "Config"],
    "std_noisescan": ["NoiseOccupancy", "Config"],
    "std_totscan": ["MeanTotMap", "SigmaTotMap"],
    "std_discbumpscan": ["OccupancyMap", "Config"],
    "std_mergedbumpscan": ["OccupancyMap", "Config"],
    "std_thresholdscan_zerobias": ["Chi2Map", "ThresholdMap", "NoiseMap", "Config"],
    "selftrigger_source": ["Occupancy", "Config"],
}


def findLatestResults(path, tests):
    path = str(path.resolve())

    log.debug(f"Searching for latest YARR scan results in {path} for {tests}")
    alldirs = sorted(Path(path).glob("*"))

    # Make structure to hold location of results
    latest_results = {}
    for t in tests:
        if t not in results_from_scans:
            continue  # Only save scans that we will use for analysis
        latest_results.update({t: "null"})

    # Find latest YARR scans, assumes directories named with run numbers
    for d in alldirs:
        if "last_scan" in d:
            alldirs.remove(d)
        for s in latest_results:
            if s in d:
                latest_results.update({s: d})
                break
    return latest_results


def getDataFile(mname, latest_results, test_name, n_chips):
    log.debug(f"Setting module SN to {mname}")

    firstscan = next(iter(latest_results.values()))
    path = Path(firstscan + "/scanLog.json")
    with path.open(mode="r", encoding="utf-8") as f:
        logfile = json.load(f)

    try:
        chipType = logfile["connectivity"][0]["chipType"]
    except Exception:
        chipType = "Not Found"
        log.warning(bcolors.WARNING + "Chip type (chipType) Not Found." + bcolors.ENDC)

    try:
        yarr_version = logfile["yarr_version"]["git_tag"]
    except Exception:
        yarr_version = ""
        log.warning(
            bcolors.WARNING + "YARR version (git_tag) Not Found." + bcolors.ENDC
        )

    start_times = []
    end_times = []

    # Setup structure of output
    config_file = {
        "datadir": "",  # Full paths are stored for each file now
        "YARR_VERSION": yarr_version,
        "module": {"serialNumber": mname, "chipType": chipType},
        "TimeStart": 0,
        "TimeEnd": 0,
        "chip": [],
    }

    # Collect necessary data from each scan
    chip_data = {}
    for scan in latest_results:
        _yarr_version = ""
        if latest_results.get(scan) == "null":
            if "discbump" in scan:
                log.warning(
                    bcolors.WARNING + f"No results for {scan} found." + bcolors.ENDC
                )
                continue
            msg = f"No results for {scan} found! This is required for {test_name}. Please fix."
            raise RuntimeError(msg)
        log.debug(f"Searching for {scan} scans")
        path = Path(latest_results.get(scan) + "/scanLog.json")
        with path.open(mode="r", encoding="utf-8") as f:
            logfile = json.load(f)
            _yarr_version = logfile["yarr_version"]["git_tag"]
            start_times.append(logfile["startTime"])
            end_times.append(logfile["finishTime"])
        log.debug(f"yarr_version {yarr_version} _yarr_version: {_yarr_version}")
        if _yarr_version != yarr_version:
            msg = f"Scans were not obtained with the same YARR version: {yarr_version} and {_yarr_version}"
            raise RuntimeError(msg)
        for v in results_from_scans.get(scan):
            if v == "Config":
                data = list(Path(latest_results.get(scan)).glob("0x*.json.before"))
            else:
                data = list(Path(latest_results.get(scan)).glob(f"*_{v}*.json"))

            # Check data that was found
            if len(data) == 0:
                msg = f"No results found for {v} in {latest_results.get(scan)} - please fix!"
                raise RuntimeError(msg)
            if len(data) != n_chips:
                log.error(
                    bcolors.WARNING
                    + f"Found {len(data)} results for {v} in {latest_results.get(scan)}, but results from {n_chips} chips expected! Please be aware that you are missing data from at least one chip:."
                    + bcolors.ENDC
                )
                log.error(bcolors.WARNING + f"{data}" + bcolors.ENDC)

            for d in data:
                log.debug(f"Found {d}")
                chipname = d.stem.split("_")[0]
                if chip_data.get(chipname):
                    chip_data[chipname]["filepaths"].update(
                        {scan.replace("std_", "") + "_" + v: str(d)}
                    )
                else:
                    chip_data[chipname] = {
                        "serialNumber": convert_name_to_serial(chipname),
                        "filepaths": {scan.replace("std_", "") + "_" + v: str(d)},
                    }
    for item in chip_data.values():
        config_file["chip"].append(item)
        log.info(
            f"Found {len(item['filepaths'])} YARR scans for chip {item.get('serialNumber')}"
        )

    config_file["TimeStart"] = min(start_times)
    config_file["TimeEnd"] = max(end_times)
    config_file["TimeDuration"] = sum(
        end_time - start_time for start_time, end_time in zip(start_times, end_times)
    )
    return config_file


app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    output_yarr: Path = OPTIONS["output_yarr"],
    module_sn: str = OPTIONS["moduleSN"],
    verbosity: LogLevel = OPTIONS["verbosity"],
    test_name: str = OPTIONS["test_name"],
    digitalscan: Path = OPTIONS["digitalscan"],
    analogscan: Path = OPTIONS["analogscan"],
    thresholdscan_hr: Path = OPTIONS["thresholdscan_hr"],
    thresholdscan_hd: Path = OPTIONS["thresholdscan_hd"],
    noisescan: Path = OPTIONS["noisescan"],
    totscan: Path = OPTIONS["totscan"],
    thresholdscan_zerobias: Path = OPTIONS["thresholdscan_zerobias"],
    discbumpscan: Path = OPTIONS["discbumpscan"],
    mergedbumpscan: Path = OPTIONS["mergedbumpscan"],
    sourcescan: Path = OPTIONS["sourcescan"],
):
    """
    Given a directory with YARR scans, the script will identify the latest YARR scans needed for all analyses. Alternatively, the paths to YARR scans for each type of scan can be supplied to the script.

    Before running analysis involving YARR scans (such as `MIN_HEALTH_TEST`, `TUNING`, `PIXEL_FAILURE_ANALYSIS`), the YARR scans to be analyzed need to be identified.
    """
    log.setLevel(verbosity.value)

    log.info("")
    log.info(" ==============================================================")
    log.info(f" \tCollecting YARR scan output for module {module_sn}")
    log.info(" ==============================================================")
    log.info("")

    check_sn_format(module_sn)
    nChips = get_n_chips(get_layer_from_sn(module_sn))
    collect_tests = required_tests.get(test_name)
    if not collect_tests:
        msg = f"{test_name} not recognized! Must be one of: {required_tests.keys()}"
        raise RuntimeError(msg)

    # Find latest results if path to all YARR output is supplied
    latest_results = {}

    # Fill in user-supplied YARR output directories
    if digitalscan is not None:
        latest_results.update({"std_digitalscan": str(digitalscan.resolve())})
    if analogscan is not None:
        latest_results.update({"std_analogscan": str(analogscan.resolve())})
    if thresholdscan_hr is not None:
        latest_results.update({"std_thresholdscan_hr": str(thresholdscan_hr.resolve())})
    if thresholdscan_hd is not None:
        latest_results.update({"std_thresholdscan_hd": str(thresholdscan_hd.resolve())})
    if noisescan is not None:
        latest_results.update({"std_noisescan": str(noisescan.resolve())})
    if thresholdscan_zerobias is not None:
        latest_results.update(
            {"std_thresholdscan_zerobias": str(thresholdscan_zerobias.resolve())}
        )
    if totscan is not None:
        latest_results.update({"std_totscan": str(totscan.resolve())})
    if discbumpscan is not None:
        latest_results.update({"std_discbumpscan": str(discbumpscan.resolve())})
    if mergedbumpscan is not None:
        latest_results.update({"std_mergedbumpscan": str(mergedbumpscan.resolve())})
    if sourcescan is not None:
        latest_results.update({"selftrigger_source": str(sourcescan.resolve())})

    if len(latest_results.keys()) == 0:
        msg = "No YARR results found. Please specify directory to latest YARR scan results, or supply each YARR scan output with appropriate flags. Type `analysis-load-yarr-scans -h` for help"
        raise RuntimeError(msg)

    output_json = getDataFile(module_sn, latest_results, test_name, nChips)

    # Write to output
    with Path(str(output_yarr) + f"/info_{test_name}.json").open(
        "w", encoding="utf-8"
    ) as f:
        log.info("Writing " + str(output_yarr) + f"/info_{test_name}.json")
        json.dump(
            output_json,
            f,
            ensure_ascii=False,
            indent=4,
            sort_keys=False,
            separators=(",", ": "),
        )


if __name__ == "__main__":
    typer.run(main)
