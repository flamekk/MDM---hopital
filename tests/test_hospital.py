from contextlib import closing
from datetime import date
from pathlib import Path
import sqlite3
import tempfile
import unittest
from mdm import store
from mdm.hospital import generate_hospital, attribute_conflicts, allergy_rows, stock_flags, RELATED_TABLES
from mdm.io import read_csv, write_csv
from mdm.pipeline import run


class HospitalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        generate_hospital(self.root,size=12)
        self.first=run(self.root)

    def test_eight_relations_and_no_automatic_allergy_validation(self):
        self.assertEqual(set(self.first['related']),set(RELATED_TABLES))
        self.assertTrue(self.first['related']['sejours.csv'])
        self.assertTrue(self.first['related']['equipements.csv'])
        self.assertEqual({r['validation_status'] for r in allergy_rows(self.first)},{'a_valider'})
        self.assertTrue(all(r['master_id'] for rows in self.first['related'].values() for r in rows))

    def test_attribute_selection_is_applied_with_provenance_in_next_version(self):
        conflict=next(r for r in attribute_conflicts(self.first) if r['field']=='given_names')
        candidate=conflict['candidates'][-1]
        before=store.load_run(self.root,self.first['run_id'])
        store.attribute_review(self.root,self.first['run_id'],conflict['case_id'],'SELECT_VALUE','STEWARD','Valeur corroborée dans la source',candidate)
        second=run(self.root,base_run=self.first['run_id'])
        master=next(r for r in second['masters'] if r['master_id']==conflict['master_id'])
        proof=next(r for r in second['provenance'] if r['master_id']==master['master_id'] and r['field']==conflict['field'])
        self.assertEqual(master['given_names'],candidate['value'])
        self.assertEqual(proof['selected_source'],candidate['source'])
        self.assertEqual(proof['policy'],'HUMAN_SELECTED_VALUE')
        self.assertEqual(proof['resolution_status'],'RESOLVED')
        self.assertEqual(store.load_run(self.root,self.first['run_id']),before)
        self.assertTrue(store.verify(self.root))

    def test_unobserved_attribute_value_is_refused(self):
        conflict=attribute_conflicts(self.first)[0]
        with self.assertRaises(ValueError):
            store.attribute_review(self.root,self.first['run_id'],conflict['case_id'],'SELECT_VALUE','S','test',{'value':'inventée'})

    def test_clinical_decision_survives_reconciliation_without_affecting_identity(self):
        row=self.first['related']['allergies.csv'][0]
        store.clinical_review(self.root,self.first['run_id'],row['assertion_id'],'CONFIRM','DEMO_MEDECIN','Médecin','Déclaration vérifiée pour la démonstration')
        live=store.extra_decisions(self.root,self.first['run_id'],'clinical')
        self.assertEqual(next(r for r in allergy_rows(self.first,live) if r['assertion_id']==row['assertion_id'])['validation_status'],'confirmee')
        second=run(self.root,base_run=self.first['run_id'])
        self.assertEqual(self.first['pairs'],second['pairs'])
        self.assertEqual(self.first['xrefs'],second['xrefs'])
        self.assertEqual(next(r for r in second['related']['allergies.csv'] if r['assertion_id']==row['assertion_id'])['validation_status'],'confirmee')
        self.assertEqual(next(r for r in second['related']['allergies.csv'] if r['assertion_id']==row['assertion_id'])['source_record']['validation_status'],'a_valider')
        self.assertEqual(store.load_run(self.root,self.first['run_id'])['related']['allergies.csv'][0]['validation_status'],'a_valider')
        self.assertTrue(store.verify(self.root))

    def test_modified_assertion_does_not_inherit_clinical_validation(self):
        row=self.first['related']['allergies.csv'][0]
        store.clinical_review(self.root,self.first['run_id'],row['assertion_id'],'CONFIRM','M','Médecin','test')
        path=self.root/'related/allergies.csv'
        rows=read_csv(path)
        rows[0]['substance']='Autre substance déclarée'
        write_csv(path,rows)
        second=run(self.root,base_run=self.first['run_id'])
        self.assertEqual(second['related']['allergies.csv'][0]['validation_status'],'a_valider')

    def test_clinical_validation_requires_role_and_justification(self):
        row=self.first['related']['allergies.csv'][0]
        with self.assertRaises(ValueError):
            store.clinical_review(self.root,self.first['run_id'],row['assertion_id'],'CONFIRM','M','Data Steward','test')
        with self.assertRaises(ValueError):
            store.clinical_review(self.root,self.first['run_id'],row['assertion_id'],'CONFIRM','M','Médecin','')

    def test_preview_does_not_create_a_version_or_audit_event(self):
        before=store.audit_log(self.root)
        proposal=run(self.root,base_run=self.first['run_id'],persist=False)
        self.assertEqual(len(store.list_runs(self.root)),1)
        self.assertEqual(store.audit_log(self.root),before)
        self.assertEqual(proposal['xrefs'],self.first['xrefs'])

    def test_clinical_audit_detects_tampering(self):
        row=self.first['related']['allergies.csv'][0]
        store.clinical_review(self.root,self.first['run_id'],row['assertion_id'],'REQUEST_INFO','M','Médecin','test')
        with closing(sqlite3.connect(self.root/'mdm.sqlite3')) as db:
            with db: db.execute("UPDATE clinical_decisions SET decision='CONFIRM'")
        self.assertFalse(store.verify(self.root))

    def test_scenarios_preserve_population_but_change_quality(self):
        other=self.root/'other'
        generate_hospital(other,size=12,scenario='S3_30pct')
        degraded=run(other)
        self.assertEqual(len(degraded['xrefs']),len(self.first['xrefs']))
        patient=lambda p:next(q for q in p['quality'] if q['domain']=='patient')
        self.assertLess(patient(degraded)['validity'],patient(self.first)['validity'])

    def test_stock_alerts_use_dates_and_quantities_only(self):
        self.assertEqual(stock_flags({'expiry_date':'2026-10-01','quantity':'5','reorder_level':'10'},date(2026,11,3)),{'expired':True,'low_stock':True,'invalid_expiry':False,'invalid_quantity':False})

    def test_invalid_stock_is_not_reported_as_valid(self):
        result=stock_flags({'expiry_date':'2026-02-30','quantity':'NaN'})
        self.assertTrue(result['invalid_expiry'])
        self.assertTrue(result['invalid_quantity'])


if __name__=='__main__': unittest.main()
