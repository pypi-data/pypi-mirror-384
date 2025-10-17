# module-qc-database-tools history

---

All notable changes to module-qc-tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

**_Changed:_**

**_Added:_**

- `mqdbt pull-component --sns` command to pull multiple components via
  commandline (!139)
- `mqdbt assign-tag --sn <serial number> --tag tag1 --tag tag2` command to
  assign tags to components via commandline (!136)
- Support loading localDB/mongoDB information and default tags from hardware
  config (!132)

**_Fixed:_**

## [2.8.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.8.0) - 2025-09-30 ## {: #mqdbt-v2.8.0 }

**_Changed:_**

- The IREF trim saved in the chip config uses the value stored in the chip
  property `TARGET_IREF_TRIM` if available, otherwise uses wafer probing data
  (!131)

## [2.7.2](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.7.2) - 2025-07-01 ## {: #mqdbt-v2.7.2 }

**_Changed:_**

- Removed obsoleted keys from the FE Wafer Probing data check (!120)
- updated error message to mention which measurement path provided does not have
  any valid input files (!119)
- Use `module_qc_data_tools.utils.validate_measurement` to validate measurements
  before uploading (!128) and comes with much nicer and more helpful error
  messages

## [2.7.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.7.1) - 2025-07-01 ## {: #mqdbt-v2.7.1 }

**_Fixed:_**

- Generating data merging config: correct `rx`, ensure `EnChipId` is set to `1`
  and `SerEnLane` is `15` (!122)

## [2.7.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.7.0) - 2025-06-16 ## {: #mqdbt-v2.7.0 }

**_Changed:_**

- add developer info (!118)
- use warm config to run LP mode test in `run-full-qc` (!117)

  !!! important

        Requires mqt version >= 2.6.0

**_Added:_**

- Zenodo files (!111)

## [2.6.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.6.0) - 2025-06-02 ## {: #mqdbt-v2.6.0 }

**_Changed:_**

- drop deprecated `importlib` dependency (!110)
- drop python 3.8 and update python version info (!105)
- increased `itksn` version to `0.4.2` and `mqdt` version to `1.1.4rc8` (!101)
- migrate from `mqdbt.get_layer_from_serial_number` to `mqdt.get_layer_from_sn`.
  Importantly, `"R0", "R0.5"` are treated as `"L0"` (!94)
- move common utilities from this package to `module-qc-data-tools` (!94)
- [mqdbt component review][mqdbt-component-review] is renamed from [mqdbt
  review-component][mqdbt-review-component]
- require backside measurement for `PARYLENE_MASKING` when reviewing components
  (!108)
- minimum localDB version increased to `2.4.0` (!114)

**_Added:_**

- generate data merging config by adding e.g. `--dm 4-to-1` (!82)
- default `InjCap` value in chip template in case it's not measured during wafer
  probing (!97)
- [mqdbt component download][mqdbt-component-download] to download component
  test runs to disk
- schema check in [mqdbt upload-measurement][mqdbt-upload-measurement] before
  uploading (!107)
- check for missing front-end chip data from wafer probing:
  [check_missing_fechip_test_data][module_qc_database_tools.review.checks.check_missing_fechip_test_data]
  (!109)

**_Fixed:_**

- deal with missing k-factor from wafer probing (k-factor is -1 if missing from
  wafer probing) (!100 🎉)
- python version comparison in `upload_measurement` (!91)
- fix relative imports in `localdbtool-retrieve` (!103)
- support `username` and `password` again for backwards-compatibility with
  `localdbtools-xyz` interfaces (!104)

## [2.5.6](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.6) - 2025-04-02 ## {: #mqdbt-v2.5.6 }

**_Changed:_**

- harmonized CLI options with `-sn` becoming `--sn`
- drop `-t` for test run in favor of `tags`

## [2.5.5](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.5) - 2025-04-02 ## {: #mqdbt-v2.5.5 }

**_Changed:_**

- format in module info changed for both quads and triplets to accommodate
  triplets; no `"V_FULLDEPL"` block in case of digital or dummy modules (!87)

  ```json
  {
    "PCB_BOM_VERSION": {
      "code": "09",
      "value": "Unknown"
    },
    "V_FULLDEPL": {
      "20UPIS18100366": 5,
      "20UPIS18100359": 5,
      "20UPIS18100364": 5
    }
  }
  ```

- Refer to `FE1/2/3/4` in terminal output according to recommendations by the
  Yield Taskforce (!89)

**_Fixed:_**

- when setting component stage in PDB, use `rework` flag in case one needs to
  revert to older stage (!86)

## [2.5.4](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.4) - 2025-04-01 ## {: #mqdbt-v2.5.4 }

**_Changed:_**

- `LocalModule` exits more quickly when it cannot find component given the
  serial number (!88)
- `ssl` command-line option dropped everywhere, use the `ssl=true` URL parameter
  instead when specifying your `MongoDB` URI. (!88)

**_Added:_**

**_Fixed:_**

- Use `database` and not `client` when instantiating the `LocalModule` class
  (!88)

## [2.5.3](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.3) - 2025-03-28 ## {: #mqdbt-v2.5.3 }

**_Changed:_**

- minimum localDB version compatibility is set to `v2.3.0`

## [2.5.2](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.2) - 2025-03-28 ## {: #mqdbt-v2.5.2 }

**_Added:_**

- `upload-measurement` now supports tags (!67)
- `run-full-qc` to `mqdbt` CLI (!81)

**_Fixed:_**

- authentication check for upload of yarr scans (!83)

## [2.5.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.1) - 2025-03-25 ## {: #mqdbt-v2.5.1 }

**_Changed:_**

- bulk recycle now functions correctly and prints out reasons for failures (!75)
- minimum required localDB for recycling functionality is `v2.2.41` (!75)
- bulk recycle renamed to `recycle-esummary` and requires a `stage` (!78)

**_Added:_**

- CLI to recycle a single analysis (!75)
- utility to check minimum required localDB version (!75)
- bulk recycle and recycle single analysis will check minimum required localDB
  version (!75)

**_Fixed:_**

- recycling did not work properly due to interactions with localDB not providing
  JSON data (!75 !74)
- recycling of complex analyses is fixed (!77)
- uv version (!72)

## [2.5.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.5.0) - 2025-03-11 ## {: #mqdbt-v2.5.0 }

**_Changed:_**

**_Added:_**

- Add a check InjCap is actually measured during wafer probing, otherwise leave
  empty (!64)
- Add a cli tool to bulk recycle the analysis (!59,!61)
- Add automated python script to run full QC (!65)
- Add functionality to support BOM retrieval and usage (!70, !71)
- Add snippet as python script (!65)

**_Fixed:_**

- IShuntSensek-factor calculated based on the expected value of 21600 (and
  not 26000) (!69,!66 )

## [2.4.9](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.9) - 2024-12-19 ## {: #mqdbt-v2.4.9 }

**_Fixed:_** Wrong function name in localDB interface (!58)

## [2.4.8](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.8) - 2024-12-09 ## {: #mqdbt-v2.4.8 }

**_Changed:_**

- Update `itkdb` version to 0.6.12 and `itksn` version to 0.3.0
- Update `subproject_code` to `component_code` according to the changes in
  `itksn`

## [2.4.7](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.7) - 2024-11-21 ## {: #mqdbt-v2.4.7 }

**_Fixed:_**

- misleading error message for `KeyError` raised when trying to access with an
  incorrect chip type

## [2.4.6](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.6) - 2024-11-21 ## {: #mqdbt-v2.4.6 }

**_Fixed:_**

- bug in checking for authentication with mongo for uploading yarr scans

## [2.4.5](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.5) - 2024-11-21 ## {: #mqdbt-v2.4.5 }

**_Fixed:_**

- bug in changing `Protocol` for uploading measurements (#36)

## [2.4.4](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.4) - 2024-10-03 ## {: #mqdbt-v2.4.4 }

**_Changed:_**

- migrate from `currentStage` to `stage` for LDB interactions
  (1a60273d284a1cb8f3c878a4cdb1d416821b36fe,
  3a18800a5e9859c83ea6a24ee9d3256a1e79d8db,
  cc26823091aa51ce74fe2dfad886f0b9e508961f,
  343d26d1cdb693cf785eab0c3483913452265295)

**_Added:_**

- add three command-line interfaces migrated from `YARR`: `localdbtool-upload`,
  `localdbtool-retrieve`, `influxdbtool-retrieve` (!56)

**_Fixed:_**

- make `mqdbt upload-measurement` more robust to errors from LDB that are not
  JSON-formatted (b09b759f5ce49662b01f471369714cc4e84910fb,
  ba120930633f29ebc8a386266aa76d3dc4166fab)
- sort entries using the `tuple` form instead of the `dict` form
  (bb87551d5e2a3acf59102c2b98fde4cf8d495424)

## [2.4.3](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.3) - 2024-10-15 ## {: #mqdbt-v2.4.3 }

**_Changed:_**

- add support for fetching reference IVs of triplet modules (!55)

## [2.4.2](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.2) - 2024-10-03 ## {: #mqdbt-v2.4.2 }

**_Fixed:_**

- add some protection for attachment titles that may be missing or not set
  (4cabe51038e58fd7a48863b9c827bbb4c83853cf)

## [2.4.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.1) - 2024-10-03 ## {: #mqdbt-v2.4.1 }

**_Changed:_**

- improve support of triplet modules by making sure we identify it correctly
  from `itksn` (06542155f8fc136ee5341391a8654731f6ae1304)

## [2.4.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.4.0) - 2024-07-13 ## {: #mqdbt-v2.4.0 }

**_Changed:_**

- refactored some common code across the command-line interfaces

**_Added:_**

- ability to sync component stages recursively (!51)

## [2.3.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-database-tools/-/tags/v2.3.0) - 2024-07-13 ## {: #mqdbt-v2.3.0 }

First release for this documentation. (!47)

**_Changed:_**

- connectivity generation supports a `--dp`/`--port` option for specifying the
  DP Port (!42)

**_Added:_**

- command-line interface for fetching reference IVs (!46)
- support for ITkPix v2 (!39, !43)
- `ssl` option for mongo-client connections from command line (!37)

**_Fixed:_**

- bug in obtaining chip type from config when saving to localDB (!45)

```

```
