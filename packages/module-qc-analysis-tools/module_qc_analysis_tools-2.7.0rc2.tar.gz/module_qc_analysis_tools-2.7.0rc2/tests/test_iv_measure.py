import json
from pathlib import Path

import matplotlib.pyplot as plt
import pytest
from module_qc_data_tools import (
    get_layer_from_sn,
    load_json,
)

from module_qc_analysis_tools.analysis.iv_measure import analyse
from module_qc_analysis_tools.utils.misc import convert_prefix, get_inputs


@pytest.fixture
def data_path():
    return Path() / "tests" / "test_iv_measure"


@pytest.mark.parametrize(
    ("measurement", "passes"),
    [
        ("20UPGM23210110_INITIAL_COLD.json", True),
        ("20UPGM23210493_FINAL_COLD.json", True),
        ("20UPGM23210494_FINAL_COLD.json", True),
        ("20UPGM23211355_INITIAL_COLD.json", True),
        ("20UPGM22110566_FINAL_WARM.json", False),
        ("20UPGM22210083_INITIAL_WARM.json", False),
        ("20UPGM23210951_INITIAL_WARM.json", False),
        ("20UPGM23210964_INITIAL_COLD.json", True),
        ("20UPIM12602109_INITIAL_WARM.json", False),
        ("20UPIM02202117_INITIAL_WARM.json", False),
        ("20UPIM02202118_INITIAL_WARM.json", True),
    ],
)
## just a simplified version of IV_MEASURE.py without checks and stuff
def test_iv_measure(data_path, measurement, passes):
    serial_number = measurement.split("_")[0]
    allinputs = get_inputs(data_path / measurement)
    reference_iv = get_inputs(data_path / Path(serial_number + "_ref.json"))

    for filename in sorted(allinputs):
        inputDFs = load_json(filename)

        for inputDF in inputDFs:
            # Get info
            qcframe = inputDF.get_results()
            metadata = qcframe.get_meta_data()
            module_sn = metadata.get("ModuleSN")
            layer = get_layer_from_sn(module_sn)

            # Simplistic QC criteria
            meas_array = {}
            _prefix = None

            if qcframe._data["current"]["Unit"] != "uA":
                _prefix = qcframe._data["current"]["Unit"]

            for key in ["current", "sigma current"]:
                qcframe._data[key]["Values"] = convert_prefix(
                    qcframe._data[key]["Values"],
                    inprefix=qcframe._data[key]["Unit"],
                    targetprefix="u",
                )
                qcframe._data[key]["Unit"] = "uA"

            for key in qcframe._data:
                meas_array[key] = qcframe._data[key]["Values"]
            inputdata = None
            with Path(reference_iv[0]).open(encoding="utf-8") as serialized:
                inputdata = json.load(serialized)
                if not isinstance(inputdata, list):
                    inputdata = [inputdata]

            inputdata_dict = {jtem["target_component"]: jtem for jtem in inputdata}
            baremoduleIV = inputdata_dict.get(module_sn)

            _results, passes_qc, _summary, fig = analyse(
                meas_array,
                None,
                module_sn,
                layer,
                baremoduleIV,
                metadata.get("AverageTemperature"),
            )
            if fig:
                plt.close()

    assert passes_qc == passes
