# module-qc-data-tools history

---

All notable changes to module-qc-data-tools will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

**_Changed:_**

- Update `WIREBOND_PULL_TEST` schema to support array-type input for pull
  strength measurements (!65)

**_Added:_**

- schema for hardware configuration, including a new section for `localdb`
  configuration (!64)
- utilities for checking and loading the hardware configuration (!64)
- `THERMAL_PERFORMANCE`, `THERMAL_CYCLING`, `GLUE_MODULE_CELL_ATTACH`,
  `COLD_CYCLE` to schema (!66)
- added schemata for several Flex PCB QA tests (!65) including
  - `HV_LV_TEST`
  - `NTC_VERIFICATION`
  - `SLDO_RESISTORS`
  - `VIA_RESISTANCE`

**_Fixed:_**

- `get_layer_from_sn` returns `L2` for `outer_pixel_barrel` components (!66)

## [1.3.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.3.1) - 2025-07-23 ## {: #mqdt-v1.3.1 }

**_Added:_**

- `DE_MASKING` to schema (!62)

**_Fixed:_**

- catch when passing `None` to
  [module_qc_data_tools.utils.chip_uid_to_serial_number][] (!61)
- schema now checks that `MEASUREMENT_DATE` is a valid date (!62)

## [1.3.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.3.0) - 2025-06-16 ## {: #mqdt-v1.3.0 }

**_Added:_**

- added schema for various non--electrical QC measurements (!48, !59) including
  - `MASS_MEASUREMENT`
  - `GLUE_MODULE_FLEX_ATTACH`
  - `FLATNESS`
  - `TRIPLET_METROLOGY`
  - `WIREBONDING`
  - `WIREBONDING_PULL_TEST`
  - `PARYLENE`
  - `QUAD_MODULE_METROLOGY`

## [1.2.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.2.0) - 2025-06-02 ## {: #mqdt-v1.2.0 }

**_Changed:_**

- drop deprecated `importlib` dependency (!57)
- drop python 3.8 and update python version info (!56)
- huge restructuring to split up the files and make the package more
  maintainable (!44)
- dropped python 3.7 (`itksn` dropped it) (!44)
- updated [get_nominal_current][module_qc_data_tools.utils.get_nominal_current]
  to include the bom information, since V2+V1bom and V2+V2bom will have
  different nominal currents from here on out (!49 and !50)
- updated
  [get_chip_type_from_serial_number][module_qc_data_tools.utils.get_chip_type_from_serial_number]
  to handle additional serial number parsing from `itksn` (!53)

**_Added:_**

- these docs (!44)
- type-hints (!44)
- new CLI: [mqdt validate sn][mqdt-validate-sn], [mqdt validate
  measurement][mqdt-validate-measurement], [mqdt validate
  analysis][mqdt-validate-analysis] (!44)
- migrated more utilities from `module-qc-database-tools`
  - [module_qc_data_tools.utils.chip_serial_number_to_uid][]
  - [module_qc_data_tools.utils.chip_uid_to_serial_number][]
  - [module_qc_data_tools.utils.get_chip_type_from_serial_number][]
  - [module_qc_data_tools.utils.get_chip_type_from_config][]
  - [module_qc_data_tools.utils.get_config_type_from_connectivity_path][]

**_Fixed:_**

## [1.1.3](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.1.3) - 2025-04-02 ## {: #mqdt-v1.1.3 }

**_Added:_**

- `DCSdata` is now part of the output (!42)

## [1.1.2](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.1.2) - 2025-03-31 ## {: #mqdt-v1.1.2 }

**_Changed:_**

- display units of current in appropriate precision if nanoamperes or
  microamperes (!43)

**_Fixed:_**

- raise exceptions instead of `sys.exit` in various function calls
  (d8b1bc5eed3d78807ed6c34e39b124e55b24a83b)

## [1.1.1](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.1.1) - 2025-03-04 ## {: #mqdt-v1.1.1 }

**_Changed:_**

**_Added:_**

**_Fixed:_**

## [1.1.0](https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-data-tools/-/tags/v1.1.0) - 2025-03-04 ## {: #mqdt-v1.1.0 }

**_Fixed:_**

- switched to `pymongo` for the `bson` dependency
  (fe9fba41845f1b63fb3ec4a8a7423714ab34c963)
