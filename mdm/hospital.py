"""Contexte hospitalier synthétique, indépendant des critères d'identité."""
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from .demo import generate
from .io import digest, read_csv, write_csv

HOSPITAL_NAME = 'Hôpital Al Amal'
SCENARIOS = {
    'S1_5pct': 'S1 · Qualité élevée',
    'S2_15pct': 'S2 · Qualité intermédiaire',
    'S3_30pct': 'S3 · Qualité dégradée',
}
RELATED_TABLES = {
    'allergies.csv': ('patient', ['substance']),
    'sejours.csv': ('patient', ['service', 'admission_date']),
    'contacts_urgence.csv': ('patient', ['contact_name', 'relationship']),
    'affectations.csv': ('personnel', ['service']),
    'formations.csv': ('personnel', ['training_name']),
    'gardes.csv': ('personnel', ['service', 'shift_date']),
    'stocks.csv': ('produit', ['lot', 'quantity']),
    'equipements.csv': ('produit', ['serial_number', 'service']),
}


def generate_hospital(root, size=48, scenario='S1_5pct'):
    if scenario not in SCENARIOS:
        raise ValueError('Scénario inconnu.')
    root = Path(root)
    generate(root, size=size)
    # Même population et même couverture ; corruption supplémentaire emboîtée S2/S3.
    # Les suffixes historiques 5/15/30 désignent des profils, pas un taux mesuré garanti.
    extra = {'S1_5pct': 0, 'S2_15pct': 3, 'S3_30pct': 7}[scenario]
    for path in sorted((root / 'sources').glob('*/*.csv')):
        rows = read_csv(path)
        domain = path.parent.name
        for i, row in enumerate(rows):
            if path.stem in ('admission', 'rh', 'pharmacie') or i % 12 >= extra:
                continue
            row['qualified_id'] = ''
            if domain == 'produit':
                row['package_quantity'] = '' if i % 2 else 'inconnu'
            else:
                row['email'], row['phone'] = '', '000'
                if domain == 'patient' and i % 2 == 0:
                    row['birth_date'] = ''
                if i % 3 == 0:
                    row['given_names'] = row['given_names'][:1]
        write_csv(path, rows)
    services = ['Urgences', 'Cardiologie', 'Pédiatrie', 'Médecine interne', 'Chirurgie', 'Laboratoire']
    allergies, stays, contacts, assignments, training, shifts, stocks, equipment = ([] for _ in range(8))
    admission = read_csv(root / 'sources/patient/admission.csv')
    dpi = {r['local_id']: r for r in read_csv(root / 'sources/patient/dpi.csv')}
    for i, row in enumerate(admission):
        source = 'dpi' if f'dpi-{i:04}' in dpi else 'admission'
        local = f'{source}-{i:04}'
        if i % 4 == 0:
            substance, kind, reaction = [('Pénicilline', 'Médicamenteuse', 'Éruption cutanée déclarée'),
                                         ('Latex', 'Contact', 'Prurit déclaré'),
                                         ('Arachide', 'Alimentaire', 'Réaction rapportée, détail à compléter')][(i // 4) % 3]
            allergies.append(dict(record_id=f'ALG-{i:04}', source=source, local_id=local, substance=substance,
                                  allergy_category=kind, manifestation=reaction, reported_severity='non renseignée',
                                  clinical_status='suspectee', validation_status='a_valider', validated_by='',
                                  reported_at='2026-10-20', provenance=f'{source}.allergie_patient'))
        if i % 12 == 0:
            # Deux déclarations sourcées pour une même identité ; aucune déduplication clinique.
            allergies.append(dict(record_id=f'ALG-LATEX-{i:04}', source='admission', local_id=row['local_id'],
                                  substance='Latex', allergy_category='Contact', manifestation='Déclaration à documenter',
                                  reported_severity='non renseignée', clinical_status='suspectee', validation_status='a_valider',
                                  validated_by='', reported_at='2026-10-21', provenance='admission.allergie_patient'))
        stays.append(dict(record_id=f'SEJ-{i:04}', source='admission', local_id=row['local_id'],
                          service=services[i % 6], care_type='Hospitalisation' if i % 3 == 0 else 'Consultation',
                          admission_date=f'2026-10-{10 + i % 18:02}', discharge_date='' if i % 3 == 0 else f'2026-10-{10 + i % 18:02}',
                          room=f'{100 + i // 2}', bed=str(1 + i % 2), care_status='en_cours' if i % 3 == 0 else 'termine'))
        if i % 2 == 0:
            contacts.append(dict(record_id=f'URG-{i:04}', source='admission', local_id=row['local_id'],
                                 contact_name=f'Contact démo {i + 1}', relationship='Proche désigné', phone=f'07{i + 20000000:08}',
                                 provenance='admission.contact_urgence'))
    for i, row in enumerate(read_csv(root / 'sources/personnel/rh.csv')):
        assignments.append(dict(record_id=f'AFF-{i:04}', source='rh', local_id=row['local_id'], service=services[i % 6],
                                role=row['professional_category'], start_date='2026-09-01', end_date='', establishment=HOSPITAL_NAME))
        training.append(dict(record_id=f'FOR-{i:04}', source='rh', local_id=row['local_id'],
                             training_name=['Identitovigilance', 'Hygiène hospitalière', 'Traçabilité des dispositifs'][i % 3],
                             completion_date='2026-09-15', renewal_date='2027-09-15', status='realisee', provenance='formation.attestation_demo'))
        shifts.append(dict(record_id=f'GAR-{i:04}', source='rh', local_id=row['local_id'], service=services[i % 6],
                           shift_date='2026-11-04', shift_period='Jour' if i % 2 else 'Nuit', provenance='planning.garde_demo'))
    for i, row in enumerate(read_csv(root / 'sources/produit/pharmacie.csv')):
        stocks.append(dict(record_id=f'STK-{i:04}', source='pharmacie', local_id=row['local_id'], lot=f'LOT-AA-{i:04}',
                           quantity=str(5 if i % 9 == 0 else 25 + i), reorder_level='10',
                           expiry_date='2026-10-01' if i % 13 == 0 else '2027-06-30', location=['Pharmacie centrale', 'Magasin bloc', 'Réserve laboratoire'][i % 3],
                           provenance='pharmacie.stock_demo'))
        if row['category'] == 'equipement':
            equipment.append(dict(record_id=f'EQP-{i:04}', source='pharmacie', local_id=row['local_id'], serial_number=f'AA-SN-{i:05}',
                                  service=services[i % 6], inventory_status='en_service', last_maintenance='2026-08-10',
                                  next_maintenance='2026-12-10', provenance='biomedical.inventaire_demo'))
    for name, rows in zip(RELATED_TABLES, [allergies, stays, contacts, assignments, training, shifts, stocks, equipment]):
        write_csv(root / 'related' / name, rows)
    (root / 'hospital.json').write_text(__import__('json').dumps(dict(name=HOSPITAL_NAME, scenario=scenario, synthetic=True), ensure_ascii=False), encoding='utf-8')


def load_related(root, xrefs):
    root = Path(root)
    mapping = {(r['domain'], r['source'], r['local_id']): r['master_id'] for r in xrefs}
    related, manifest = {}, []
    for name, (domain, required) in RELATED_TABLES.items():
        path = root / 'related' / name
        if not path.exists():
            continue
        raw = read_csv(path)
        manifest.append(dict(path=f'related/{name}', sha256=__import__('hashlib').sha256(path.read_bytes()).hexdigest(), rows=len(raw)))
        linked, seen = [], set()
        for i, row in enumerate(raw):
            master_id = mapping.get((domain, row.get('source'), row.get('local_id')))
            if not master_id:
                raise ValueError(f'Relation orpheline dans {name}: {row.get("local_id")}')
            if any(not row.get(f, '').strip() for f in required):
                raise ValueError(f'Champs requis absents dans {name}, ligne {i+2}.')
            assertion = digest([name, row.get('source'), row.get('local_id'), row.get('record_id', str(i))])[:24]
            if assertion in seen:
                raise ValueError(f'Déclaration dupliquée dans {name}.')
            seen.add(assertion)
            linked.append(dict(row, assertion_id=assertion, source_hash=digest(row), source_record=dict(row), master_id=master_id))
        related[name] = linked
    return related, manifest


def conflict_id(row):
    return digest([row['master_id'], row['field']])[:24]


def attribute_conflicts(payload):
    result = []
    for row in payload['provenance']:
        if row['conflict']:
            result.append(dict(row, case_id=conflict_id(row), resolution_status=row.get('resolution_status', 'PROPOSED')))
    return result


def apply_attribute_decisions(payload, decisions):
    masters = {r['master_id']: r for r in payload['masters']}
    for row in payload['provenance']:
        event = decisions.get(conflict_id(row))
        if not row['conflict'] or not event:
            continue
        if event['decision'] == 'ESCALATE':
            row['resolution_status'] = 'ESCALATED'
            continue
        chosen = next((c for c in row['candidates'] if c['value'] == event['selected_value'] and c['source'] == event['selected_source'] and c['local_id'] == event['selected_local_id']), None)
        if chosen:
            row.update(value=chosen['value'], selected_source=chosen['source'], selected_local_id=chosen['local_id'],
                       policy='HUMAN_SELECTED_VALUE', resolution_status='RESOLVED', reviewed_by=event['reviewer'])
            masters[row['master_id']][row['field']] = chosen['value']


def allergy_rows(payload, live_decisions=None):
    decisions = dict(payload.get('applied_clinical_decisions', {}))
    decisions.update(live_decisions or {})
    result = []
    for row in payload.get('related', {}).get('allergies.csv', []):
        event = decisions.get(row.get('assertion_id'))
        enriched = dict(row)
        enriched.setdefault('validation_status', 'a_valider')
        if event and event['source_hash'] == row['source_hash']:
            enriched.update(validation_status={'CONFIRM': 'confirmee', 'REFUTE': 'ecartee', 'REQUEST_INFO': 'a_completer'}[event['decision']],
                            validated_by=event['reviewer'], validated_at=event['created_at'], validation_comment=event['comment'])
        result.append(enriched)
    return result


def stock_flags(row, today=None):
    today = today or date.today()
    invalid_expiry=False
    try:
        expired = bool(row.get('expiry_date') and date.fromisoformat(row['expiry_date']) < today)
    except ValueError:
        expired = False
        invalid_expiry=True
    invalid_quantity=False
    try:
        quantity=Decimal(str(row['quantity']))
        threshold=Decimal(str(row.get('reorder_level') or 0))
        if not quantity.is_finite() or not threshold.is_finite() or quantity<0 or threshold<0:
            raise ValueError('Quantité invalide')
        low = quantity < threshold
    except (ValueError, KeyError, InvalidOperation):
        low = False
        invalid_quantity=True
    return dict(expired=expired, low_stock=low, invalid_expiry=invalid_expiry, invalid_quantity=invalid_quantity)
