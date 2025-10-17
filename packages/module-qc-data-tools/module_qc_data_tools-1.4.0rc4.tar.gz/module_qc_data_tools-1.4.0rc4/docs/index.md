# module-qc-data-tools (mqdt)

<!--![mqt logo](assets/images/logo.svg){ align="left" width="300" role="img" }

--8<-- "README.md:badges"

---

This project contains the modules needed to write/read the data files used in
the module QC flow documented at [itk.docs][]. This project is to be added as a dependency in other
projects.

- automate measurements: [module-qc-tools](https://pypi.org/project/module-qc-tools)
- perform analysis, grading: [module-qc-analysis-tools](https://pypi.org/project/module-qc-analysis-tools)
- handle database interactions: [module-qc-database-tools](https://pypi.org/project/module-qc-database-tools)
- organization of local data: [localDB](https://atlas-itk-pixel-localdb.web.cern.ch/)
- interfactions with production DB: [itkdb](https://pypi.org/project/itkdb)

## Features

<!-- prettier-ignore-start -->

- automatically perform non-YARR measurements
- measurements are performed at chip level
- result summarized per-module, but can be summarized per-chip

<!-- prettier-ignore-end -->

## License

module-qc-data-tools is distributed under the terms of the [MIT][license-link]
license.

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
