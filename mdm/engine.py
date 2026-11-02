"""Ingestion, normalisation, blocking, scoring, clustering et survivorship.

Ce module ne lit aucune étiquette d'évaluation. Les attributs cliniques sont exclus.
"""
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from itertools import combinations
import math
from pathlib import Path
import re
import unicodedata
import uuid
from rapidfuzz.distance import JaroWinkler
from .config import DOMAINS, FS, METHODS, RULE_VERSION, THRESHOLDS
from .io import digest, read_csv


def text(value):
    value = unicodedata.normalize("NFKD", str(value or ""))
    return re.sub(r"\s+", " ", "".join(c for c in value if not unicodedata.combining(c)).lower()).strip()


def normalise(field, value):
    raw = str(value or "").strip()
    if not raw:
        return "", None
    if field == "birth_date":
        parsed = None
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                parsed = datetime.strptime(raw, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None or parsed > date.today() or parsed.year < 1850:
            return "", "INVALID_DATE"
        return parsed.isoformat(), None
    if field == "phone":
        digits = re.sub(r"\D", "", raw)
        if digits.startswith("00212"):
            digits = "0" + digits[5:]
        elif digits.startswith("212") and len(digits) == 12:
            digits = "0" + digits[3:]
        return (digits, None) if re.fullmatch(r"0[5-7]\d{8}", digits) else ("", "INVALID_PHONE")
    if field == "email":
        clean = raw.lower()
        return (clean, None) if re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", clean) else ("", "INVALID_EMAIL")
    if field == "package_quantity":
        try:
            number = Decimal(raw.replace(",", "."))
            if number.is_finite() and number > 0:
                return format(number.normalize(), "f"), None
        except InvalidOperation:
            pass
        return "", "INVALID_QUANTITY"
    clean = text(raw)
    if field == "package_unit":
        clean = {"unites": "unite", "unité": "unite", "unit": "unite", "units": "unite", "ml": "ml"}.get(clean, clean)
    if field == "category" and clean not in {"medicament", "reactif", "prelevement", "consommable", "dispositif", "equipement"}:
        return "", "INVALID_CATEGORY"
    if field == "professional_category" and clean not in {"medecin", "infirmier", "stagiaire", "technicien", "administratif", "autre"}:
        return "", "INVALID_CATEGORY"
    if field == "sterile" and clean not in {"oui", "non", "inconnu"}:
        return "", "INVALID_STERILITY"
    return clean, None


def ingest(root):
    raw, clean, issues, catalogue, manifests = {}, {}, [], [], []
    for domain, spec in DOMAINS.items():
        raw[domain], clean[domain] = [], []
        seen = set()
        for path in sorted((Path(root) / "sources" / domain).glob("*.csv")):
            rows = read_csv(path)
            source = path.stem
            manifests.append(dict(path=path.relative_to(root).as_posix(), sha256=__import__("hashlib").sha256(path.read_bytes()).hexdigest(), rows=len(rows)))
            catalogue.append(dict(domain=domain, table=f"{source}.{domain}", source=source,
                                  description=f"Identités locales du domaine {spec['label']}",
                                  granularity="une identité par clé locale", local_key="local_id",
                                  owner=spec["owner"], classification=spec["classification"], format="CSV UTF-8",
                                  refresh="à chaque import du prototype", consumers="hub MDM / Data Steward",
                                  rows=len(rows), columns=list(rows[0]) if rows else [],
                                  controls="clé locale unique ; complétude ; domaines ; validité ; contradictions"))
            for row in rows:
                local = row.get("local_id", "").strip()
                if not local:
                    raise ValueError(f"{path.name} : local_id manquant.")
                key = (source, local)
                if key in seen:
                    raise ValueError(f"Clé source dupliquée : {domain}/{source}/{local}")
                seen.add(key)
                rid = digest([domain, source, local])[:24]
                raw[domain].append(dict(row, source=source, rid=rid))
                result = dict(source=source, local_id=local, rid=rid, updated_at=row.get("updated_at", ""))
                for field in spec["fields"]:
                    value, error = normalise(field, row.get(field))
                    result[field] = value
                    if error:
                        issues.append(dict(domain=domain, rid=rid, source=source, local_id=local, field=field,
                                           code=error, raw_value=row.get(field, "")))
                for field in spec["required"]:
                    if not result[field]:
                        issues.append(dict(domain=domain, rid=rid, source=source, local_id=local, field=field,
                                           code="MISSING_REQUIRED", raw_value=row.get(field, "")))
                clean[domain].append(result)
    if not any(clean.values()):
        raise ValueError("Aucune source trouvée. Exécuter python -m mdm demo.")
    return dict(raw=raw, clean=clean, issues=issues, catalogue=catalogue, manifest=manifests)


def blocking_keys(row, domain):
    keys = []
    if row.get("qualified_id") and row.get("id_issuer"):
        keys.append(("id", row["id_issuer"], row["qualified_id"]))
    if domain == "produit":
        if row["preferred_name"]:
            keys.append(("label", row["category"], row["preferred_name"][:6]))
        if row["model_reference"]:
            keys.append(("model", row["manufacturer"], row["model_reference"]))
    else:
        for field in ("phone", "email"):
            if row[field]:
                keys.append((field, row[field]))
        if row["family_name"] and row["given_names"]:
            keys.append(("name", row["family_name"][:4], row["given_names"][:1]))
        if domain == "patient" and row["birth_date"] and row["given_names"]:
            keys.append(("dob", row["birth_date"], row["given_names"][:1]))
    return keys


def candidates(rows, domain):
    blocks, pairs = defaultdict(list), set()
    for i, row in enumerate(rows):
        for key in blocking_keys(row, domain):
            blocks[key].append(i)
    for indexes in blocks.values():
        if len(indexes) > 1000:
            raise ValueError("Bloc supérieur à 1 000 lignes : affiner les règles de blocking avant exécution.")
        pairs.update(combinations(indexes, 2))
    return sorted(pairs)


def critical_conflicts(a, b, domain):
    conflicts = [f for f in DOMAINS[domain]["critical"] if a.get(f) and b.get(f) and a[f] != b[f]]
    if a.get("id_issuer") and a.get("id_issuer") == b.get("id_issuer") and a.get("qualified_id") and b.get("qualified_id") and a["qualified_id"] != b["qualified_id"]:
        conflicts.append("qualified_id")
    return conflicts


def strong_evidence(a, b, domain):
    def eq(field):
        return bool(a.get(field) and a.get(field) == b.get(field))
    same_id = eq("qualified_id") and eq("id_issuer")
    if domain == "produit":
        required = ["category", "package_quantity", "package_unit"]
        if a.get("category") == "medicament":
            required += ["dosage", "form"]
        if a.get("category") == "equipement":
            required += ["model_reference", "manufacturer"]
        if not all(eq(f) for f in required):
            return False
        return (same_id or eq("model_reference")) and bool(a["preferred_name"] and b["preferred_name"] and JaroWinkler.normalized_similarity(a["preferred_name"], b["preferred_name"]) >= .8)
    names = all(a[f] and b[f] and JaroWinkler.normalized_similarity(a[f], b[f]) >= .88 for f in ("family_name", "given_names"))
    if domain == "patient":
        return names and eq("birth_date") and (same_id or eq("phone") or eq("email"))
    return names and (same_id or eq("email"))


def compare(a, b, domain, method="weighted"):
    if method not in METHODS:
        raise ValueError("Méthode inconnue.")
    features, weighted, observed = {}, 0.0, 0.0
    log_odds = math.log(FS["prior"] / (1 - FS["prior"]))
    active_weights = dict(DOMAINS[domain]["weights"])
    if domain == "produit":
        if a.get('category') != 'medicament' or b.get('category') != 'medicament':
            active_weights.pop('dosage', None)
            active_weights.pop('form', None)
        if a.get('category') != 'equipement' or b.get('category') != 'equipement':
            active_weights.pop('model_reference', None)
    for field, weight in active_weights.items():
        va, vb = a.get(field), b.get(field)
        if not va or not vb:
            features[field] = None
            continue
        sim = JaroWinkler.normalized_similarity(va, vb) if field in {"family_name", "given_names", "preferred_name", "manufacturer"} else float(va == vb)
        features[field] = round(sim, 6)
        weighted += weight * sim
        observed += weight
        level = "agreement" if sim >= .95 else "partial" if sim >= .80 else "disagreement"
        log_odds += math.log(FS[level + "_match"] / FS[level + "_nonmatch"])
    # Les NULL ne sont jamais des accords. La couverture empêche un nom seul d'avoir un score élevé.
    weighted_score = weighted / observed if observed else 0.0
    score = weighted_score if method == "weighted" else 1 / (1 + math.exp(-max(-700, min(700, log_odds))))
    coverage = observed / sum(active_weights.values()) if active_weights else 0
    conflicts = critical_conflicts(a, b, domain)
    evidence = strong_evidence(a, b, domain)
    if method == "exact":
        fields = list(DOMAINS[domain]["weights"])
        score = float(evidence and all(not a.get(f) or not b.get(f) or a[f] == b[f] for f in fields))
        decision = "AUTO" if score else "REVIEW" if weighted_score >= .70 else "NO_MATCH"
    else:
        low, high = THRESHOLDS[method]
        decision = "AUTO" if score >= high and coverage >= .65 and evidence else "REVIEW" if score >= low else "NO_MATCH"
    reason = "SUFFICIENT_EVIDENCE" if decision == "AUTO" else "INSUFFICIENT_EVIDENCE_OR_SCORE"
    if conflicts:
        same_id = bool(a.get('qualified_id') and a.get('id_issuer') and a['qualified_id'] == b.get('qualified_id') and a['id_issuer'] == b.get('id_issuer'))
        decision = "REVIEW" if same_id or ("qualified_id" not in conflicts and weighted_score >= .85) else "NO_MATCH"
        reason = "CRITICAL_CONFLICT:" + ",".join(conflicts)
    return dict(case_id=digest([domain, *sorted([a["rid"], b["rid"]])])[:24], domain=domain,
                a=a["rid"], b=b["rid"], source_a=a["source"], local_id_a=a["local_id"], source_b=b["source"], local_id_b=b["local_id"],
                score=round(score, 6), coverage=round(coverage, 6), features=features, decision=decision,
                reason=reason, critical_conflicts=conflicts)


def cluster(rows, pairs, domain, decisions=None):
    """Contrôles au niveau du groupe entier, y compris contraintes de non-fusion."""
    decisions = decisions or {}
    parent = {r["rid"]: r["rid"] for r in rows}
    groups = {r["rid"]: {r["rid"]} for r in rows}
    lookup = {r["rid"]: r for r in rows}
    rejected = {frozenset((p["a"], p["b"])) for p in pairs if decisions.get(p["case_id"], {}).get("decision") in {"REJECT", "ESCALATE"}}
    def find(key):
        while parent[key] != key:
            key = parent[key]
        return key
    events = []
    for pair in sorted(pairs, key=lambda p: (-p["score"], p["case_id"])):
        manual = decisions.get(pair["case_id"], {}).get("decision")
        pair["review_decision"] = manual or ""
        pair["cluster_result"] = "NOT_APPLIED"
        if manual in {"REJECT", "ESCALATE"} or (manual != "CONFIRM" and pair["decision"] != "AUTO"):
            continue
        ga, gb = find(pair["a"]), find(pair["b"])
        if ga == gb:
            pair["cluster_result"] = "ALREADY_LINKED"
            continue
        cross = [(lookup[x], lookup[y]) for x in groups[ga] for y in groups[gb]]
        conflict = any(critical_conflicts(x, y, domain) for x, y in cross)
        forbidden = any(frozenset((x["rid"], y["rid"])) in rejected for x, y in cross)
        if conflict or forbidden:
            pair["cluster_result"] = "BLOCKED_CRITICAL_CONFLICT" if conflict else "BLOCKED_REJECTED_LINK"
        else:
            keep, remove = sorted([ga, gb])
            parent[remove] = keep
            groups[keep] |= groups.pop(remove)
            pair["cluster_result"] = "MERGED_HUMAN" if manual == "CONFIRM" else "MERGED_AUTO"
        events.append(dict(case_id=pair["case_id"], domain=domain, result=pair["cluster_result"], evidence=pair["reason"]))
    return [sorted(members) for _, members in sorted(groups.items())], events


def golden_records(rows, groups, domain):
    lookup = {r["rid"]: r for r in rows}
    spec = DOMAINS[domain]
    priority = {s: i for i, s in enumerate(spec["sources"])}
    masters, xrefs, provenance = [], [], []
    for group in groups:
        master_id = str(uuid.uuid5(uuid.NAMESPACE_URL, domain + ":" + ":".join(group)))
        members = [lookup[rid] for rid in group]
        members.sort(key=lambda r: (priority.get(r["source"], 99), r["source"], r["local_id"]))
        master = dict(master_id=master_id, domain=domain, status="ACTIVE", rules_version=RULE_VERSION,
                      member_count=len(members), source_count=len({r['source'] for r in members}))
        for field in spec["fields"]:
            candidates_for_field = [dict(value=r[field], source=r["source"], local_id=r["local_id"], rid=r["rid"]) for r in members if r[field]]
            chosen = candidates_for_field[0] if candidates_for_field else {}
            master[field] = chosen.get("value", "")
            provenance.append(dict(master_id=master_id, domain=domain, field=field, value=master[field],
                                   selected_source=chosen.get("source", ""), selected_local_id=chosen.get("local_id", ""),
                                   policy="SOURCE_PRIORITY_THEN_LOCAL_ID", conflict=len({c['value'] for c in candidates_for_field}) > 1,
                                   candidates=candidates_for_field))
        masters.append(master)
        xrefs += [dict(domain=domain, source=r["source"], local_id=r["local_id"], rid=r["rid"], master_id=master_id) for r in members]
    return masters, xrefs, provenance


def quality(rows, raw, issues, domain):
    spec = DOMAINS[domain]
    fields = spec["required"]
    denominator = len(rows) * len(fields)
    valid_cells = sum(bool(r[f]) for r in rows for f in fields)
    raw_cells = sum(bool(str(r.get(f, "")).strip()) for r in raw for f in fields)
    invalid = {(i['rid'], i['field']) for i in issues if i['domain'] == domain and i['code'].startswith("INVALID")}
    supplied = sum(bool(str(r.get(f, "")).strip()) for r in raw for f in spec["fields"])
    return dict(domain=domain, records=len(rows), raw_completeness=raw_cells / denominator if denominator else None,
                valid_required_completeness=valid_cells / denominator if denominator else None,
                validity=(supplied-len(invalid)) / supplied if supplied else None,
                invalid_cells=len(invalid), required_cells=denominator,
                note="Complétude requise et validité syntaxique ; aucune preuve d'exactitude clinique.")
