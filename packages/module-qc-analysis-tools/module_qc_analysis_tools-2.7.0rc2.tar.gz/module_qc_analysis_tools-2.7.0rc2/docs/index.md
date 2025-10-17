# module-qc-analysis-tools (mqat)

<!--![mqat logo](assets/images/logo.svg){ align="left" width="300" role="img" }

--8<-- "README.md:badges"

---

A general python tool for running ITkPixV1.1 and ITkPixV2 module QC tests for the ATLAS
ITk project documented at [itk.docs][]. This is one package as part of the Module QC ecosystem to:

- automate measurements: [module-qc-tools](https://pypi.org/project/module-qc-tools)
- automate analysis and grading: [module-qc-analysis-tools](https://pypi.org/project/module-qc-analysis-tools)
- automate chip config generation: [module-qc-database-tools](https://pypi.org/project/module-qc-database-tools)
- automate data organization locally: [localDB](https://atlas-itk-pixel-localdb.web.cern.ch/)
- automate interfacing with production DB: [itkdb](https://pypi.org/project/itkdb)

This project contains the code used to analyze the data from electrical testing
of a module and determine if the module passes or fails the QC requirements. It
also format the output of the analysis such that it can be easily uploaded to
the ITkPD.

## Features

<!-- prettier-ignore-start -->

- automatically perform non-YARR measurements
- measurements are performed at chip level
- result summarized per-module, but can be summarized per-chip

<!-- prettier-ignore-end -->

## License

module-qc-analysis-tools is distributed under the terms of the
[MIT][license-link] license.

## Navigation

Documentation for specific `MAJOR.MINOR` versions can be chosen by using the
dropdown on the top of every page. The `dev` version reflects changes that have
not yet been released.

Also, desktop readers can use special keyboard shortcuts:

| Keys                                                         | Action                          |
| ------------------------------------------------------------ | ------------------------------- |
| <ul><li><kbd>,</kbd> (comma)</li><li><kbd>p</kbd></li></ul>  | Navigate to the "previous" page |
| <ul><li><kbd>.</kbd> (period)</li><li><kbd>n</kbd></li></ul> | Navigate to the "next" page     |
| <ul><li><kbd>/</kbd></li><li><kbd>s</kbd></li></ul>          | Display the search modal        |
