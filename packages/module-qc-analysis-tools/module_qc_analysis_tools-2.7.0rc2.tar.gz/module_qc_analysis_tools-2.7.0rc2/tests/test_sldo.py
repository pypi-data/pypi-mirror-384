import numpy as np
from scipy.optimize import curve_fit

from module_qc_analysis_tools.analysis.sldo import (
    linear_func,
)


def test_sldo_lin_fit_min_Iin():
    """test the linear function used in the sldo analysis used to determine the min Iin to pass Ishunt QC criteria"""

    x = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])  # your x values array
    values1 = np.array([1, 0, 0, 0.04, 0, 0, 0, 0, 0, 0])
    values2 = np.array([0, 0, 0, 3, 4, 0, 5, 9, 0, 0])  # your y values array

    # minimal I shunt value that is trustable for the fit, here it is called threshold from which on data is taken into account
    min_I_shunt_trustable = 0.05

    # minimal I shunt to pass QC from cut file
    min_I_shunt_cut_digital = 2

    chi2 = []
    intersections = []

    for y in [values1, values2]:
        # find indexes where y in trustable region
        over_threshold = np.where(y > min_I_shunt_trustable)[0]

        if len(over_threshold) <= 3:
            intersections.append(-999)
            chi2.append(-999)

        else:
            x_over_threshold_limited = x[over_threshold][:4]
            y_over_threshold_limited = y[over_threshold][:4]

            # only take first 4 points into account for the fit

            popt = curve_fit(
                linear_func, x_over_threshold_limited, y_over_threshold_limited
            )[0]
            intersec = (min_I_shunt_cut_digital - popt[1]) / popt[0]
            intersections.append(round(intersec, 4))

            # calculate the chi-square
            residuals = y_over_threshold_limited - linear_func(
                x_over_threshold_limited, *popt
            )
            chi_square = np.sum(
                (residuals**2) / linear_func(x_over_threshold_limited, *popt)
            )
            chi2.append(round(chi_square, 5))

    assert (intersections, chi2) == ([-999, 2.5], [-999, 0.58212]), (
        f"FAIL: test_sldo_lin_fit_min_Iin detected intersections={intersections} and chi2={chi_square}, expected [-999, 2.5000] and [-999,0.58212]"
    )
