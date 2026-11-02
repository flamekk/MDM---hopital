"""Produit un SQL transactionnel, sans connexion ni secret."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mdm import store


def literal(value):
    if value is None or value == '':
        return 'NULL'
    if isinstance(value, bool):
        return 'TRUE' if value else 'FALSE'
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    return "'" + str(value).replace("'", "''") + "'"


def export(root, out):
    payload = store.load_run(root)
    if not store.verify(root):
        raise ValueError('Journal invalide : export refusé.')
    lines = ['-- Généré depuis un snapshot vérifié ; charger après sql/schema.sql.', 'BEGIN;', 'SET LOCAL standard_conforming_strings = on;']
    def insert(table, row):
        lines.append(f"INSERT INTO mdm.{table} ({','.join(row)}) VALUES ({','.join(literal(v) for v in row.values())});")
    run_id = payload['run_id']
    insert('run', dict(run_id=run_id, created_at=payload['created_at'], rules_version=payload['rules_version'],
                       method=payload['method'], source_fingerprint=payload['source_fingerprint'], snapshot=payload))
    fields = {'patient': ['family_name', 'given_names', 'birth_date', 'phone', 'email', 'address'],
              'personnel': ['family_name', 'given_names', 'professional_category', 'email', 'phone'],
              'produit': ['preferred_name', 'category', 'manufacturer', 'model_reference', 'dosage', 'form', 'package_quantity', 'package_unit', 'sterile']}
    tables = {'patient': 'patient_master', 'personnel': 'personnel_master', 'produit': 'product_master'}
    for r in payload['masters']:
        insert('master_entity', dict(run_id=run_id, **{k: r.get(k) for k in ['master_id', 'domain', 'status', 'member_count', 'source_count', 'qualified_id', 'id_issuer']}))
        insert(tables[r['domain']], dict(run_id=run_id, master_id=r['master_id'], **{k: r.get(k) for k in fields[r['domain']]}))
    for r in payload['xrefs']:
        insert('source_link', dict(run_id=run_id, **r))
    for r in payload['provenance']:
        insert('attribute_provenance', dict(run_id=run_id, **{k: r[k] for k in ['master_id', 'field', 'value', 'selected_source', 'selected_local_id', 'policy', 'conflict', 'candidates']}))
    for relation, records in payload['related'].items():
        for i, r in enumerate(records):
            insert('related_record', dict(run_id=run_id, relation_type=relation, ordinal=i, master_id=r['master_id'], payload=r))
    lines.append('COMMIT;')
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return out


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--workspace', type=Path, default=Path('workspace'))
    p.add_argument('--output', type=Path, default=Path('dist/import_mdm.sql'))
    args = p.parse_args()
    print(export(args.workspace, args.output))
