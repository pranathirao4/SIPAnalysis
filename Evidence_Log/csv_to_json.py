"""Rebuild golden_set.json from the reviewed cases CSV.
Usage: python csv_to_json.py golden_set_cases.csv golden_set.json golden_set_new.json
Scenarios, targets and the judge rubric are taken from the existing JSON (they are code-facing).
Rows where keep_or_edit is 'drop' are skipped."""
import csv, json, sys
cases_csv, old_json, new_json = sys.argv[1:4]
base = json.load(open(old_json, encoding="utf-8"))
split = lambda s: [x for x in s.split("|") if x] if s else []
cases = []
with open(cases_csv, newline="", encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        if r["keep_or_edit"].strip().lower() == "drop":
            continue
        c = {"id": r["id"], "group": r["group"], "scenario": r["scenario"], "q": r["question"], "route": r["expected_route"]}
        if split(r["must_cite"]) or r["group"] in ("explanation","in_scope"): c["cite"] = split(r["must_cite"])
        if split(r["must_include"]): c["require"] = split(r["must_include"])
        if split(r["must_not_include"]): c["must_not"] = split(r["must_not_include"])
        if r["judged_by_ai"].strip().lower() == "yes": c["judge"] = True
        if r["notes"]: c["note"] = r["notes"]
        c["evidence_log_ref"] = r["evidence_log_ref"]
        cases.append(c)
base["cases"] = cases
json.dump(base, open(new_json, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(len(cases), "cases written to", new_json)
