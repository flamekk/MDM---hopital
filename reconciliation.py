from pathlib import Path
import hashlib
import pandas as pd

def _read(path):
    try:
        return pd.read_csv(path)
    except (FileNotFoundError, pd.errors.EmptyDataError):
        return pd.DataFrame()

def _safe_int(value):
    try:
        return int(value) if pd.notna(value) else 0
    except (TypeError, ValueError):
        return 0

def build_reconciliation(data_dir, scenario):
    """Prépare une proposition de réconciliation sans modifier les fichiers de référence."""
    root = Path(data_dir)
    scen_dir = root / scenario
    membership = _read(scen_dir / "golden_record" / "cluster_membership.csv")
    golden = _read(scen_dir / "golden_record" / "golden_records.csv")
    queue = _read(root / "human_review_queue.csv")
    if membership.empty or golden.empty:
        raise ValueError(f"Golden Records ou membership absents/vides pour {scenario}.")
    required = {"scenario", "golden_record_id", "source_system", "source_patient_id"}
    if not required.issubset(membership.columns):
        raise ValueError(f"Colonnes absentes de cluster_membership.csv : {sorted(required-set(membership.columns))}")
    required_golden = {"golden_record_id"}
    if not required_golden.issubset(golden.columns):
        raise ValueError("Colonne golden_record_id absente de golden_records.csv.")
    membership = membership[membership["scenario"].astype(str).eq(scenario)].copy()
    if "scenario" in golden:
        golden = golden[golden["scenario"].astype(str).eq(scenario)].copy()
    if membership.empty or golden.empty:
        raise ValueError(f"Aucune donnée de référence pour {scenario}.")

    if not queue.empty and "scenario" in queue:
        queue = queue[queue["scenario"].astype(str).eq(scenario)].copy()
    # Never infer confirmation from a generic status alone: require explicit decision.
    confirmed = queue[
        queue.get("reviewer_decision", pd.Series(index=queue.index, dtype=str))
             .fillna("").astype(str).str.upper().eq("CONFIRM_MATCH")
    ].copy() if not queue.empty else pd.DataFrame()

    member_to_cluster = {}
    for _, row in membership.iterrows():
        key = (str(row["source_system"]), str(row["source_patient_id"]))
        member_to_cluster[key] = str(row["golden_record_id"])

    dob_lookup = {}
    std_dir = scen_dir / "standardized"
    for path in std_dir.glob("*.csv") if std_dir.exists() else []:
        df = _read(path)
        if not {"source_system", "source_patient_id"}.issubset(df.columns):
            continue
        dob_col = next((c for c in ["std__date_of_birth", "date_of_birth", "dob"] if c in df.columns), None)
        if dob_col:
            for _, row in df.iterrows():
                value = row[dob_col]
                dob_lookup[(str(row["source_system"]), str(row["source_patient_id"]))] = (
                    "" if pd.isna(value) else str(value).strip()
                )

    clusters = {}
    for _, row in membership.iterrows():
        clusters.setdefault(str(row["golden_record_id"]), []).append(
            (str(row["source_system"]), str(row["source_patient_id"]))
        )
    parent = {gid: gid for gid in clusters}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def members_for(gid):
        r = find(gid)
        return [member for old_gid, members in clusters.items() if find(old_gid) == r for member in members]

    accepted, rejected = [], []
    for _, row in confirmed.sort_values("case_id" if "case_id" in confirmed else confirmed.columns[0]).iterrows():
        case_id = row.get("case_id", "")
        a = (str(row.get("source_system_a", "")), str(row.get("source_patient_id_a", "")))
        b = (str(row.get("source_system_b", "")), str(row.get("source_patient_id_b", "")))
        if a not in member_to_cluster or b not in member_to_cluster:
            rejected.append({"case_id": case_id, "cluster_a": "", "cluster_b": "",
                             "result": "REJECTED", "reason": "IDENTITY_NOT_FOUND_IN_BASELINE"})
            continue
        ga, gb = find(member_to_cluster[a]), find(member_to_cluster[b])
        if ga == gb:
            accepted.append({"case_id": case_id, "cluster_a": ga, "cluster_b": gb,
                             "result": "ALREADY_CONNECTED", "reason": "NO_CHANGE"})
            continue
        combined = members_for(ga) + members_for(gb)
        systems = [s for s, _ in combined]
        if len(systems) != len(set(systems)):
            rejected.append({"case_id": case_id, "cluster_a": ga, "cluster_b": gb,
                             "result": "REJECTED", "reason": "SAME_SOURCE_SYSTEM"})
            continue
        dobs = {dob_lookup.get((s, pid), "") for s, pid in combined}
        dobs.discard("")
        if len(dobs) > 1:
            rejected.append({"case_id": case_id, "cluster_a": ga, "cluster_b": gb,
                             "result": "REJECTED", "reason": "CONFLICTING_DATE_OF_BIRTH"})
            continue
        root_a, root_b = sorted([ga, gb])
        parent[root_b] = root_a
        accepted.append({"case_id": case_id, "cluster_a": root_a, "cluster_b": root_b,
                         "result": "MERGED", "reason": "HUMAN_CONFIRMED_AND_SAFETY_CHECKS_PASSED"})

    grouped = {}
    for gid, members in clusters.items():
        grouped.setdefault(find(gid), []).extend(members)
    baseline_by_id = golden.set_index("golden_record_id", drop=False).to_dict("index")
    new_golden, new_membership, lineage = [], [], []
    for i, (root_id, members) in enumerate(sorted(grouped.items()), start=1):
        old_gids = sorted({member_to_cluster[m] for m in members})
        source_rows = [baseline_by_id[g] for g in old_gids if g in baseline_by_id]
        source_rows.sort(key=lambda r: (-_safe_int(r.get("source_count", 0)),
                                        -_safe_int(r.get("member_count", 0)),
                                        str(r.get("golden_record_id", ""))))
        winner = dict(source_rows[0]) if source_rows else {}
        new_id = f"{scenario}_REC_GR{i:06d}"
        winner.update({
            "scenario": scenario,
            "golden_record_id": new_id,
            "member_count": len(members),
            "source_count": len({s for s, _ in members}),
            "source_systems": " | ".join(sorted({s for s, _ in members})),
            "baseline_golden_record_ids": " | ".join(old_gids),
        })
        new_golden.append(winner)
        for s, pid in sorted(members):
            new_membership.append({
                "scenario": scenario, "golden_record_id": new_id,
                "source_system": s, "source_patient_id": pid,
                "baseline_golden_record_id": member_to_cluster[(s, pid)],
                "member_count": len(members), "source_count": len({x for x, _ in members})
            })
        for old_gid in old_gids:
            lineage.append({"scenario": scenario, "reconciled_golden_record_id": new_id,
                            "baseline_golden_record_id": old_gid,
                            "relationship": "SURVIVED" if len(old_gids) == 1 else "MERGED_INTO"})
    return {
        "golden_records": pd.DataFrame(new_golden),
        "cluster_membership": pd.DataFrame(new_membership),
        "lineage": pd.DataFrame(lineage),
        "accepted_decisions": pd.DataFrame(accepted),
        "rejected_decisions": pd.DataFrame(rejected),
        "confirmed_decisions_count": len(confirmed),
        "baseline_golden_count": len(golden),
        "reconciled_golden_count": len(new_golden),
        "data_dir": root, "scenario": scenario,
    }

def save_reconciliation(result):
    """Écrit une nouvelle version numérotée; ne remplace jamais une version existante."""
    root = Path(result["data_dir"])
    scenario = result["scenario"]
    scen_dir = root / scenario
    existing = []
    for path in scen_dir.glob("reconciliation_v*"):
        if path.is_dir():
            try:
                existing.append(int(path.name.removeprefix("reconciliation_v")))
            except ValueError:
                pass
    version = max(existing, default=0) + 1
    out = scen_dir / f"reconciliation_v{version}"
    out.mkdir(parents=True, exist_ok=False)
    result["golden_records"].to_csv(out / "golden_records.csv", index=False)
    result["cluster_membership"].to_csv(out / "cluster_membership.csv", index=False)
    result["lineage.csv"] = result.get("lineage", pd.DataFrame())
    result["lineage.csv"].to_csv(out / "golden_record_lineage.csv", index=False)
    result["accepted_decisions"].to_csv(out / "reconciliation_decisions.csv", index=False)
    result["rejected_decisions"].to_csv(out / "reconciliation_rejections.csv", index=False)
    summary = pd.DataFrame([{
        "scenario": scenario, "version": version,
        "baseline_golden_records": result["baseline_golden_count"],
        "reconciled_golden_records": result["reconciled_golden_count"],
        "confirmed_human_decisions": result["confirmed_decisions_count"],
        "accepted_merge_events": int((result["accepted_decisions"].get("result", pd.Series(dtype=str)) == "MERGED").sum()),
        "rejected_merge_events": len(result["rejected_decisions"]),
        "note": "Version append-only; Golden Records de référence inchangés."
    }])
    summary.to_csv(out / "reconciliation_summary.csv", index=False)
    return out
