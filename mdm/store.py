"""Snapshots et décisions append-only dans une base SQLite transactionnelle locale."""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
import uuid
from .io import digest


def utc():
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@contextmanager
def connect(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(root / "mdm.sqlite3", timeout=20)
    db.row_factory = sqlite3.Row
    db.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE IF NOT EXISTS runs(run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, payload TEXT NOT NULL, payload_hash TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS decisions(event_id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES runs(run_id), case_id TEXT NOT NULL,
      decision TEXT NOT NULL CHECK(decision IN ('CONFIRM','REJECT','ESCALATE')), reviewer TEXT NOT NULL, comment TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, previous_hash TEXT NOT NULL, event_hash TEXT NOT NULL);
    """)
    try:
        yield db
    finally:
        db.close()


def audit(db, event):
    last = db.execute("SELECT event_hash FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
    previous = last[0] if last else "GENESIS"
    db.execute("INSERT INTO audit(event,previous_hash,event_hash) VALUES (?,?,?)",
               (json.dumps(event, ensure_ascii=False, sort_keys=True), previous, digest([previous, event])))


def save_run(root, payload):
    with connect(root) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO runs VALUES (?,?,?,?)", (payload['run_id'], payload['created_at'], json.dumps(payload, ensure_ascii=False), digest(payload)))
        audit(db, dict(action="PIPELINE_RUN", run_id=payload['run_id'], created_at=payload['created_at'], payload_hash=digest(payload)))
        db.commit()


def list_runs(root):
    with connect(root) as db:
        return [dict(r) for r in db.execute("SELECT run_id,created_at,payload_hash FROM runs ORDER BY rowid DESC")]


def load_run(root, run_id=None):
    with connect(root) as db:
        row = db.execute("SELECT payload,payload_hash FROM runs WHERE run_id=?", (run_id,)).fetchone() if run_id else db.execute("SELECT payload,payload_hash FROM runs ORDER BY rowid DESC LIMIT 1").fetchone()
        if row is None:
            raise ValueError("Aucune exécution disponible.")
        payload = json.loads(row['payload'])
        if digest(payload) != row['payload_hash']:
            raise ValueError("Snapshot altéré : empreinte invalide.")
        return payload


def review(root, run_id, case_id, decision, reviewer, comment):
    if not verify(root):
        raise ValueError("Intégrité du journal invalide ; décision refusée.")
    if decision not in {"CONFIRM", "REJECT", "ESCALATE"}:
        raise ValueError("Décision inconnue.")
    if not reviewer.strip() or not comment.strip():
        raise ValueError("Réviseur et justification obligatoires.")
    payload = load_run(root, run_id)
    pair = next((p for p in payload['pairs'] if p['case_id'] == case_id), None)
    if pair is None:
        raise ValueError("Cas absent de cette exécution.")
    if decision == "CONFIRM" and pair['critical_conflicts']:
        raise ValueError("Corriger les sources contradictoires avant de confirmer ce cas.")
    event = dict(event_id=str(uuid.uuid4()), run_id=run_id, case_id=case_id, decision=decision,
                 reviewer=reviewer.strip(), comment=comment.strip(), created_at=utc())
    with connect(root) as db:
        db.execute("BEGIN IMMEDIATE")
        db.execute("INSERT INTO decisions VALUES (:event_id,:run_id,:case_id,:decision,:reviewer,:comment,:created_at)", event)
        audit(db, dict(action="REVIEW", **event))
        db.commit()
    return event


def decisions(root, run_id):
    with connect(root) as db:
        return {r['case_id']: dict(r) for r in db.execute("SELECT * FROM decisions WHERE run_id=? ORDER BY rowid", (run_id,))}


def audit_log(root):
    with connect(root) as db:
        return [dict(r) for r in db.execute("SELECT * FROM audit ORDER BY seq")]


def verify(root):
    previous = "GENESIS"
    for row in audit_log(root):
        if row['previous_hash'] != previous or row['event_hash'] != digest([previous, json.loads(row['event'])]):
            return False
        previous = row['event_hash']
    # Vérifie aussi les données par rapport aux événements du journal.
    with connect(root) as db:
        recorded_reviews = {}
        recorded_runs = {}
        for r in db.execute("SELECT event FROM audit"):
            event = json.loads(r[0])
            if event['action'] == 'REVIEW':
                recorded_reviews[event['event_id']] = {k: v for k, v in event.items() if k != 'action'}
            elif event['action'] == 'PIPELINE_RUN':
                recorded_runs[event['run_id']] = event['payload_hash']
        actual_reviews = {r['event_id']: dict(r) for r in db.execute("SELECT * FROM decisions")}
        if actual_reviews != recorded_reviews:
            return False
        actual_runs = {r['run_id']: r for r in db.execute("SELECT * FROM runs")}
        if set(actual_runs) != set(recorded_runs):
            return False
        return all(digest(json.loads(r['payload'])) == r['payload_hash'] == recorded_runs[k] for k, r in actual_runs.items())
