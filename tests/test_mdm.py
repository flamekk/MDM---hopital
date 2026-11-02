import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from mdm.demo import generate
from mdm.engine import normalise, ingest, compare, cluster, candidates
from mdm.io import read_csv, write_csv, csv_download
from mdm.pipeline import run
from mdm import store


class NormalisationTests(unittest.TestCase):
    def test_dates_and_nulls(self):
        self.assertEqual(normalise('birth_date', '30/02/2026'), ('', 'INVALID_DATE'))
        self.assertEqual(normalise('birth_date', '02/11/1990'), ('1990-11-02', None))
        self.assertEqual(normalise('birth_date', ''), ('', None))

    def test_contacts_and_accents(self):
        self.assertEqual(normalise('phone', '+212 6 12 34 56 78'), ('0612345678', None))
        self.assertEqual(normalise('phone', '123'), ('', 'INVALID_PHONE'))
        self.assertEqual(normalise('family_name', '  BÉNNANI  '), ('bennani', None))
        self.assertEqual(normalise('email', 'erreur')[1], 'INVALID_EMAIL')

    def test_quantities(self):
        self.assertEqual(normalise('package_quantity', '10,00'), ('10', None))
        for value in ('-1', '0', 'NaN', 'Infinity'):
            self.assertEqual(normalise('package_quantity', value)[1], 'INVALID_QUANTITY')

    def test_csv_formula_protection(self):
        self.assertIn("'=CMD", csv_download([{'name': '=CMD'}]).decode('utf-8-sig'))


class MatchingTests(unittest.TestCase):
    def person(self, rid, dob='1980-01-01'):
        return dict(rid=rid, source=rid, local_id=rid, family_name='bennani', given_names='imane',
                    birth_date=dob, phone='0612345678', email='', address='', qualified_id='', id_issuer='')

    def pair(self, a, b, score=1):
        return dict(case_id=a+b, a=a, b=b, score=score, decision='AUTO', reason='test')

    def test_missing_evidence_does_not_auto_merge(self):
        a, b = self.person('A', ''), self.person('B', '')
        a['phone'] = b['phone'] = ''
        for method in ('exact', 'weighted', 'probabilistic'):
            self.assertNotEqual(compare(a, b, 'patient', method)['decision'], 'AUTO')

    def test_dob_contradiction_blocks_human_and_auto(self):
        a, b = self.person('A'), self.person('B', '1990-01-01')
        p = compare(a, b, 'patient')
        groups, events = cluster([a, b], [p], 'patient', {p['case_id']: {'decision': 'CONFIRM'}})
        self.assertEqual(len(groups), 2)
        self.assertEqual(events[0]['result'], 'BLOCKED_CRITICAL_CONFLICT')

    def test_transitive_conflict_is_blocked(self):
        rows = [self.person('A'), self.person('B', ''), self.person('C', '1990-01-01')]
        groups, events = cluster(rows, [self.pair('A', 'B'), self.pair('B', 'C', .99)], 'patient')
        self.assertEqual(len(groups), 2)
        self.assertTrue(any(e['result'] == 'BLOCKED_CRITICAL_CONFLICT' for e in events))

    def test_rejection_is_enforced_transitively(self):
        rows = [self.person(k) for k in 'ABC']
        pairs = [self.pair('A', 'B'), self.pair('B', 'C', .99), self.pair('A', 'C', .98)]
        groups, _ = cluster(rows, pairs, 'patient', {'AC': {'decision': 'REJECT'}})
        self.assertFalse(any('A' in g and 'C' in g for g in groups))

    def test_product_conditioning_is_critical(self):
        product = dict(rid='A', source='pharmacie', local_id='1', preferred_name='paracetamol', category='medicament',
                       manufacturer='demo', model_reference='', dosage='500 mg', form='comprime',
                       package_quantity='10', package_unit='unite', sterile='non', qualified_id='P1', id_issuer='demo')
        other = dict(product, rid='B', local_id='2', package_quantity='20')
        result = compare(product, other, 'produit')
        self.assertEqual(result['decision'], 'REVIEW')
        self.assertIn('package_quantity', result['critical_conflicts'])

    def test_equal_local_ids_are_not_global_evidence(self):
        a, b = self.person('A'), self.person('B')
        b.update(family_name='autre', given_names='personne', birth_date='1970-01-01', phone='')
        a['local_id'] = b['local_id'] = '1'
        self.assertNotEqual(compare(a, b, 'patient')['decision'], 'AUTO')


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        generate(self.root, size=12)

    def test_ingestion_preserves_raw_and_unique_coverage(self):
        payload = run(self.root)
        self.assertEqual(len(payload['xrefs']), sum(len(r) for r in payload['raw'].values()))
        self.assertEqual(len({r['rid'] for r in payload['xrefs']}), len(payload['xrefs']))
        self.assertEqual({r['domain'] for r in payload['masters']}, {'patient', 'personnel', 'produit'})
        self.assertTrue(any(r['code'] == 'INVALID_DATE' for r in payload['issues']))
        self.assertTrue(store.verify(self.root))
        self.assertEqual({r['clinical_status'] for r in payload['related']['allergies.csv']}, {'a_valider'})

    def test_duplicate_local_id_is_refused(self):
        path = self.root / 'sources/patient/admission.csv'
        rows = read_csv(path)
        write_csv(path, rows + [rows[0]])
        with self.assertRaisesRegex(ValueError, 'dupliquée'):
            ingest(self.root)

    def test_no_ground_truth_leakage(self):
        first = run(self.root)
        path = self.root / 'evaluation/truth.csv'
        truth = read_csv(path)
        for i, row in enumerate(truth):
            row['entity_id'] = str(i)
        write_csv(path, truth)
        second = run(self.root)
        for field in ('pairs', 'masters', 'xrefs', 'provenance'):
            self.assertEqual(first[field], second[field])
        self.assertNotEqual(first['metrics'], second['metrics'])

    def test_operation_without_evaluation(self):
        first = run(self.root, evaluate=False)
        self.assertEqual(first['metrics'], [])
        self.assertTrue(first['masters'])

    def test_decision_new_version_and_split_without_overwrite(self):
        first = run(self.root)
        pair = next(p for p in first['pairs'] if p['cluster_result'] == 'MERGED_AUTO')
        original = store.load_run(self.root, first['run_id'])
        store.review(self.root, first['run_id'], pair['case_id'], 'REJECT', 'steward', 'Identités distinctes après contrôle')
        second = run(self.root, base_run=first['run_id'])
        lookup = {r['rid']: r['master_id'] for r in second['xrefs']}
        self.assertNotEqual(lookup[pair['a']], lookup[pair['b']])
        self.assertEqual(original, store.load_run(self.root, first['run_id']))
        self.assertTrue(second['lineage'])
        third = run(self.root, base_run=second['run_id'])
        self.assertEqual(second['xrefs'], third['xrefs'])
        self.assertTrue(store.verify(self.root))

    def test_source_change_invalidates_inherited_decisions(self):
        first = run(self.root)
        path = self.root / 'sources/patient/admission.csv'
        path.write_text(path.read_text(encoding='utf-8-sig') + '\n', encoding='utf-8-sig')
        with self.assertRaisesRegex(ValueError, 'modifiées'):
            run(self.root, base_run=first['run_id'])

    def test_review_requires_justification_and_safe_sources(self):
        first = run(self.root)
        conflict = next(p for p in first['pairs'] if p['critical_conflicts'])
        with self.assertRaises(ValueError):
            store.review(self.root, first['run_id'], conflict['case_id'], 'CONFIRM', 'steward', 'test')
        with self.assertRaises(ValueError):
            store.review(self.root, first['run_id'], conflict['case_id'], 'REJECT', '', '')

    def test_tampered_decision_is_detected(self):
        first = run(self.root)
        case = first['pairs'][0]['case_id']
        store.review(self.root, first['run_id'], case, 'REJECT', 'steward', 'test')
        with closing(sqlite3.connect(self.root / 'mdm.sqlite3')) as db:
            with db:
                db.execute("UPDATE decisions SET comment='altéré'")
        self.assertFalse(store.verify(self.root))

    def test_orphan_relation_is_refused(self):
        path = self.root / 'related/allergies.csv'
        rows = read_csv(path)
        rows[0]['local_id'] = 'absent'
        write_csv(path, rows)
        with self.assertRaisesRegex(ValueError, 'orpheline'):
            run(self.root)


if __name__ == '__main__':
    unittest.main()
