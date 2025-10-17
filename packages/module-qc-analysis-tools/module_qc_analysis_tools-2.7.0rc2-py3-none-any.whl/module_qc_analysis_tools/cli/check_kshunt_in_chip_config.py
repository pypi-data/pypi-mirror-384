from __future__ import annotations

import json
import logging
from pathlib import Path

import typer

from module_qc_analysis_tools.cli.globals import CONTEXT_SETTINGS, OPTIONS
from module_qc_analysis_tools.utils.misc import bcolors, get_inputs, lookup

log = logging.getLogger(__name__)
log.setLevel("INFO")


class WriteKshunt:
    """
    This class ensures kshunt values are are using the new estimate in the chip config files.

    - `module_dir_path` must be the path to the module directory containing the chip config files.
    """

    def __init__(self, module_dir_path: Path):
        # list repositories in module directory and find the cold, warm, and LP config directories
        log.info(
            "Ensuring KSenseShuntA and KSenseShuntD are updated in chip config files."
        )
        self.config_files = []
        for qc_type in ["cold", "warm", "LP"]:
            type_dir = sorted(module_dir_path.glob(f"*_{qc_type}"))
            if len(type_dir) == 1:
                config_dir_path = type_dir[0]
                self.config_files.extend(get_inputs(config_dir_path))
            else:
                log.error(
                    f"Expected to find one {qc_type} directory in module directory, but found {len(type_dir)}!"
                )

        self.stack = []

    def overwrite(self, config_file, search_key, set_value):
        # search_key is a string which is the name of the parameter that will be overwritten.
        # set_value is the value the parameter that will be overwritten to.
        with config_file.open(encoding="utf-8") as jsonFile:
            config_file_data = json.load(jsonFile)
        self.stack = []
        original_search_key = lookup(config_file_data, search_key, self.stack)
        if original_search_key is None:
            msg = f"Parameter {search_key} not found in config file {config_file} "
            raise KeyError(msg)
        log.info(
            f"Chip [{search_key}] change from {original_search_key} to {set_value}"
        )

        original_search_key = set_value
        self.stack.reverse()

        # iterate through the keys in the reversed stack to navigate to the correct nested dictionary in the JSON structure
        part_config_file_data = config_file_data
        for k in self.stack:
            part_config_file_data = part_config_file_data[k]
        part_config_file_data[search_key] = original_search_key

        with config_file.open("w", encoding="utf-8") as jsonFile:
            json.dump(config_file_data, jsonFile, indent=4)

    def update_kshunt(self):
        for config_file in self.config_files:
            with config_file.open(encoding="utf-8") as jsonFile:
                config_file_data = json.load(jsonFile)

            log.info(f"Checking kshunt in {config_file}")

            k_in_A = lookup(config_file_data, "KSenseInA")
            k_in_D = lookup(config_file_data, "KSenseInD")
            k_shunt_A = lookup(config_file_data, "KSenseShuntA")
            k_shunt_D = lookup(config_file_data, "KSenseShuntD")

            k_shunt_A_expected = int(21600 / 21000 * k_in_A)
            k_shunt_D_expected = int(21600 / 21000 * k_in_D)

            if abs(k_shunt_A - k_shunt_A_expected) > 1:
                self.overwrite(config_file, "KSenseShuntA", k_shunt_A_expected)

            if abs(k_shunt_D - k_shunt_D_expected) > 1:
                self.overwrite(config_file, "KSenseShuntD", k_shunt_D_expected)


app = typer.Typer(context_settings=CONTEXT_SETTINGS)


@app.command()
def main(
    config_dir: Path = OPTIONS["config_dir"],
):
    """
    This script updates the KSenseShuntA and KSenseShuntD parameters in the chip config.
    """
    log.addHandler(logging.FileHandler(Path(config_dir).joinpath("output_update.log")))
    log.info(" ==========================================")
    if not config_dir.is_dir():
        log.error(
            bcolors.BADRED
            + f"Module directory ({config_dir}) should be path to directory containing the connectivity file and chip configs - not a file!"
            + bcolors.ENDC
        )
        return

    wk = WriteKshunt(config_dir)
    wk.update_kshunt()


if __name__ == "__main__":
    typer.run(main)
