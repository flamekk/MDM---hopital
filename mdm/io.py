import csv
import hashlib
import json
from pathlib import Path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def read_csv(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in r.items()} for r in rows)


def csv_download(rows):
    """Export Excel : neutralise les cellules interprétables comme formules."""
    import io
    buf = io.StringIO(newline="")
    fields = list(dict.fromkeys(k for r in rows for k in r))
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        cleaned = {}
        for k, value in row.items():
            value = json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else str(value if value is not None else "")
            cleaned[k] = "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value
        writer.writerow(cleaned)
    return buf.getvalue().encode("utf-8-sig")
