from __future__ import annotations

import json
import logging
from array import array
from importlib import resources
from pathlib import Path
from typing import Any

import numpy as np
from module_qc_data_tools.utils import (
    get_chip_type_from_config,
    get_chip_type_from_serial_number,
)
from module_qc_database_tools.utils import (
    default_BOMCode_from_layer,
    get_cutFile_suffix,
)

from module_qc_analysis_tools import data

log = logging.getLogger(__name__)
log.setLevel("INFO")


class JsonFileCheckFailure(Exception):
    pass


class LengthMismatchError(Exception):
    pass


class NegativeMeasurementError(Exception):
    pass


class bcolors:
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    ERROR = "\033[91m"
    BADRED = "\033[91m"
    ENDC = "\033[0m"


def getVmuxMap():
    return {
        0: "GADC",
        1: "ImuxPad",
        2: "Vntc",
        3: "VcalDac",
        4: "VDDAcapmeas",
        5: "VPolSensTop",
        6: "VPolSensBottom",
        7: "VcalHi",
        8: "VcalMed",
        9: "VDiffVTH2",
        10: "VDiffVTH1Main",
        11: "VDiffVTH1Left",
        12: "VDiffVTH1Right",
        13: "VRadSensAna",
        14: "VMonSensAna",
        15: "VRadSensDig",
        16: "VMonSensDig",
        17: "VRadSensCenter",
        18: "VMonSensAcb",
        19: "AnaGND19",
        20: "AnaGND20",
        21: "AnaGND21",
        22: "AnaGND22",
        23: "AnaGND23",
        24: "AnaGND24",
        25: "AnaGND25",
        26: "AnaGND26",
        27: "AnaGND27",
        28: "AnaGND28",
        29: "AnaGND29",
        30: "AnaGND30",
        31: "VrefCore",
        32: "VrefOVP",
        33: "VinA",
        34: "VDDA",
        35: "VrefA",
        36: "Vofs",
        37: "VinD",
        38: "VDDD",
        39: "VrefD",
    }


def getImuxMap():
    return {
        0: "Iref",
        1: "CdrVcoMainBias",
        2: "CdrVcoBuffBias",
        3: "ICdrCP",
        4: "ICdrFD",
        5: "CdrBuffBias",
        6: "CMLDrivTap2Bias",
        7: "CMLDrivTap1Bias",
        8: "CMLDrivMainBias",
        9: "Intc",
        10: "CapMeas",
        11: "CapMeasPar",
        12: "IDiffPreMain",
        13: "IDiffPreampComp",
        14: "IDiffComp",
        15: "IDiffVth2",
        16: "IDiffVth1Main",
        17: "IDiffLcc",
        18: "IDiffFB",
        19: "IDiffPreampLeft",
        20: "IDiffVth1Left",
        21: "IDiffPreampRight",
        22: "IDiffPreampTopLeft",
        23: "IDiffVth1Right",
        24: "IDiffPreampTop",
        25: "IDiffPreampTopRight",
        26: "NotUsed26",
        27: "NotUsed27",
        28: "IinA",
        29: "IshuntA",
        30: "IinD",
        31: "IshuntD",
    }


class JsonChecker:
    def __init__(self, inputDF, test_type_from_script) -> None:
        # init all available qc types
        self.qc_type = test_type_from_script
        self.inputdataframe = inputDF
        self.qcdataframe = inputDF.get_results()

        self.dict_map = {
            "DATA_TRANSMISSION": {
                "required_keys": ["Delay", "EyeOpening0"],
                "DT_EYE": {"required_keys": ["Delay", "EyeOpening0"]},
                "DT_MERGE": {"required_keys": ["2-to-1", "4-to-1"]},
            },
            "VCAL_CALIBRATION": {
                "VCAL_HIGH": {
                    "required_keys": ["DACs_input", "Vmux30", "Vmux7"],
                    "InjVcalRange": 1,
                    "MonitorV": 7,
                },
                "VCAL_HIGH_SMALL_RANGE": {
                    "required_keys": ["DACs_input", "Vmux30", "Vmux7"],
                    "InjVcalRange": 0,
                    "MonitorV": 7,
                },
                "VCAL_MED": {
                    "required_keys": ["DACs_input", "Vmux30", "Vmux8"],
                    "InjVcalRange": 1,
                    "MonitorV": 8,
                },
                "VCAL_MED_SMALL_RANGE": {
                    "required_keys": ["DACs_input", "Vmux30", "Vmux8"],
                    "InjVcalRange": 0,
                    "MonitorV": 8,
                },
            },
            "ADC_CALIBRATION": {
                "required_keys": ["DACs_input", "ADC_Vmux8", "Vmux30", "Vmux8"],
                "InjVcalRange": 1,
            },
            "SLDO": {
                "required_keys": [
                    "Temperature",
                    "Current",
                    "Vmux30",
                    "Vmux33",
                    "Vmux37",
                    "Vmux34",
                    "Vmux38",
                    "Vmux36",
                    "Vmux32",
                    "Imux0",
                    "Imux28",
                    "Imux29",
                    "Imux30",
                    "Imux31",
                    "Imux63",
                ]
            },
            "INJECTION_CAPACITANCE": {
                "required_keys": ["Vmux4", "Vmux30", "Imux10", "Imux11", "Imux63"]
            },
            "ANALOG_READBACK": {
                "AR_VMEAS": {
                    "required_keys": [
                        "Vmux30",
                        "Vmux33",
                        "Vmux34",
                        "Vmux35",
                        "Vmux36",
                        "Vmux37",
                        "Vmux38",
                        "Imux28",
                        "Imux29",
                        "Imux30",
                        "Imux31",
                        "Imux63",
                    ],
                },
                "AR_TEMP": {
                    "required_keys": [
                        "Vmux14",
                        "Vmux16",
                        "Vmux18",
                        "Vmux2",
                        "Vmux30",
                        "Imux9",
                        "Imux63",
                        "TExtExtNTC",
                    ],
                },
                "AR_VDD": {
                    "required_keys": [
                        "Vmux34",
                        "Vmux38",
                        "Vmux30",
                        "ROSC0",
                        "ROSC1",
                        "ROSC2",
                        "ROSC3",
                        "ROSC4",
                        "ROSC5",
                        "ROSC6",
                        "ROSC7",
                        "ROSC8",
                        "ROSC9",
                        "ROSC10",
                        "ROSC11",
                        "ROSC12",
                        "ROSC13",
                        "ROSC14",
                        "ROSC15",
                        "ROSC16",
                        "ROSC17",
                        "ROSC18",
                        "ROSC19",
                        "ROSC20",
                        "ROSC21",
                        "ROSC22",
                        "ROSC23",
                        "ROSC24",
                        "ROSC25",
                        "ROSC26",
                        "ROSC27",
                        "ROSC28",
                        "ROSC29",
                        "ROSC30",
                        "ROSC31",
                        "ROSC32",
                        "ROSC33",
                        "ROSC34",
                        "ROSC35",
                        "ROSC36",
                        "ROSC37",
                        "ROSC38",
                        "ROSC39",
                        "ROSC40",
                        "ROSC41",
                    ],
                },
                "AR_REGISTER": {
                    "required_keys": [
                        "IrefTrimSense",
                    ],
                },
            },
            "OVERVOLTAGE_PROTECTION": {
                "required_keys": [
                    "Temperature",
                    "Current",
                    "Vmux30",
                    "Vmux32",
                    "Imux28",
                    "Imux30",
                    "Imux63",
                ],
            },
            "LP_MODE": {
                "required_keys": [
                    "FailingPixels",
                    "Temperature",
                    "Current",
                    "Vmux30",
                    "Vmux33",
                    "Vmux36",
                    "Vmux37",
                    "Imux0",
                    "Imux28",
                    "Imux29",
                    "Imux30",
                    "Imux31",
                    "Imux63",
                ]
            },
            "UNDERSHUNT_PROTECTION": {
                "required_keys": [
                    "Temperature",
                    "SetCurrent",
                    "Current",
                    "Vmux30",
                    "Vmux33",
                    "Vmux34",
                    "Vmux35",
                    "Vmux37",
                    "Vmux38",
                    "Vmux39",
                    "Imux0",
                    "Imux28",
                    "Imux29",
                    "Imux30",
                    "Imux31",
                    "Imux63",
                ]
            },
            "IV_MEASURE": {
                "required_keys": [
                    "voltage",
                    "current",
                    "temperature",
                ]
            },
            "LONG_TERM_STABILITY_DCS": {
                "required_keys": [
                    "time",
                    "BIAS_VOLT",
                    "LEAKAGE_CURR",
                    "LV_VOLT",
                    "LV_CURR",
                    "MOD_TEMP",
                    # "humidity",  # not required yet
                ]
            },
            "FLATNESS": {
                "required_keys": [
                    "BACKSIDE_FLATNESS",
                ]
            },
            "QUAD_BARE_MODULE_METROLOGY": {
                "required_keys": [
                    "SENSOR_X",
                    "SENSOR_Y",
                    "FECHIPS_X",
                    "FECHIPS_Y",
                    "FECHIP_THICKNESS",
                    "BARE_MODULE_THICKNESS",
                ]
            },
            "QUAD_MODULE_METROLOGY": {
                "required_keys": [
                    "AVERAGE_THICKNESS",
                    "THICKNESS_INCLUDING_POWER_CONNECTOR",
                    "HV_CAPACITOR_THICKNESS",
                    "DISTANCE_PCB_BARE_MODULE_TOP_LEFT",
                    "DISTANCE_PCB_BARE_MODULE_BOTTOM_RIGHT",
                ]
            },
            "WP_ENVELOPE": {
                "required_keys": [
                    "THICKNESS_MEAN_GA1",
                    "THICKNESS_MEAN_GA2",
                    "THICKNESS_MEAN_GA3",
                    "THICKNESS_MEAN_GA4",
                    "Connectivity_GA1",
                    "Connectivity_GA4",
                    "VISIBILITY",
                ]
            },
            "METROLOGY": {  # Quad PCB
                "required_keys": [
                    "X-Y_DIMENSION_WITHIN_ENVELOP",
                    "AVERAGE_THICKNESS_FECHIP_PICKUP_AREAS",
                    "STD_DEVIATION_THICKNESS_FECHIP_PICKUP_AREAS",
                    "HV_CAPACITOR_THICKNESS",
                    "AVERAGE_THICKNESS_POWER_CONNECTOR",
                    "HV_CAPACITOR_THICKNESS_WITHIN_ENVELOP",
                ]
            },
        }

    def check_testtype(self):
        if (
            self.inputdataframe._subtestType != ""
            and self.inputdataframe._subtestType is not None
        ):
            self.sub_test_type = self.inputdataframe._subtestType
            required_testtype = self.qc_type
            self.required_keywords = self.dict_map[self.qc_type][self.sub_test_type][
                "required_keys"
            ]
        else:
            required_testtype = self.qc_type
            self.required_keywords = self.dict_map[self.qc_type]["required_keys"]

        testtype_from_file = self.inputdataframe._testType
        if required_testtype != testtype_from_file:
            log.error(
                bcolors.ERROR
                + f"Required testtype of the file '{required_testtype}' is not matched to '{testtype_from_file}' from the file! "
                + bcolors.ENDC
            )
            raise KeyError()

    def check_metadata(self):
        required_metadata = ["ModuleSN", "Institution"]
        input_metadata = self.qcdataframe.get_identifiers()
        for key in required_metadata:
            if input_metadata[key] is None:
                log.error(
                    bcolors.ERROR
                    + f" Metadata not complete: {key} missing"
                    + bcolors.ENDC
                )
                raise KeyError()

    def check_keywords_exist(self) -> None:
        for required_keyword in self.required_keywords:
            if required_keyword not in self.qcdataframe._data:
                log.error(
                    bcolors.ERROR + f"{required_keyword} not found! " + bcolors.ENDC
                )
                raise KeyError()

    def check_keywords_length(self) -> None:
        # Check whether the length of measurements are same.
        first_keyword = True
        len_x = 0
        for required_keyword in self.required_keywords:
            if first_keyword:
                len_x = len(self.qcdataframe[required_keyword])
                self.var_x = required_keyword
                first_keyword = False
            if self.qcdataframe.get_x(required_keyword) is True:
                len_x = len(self.qcdataframe[required_keyword])
                self.var_x = required_keyword

        if len_x == 0:
            log.error(
                bcolors.ERROR + "The input is empty! Please check." + bcolors.ENDC
            )
            raise LengthMismatchError()

        for required_keyword in self.required_keywords:
            if len_x != len(self.qcdataframe[required_keyword]):
                log.error(
                    bcolors.ERROR
                    + f"The length of {required_keyword} is not equal to {self.var_x}!"
                    + bcolors.ENDC
                )
                raise LengthMismatchError()

    def check_positive_values(self) -> None:
        # Check whether the contents of measurements are valid, i.e. all positive.
        for required_keyword in self.required_keywords:
            # Allow for negative temperatures
            if required_keyword.lower() in [
                "temperature",
                "failingpixels",
                "textextntc",
                "voltage",
                "current",
                "bias_volt",
                "mod_temp",
                "vmux30",
                "imux63",
            ]:
                continue
            if ((self.qcdataframe[required_keyword]) < 0).sum() > 0:
                log.error(
                    bcolors.ERROR
                    + f"Negative measurements observed in {required_keyword}"
                    + bcolors.ENDC
                )
                raise NegativeMeasurementError()

    def check_parameters_overwritten(self) -> None:
        # Check whether the parameters are overwritten correctly.
        if self.inputdataframe._subtestType != "":
            parameters_to_check = self.dict_map[self.qc_type][self.sub_test_type].copy()
        else:
            parameters_to_check = self.dict_map[self.qc_type].copy()

        parameters_to_check.pop("required_keys")

        for k, v in parameters_to_check.items():
            value_from_file = lookup(self.qcdataframe._meta_data, k)
            if value_from_file is None:
                log.error(
                    bcolors.ERROR
                    + f"Measurement output file Corrupted! Please check this key: {k}"
                    + bcolors.ENDC
                )
                raise KeyError(k)
            if v != value_from_file:
                log.error(
                    bcolors.ERROR
                    + f"Values Mismathed for this key {k}: {value_from_file} from file, but required {v} "
                    + bcolors.ENDC
                )
                raise KeyError()

    def check(self, *, keywords_length=True) -> None:
        self.check_testtype()
        self.check_keywords_exist()
        if keywords_length:
            self.check_keywords_length()
        self.check_positive_values()
        self.check_parameters_overwritten()
        self.check_metadata()


class DataExtractor(JsonChecker):
    def __init__(self, inputDF, test_type_from_script) -> None:
        super().__init__(inputDF, test_type_from_script)
        qcframe = inputDF.get_results()
        self.df = qcframe._data
        chip_name = ""
        try:
            chip_name = next(iter(qcframe._meta_data["ChipConfigs"]))
        except IndexError:
            log.error(
                bcolors.BADRED
                + "One of the configuration files is empty"
                + bcolors.ENDC
            )

        if chip_name not in {"RD53B", "ITKPIXV2"}:
            log.warning(
                bcolors.WARNING
                + "Chip type in configuration not one of the expected chip names (RD53B or ITKPIXV2)"
                + bcolors.ENDC
            )

        self.rImux = qcframe._meta_data["ChipConfigs"][chip_name]["Parameter"].get(
            "R_Imux", 10000.0
        )
        self.kIinA = qcframe._meta_data["ChipConfigs"][chip_name]["Parameter"].get(
            "KSenseInA", 21000.0
        )
        self.kIinD = qcframe._meta_data["ChipConfigs"][chip_name]["Parameter"].get(
            "KSenseInD", 21000.0
        )
        self.kIshuntA = qcframe._meta_data["ChipConfigs"][chip_name]["Parameter"].get(
            "KSenseShuntA", 21600.0
        )
        self.kIshuntD = qcframe._meta_data["ChipConfigs"][chip_name]["Parameter"].get(
            "KSenseShuntD", 21600.0
        )

        # check if kIshuntA/D were using the latest estimate, if not overwrite them and print out a warning
        k_shunt_A_expected = int(21600 / 21000 * self.kIinA)
        k_shunt_D_expected = int(21600 / 21000 * self.kIinD)
        if abs(self.kIshuntA - k_shunt_A_expected) > 1:
            self.kIshuntA = k_shunt_A_expected
            log.warning(
                bcolors.WARNING
                + "KSenseShuntA in measurement metadata is not using the latest estimate. "
                + "Running analysis with latest estimate instead. Please run the following command before "
                + "continuing your measurements: "
                + "$ analysis-check-kshunt-in-chip-config -c /path/to/module/dir/like/20UPIM13602014"
                + bcolors.ENDC
            )
        if abs(self.kIshuntD - k_shunt_D_expected) > 1:
            self.kIshuntD = k_shunt_D_expected
            log.warning(
                bcolors.WARNING
                + "KSenseShuntD in measurement metadata is not using the latest estimate. "
                + "Running analysis with latest estimate instead. Please run the following command before "
                + "continuing your measurements: "
                + "$ analysis-check-kshunt-in-chip-config -c /path/to/module/dir/like/20UPIM13602014"
                + bcolors.ENDC
            )

        self.VmuxGnd = "Vmux30"
        self.ImuxGnd = "Imux63"

    def getQuantity(self, key):
        return getattr(self, key, lambda: False)()

    def Vmux0(self):
        return {
            getVmuxMap()[0]: {
                "X": self.df["Vmux0"]["X"],
                "Unit": self.df["Vmux0"]["Unit"],
                "Values": (
                    self.df["Vmux0"]["Values"] - self.df[self.VmuxGnd]["Values"]
                ),
            }
        }

    def Vmux2(self):
        return {
            getVmuxMap()[2]: {
                "X": self.df["Vmux2"]["X"],
                "Unit": self.df["Vmux2"]["Unit"],
                "Values": (
                    self.df["Vmux2"]["Values"] - self.df[self.VmuxGnd]["Values"]
                ),
            }
        }

    def Vmux3(self):
        return {
            getVmuxMap()[3]: {
                "X": self.df["Vmux3"]["X"],
                "Unit": self.df["Vmux3"]["Unit"],
                "Values": (self.df["Vmux3"]["Values"] - self.df[self.VmuxGnd]["Values"])
                * 2,
            }
        }

    def Vmux4(self):
        return {
            getVmuxMap()[4]: {
                "X": self.df["Vmux4"]["X"],
                "Unit": self.df["Vmux4"]["Unit"],
                "Values": (self.df["Vmux4"]["Values"] - self.df[self.VmuxGnd]["Values"])
                * 2,
            }
        }

    def Vmux5(self):
        return {
            getVmuxMap()[5]: {
                "X": self.df["Vmux5"]["X"],
                "Unit": self.df["Vmux5"]["Unit"],
                "Values": self.df["Vmux5"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux6(self):
        return {
            getVmuxMap()[6]: {
                "X": self.df["Vmux6"]["X"],
                "Unit": self.df["Vmux6"]["Unit"],
                "Values": self.df["Vmux6"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux7(self):
        return {
            getVmuxMap()[7]: {
                "X": self.df["Vmux7"]["X"],
                "Unit": self.df["Vmux7"]["Unit"],
                "Values": self.df["Vmux7"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux8(self):
        return {
            getVmuxMap()[8]: {
                "X": self.df["Vmux8"]["X"],
                "Unit": self.df["Vmux8"]["Unit"],
                "Values": self.df["Vmux8"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux9(self):
        return {
            getVmuxMap()[9]: {
                "X": self.df["Vmux9"]["X"],
                "Unit": self.df["Vmux9"]["Unit"],
                "Values": self.df["Vmux9"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux10(self):
        return {
            getVmuxMap()[10]: {
                "X": self.df["Vmux10"]["X"],
                "Unit": self.df["Vmux10"]["Unit"],
                "Values": self.df["Vmux10"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux11(self):
        return {
            getVmuxMap()[11]: {
                "X": self.df["Vmux11"]["X"],
                "Unit": self.df["Vmux11"]["Unit"],
                "Values": self.df["Vmux11"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux12(self):
        return {
            getVmuxMap()[12]: {
                "X": self.df["Vmux12"]["X"],
                "Unit": self.df["Vmux12"]["Unit"],
                "Values": self.df["Vmux12"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux13(self):
        return {
            getVmuxMap()[13]: {
                "X": self.df["Vmux13"]["X"],
                "Unit": self.df["Vmux13"]["Unit"],
                "Values": self.df["Vmux13"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux14(self):
        return {
            getVmuxMap()[14]: {
                "X": self.df["Vmux14"]["X"],
                "Unit": self.df["Vmux14"]["Unit"],
                "Values": self.df["Vmux14"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux15(self):
        return {
            getVmuxMap()[15]: {
                "X": self.df["Vmux15"]["X"],
                "Unit": self.df["Vmux15"]["Unit"],
                "Values": self.df["Vmux15"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux16(self):
        return {
            getVmuxMap()[16]: {
                "X": self.df["Vmux16"]["X"],
                "Unit": self.df["Vmux16"]["Unit"],
                "Values": self.df["Vmux16"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux17(self):
        return {
            getVmuxMap()[17]: {
                "X": self.df["Vmux17"]["X"],
                "Unit": self.df["Vmux17"]["Unit"],
                "Values": self.df["Vmux17"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux18(self):
        return {
            getVmuxMap()[18]: {
                "X": self.df["Vmux18"]["X"],
                "Unit": self.df["Vmux18"]["Unit"],
                "Values": self.df["Vmux18"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux30(self):
        return {
            getVmuxMap()[30]: {
                "X": self.df["Vmux30"]["X"],
                "Unit": self.df["Vmux30"]["Unit"],
                "Values": self.df["Vmux30"]["Values"],
            }
        }

    def Vmux31(self):
        return {
            getVmuxMap()[31]: {
                "X": self.df["Vmux31"]["X"],
                "Unit": self.df["Vmux31"]["Unit"],
                "Values": self.df["Vmux31"]["Values"] - self.df[self.VmuxGnd]["Values"],
            }
        }

    def Vmux32(self):
        return {
            getVmuxMap()[32]: {
                "X": self.df["Vmux32"]["X"],
                "Unit": self.df["Vmux32"]["Unit"],
                "Values": (
                    self.df["Vmux32"]["Values"] - self.df[self.VmuxGnd]["Values"]
                )
                * 3.33,
            }
        }

    def Vmux33(self):
        return {
            getVmuxMap()[33]: {
                "X": self.df["Vmux33"]["X"],
                "Unit": self.df["Vmux33"]["Unit"],
                "Values": (
                    self.df["Vmux33"]["Values"] - self.df[self.VmuxGnd]["Values"]
                )
                * 4,
            }
        }

    def Vmux34(self):
        return {
            getVmuxMap()[34]: {
                "X": self.df["Vmux34"]["X"],
                "Unit": self.df["Vmux34"]["Unit"],
                "Values": (
                    self.df["Vmux34"]["Values"] - self.df[self.VmuxGnd]["Values"]
                )
                * 2,
            }
        }

    def Vmux35(self):
        return {
            getVmuxMap()[35]: {
                "X": self.df["Vmux35"]["X"],
                "Unit": self.df["Vmux35"]["Unit"],
                "Values": (
                    self.df["Vmux35"]["Values"] - self.df[self.VmuxGnd]["Values"]
                ),
            }
        }

    def Vmux36(self):
        return {
            getVmuxMap()[36]: {
                "X": self.df["Vmux36"]["X"],
                "Unit": self.df["Vmux36"]["Unit"],
                "Values": (
                    self.df["Vmux36"]["Values"] - self.df[self.VmuxGnd]["Values"]
                )
                * 4,
            }
        }

    def Vmux37(self):
        return {
            getVmuxMap()[37]: {
                "X": self.df["Vmux37"]["X"],
                "Unit": self.df["Vmux37"]["Unit"],
                "Values": (
                    self.df["Vmux37"]["Values"] - self.df[self.VmuxGnd]["Values"]
                )
                * 4,
            }
        }

    def Vmux38(self):
        return {
            getVmuxMap()[38]: {
                "X": self.df["Vmux38"]["X"],
                "Unit": self.df["Vmux38"]["Unit"],
                "Values": (
                    self.df["Vmux38"]["Values"] - self.df[self.VmuxGnd]["Values"]
                )
                * 2,
            }
        }

    def Vmux39(self):
        return {
            getVmuxMap()[39]: {
                "X": self.df["Vmux39"]["X"],
                "Unit": self.df["Vmux39"]["Unit"],
                "Values": (
                    self.df["Vmux39"]["Values"] - self.df[self.VmuxGnd]["Values"]
                ),
            }
        }

    def Imux0(self):
        return {
            getImuxMap()[0]: {
                "X": self.df["Imux0"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux0"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux1(self):
        return {
            getImuxMap()[1]: {
                "X": self.df["Imux1"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux1"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux2(self):
        return {
            getImuxMap()[2]: {
                "X": self.df["Imux2"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux2"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux3(self):
        return {
            getImuxMap()[3]: {
                "X": self.df["Imux3"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux3"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux4(self):
        return {
            getImuxMap()[4]: {
                "X": self.df["Imux4"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux4"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux5(self):
        return {
            getImuxMap()[5]: {
                "X": self.df["Imux5"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux5"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux6(self):
        return {
            getImuxMap()[6]: {
                "X": self.df["Imux6"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux6"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux7(self):
        return {
            getImuxMap()[7]: {
                "X": self.df["Imux7"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux7"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux8(self):
        return {
            getImuxMap()[8]: {
                "X": self.df["Imux8"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux8"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux9(self):
        return {
            getImuxMap()[9]: {
                "X": self.df["Imux9"]["X"],
                "Unit": "A",
                "Values": (self.df["Imux9"]["Values"] - self.df[self.ImuxGnd]["Values"])
                / self.rImux,
            }
        }

    def Imux10(self):
        return {
            getImuxMap()[10]: {
                "X": self.df["Imux10"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux10"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux11(self):
        return {
            getImuxMap()[11]: {
                "X": self.df["Imux11"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux11"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux12(self):
        return {
            getImuxMap()[12]: {
                "X": self.df["Imux12"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux12"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux13(self):
        return {
            getImuxMap()[13]: {
                "X": self.df["Imux13"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux13"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux14(self):
        return {
            getImuxMap()[14]: {
                "X": self.df["Imux14"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux14"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux15(self):
        return {
            getImuxMap()[15]: {
                "X": self.df["Imux15"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux15"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux16(self):
        return {
            getImuxMap()[16]: {
                "X": self.df["Imux16"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux16"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux17(self):
        return {
            getImuxMap()[17]: {
                "X": self.df["Imux17"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux17"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux18(self):
        return {
            getImuxMap()[18]: {
                "X": self.df["Imux18"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux18"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux19(self):
        return {
            getImuxMap()[19]: {
                "X": self.df["Imux15"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux15"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux20(self):
        return {
            getImuxMap()[20]: {
                "X": self.df["Imux20"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux20"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux21(self):
        return {
            getImuxMap()[21]: {
                "X": self.df["Imux21"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux21"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux22(self):
        return {
            getImuxMap()[22]: {
                "X": self.df["Imux22"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux22"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux23(self):
        return {
            getImuxMap()[23]: {
                "X": self.df["Imux23"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux23"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux24(self):
        return {
            getImuxMap()[24]: {
                "X": self.df["Imux24"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux24"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux25(self):
        return {
            getImuxMap()[25]: {
                "X": self.df["Imux25"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux25"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux,
            }
        }

    def Imux28(self):
        return {
            getImuxMap()[28]: {
                "X": self.df["Imux28"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux28"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux
                * self.kIinA,
            }
        }

    def Imux29(self):
        return {
            getImuxMap()[29]: {
                "X": self.df["Imux29"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux29"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux
                * self.kIshuntA,
            }
        }

    def Imux30(self):
        return {
            getImuxMap()[30]: {
                "X": self.df["Imux30"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux30"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux
                * self.kIinD,
            }
        }

    def Imux31(self):
        return {
            getImuxMap()[31]: {
                "X": self.df["Imux31"]["X"],
                "Unit": "A",
                "Values": (
                    self.df["Imux31"]["Values"] - self.df[self.ImuxGnd]["Values"]
                )
                / self.rImux
                * self.kIshuntD,
            }
        }

    def IcoreA(self):
        return {
            "IcoreA": {
                "X": False,
                "Unit": "A",
                "Values": self.df["IinA"]["Values"] - self.df["IshuntA"]["Values"],
            }
        }

    def IcoreD(self):
        return {
            "IcoreD": {
                "X": False,
                "Unit": "A",
                "Values": self.df["IinD"]["Values"] - self.df["IshuntD"]["Values"],
            }
        }

    def Iin(self):
        return {
            "Iin": {
                "X": False,
                "Unit": "A",
                "Values": self.df["IinA"]["Values"] + self.df["IinD"]["Values"],
            }
        }

    def calculate(self):
        # Convert values from list to numpy array
        for key, value in self.df.items():
            self.df.update(
                {
                    key: {
                        "X": value["X"],
                        "Unit": value["Unit"],
                        "Values": np.array(value["Values"]),
                    }
                }
            )

        df_keys = self.df.copy().keys()

        # Calculate basic quantities
        for key in df_keys:
            newQuantity = self.getQuantity(key)
            if newQuantity:
                self.df.update(newQuantity)

        # Calculated complex quantities
        if self.df.get("IinA") and self.df.get("IshuntA"):
            self.df.update(self.getQuantity("IcoreA"))
        if self.df.get("IinD") and self.df.get("IshuntD"):
            self.df.update(self.getQuantity("IcoreD"))
        if self.df.get("IinA") and self.df.get("IinD"):
            self.df.update(self.getQuantity("Iin"))

        return self.df


def linear_fit(x, y):
    """Linear fit with PyROOT

    Args:
        x (array): the x values, input DACs for VCal calibration
        y (array): the y values, measured Vmux[int] for VCal calibration

    Returns:
        result (tuple(float, float)): the offset and slope of the fitted line
    """
    try:
        from ROOT import (  # pylint: disable=import-outside-toplevel  # noqa: PLC0415
            TF1,
            TGraph,
        )
    except ImportError as exc:
        msg = "ROOT did not import successfully."
        raise RuntimeError(msg) from exc

    gr = TGraph(len(x), array("d", x), array("d", y))

    f = TF1("f", "[1] * x + [0]")
    result = gr.Fit(f, "S")

    return result.Parameter(1), result.Parameter(0), (result.Chi2() / len(x)) ** 0.5


def linear_fit_np(x, y):
    """Linear fit with NumPy. numpy.linalg.lstsq() is called.

    Args:
        x (array): the x values, input DACs for VCal calibration
        y (array): the y values, measured Vmux[int] for VCal calibration

    Returns:
        p1 (float): the slope of the fitted line
        p0 (float): the offset of the fitted line
    """
    A = np.vstack([x, np.ones(len(x))]).T
    fit = np.linalg.lstsq(A, y, rcond=None)
    p1, p0 = fit[0]
    residual = 1000
    if len(fit[1]) > 0:
        residual = fit[1][0]
    return p1, p0, (residual / len(x)) ** 0.5


def get_inputs(input_meas: Path) -> list[Path]:
    # Figure out if input if single file or directory
    allinputs = []
    if input_meas.is_file():
        allinputs = [input_meas]
    elif input_meas.is_dir():
        allinputs = sorted(input_meas.glob("*.json"))
        if not allinputs:
            log.error(
                bcolors.ERROR
                + f"No input json files in `{input_meas}` are found! Please check the input path."
                + bcolors.ENDC
            )
            raise FileNotFoundError()
    else:
        log.error(
            bcolors.ERROR
            + "Input is not recognized as single file or path to directory containing files. Please check the input."
            + bcolors.ENDC
        )
        raise FileNotFoundError()
    return allinputs


def get_time_stamp(filename):
    # Read timestamp from measurement output file name
    # Assumes that filename ends with pattern: "/{timestamp}/{chipname}.json"
    return filename.parent.name


def recursive_json_update(dict1, dict2):
    for key, value in dict2.items():
        if key in dict1:
            if isinstance(value, dict) and isinstance(dict1[key], dict):
                recursive_json_update(dict1[key], value)
            else:
                dict1[key] = value
        else:
            dict1[key] = value


def get_BOMCode_from_metadata(metadata, layer):
    # this covers when the measurement file does not contain the BOM information, but we know

    BOMCode = metadata.get("BOMCode")
    if BOMCode is None:
        chip_config = metadata.get("ChipConfigs")
        chip_type = get_chip_type_from_config(chip_config)
        if chip_type != "RD53B":
            msg = "The BOMCode is not available in the output measurement file. Assume the V1.1 BOM is used"
            log.warning(msg)
        BOMCode = default_BOMCode_from_layer(
            layer
        )  ##defaulted  to be V1.1 BOM, with layer inform

    return BOMCode


def get_qc_config(
    qc_criteria_path: Path | None = None,
    test_type: str | None = None,
    mod_SN="",
    bom="",
) -> dict[str, Any]:
    if qc_criteria_path is None:
        try:
            chip_type = get_chip_type_from_serial_number(mod_SN)
        except Exception as e:
            log.error(e)
            log.error(
                bcolors.ERROR + " Couldn't get chip type from module SN" + bcolors.ENDC
            )
            raise RuntimeError() from e
        default_qc_criteria_path = data / "analysis_cuts.json"
        log.info(f"Using {default_qc_criteria_path} for QC criteria")

        try:
            with resources.as_file(default_qc_criteria_path) as path:
                default_qc_config = json.loads(path.read_text(encoding="utf-8"))

            if chip_type == "ITKPIXV2":
                if bom:
                    BOM_suffix = get_cutFile_suffix(bom)
                    qc_criteria_path_V2 = (
                        data / f"analysis_cuts_V2chip{BOM_suffix}.json"
                    )
                else:
                    qc_criteria_path_V2 = data / "analysis_cuts_V2chip_V1bom.json"

                with resources.as_file(qc_criteria_path_V2) as bom_dependend_cuts:
                    temp_qc_config = json.loads(
                        bom_dependend_cuts.read_text(encoding="utf-8")
                    )
                    ##only for the V2 chips we have different BOM versions. Make sure that if a test has cuts sets in the BOM dependent file, the BOM information is present in the measurement file
                    if (
                        (test_type in temp_qc_config)
                        and (
                            test_type
                            not in [
                                "MIN_HEALTH_TEST",
                                "TUNING_TUNED",
                                "TUNING_UNTUNED",
                                "PIXEL_FAILURE_ANALYSIS",
                            ]
                        )
                        and not bom
                    ):
                        msg = f"The cuts for '{test_type}' depends on the BOM. A BOM version need to be stored in the measurement output file and passed to the get_qc_config for this cuts."
                        raise ValueError(msg)

                    recursive_json_update(default_qc_config, temp_qc_config)
                    log.info(f"Updating QC criteria with {qc_criteria_path_V2} ")

            else:
                qc_criteria_path_V1 = data / "analysis_cuts_V1chip.json"
                with resources.as_file(qc_criteria_path_V1) as path_V1:
                    temp_qc_config = json.loads(path_V1.read_text(encoding="utf-8"))
                    recursive_json_update(default_qc_config, temp_qc_config)
                log.info(f"Updating QC criteria with {qc_criteria_path_V1} ")

        except Exception as e:
            log.error(e)
            log.error(
                bcolors.ERROR
                + f" QC criteria json file is ill-formated ({qc_criteria_path}) - please fix! Exiting."
                + bcolors.ENDC
            )
            raise RuntimeError() from e

    # when we pass the input cut file directly, it assume the file contains the full lists of cuts to be applied
    else:
        with resources.as_file(qc_criteria_path) as path:
            default_qc_config = json.loads(path.read_text(encoding="utf-8"))
    if test_type and test_type not in default_qc_config:
        log.error(
            bcolors.ERROR
            + f" QC criteria for {test_type} not found in {qc_criteria_path} - please fix! Exiting."
            + bcolors.ENDC
        )
        raise FileNotFoundError()
    return default_qc_config.get(test_type)


def lookup(input_dict, search_key, stack=None):
    # recursion to look up the desired key in a dict and record the path
    for k, v in input_dict.items():
        if k == search_key:
            return v

        if isinstance(v, dict):
            _v = lookup(v, search_key, stack)
            if _v is not None:
                if stack is not None:
                    stack.append(k)
                return _v

    return None


def convert_prefix(invalue, inprefix=None, targetprefix="u"):
    prefix = {
        "y": 1e-24,  # yocto
        "z": 1e-21,  # zepto
        "a": 1e-18,  # atto
        "f": 1e-15,  # femto
        "p": 1e-12,  # pico
        "n": 1e-9,  # nano
        "u": 1e-6,  # micro
        "m": 1e-3,  # mili
        "c": 1e-2,  # centi
        "d": 1e-1,  # deci
        "": 1e0,  # no prefix, but not None
        "k": 1e3,  # kilo
        "M": 1e6,  # mega
        "G": 1e9,  # giga
        "T": 1e12,  # tera
        "P": 1e15,  # peta
        "E": 1e18,  # exa
        "Z": 1e21,  # zetta
        "Y": 1e24,  # yotta
    }
    if len(inprefix) == 2:
        inprefix = inprefix[0]
    elif len(inprefix) == 1 and inprefix not in prefix:  ## e.g. if inprefix is "A"
        inprefix = ""
    elif (
        inprefix is None or len(inprefix) > 2
    ):  ## if no inprefix is given or if unclear, determine the average value
        log.warning(
            bcolors.WARNING
            + f'Cannot decipher the prefix "{inprefix}"! Guessing from data: {guess_prefix(invalue)}'
            + bcolors.ENDC
        )
        inprefix = guess_prefix(invalue)

    if inprefix not in prefix:
        log.error(
            bcolors.ERROR + f'Not a valid input prefix: "{inprefix}"' + bcolors.ENDC
        )
        raise KeyError()

    if len(targetprefix) == 2:
        targetprefix = targetprefix[0]
    elif len(targetprefix) == 1 and targetprefix not in prefix:
        targetprefix = ""

    if len(targetprefix) > 2 or targetprefix not in prefix:
        log.error(
            bcolors.ERROR
            + f'Not a valid target prefix: "{targetprefix}"'
            + bcolors.ENDC
        )
        raise KeyError()

    outvalue = []
    try:
        outvalue = [item * prefix[inprefix] / prefix[targetprefix] for item in invalue]
    except Exception as e:
        if isinstance(invalue, (int, float)):
            outvalue = invalue * prefix[inprefix] / prefix[targetprefix]
        else:
            log.warning(f"Can't process input {invalue}! {e}")
            raise ValueError() from e
    return outvalue


def guess_prefix(invalue):  ## TODO: check with more data and across vendors
    ## assumes data is leakage current
    if not isinstance(invalue, (list, np.ndarray, tuple)):
        log.error(
            bcolors.ERROR
            + f"A list/array/tuple of values is expected. Cannot determine prefix based on input {invalue} of type {type(invalue)}."
            + bcolors.ENDC
        )
        raise TypeError()

    invalue = [abs(c) for c in invalue]

    ## leakage current should be between 5nA (cold HPK) and a few uA
    if np.average(invalue) <= 5e-6:
        return ""
    if 5e-6 < np.average(invalue) <= 2e-3:  ## 0.000005 - 0.002
        return "m"
    if 2e-3 < np.average(invalue) <= 5e0:  ## 0.002 - 5
        return "u"
    if 5e0 < np.average(invalue) <= 2e3:  ## 5 - 2000
        return "n"

    log.error(
        bcolors.ERROR
        + f"Input data out of range of interest: {np.average(invalue)}"
        + bcolors.ENDC
    )
    raise ValueError()
