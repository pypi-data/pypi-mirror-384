from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np
import typer
from module_qc_data_tools import convert_name_to_serial

from module_qc_analysis_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_analysis_tools.utils.misc import bcolors, get_inputs, lookup

log = logging.getLogger(__name__)
log.setLevel("INFO")


class WriteConfig:
    """
    This class converts a parameter in a chip config to a given value.

    - `in_path` must be the path to the output directory of the analysis.
    - `config_path` must be the path to the directory ofchip config file in Yarr.
    - if `permodule` enabled, the paths provided much be the path of the correct directory.
    """

    def __init__(
        self,
        in_path: Path | None = None,
        config_path: Path | None = None,
        config_type: str | None = None,
        override: bool | None = None,
    ):
        self.in_path = in_path or Path()
        _config_path = config_path or Path()
        self.config_path = (
            _config_path.joinpath(config_type) if config_type else _config_path
        )
        if not self.config_path.exists():
            log.error(
                bcolors.BADRED
                + f"Path to chip config files ({self.config_path}) does not exist! Please check input module configuration directory and config type"
                + bcolors.ENDC
            )
            raise NotADirectoryError()
        self.stack = []
        self.all_test_types = [
            "ADC_CALIBRATION",
            "ANALOG_READBACK",
            "VCAL_CALIBRATION",
            "INJECTION_CAPACITANCE",
        ]
        self.config_chip_name = ""
        self.in_files = get_inputs(self.in_path)
        self.config_files = get_inputs(self.config_path)
        self.override = override

    def reset_stack(self):
        self.stack = []

    def set_ADCcalPar(self, in_file, config_file):
        # Set the calibrated ADC parameters from the analysis.
        ADC_CALIBRATION_SLOPE = float(lookup(in_file, "ADC_CALIBRATION_SLOPE"))
        ADC_CALIBRATION_OFFSET = float(lookup(in_file, "ADC_CALIBRATION_OFFSET"))
        self.overwrite(config_file, "ADCcalPar", ADC_CALIBRATION_SLOPE, index=1)
        self.overwrite(config_file, "ADCcalPar", ADC_CALIBRATION_OFFSET, index=0)

    def set_trim(self, in_file, config_file):
        # Set the trim values that gives the closest to nominal vdd value.
        vdda = np.array(lookup(in_file, "AR_VDDA_VS_TRIM"))
        vddd = np.array(lookup(in_file, "AR_VDDD_VS_TRIM"))
        SldoTrimA = int(np.absolute(vdda - 1.2).argmin())
        SldoTrimD = int(np.absolute(vddd - 1.2).argmin())
        self.overwrite(config_file, "SldoTrimA", SldoTrimA)
        self.overwrite(config_file, "SldoTrimD", SldoTrimD)

    def set_VcalPar(self, in_file, config_file):
        # Set the calibrated VCAL parameters from the analysis.
        VCAL_MED_SLOPE = float(lookup(in_file, "VCAL_MED_SLOPE"))
        VCAL_MED_OFFSET = float(lookup(in_file, "VCAL_MED_OFFSET"))
        self.overwrite(config_file, "VcalPar", [VCAL_MED_OFFSET, VCAL_MED_SLOPE])

    def set_InjCap(self, in_file, config_file):
        # Set the Injection Capacitance value from the analysis.
        INJ_CAPACITANCE = float(lookup(in_file, "INJ_CAPACITANCE"))
        # allow_missing: all V2 do not have InjCap in wafer probing
        self.overwrite(config_file, "InjCap", INJ_CAPACITANCE, allow_missing=True)

    def overwrite(
        self,
        config_file,
        search_key,
        set_value,
        index=None,
        allow_missing: bool = False,
    ):
        """
        search_key (str): the name of the parameter that will be overwritten.
        set_value (float): the value the parameter that will be overwritten to.
        allow_missing (bool): warn if the parameter is missing in the file, set instead of overwriting
        """
        with config_file.open(encoding="utf-8") as jsonFile:
            config_file_data = json.load(jsonFile)
        self.reset_stack()
        original_search_key = lookup(config_file_data, search_key, self.stack)
        if original_search_key is None:
            msg = f"Parameter not found in config file {config_file}! "
            if allow_missing:
                log.warning(msg)
            else:
                raise KeyError(msg)
        log.info(
            f"Chip {self.config_chip_name} [{search_key}] change from {original_search_key} to {set_value}."
        )
        if index is None:
            original_search_key = set_value
        else:
            original_search_key[index] = set_value

        self.stack.reverse()

        part_config_file_data = config_file_data
        for k in self.stack:
            part_config_file_data = part_config_file_data[k]
        part_config_file_data[search_key] = original_search_key

        with config_file.open("w", encoding="utf-8") as jsonFile:
            json.dump(config_file_data, jsonFile, indent=4)

    def update_config(self):
        for config_file in self.config_files:
            with config_file.open(encoding="utf-8") as jsonFile:
                config_file_data = json.load(jsonFile)

            out_file = self.in_path.joinpath(f"{config_file.name}.before")
            if out_file.exists():
                log.warning(
                    bcolors.WARNING
                    + f"File {out_file} already exists! Skip overwriting!"
                    + bcolors.ENDC
                )
            else:
                with out_file.open("w", encoding="utf-8") as fp:
                    json.dump(config_file_data, fp, indent=4)
            self.config_chip_name = lookup(config_file_data, "Name")
            config_chip_serial = convert_name_to_serial(self.config_chip_name)

            # overwrite the parameter
            for in_file in self.in_files:
                found_chip = False
                with in_file.open(encoding="utf-8") as jsonFile:
                    in_file_data = json.load(jsonFile)

                # Check if loaded json file is analysis output
                if len(in_file_data) == 0:
                    log.error(
                        bcolors.BADRED
                        + f"Input data read from {in_file} is empty! Please check"
                        + bcolors.ENDC
                    )
                    continue
                if isinstance(in_file_data[0], list):
                    log.error(
                        bcolors.BADRED
                        + f"Results read from {in_file} are ill-formatted - please check that you are passing analysis results and not measurement results!"
                        + bcolors.ENDC
                    )
                    continue

                for chip_data in in_file_data:
                    # Check if chip name matched
                    in_chip_serial = lookup(chip_data, "serialNumber")
                    if in_chip_serial is None:
                        log.warning(
                            bcolors.WARNING
                            + f"Chip {self.config_chip_name} not found in the input files! Please check the input files."
                            + bcolors.ENDC
                        )
                        continue
                    if in_chip_serial != config_chip_serial:
                        log.debug(
                            bcolors.WARNING
                            + f"Chip {self.config_chip_name} not found in config. Checking the next chip."
                            + bcolors.ENDC
                        )
                    else:
                        found_chip = True
                        test_type = lookup(chip_data, "testType")
                        if test_type not in [
                            "ADC_CALIBRATION",
                            "ANALOG_READBACK",
                            "VCAL_CALIBRATION",
                            "INJECTION_CAPACITANCE",
                        ]:
                            log.warning(
                                bcolors.WARNING
                                + f"Chip configs do not need to be updated with results from {test_type}. Skipping."
                                + bcolors.ENDC
                            )
                            continue

                        in_chip_passqc = lookup(chip_data, "passed")
                        if not in_chip_passqc:
                            log.warning(
                                bcolors.WARNING
                                + f"Chip {self.config_chip_name} does not pass QC."
                                + bcolors.ENDC
                            )
                            if self.override:
                                log.warning(
                                    bcolors.WARNING
                                    + "Option --override has been provided; therefore chip configuration will be updated even if the chip failed QC"
                                    + bcolors.ENDC
                                )
                            else:
                                log.warning(
                                    bcolors.WARNING
                                    + "Will not update parameters. Re-run with --override if you would like to update the chip configuration even if the chip failed QC"
                                    + bcolors.ENDC
                                )
                                continue

                        if test_type == "ADC_CALIBRATION":
                            self.set_ADCcalPar(chip_data, config_file)
                        elif test_type == "ANALOG_READBACK":
                            self.set_trim(chip_data, config_file)
                        elif test_type == "VCAL_CALIBRATION":
                            self.set_VcalPar(chip_data, config_file)
                        elif test_type == "INJECTION_CAPACITANCE":
                            self.set_InjCap(chip_data, config_file)
                        else:
                            log.warning(
                                bcolors.BADRED
                                + "Something went wrong. Chip configs not updated. Please check"
                                + bcolors.ENDC
                            )
                        break
                if found_chip:
                    break
            with config_file.open(encoding="utf-8") as jsonFile:
                config_file_data = json.load(jsonFile)

            out_file = self.in_path.joinpath(f"{config_file.name}.after")
            with out_file.open("w", encoding="utf-8") as fp:
                json.dump(config_file_data, fp, indent=4)
            if not found_chip:
                log.warning(
                    bcolors.WARNING
                    + f"Chip {self.config_chip_name} with serial number {config_chip_serial} not found! The corresponding config will not be updated."
                    + bcolors.ENDC
                )
                continue


app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    input_dir: Path = OPTIONS["input_dir"],
    config_dir: Path = OPTIONS["config_dir"],
    config_type: str = OPTIONS["config_type"],
    override: bool = OPTIONS["override"],
):
    """
        This script reads the analysis test type and update the corresponding parameters
    in the chip config.

        Run this command after each analysis.
    """
    log.addHandler(logging.FileHandler(Path(input_dir).joinpath("output_update.log")))
    log.info(" ==========================================")
    if not config_dir.is_dir():
        log.error(
            bcolors.BADRED
            + f"Module configuration directory ({config_dir}) should be path to directory containing the connectivity file and chip configs - not a file!"
            + bcolors.ENDC
        )
        return

    wc = WriteConfig(input_dir, config_dir, config_type, override)
    wc.update_config()


if __name__ == "__main__":
    typer.run(main)
