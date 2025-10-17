<style type="text/css">
/* make sure we don't wrap first column of tables on this page */
table tr td:first-of-type {
    text-wrap: nowrap;
}
</style>

# Analyses

## Overview

An overview of the steps in the module QC procedure is documented in the
[Electrical specification and QC procedures for ITkPixV1.1 modules](https://gitlab.cern.ch/atlas-itk/pixel/module/itkpix-electrical-qc/)
document and in
[this spreadsheet](https://docs.google.com/spreadsheets/d/1qGzrCl4iD9362RwKlstZASbhphV_qTXPeBC-VSttfgE/edit#gid=989740987).
The analysis scripts in this repository require input files with measurement
data. The measurement data should be collected using the
[module-qc-tools](https://atlas-itk-pixel-mqat.docs.cern.ch) package.

### Example Commands

Below are some example commands for a chip in a quad module

```
mqat analysis adc-calibration -i ../module-qc-tools/emulator/outputs/Measurements/ADC_CALIBRATION/1000000001/
mqat analysis sldo -i ../module-qc-tools/emulator/outputs/Measurements/SLDO/1000000001/
mqat analysis analog-readback -i ../module-qc-tools/emulator/outputs/Measurements/ANALOG_READBACK/1000000001/
mqat analysis vcal-calibration -i ../module-qc-tools/emulator/outputs/Measurements/VCAL_CALIBRATION/1000000001/
mqat analysis injection-capacitance -i ../module-qc-tools/emulator/outputs/Measurements/INJECTION_CAPACITANCE/1000000001/
```

### Updating Chip Configs

After each analysis, you must update your chip configs

- [`mqat config update`](reference/cli.md#mqat-config-update)
- [`module-qc-analysis-tools config update`](reference/cli.md#mqat-config-update)
- [`analysis-update-chip-config`](reference/cli.md#mqat-config-update)

### Preparing for Complex Analysis

Some analyses require analysing YARR scans. To prepare for this, you need to
load the YARR scans in first

- [`mqat config load-yarr-scans`](reference/cli.md#mqat-config-load-yarr-scans)
- [`module-qc-analysis-tools config load-yarr-scans`](reference/cli.md#mqat-config-load-yarr-scans)
- [`analysis-load-yarr-scans`](reference/cli.md#mqat-config-load-yarr-scans)

## Sensor IV Measurement

- [`mqat analysis iv-measure`](reference/cli.md#mqat-analysis-iv-measure)
- [`module-qc-tools analysis iv-measure`](reference/cli.md#mqat-analysis-iv-measure)
- [`analysis-IV-MEASURE`](reference/cli.md#mqat-analysis-iv-measure)

## ADC calibration

- [`mqat analysis adc-calibration`](reference/cli.md#mqat-analysis-adc-calibration)
- [`module-qc-tools analysis adc-calibration`](reference/cli.md#mqat-analysis-adc-calibration)
- [`analysis-ADC-CALIBRATIOn`](reference/cli.md#mqat-analysis-adc-calibration)

## Analog readback

- [`mqat analysis analog-readback`](reference/cli.md#mqat-analysis-analog-readback)
- [`module-qc-tools analysis analog-readback`](reference/cli.md#mqat-analysis-analog-readback)
- [`analysis-ANALOG-READBACK`](reference/cli.md#mqat-analysis-analog-readback)

## SLDOVI

- [`mqat analysis sldo`](reference/cli.md#mqat-analysis-sldo)
- [`module-qc-tools analysis sldo`](reference/cli.md#mqat-analysis-sldo)
- [`analysis-SLDO`](reference/cli.md#mqat-analysis-sldo)

## VCal calibration

- [`mqat analysis vcal-calibration`](reference/cli.md#mqat-analysis-vcal-calibration)
- [`module-qc-tools analysis vcal-calibration`](reference/cli.md#mqat-analysis-vcal-calibration)
- [`analysis-VCAL-CALIBRATION`](reference/cli.md#mqat-analysis-vcal-calibration)

## Injection capacitance

- [`mqat analysis injection-capacitance`](reference/cli.md#mqat-analysis-injection-capacitance)
- [`module-qc-tools analysis injection-capacitance`](reference/cli.md#mqat-analysis-injection-capacitance)
- [`analysis-INJECTION-CAPACITANCE`](reference/cli.md#mqat-analysis-injection-capacitance)

## Low Power Mode

- [`mqat analysis lp-mode`](reference/cli.md#mqat-analysis-lp-mode)
- [`module-qc-tools analysis lp-mode`](reference/cli.md#mqat-analysis-lp-mode)
- [`analysis-LP-MODE`](reference/cli.md#mqat-analysis-lp-mode)

## Overvoltage Protection

- [`mqat analysis overvoltage-protection`](reference/cli.md#mqat-analysis-overvoltage-protection)
- [`module-qc-tools analysis overvoltage-protection`](reference/cli.md#mqat-analysis-overvoltage-protection)
- [`analysis-OVERVOLTAGE-PROTECTION`](reference/cli.md#mqat-analysis-overvoltage-protection)

## Undershunt Protection

- [`mqat analysis undershunt-protection`](reference/cli.md#mqat-analysis-undershunt-protection)
- [`module-qc-tools analysis undershunt-protection`](reference/cli.md#mqat-analysis-undershunt-protection)
- [`analysis-UNDERSHUNT-PROTECTION`](reference/cli.md#mqat-analysis-undershunt-protection)

## Data transmission

- [`mqat analysis data-transmission`](reference/cli.md#mqat-analysis-data-transmission)
- [`module-qc-tools analysis data-transmission`](reference/cli.md#mqat-analysis-data-transmission)
- [`analysis-DATA-TRANSMISSION`](reference/cli.md#mqat-analysis-data-transmission)

## Minimum health

- [`mqat analysis min-health-test`](reference/cli.md#mqat-analysis-min-health-test)
- [`module-qc-tools analysis min-health-test`](reference/cli.md#mqat-analysis-min-health-test)
- [`analysis-MIN-HEALTH-TEST`](reference/cli.md#mqat-analysis-min-health-test)

## Tuning performance

- [`mqat analysis tuning`](reference/cli.md#mqat-analysis-tuning)
- [`module-qc-tools analysis tuning`](reference/cli.md#mqat-analysis-tuning)
- [`analysis-TUNING`](reference/cli.md#mqat-analysis-tuning)

## Pixel failure

- [`mqat analysis pixel-failure-analysis`](reference/cli.md#mqat-analysis-pixel-failure-analysis)
- [`module-qc-tools analysis pixel-failure-analysis`](reference/cli.md#mqat-analysis-pixel-failure-analysis)
- [`analysis-PIXEL-FAILURE-ANALYSIS`](reference/cli.md#mqat-analysis-pixel-failure-analysis)

## Long-term stability DCS

- [`mqat analysis long-term-stability-dcs`](reference/cli.md#mqat-analysis-long-term-stability-dcs)
- [`module-qc-tools analysis long-term-stability-dcs`](reference/cli.md#mqat-analysis-long-term-stability-dcs)
- [`analysis-LONG-TERM-STABILITY-DCS`](reference/cli.md#mqat-analysis-long-term-stability-dcs)

## Visual Inspection (non-elec)

- [`mqat analysis visual-inspection`](reference/cli.md#mqat-analysis-visual-inspection)
- [`module-qc-tools analysis visual-inspection`](reference/cli.md#mqat-analysis-visual-inspection)
- [`analysis-VISUAL-INSPECTION`](reference/cli.md#mqat-analysis-visual-inspection)

## Mass Measurement (non-elec)

- [`mqat analysis mass-measurement`](reference/cli.md#mqat-analysis-mass-measurement)
- [`module-qc-tools analysis mass-measurement`](reference/cli.md#mqat-analysis-mass-measurement)
- [`analysis-MASS-MEASUREMENT`](reference/cli.md#mqat-analysis-mass-measurement)

## PCB Mass Measurement (non-elec)

- [`mqat analysis mass`](reference/cli.md#mqat-analysis-mass)
- [`module-qc-analysis-tools analysis mass`](reference/cli.md#mqat-analysis-mass)
- [`analysis-MASS`](reference/cli.md#mqat-analysis-mass)

## Quad Module Metrology (non-elec)

- [`mqat analysis quad-module-metrology`](reference/cli.md#mqat-analysis-quad-module-metrology)
- [`module-qc-tools analysis quad-module-metrology`](reference/cli.md#mqat-analysis-quad-module-metrology)
- [`analysis-QUAD-MODULE-METROLOGY`](reference/cli.md#mqat-analysis-quad-module-metrology)

## Quad Bare Module Metrology (non-elec)

- [`mqat analysis quad-bare-module-metrology`](reference/cli.md#mqat-analysis-quad-bare-module-metrology)
- [`module-qc-tools analysis quad-bare-module-metrology`](reference/cli.md#mqat-analysis-quad-bare-module-metrology)
- [`analysis-QUAD-BARE-MODULE-METROLOGY`](reference/cli.md#mqat-analysis-quad-bare-module-metrology)

## Wirebonding Pull Test (non-elec)

- [`mqat analysis wirebond-pull-test`](reference/cli.md#mqat-analysis-wirebond-pull-test)
- [`module-qc-tools analysis wirebond-pull-test`](reference/cli.md#mqat-analysis-wirebond-pull-test)
- [`analysis-WIREBOND-PULL-TEST`](reference/cli.md#mqat-analysis-wirebond-pull-test)

## Glue Module Flex Attach (non-elec)

- [`mqat analysis glue-module-flex-attach`](reference/cli.md#mqat-analysis-glue-module-flex-attach)
- [`module-qc-tools analysis glue-module-flex-attach`](reference/cli.md#mqat-analysis-glue-module-flex-attach)
- [`analysis-GLUE-MODULE-FLEX-ATTACH`](reference/cli.md#mqat-analysis-glue-module-flex-attach)

## Wirebonding (non-elec)

- [`mqat analysis wirebonding-information`](reference/cli.md#mqat-analysis-wirebonding-information)
- [`module-qc-tools analysis wirebonding-information`](reference/cli.md#mqat-analysis-wirebonding-information)
- [`analysis-WIREBONDING`](reference/cli.md#mqat-analysis-wirebonding-information)

## Parylene (non-elec)

- [`mqat analysis parylene`](reference/cli.md#mqat-analysis-parylene)
- [`module-qc-tools analysis parylene`](reference/cli.md#mqat-analysis-parylene)
- [`analysis-PARYLENE`](reference/cli.md#mqat-analysis-parylene)

## Thermal Cycling (non-elec)

- [`mqat analysis thermal-cycling`](reference/cli.md#mqat-analysis-thermal-cycling)
- [`module-qc-tools analysis thermal-cycling`](reference/cli.md#mqat-analysis-thermal-cycling)
- [`analysis-THERMAL-CYCLING`](reference/cli.md#mqat-analysis-thermal-cycling)

## Flatness (non-elec)

- [`mqat analysis flatness`](reference/cli.md#mqat-analysis-flatness)
- [`module-qc-tools analysis flatness`](reference/cli.md#mqat-analysis-flatness)
- [`analysis-FLATNESS`](reference/cli.md#mqat-analysis-flatness)

## Module PCB Tab Cutting Information (non-elec)

- [`mqat analysis cutter-pcb-tab`](reference/cli.md#mqat-analysis-cutter-pcb-tab)
- [`module-qc-tools analysis cutter-pcb-tab`](reference/cli.md#mqat-analysis-cutter-pcb-tab)
- [`analysis-CUTTER-PCB-TAB`](reference/cli.md#mqat-analysis-cutter-pcb-tab)

## HV LV Tests (non-elec)

- [`mqat analysis hv-lv-test`](reference/cli.md#mqat-analysis-hv-lv-test)
- [`module-qc-tools analysis hv-lv-test`](reference/cli.md#mqat-analysis-hv-lv-test)
- [`analysis-HV-LV-TEST`](reference/cli.md#mqat-analysis-hv-lv-test)

## NTC Verification (non-elec)

- [`mqat analysis ntc-verification`](reference/cli.md#mqat-analysis-ntc-verification)
- [`module-qc-tools analysis ntc-verification`](reference/cli.md#mqat-analysis-ntc-verification)
- [`analysis-NTC-VERIFICATION`](reference/cli.md#mqat-analysis-ntc-verification)

## SLDO Resistors (non-elec)

- [`mqat analysis sldo-restiors`](reference/cli.md#mqat-analysis-sldo-resistors)
- [`module-qc-tools analysis ntc-verification`](reference/cli.md#mqat-analysis-sldo-resistors)
- [`analysis-SLDO-RESISTORS`](reference/cli.md#mqat-analysis-sldo-resistors)

## VIA-RESISTANCE (non-elec)

- [`mqat analysis via-resistance`](reference/cli.md#mqat-analysis-via-resistance)
- [`module-qc-tools analysis via-resistance`](reference/cli.md#mqat-analysis-via-resistance)
- [`analysis-VIA-RESISTANCE`](reference/cli.md#mqat-analysis-via-resistance)
