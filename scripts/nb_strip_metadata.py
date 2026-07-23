"""Git clean filter: strip notebook/cell metadata, keep source and outputs.

Registered as the `strip-notebook-metadata` filter
(see notebooks/.gitattributes and README.md) so committed notebooks
don't carry kernelspec, language_info, execution counts, or per-cell metadata
that differ machine to machine and otherwise churn every diff.
"""

from __future__ import annotations

import json
import sys


def clean(nb: dict) -> dict:
    nb["metadata"] = {}
    for cell in nb.get("cells", []):
        cell["metadata"] = {}
        if cell.get("cell_type") == "code":
            cell["execution_count"] = None
            for out in cell.get("outputs", []):
                out.pop("execution_count", None)
    return nb


def main() -> int:
    nb = json.load(sys.stdin)
    json.dump(clean(nb), sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
