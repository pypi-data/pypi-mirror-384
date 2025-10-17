from module_qc_analysis_tools.cli.ANALOG_READBACK import (
    check_vdd_trim_saturation,
)


def test_vdd_saturation_true():
    linear_data = [1.1 + (x * 0.1) for x in range(16)]
    nonlinear_data = linear_data[:-3] + [linear_data[-4]] * 3
    trim = check_vdd_trim_saturation(nonlinear_data)
    assert trim == 12, (
        f"FAIL: check_vdd_trim_saturation detected trim={trim}, expected 12."
    )


def test_vdd_saturation_false():
    linear_data = [1.1 + (x * 0.1) for x in range(16)]
    trim = check_vdd_trim_saturation(linear_data)
    assert trim == -1, (
        f"FAIL: check_vdd_trim_saturation detected trim={trim}, expected -1.0"
    )
