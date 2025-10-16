# LabCAS Utilities

This is a hodge-podge collection of various utilities for managing, reporting on, and maintaining instances of the [Laboratory Catalog and Archive System](https://github.com/jpl-labcas) (LabCAS).


## 📀 Installation

Using Python 3.9 or newer, create a virtual environment and install it:

    python3 -m venv venv
    venv/bin/pip install jpl.labacs.utils


## 🔧 The Utilities

The numerous utilities are quickly summarized below:

- `assign-uuids` — finds Solr documents without a UUID and assign one
- `backup-labcas` — issues backup commands for the Solr cores for LabCAS, "collections", "datasets", and "files"
- `common-prefixes` — allegedly finds common prefixes in FileLocation fields in Solr (but doesn't?)
- `date-report` — writes a CSV to stdout of protocols with dates and dates of corresponding collections in LabCAS
- `dcm-header-usage` — shows usage of DICOM headers in Lung_Team_Project_2 and Prostate_MRI collections based on a Google spreadsheet for input
- `delete-collection` — deletes a collection (including all of its datasets and files) from LabCAS Solr
- `delete-datasets` — deletes datasets from LabCAS Solr while producing a CSV of the corresponding files that will need to be deleted from disk
- `delete-field` — deletes a field from documents in Solr
- `field-usage` — tells what fields are in use by collections, datasets, and files in Solr and marks those that appear in collection and dataset `.cfg` files
- `fix-event-ids` — repairs event IDs in Solr after publication of a dataset (or collection) that uses event IDs based on a [LabCAS publish](https://github.com/jpl-labcas/publish) `alias.json` file
- `fix-patient-ids` — overwrites `PatiendID` field in DICOM files with event IDs from Solr
- `fix-principals` — sets the `OwnerPrincipal` fields of the "collections", "datasets", and "files" cores in Solr based on information in [metadata `.cfg` files](https://github.com/EDRN/EDRN-metadata)
- `mangle-headers` — mangles DICOM headers according to Radka's specifications
- `mass-spec-fix` — fixed misspelled "mass spectrometry" in Solr cores
- `missing-bbd-dcis` — finds missing anonymized BBD and DCIS not specified in a given `.csv` file
- `missing-event-ids` — given event IDs, report which are missing in LabCAS Solr
- `populate-bbd-dcis` — populate the BBD or DCIS files in Solr with filenames in a BBD or DCIS `.csv` file
- `replace-field` — replace a list field in Solr with a new single value
- `replace-fields` — replace a list field in Solr with multiple values
- `report` — generate various reports, including events, privacy, event correlation, availability, or patient IDs
- `report-fields` — generate a report on requested fields
- `report-file-size` — report total size of all files in LabCAS using Solr metadata
- `restructure-bbd-dcis` — make symlinks into the `Validation` and `Discovery` folders for BBD and DCIS data on disk
- `s3-report` — generate a report about files, sub-folders, and average number of files in sub-folders in S3
- `split-brsi` — split the contents of a gzip'd tar file into training and validation folders based on a spreadsheet input
- `sub-field` — substitute the value of a field in multiple documents

Many of these utilities are one-offs, which is typical for LabCAS.


## 🔁 Looping

Some of these utilities loop over large collections of data, paginating through results and making updates. You may have to run the utilities multiple times until they report updating no more documents.


## 🛤️ Solr and Tunneling

Many of these utilities operate on Solr that's assumed to be at `https://localhost:8984/solr/` with a self-signed certificate. You can override these with a `--solr` option.

Feel free to tunnel these connection over `ssh` to a preferential Solr, or run it directly on a host like `edrn-labcas`, `mcl-labcas`, `labcas-dev`, and so forth.


## 🖥️ Development

To install from source:

    git clone https://github.com/jpl-labcas/jpl.labcas.utils.git
    cd jpl.labcas.utils
    pre-commit install
    python3 -m venv .venv
    source .venv/bin/activate  # or activate.csh if you're a csh/tcsh user
    pip install --editable .

To release to PyPI:

    python3 -m build .
    twine upload dist/*


## 👩‍🎨 Creators

The principal developer is:

- [Sean Kelly](https://github.com/nutjob4life)

To contact the team as a whole, [email the Informatics Center](mailto:ic-portal@jpl.nasa.gov).

## 📃 License

The project is licensed under the [Apache version 2](LICENSE.md) license.
