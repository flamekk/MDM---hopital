import json
from pathlib import Path
import uuid
from .config import DOMAINS, FS, METHODS, RULE_VERSION, THRESHOLDS
from .engine import ingest, candidates, compare, cluster, golden_records, quality
from .io import digest, read_csv, write_csv
from . import store
from .hospital import load_related, apply_attribute_decisions, allergy_rows


def run(root, method="weighted", base_run=None, evaluate=True, persist=True):
    if method not in METHODS:
        raise ValueError("Méthode inconnue.")
    root = Path(root)
    data = ingest(root)
    inherited, previous = {}, None
    attribute_decisions, clinical_decisions = {}, {}
    if base_run:
        previous = store.load_run(root, base_run)
        if previous['manifest'] != data['manifest'] or previous['rules_version'] != RULE_VERSION:
            raise ValueError("Sources ou règles modifiées : lancer une exécution indépendante puis refaire la revue.")
        inherited = dict(previous.get('applied_decisions', {}))
        inherited.update(store.decisions(root, base_run))
        attribute_decisions = dict(previous.get('applied_attribute_decisions', {}))
        attribute_decisions.update(store.extra_decisions(root, base_run, 'attribute'))
        clinical_decisions = dict(previous.get('applied_clinical_decisions', {}))
        clinical_decisions.update(store.extra_decisions(root, base_run, 'clinical'))
    payload = dict(run_id=str(uuid.uuid4()), created_at=store.utc(), rules_version=RULE_VERSION,
                   method=method, parent_run=base_run, manifest=data['manifest'], source_fingerprint=digest(data['manifest']),
                   rules=dict(thresholds=THRESHOLDS, likelihoods=FS), applied_decisions=inherited,
                   catalogue=data['catalogue'], raw=data['raw'], standardized=data['clean'],
                   issues=data['issues'], quality=[], pairs=[], masters=[], xrefs=[], provenance=[], events=[], metrics=[], lineage=[], related={})
    payload.update(applied_attribute_decisions=attribute_decisions, applied_clinical_decisions=clinical_decisions)
    for domain, rows in data['clean'].items():
        if not rows:
            continue
        indexes = candidates(rows, domain)
        scored = [compare(rows[a], rows[b], domain, method) for a, b in indexes]
        groups, events = cluster(rows, scored, domain, inherited)
        masters, xrefs, provenance = golden_records(rows, groups, domain)
        payload['quality'].append(quality(rows, data['raw'][domain], data['issues'], domain))
        payload['pairs'] += scored
        payload['masters'] += masters
        payload['xrefs'] += xrefs
        payload['provenance'] += provenance
        payload['events'] += events
        truth_path = root / "evaluation" / "truth.csv"
        if evaluate and truth_path.exists():
            from .evaluation import evaluate as assess
            for algorithm in METHODS:
                alternative = [compare(rows[a], rows[b], domain, algorithm) for a, b in indexes]
                alt_groups, _ = cluster(rows, alternative, domain)
                _, alt_xrefs, _ = golden_records(rows, alt_groups, domain)
                metrics = assess(truth_path, [dict(r, domain=domain) for r in rows], alternative, alt_xrefs)
                payload['metrics'].append(dict(domain=domain, method=algorithm, stage="automatic_baseline", **metrics))
            current = assess(truth_path, [dict(r, domain=domain) for r in rows], scored, xrefs)
            payload['metrics'].append(dict(domain=domain, method=method, stage="current_version", **current))
    xref_by_key = {(r['domain'], r['source'], r['local_id']): r['master_id'] for r in payload['xrefs']}
    payload['related'], payload['related_manifest'] = load_related(root, payload['xrefs'])
    apply_attribute_decisions(payload, attribute_decisions)
    if 'allergies.csv' in payload['related']:
        payload['related']['allergies.csv'] = allergy_rows(payload)
    if previous:
        old = {(r['domain'], r['source'], r['local_id']): r['master_id'] for r in previous['xrefs']}
        links = {(old[k], v) for k, v in xref_by_key.items() if k in old}
        payload['lineage'] = [dict(previous_master_id=a, master_id=b, relationship="UNCHANGED" if a == b else "REBUILT") for a, b in sorted(links)]
    # Un seul rattachement par identité et couverture totale de toutes les sources.
    expected = sum(len(rows) for rows in data['clean'].values())
    if len(payload['xrefs']) != expected or len(xref_by_key) != expected:
        raise AssertionError("Couverture des correspondances invalide.")
    if not store.verify(root):
        raise ValueError("Intégrité du journal invalide ; exécution refusée.")
    if not persist:
        return payload
    out = root / 'runs' / payload['run_id']
    out.mkdir(parents=True, exist_ok=False)
    (out / 'snapshot.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    for key in ('masters', 'xrefs', 'provenance', 'pairs', 'issues', 'quality', 'catalogue', 'metrics', 'events', 'lineage'):
        write_csv(out / f'{key}.csv', payload[key])
    for domain, rows in payload['standardized'].items():
        if rows:
            write_csv(out / f'standardized_{domain}.csv', rows)
    for name, rows in payload['related'].items():
        write_csv(out / f'related_{name}', rows)
    store.save_run(root, payload)
    return payload
