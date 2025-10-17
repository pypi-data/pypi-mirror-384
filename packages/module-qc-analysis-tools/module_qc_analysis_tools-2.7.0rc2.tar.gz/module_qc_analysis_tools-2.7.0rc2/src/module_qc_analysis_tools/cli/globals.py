from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

from module_qc_analysis_tools import data

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


class FitMethod(str, Enum):
    root = "root"
    numpy = "numpy"


class LogLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"


OPTIONS = {}

OPTIONS["input_meas"]: Path = typer.Option(
    ...,
    "-i",
    "--input-meas",
    help="path to the input measurement file or directory containing input measurement files.",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
)
OPTIONS["input_yarr_config"]: Path = typer.Option(
    "info.json",
    "-i",
    "--input-yarr-config",
    help="path to the json config file containing paths to YARR scan outputs. Run analysis-load-yarr-scans.py to generate.",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
)
OPTIONS["output_dir"]: Path = typer.Option(
    "outputs",
    "-o",
    "--output-dir",
    help="output directory",
    exists=False,
    writable=True,
)
OPTIONS["qc_criteria"]: Path = typer.Option(
    None,
    "-q",
    "--qc-criteria",
    help="path to json file with QC selection criteria",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
)
OPTIONS["reference_iv"]: Path = typer.Option(
    None,
    "-r",
    "--reference-iv",
    help="path to reference IV measurement results from previous stage. For module IV, this is the bare module IV. For bare module IV, this is the sensor tile IV.",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
)
OPTIONS["pixel_classification"]: Path = typer.Option(
    str(data / "pixel_classification.json"),
    "-p",
    "--pixel-failure-config",
    help="path to json file with pixel failure selection criteria",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
)
OPTIONS["layer"]: str = typer.Option(
    "Unknown",
    "-l",
    "--layer",
    help="Layer of module, used for applying correct QC criteria settings. Options: L0, L1, L2 (default is automatically determined from the module SN)",
)
OPTIONS["moduleSN"]: str = typer.Option(
    ...,
    "-m",
    "--moduleSN",
    help="Module serial number",
)
OPTIONS["permodule"]: bool = typer.Option(
    False, help="Store results in one file per module (default: one file per chip)"
)
OPTIONS["ignore_bad_corecol"]: bool = typer.Option(
    False,
    help="Whether or not to count pixels who had their core column disabled in the chip config as failures in complex scans. Only available for RD53B (pre-production) modules (default: True)",
)
OPTIONS["fit_method"]: FitMethod = typer.Option(
    FitMethod.numpy, "-f", "--fit-method", help="fitting method"
)
OPTIONS["nchips"]: int = typer.Option(
    0,
    "-n",
    "--nChips",
    help="Number of chips powered in parallel (e.g. 4 for a quad module, 3 for a triplet, 1 for an SCC.) If no argument is provided, the number of chips is assumed from the layer.",
)
OPTIONS["verbosity"]: LogLevel = typer.Option(
    LogLevel.info,
    "-v",
    "--verbosity",
    help="Log level [options: DEBUG, INFO (default) WARNING, ERROR]",
)
OPTIONS["submit"]: bool = typer.Option(
    False,
    help="Submit QC results to: https://docs.google.com/spreadsheets/d/1pw_07F94fg2GJQr8wlvhaRUV63uhsAuBt_S1FEFBzBU/view",
)
OPTIONS["site"]: str = typer.Option(
    "",
    "--site",
    help="Your testing site. Required when submitting results. Please use same short-hand as on production DB, i.e. LBNL_PIXEL_MODULES for LBNL, IRFU for Paris-Saclay, ...",
)
OPTIONS["lp_enable"]: bool = typer.Option(False, help="low power mode")

OPTIONS["input_file"]: Path = typer.Option(
    ...,
    "-i",
    "--input-file",
    help="analysis output file",
    exists=True,
    file_okay=True,
    readable=True,
    resolve_path=True,
)

OPTIONS["config_file"]: Path = typer.Option(
    ...,
    "-c",
    "--config-file",
    help="the config file to be modified",
    exists=True,
    file_okay=True,
    readable=True,
    writable=True,
    resolve_path=True,
)

OPTIONS["input_dir"]: Path = typer.Option(
    ...,
    "-i",
    "--input-dir",
    help="Analysis output directory",
    exists=True,
    dir_okay=True,
    readable=True,
    resolve_path=True,
)
OPTIONS["config_dir"]: Path = typer.Option(
    ...,
    "-c",
    "--config-dir",
    help="Path to the module configuration directory to be modified",
    exists=True,
    dir_okay=True,
    readable=True,
    writable=True,
    resolve_path=True,
)
OPTIONS["config_type"]: str = typer.Option(
    "",
    "-t",
    "--config-type",
    help="The config type to be modified. E.g. L2_warm/L2_cold.",
)
OPTIONS["override"]: bool = typer.Option(
    False,
    help="Update chip configuration even if the chip failed QC",
)
OPTIONS["output_yarr"]: str = typer.Option(
    "./",
    "-o",
    "--output-yarr",
    help="output directory to put info_{TEST_NAME}.json which will be used as input to YARR scan analysis",
    exists=False,
    writable=True,
    resolve_path=True,
)
OPTIONS["test_name"]: Path = typer.Option(
    ...,
    "-t",
    "--test-name",
    help="Test name (MIN_HEALTH_TEST, TUNING, or PIXEL_FAILURE_ANALYSIS)",
)
OPTIONS["digitalscan"]: Path = typer.Option(
    None,
    "-ds",
    "--digital-scan",
    help="path to the digital scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["analogscan"]: Path = typer.Option(
    None,
    "-as",
    "--analog-scan",
    help="path to the analog scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["thresholdscan_hr"]: Path = typer.Option(
    None,
    "-hr",
    "--threshold-scan-hr",
    help="path to the threshold scan (high-range) output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["thresholdscan_hd"]: Path = typer.Option(
    None,
    "-hd",
    "--threshold-scan-hd",
    help="path to the threshold scan (high-def) output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["noisescan"]: Path = typer.Option(
    None,
    "-ns",
    "--noise-scan",
    help="path to the noise scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["thresholdscan_zerobias"]: Path = typer.Option(
    None,
    "-zb",
    "--zerobias",
    help="path to the threshold scan (high-def, zero-bias) output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["totscan"]: Path = typer.Option(
    None,
    "-ts",
    "--tot-scan",
    help="path to the tot scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["discbumpscan"]: Path = typer.Option(
    None,
    "-db",
    "--discbump",
    help="path to the disconnected bump scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["mergedbumpscan"]: Path = typer.Option(
    None,
    "-mb",
    "--mergedbump",
    help="path to the merged bump scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["sourcescan"]: Path = typer.Option(
    None,
    "-ss",
    "--source-scan",
    help="path to the source scan output directory to use in YARR analysis",
    exists=True,
    readable=True,
)
OPTIONS["depl_volt"]: float = typer.Option(
    None,
    "--vdepl",
    help="Depletion voltage. Do not use if unknown.",
)
