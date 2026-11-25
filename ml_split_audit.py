"""Find exact file duplicates and shared group IDs across ML dataset splits."""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path


def load_manifest(path):
    root = path.resolve().parent
    seen = set()
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        columns = reader.fieldnames or []
        if set(columns) not in ({"path", "split"}, {"path", "split", "group_id"}) or len(set(columns)) != len(columns):
            raise ValueError("expected columns path and split, with optional group_id")
        for row in reader:
            line = reader.line_num
            if None in row or None in row.values():
                raise ValueError(f"line {line}: wrong number of fields")
            split = row["split"]
            if split not in ("train", "validation", "test"):
                raise ValueError(f"line {line}: split must be train, validation, or test")
            relative = Path(row["path"])
            if not row["path"].strip() or relative.is_absolute():
                raise ValueError(f"line {line}: expected a relative file path")
            resolved = (root / relative).resolve()
            if not resolved.is_relative_to(root):
                raise ValueError(f"line {line}: path escapes the manifest directory")
            if not resolved.is_file():
                raise ValueError(f"line {line}: expected an existing regular file")
            key = (resolved, split)
            if key in seen:
                raise ValueError(f"line {line}: repeated file in the same split")
            seen.add(key)
            yield line, split, resolved, row.get("group_id", "").strip()
    if not seen:
        raise ValueError("expected at least one file")


def find_overlaps(path):
    by_digest = defaultdict(list)
    by_group = defaultdict(list)
    digests = {}
    file_count = 0
    for line, split, item, group in load_manifest(path):
        if item not in digests:
            try:
                with item.open("rb") as stream:
                    digests[item] = hashlib.file_digest(stream, "sha256").hexdigest()
            except OSError as error:
                raise ValueError(f"line {line}: file could not be read") from error
        record = {"line": line, "split": split}
        by_digest[digests[item]].append(record)
        if group:
            by_group[group].append(record)
        file_count += 1

    findings = []
    for reason, index in (("identical_bytes", by_digest), ("group_overlap", by_group)):
        for records in index.values():
            if len({record["split"] for record in records}) > 1:
                findings.append({"reason": reason, "records": records})
    return {"records": file_count, "findings": findings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        report = find_overlaps(args.manifest)
    except OSError:
        parser.error("could not read manifest or resolve a local file")
    except UnicodeError:
        parser.error("manifest must use UTF-8")
    except (ValueError, csv.Error, RuntimeError) as error:
        parser.error(str(error))
    print(json.dumps(report, indent=2))
    return int(bool(report["findings"]))


if __name__ == "__main__":
    raise SystemExit(main())
