"""Generate the IDS_mapping.csv that pairs with the diabetes dataset.

Real Kaggle file looks like:

   admission_type_id,description
   1,Emergency
   2,Urgent
   3,Elective
   4,Newborn
   ...
   discharge_disposition_id,description
   1,Discharged to home
   2,Transferred to another short term hospital
   ...
   admission_source_id,description
   1, Physician Referral
   2, Clinic Referral
   ...
"""

from __future__ import annotations

import csv
from pathlib import Path


def main() -> Path:
    out = Path(__file__).resolve().parent / "IDS_mapping.csv"

    rows: list[tuple[str, int, str]] = []
    rows.append(("admission_type_id", 1, "Emergency"))
    rows.append(("admission_type_id", 2, "Urgent"))
    rows.append(("admission_type_id", 3, "Elective"))
    rows.append(("admission_type_id", 4, "Newborn"))
    rows.append(("admission_type_id", 5, "Not Available"))
    rows.append(("admission_type_id", 6, "NULL"))
    rows.append(("admission_type_id", 7, "Trauma Center"))
    rows.append(("admission_type_id", 8, "Not Mapped"))

    for i in range(1, 30):
        rows.append(("discharge_disposition_id", i, f"Disposition-{i}"))

    for i in range(1, 26):
        rows.append(("admission_source_id", i, f"Source-{i}"))

    with open(out, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["column", "id", "description"])
        for col, id_, desc in rows:
            w.writerow([col, id_, desc])

    print(f"Wrote {out}")
    return out


if __name__ == "__main__":
    main()
