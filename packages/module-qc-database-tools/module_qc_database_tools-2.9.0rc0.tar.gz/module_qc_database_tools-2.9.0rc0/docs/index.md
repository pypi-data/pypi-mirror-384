# module-qc-database-tools (mqdbt)

<!--![mqt logo](assets/images/logo.svg){ align="left" width="300" role="img" }

--8<-- "README.md:badges"

---

A general python tool to interface with LocalDB and Production DB for common tasks for pixel module QC tests for the ATLAS ITk project documented at [itk.docs][]. This is one package as part of the Module QC ecosystem to:

- automate measurements: [module-qc-tools](https://pypi.org/project/module-qc-tools)
- automate analysis and grading: [module-qc-analysis-tools](https://pypi.org/project/module-qc-analysis-tools)
- automate data organization locally: [localDB](https://atlas-itk-pixel-localdb.web.cern.ch/)
- automate interfacing with production DB: [itkdb](https://pypi.org/project/itkdb)

## Features

<!-- prettier-ignore-start -->

- generates connectivity files and chip configs
- fetches reference IV measurements for `module-qc-analysis-tools`

<!-- prettier-ignore-end -->

## License

module-qc-database-tools is distributed under the terms of the
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
