# module-qc-analysis-tools history

---

All notable changes to module-qc-analysis-tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

**_Changed:_**

- Consolidated IV analysis (!304)
  - Simplified breakdown analysis using only currents as limits, see
    AT2-IP-ES-0033
  - Fixed issues linked in !304 and added all as tests
  - Updated IV plots with various limits
- for IV measurement plot set the temperature range to be at least 1°C span and
  the humidity range to be at least 1% span (!325)

**_Added:_**

- added number of disabled core columns to SLDO output
- support for `PCB` version of the mass measurement test type as `MASS` instead
  of `MASS_MEASUREMENT` by (!311):
  - adding cli [mass][mqat-analysis-mass]
  - updating the `MASS_MEASUREMENT` to support test type `MASS` as well
- modified `HV_LV_TEST` to comply with the common schema (!330)
- added `NTC_VERIFICATION`, `SLDO_RESISTORS`, and `VIA_RESISTANCE` analyses in
  `GENERIC_NONELEC` (!330)

**_Fixed:_**

- fixed an indentation in `WIREBOND_PULL_TEST` (!330)

## [2.6.4](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.6.4) - 2025-07-16 ## {: #mqat-v2.6.4}

**_Fixed:_**

- fixed `WB_ENVELOPE` analysis cuts based on
  [spec document](https://edms.cern.ch/ui/file/2363543/10/AT2-0000020501-L2-L4_Assembled_module_-Outer_Barrel-v13.pdf)
  and relax connectivity cuts

## [2.6.3](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.6.3) - 2025-07-09 ## {: #mqat-v2.6.3}

**_Fixed:_**

- fixed field names for `TUNING` analysis in case of missing data (!321))

## [2.6.2](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.6.2) - 2025-07-02 ## {: #mqat-v2.6.2}

**_Fixed:_**

- fixed `PULL_STRENGTH` and `PULL_STRENGTH_MIN` in `WIREBOND_PULL_TEST` analysis
  cuts (!316)
- fixed `BOND_PEEL` calculation for `WIREBONDING_PULL_TEST` (!315)

## [2.6.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.6.1) - 2025-06-18 ## {: #mqat-v2.6.1}

**_Fixed:_**

- improved support for nonelec analyses relying on `GENERIC_NONELEC` (!306)
- fixed `WP_ENVELOPE` type-casting for `VISIBILITY` parameter (!307)
- fixed `MASS_MEASUREMENT` type-casting for `MASS` parameter (!308)
- fixed `WIREBOND_PULL_TEST` to support `module-qc-nonelec-gui` inputs (!309)
- removed unused parameters from `WIREBOND_PULL_TEST` because PDB definition is
  not backwards-compatible (!310)

## [2.6.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.6.0) - 2025-06-16 ## {: #mqat-v2.6.0}

**_Changed:_**

- non-electrical tets were modified to comply with the common schema (!225)
  - flatness uses units of `μm` instead of `um` to match PDB definition
  - mass measurement, triplet metrology, and wirebond pull test are updated with
    appropriate QC criteria
  - `TRIPLET_METROLOGY`
    - `THICKNESS_HV_CAP` is `[0.0, 2.285]`
    - `THICKNESS_SMD` is `[0.0, 0.685]`
    - `THICKNESS_CONNECTOR` is `[0.0, 1.615]`
    - `FLEXFM_TO_RIGHTSENSOREDGE` is `[0.0, 0.025]`
    - `FLEXFM_TO_LEFTSENSOREDGE` is [`0.0, 0.025]`
    - `MAX_MODULE_LENGTH` is `[61.21, 61.34]`
    - `SENSOR_GAP` is `[0.05, 999.0]`
  - `MASS_MEASUREMENT` has different crtieria based on the stage:
    - `ASSEMBLY` is `[2800, 3500]`
    - `WIREBOND_PROTECTION` is `[3400, 4100]`
  - `WIREBOND_PULL_TEST`
    - `PULL_STRENGTH` is `[0.0, 7.0]`
    - `PULL_STRENGTH_MIN` is `[0.0, 4.0]`
    - `LIFT_OFFS_LESS_THAN_7G` is `[0, 9]`

**_Added:_**

- Zenodo files (!301)

## [2.5.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.5.0) - 2025-06-02 ## {: #mqat-v2.5.0}

**_Changed:_**

- drop python 3.8 and update python version info (!298)
- change name to AR parameters to be all capital. Remove AR_NOMINAL_SETTINGS
  analysis (!286)
- added criterion for [mqat analysis
  wirebond-pull-test][mqat-analysis-wirebond-pull-test] (!283)
- updated SLDO cuts to match new nominal input current for V2+V2BOM chips
  according to YTF recommendations (!293)

  !!! important

        Requires module-qc-data-tools v1.1.4rc6

**_Added:_**

**_Fixed:_**

- Fixed summary statistics calculations for the wirebonding pull test for wires
  that were pulled (!277)
- Removed extra data files from packaged python wheel (!299)
- drop deprecated `importlib` dependency (!300)

## [2.4.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.4.1) - 2025-03-28 ## {: #mqat-v2.4.1}

**_Changed:_**

- ANAGND cut for V2 modules + V2 BOM (!280)
- cuts for untuned and tuned threshold sigma (!279)

**_Added:_**

**_Fixed:_**

- SLDO crashing in case Ishunt is all 0 (!281)
- VDDD versus trim when running locally (!278)
- fix uv version (!274)
- range for SLDO fit (!271)
- data transmission does not pass QC properly (!272)
- metrology (!247)

## [2.4.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.4.0) - 2025-03-11 ## {: #mqat-v2.4.0}

**_Changed:_**

- removed QC cut on Untuned threshold from V2+V1 and V2+V2 analysis cuts
  files(!255)
- relax threshold to identify pixels as tuned bad and increased the maximum
  number of bad pixels that can fail in PFA, MHT and TUN (!252 !269)
- store IRef value measured internally by the chip in prodDB (!261)
- remove cuts on the untuned threshold mean (!216)
- linear fit extrapolates Iin for which IshuntA/D QC criteria are passed, linear
  fit is plotted in the end, x-axis range is now common among the three plots,
  output files has fit parameters, intersections and chi^2 (!245)
- Refactoring of analyses (MRs....)
- update PCB and bare modules tests (!219)
- update quad metrology average thickness to contain the average and not the
  full list of measurements (!224)
- remove IRef cut from SLDO, since it's already implemented in AR (!226)
- update the cut files structure, removing duplication between common cuts for
  all BOM and chip versions (!228 )

**_Added:_**

- VDD trim saturation in ANALOG READBACK (!214)
- Data merging analysis (!244)
- Minimum currents for SLDO to pass (!245)
- Measurement duration for electrical tests (!213)
- exclude the first 10mins of data from calculation of I_leakage std deviation
  (!215)
- cut on the tuned TDAC mean (to fail modules with wrong tuning routine) (!217)
- update (!262)

**_Fixed:_**

- Breakdown voltage for 3D (!248 !251)
- flatness analysis (!212)
- way PCB metrology is handled at different stages (!222)
- fix bugs in the AR trim cut (!220 !242)
- lowered V2 IshuntD QC cut after finding a bug in the SLDO calculator (!252)
- changed Iin and Ishunt QC cuts following the fact in IinSense factor is
  different in wafer probing and operation (!257)
- update voltage cuts for V2 modules due to wrong iref unc used in the SLDO
  calculator (!263)

## [2.3.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.3.0) - 2024-12-19 ## {: #mqat-v2.3.0}

**_Changed:_**

- refactoring of module metrology (!208)
- ITkPix v2 cuts for v1 BoM (!210)
- SLDO nominal currents (!211)

**_Added:_**

- cutter-pcb-tab (!203)
- ITkPix v2 cuts for v2 BoM (!207)

**_Fixed:_**

- timestamp in IV (!205)

## [2.2.9](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.2.9) - 2024-11-19 ## {: #mqat-v2.2.9 }

**_Changed:_**

- refactored `IV_MEASURE` analysis and outsourced functions (!189)
- kshunt factors (!192)
- SLDO, LP, and ANAGND analysis cuts V1.1 (!199)
- stage-dependent mass criteria (!200)

**_Added:_**

- measurement date
- SLDO, LP, and ANAGND analysis cuts V2 chip + V1.1 BOM (!194, !201)
- de-masking and wp-envelope analyses (!200)

**_Fixed:_**

- support other format for `TimeStart` for sensor IV (!200, #134)
- PFA analysis fails due to `COLUMN_DISABLED` being -1 (!202)
- PFA analysis fails due to missing optional zero-bias and source scan -1 (!204)

## [2.2.8](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.2.8) - 2024-10-15 ## {: #mqat-v2.2.8 }

**_Changed:_**

- missing data points in SLDO plots (!176)

**_Added:_**

- plotting of Ishunt, Vin and Iin (!183)
- YARR version as property (!184, !186)
- core column handling (!175)

**_Fixed:_**

- negative GND values for triplets (!176)
- calculation of injection capacitance (!181)

## [2.2.7](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.2.7) - 2024-08-28 ## {: #mqat-v2.2.7 }

**_Changed:_**

- changed QC criteria following up from PRR (!177)

**_Added:_**

- quad bare module metrology (!179)

**_Fixed:_**

- bug in creating per-chip json outputs for ADC calibration
  (b006412b06fb54d09ce075336b0b49e6b9a0292a)

## [2.2.6](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.2.6) - 2024-07-12 ## {: #mqat-v2.2.6 }

**_Changed:_**

- SLDO criteria cuts (!169)
- refactored `adc-calibration` to get ready for v3 (!157)

**_Added:_**

- flatness analysis (!160, !162)
- long-term stability dcs analysis (!167)
- This documentation. (!171)

**_Fixed:_**

- Removed `OBSERVATION` field for visual inspection for bare components (!158)
- Bug with TOT mean/rms for minimum health test (!159)
- Bare IV temperatures (!164)

## [2.2.5](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-analysis-tools/-/tags/v2.2.5) - 2024-07-12 ## {: #mqat-v2.2.5 }

Note: this version is skipped due to a packaging issue with `module-qc-tools`.
