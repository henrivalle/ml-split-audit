# ML Split Audit

[Português](README.pt-BR.md) · [Contributing](CONTRIBUTING.md)

Check dataset partitions before computing model quality. This offline CLI detects identical file contents and shared group IDs spanning training, validation, and test. It can audit any collection of local files without parsing their formats.

## Run the example

Run the sample from the repository root with Python 3.11 or newer.

```sh
python3 -m ml_split_audit examples/dataset.csv
```

The synthetic example has one byte-for-byte duplicate under different names and one group shared across splits. It exits `1` and reports their manifest lines. An exit of `0` means the supplied manifest has no findings for these checks. Exit `2` indicates invalid input. `python -m pip install .` also installs `ml-split-audit`.

Use a UTF-8 CSV with `path,split` and an optional `group_id` column. Paths must reference regular files within the manifest directory. Split names are `train`, `validation`, and `test`. A group might identify an original document, recording session, or capture batch. Choose groups that should stay together when you partition the data. The tool hashes file bytes with SHA-256 and reports only line numbers, splits, and finding categories. Similar but byte-different files require a separate analysis. [scikit-learn grouped splits](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html)
