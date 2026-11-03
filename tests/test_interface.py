import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from mdm.hospital import generate_hospital
from mdm.pipeline import run
from mdm import store
from ui.workflow import TABS


class InterfaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        generate_hospital(self.root,size=12)
        self.first=run(self.root)

    def app(self):
        from streamlit.testing.v1 import AppTest
        return AppTest.from_file(str(Path(__file__).resolve().parents[1]/'app.py'),default_timeout=60).run()

    def widget(self,items,key):
        return next(item for item in items if item.key==key)

    def publish(self,app):
        self.widget(app.button,'prepare_reconciliation').click().run()
        self.assertFalse(app.exception)
        self.widget(app.button,'publish_reconciliation').click().run()
        self.assertFalse(app.exception)

    def test_same_original_workflow_and_hospital_views_for_three_domains(self):
        with patch.dict(os.environ,{'MDM_WORKSPACE':str(self.root)}):
            app=self.app()
            self.assertFalse(app.exception)
            for domain in ['patient','personnel','produit']:
                self.widget(app.sidebar.radio,'mdm_domain').set_value(domain).run()
                self.assertFalse(app.exception,domain)
                self.assertEqual([t.label for t in app.tabs if t.label in TABS],TABS)
                for section in ['Vue hospitalière','Qualité & méthodes','Catalogue & aide','Référentiel MDM']:
                    self.widget(app.sidebar.radio,'workspace_section').set_value(section).run()
                    self.assertFalse(app.exception,f'{domain}/{section}')

    def test_review_saves_then_publishes_new_version(self):
        with patch.dict(os.environ,{'MDM_WORKSPACE':str(self.root)}):
            app=self.app()
            self.widget(app.sidebar.text_input,'reviewer').set_value('STEWARD_TEST').run()
            self.widget(app.selectbox,'pair_decision').set_value('ESCALATE')
            self.widget(app.text_area,'pair_comment').set_value('Paire à approfondir pendant le test')
            next(b for b in app.button if b.label=='Enregistrer la décision').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(store.decisions(self.root,self.first['run_id'])),1)
            self.publish(app)
            self.assertEqual(len(store.list_runs(self.root)),2)
            second=store.load_run(self.root)
            self.assertEqual(second['parent_run'],self.first['run_id'])
            self.assertEqual(len(second['applied_decisions']),1)

    def test_attribute_arbitration_is_published(self):
        with patch.dict(os.environ,{'MDM_WORKSPACE':str(self.root)}):
            app=self.app()
            self.widget(app.sidebar.text_input,'reviewer').set_value('STEWARD_TEST').run()
            self.widget(app.text_area,'attribute_comment').set_value('Valeur source contrôlée')
            next(b for b in app.button if b.label=='Enregistrer l’arbitrage').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(store.extra_decisions(self.root,self.first['run_id'],'attribute')),1)
            self.publish(app)
            self.assertTrue(any(r.get('policy')=='HUMAN_SELECTED_VALUE' for r in store.load_run(self.root)['provenance']))

    def test_clinical_decision_is_separate_from_identity_review(self):
        with patch.dict(os.environ,{'MDM_WORKSPACE':str(self.root)}):
            app=self.app()
            self.widget(app.sidebar.text_input,'reviewer').set_value('MEDECIN_DEMO').run()
            self.widget(app.sidebar.radio,'workspace_section').set_value('Vue hospitalière').run()
            self.widget(app.text_area,'clinical_comment').set_value('Déclaration documentée dans la démonstration')
            next(b for b in app.button if b.label=='Enregistrer la validation clinique').click().run()
            self.assertFalse(app.exception)
            self.assertEqual(len(store.extra_decisions(self.root,self.first['run_id'],'clinical')),1)
            self.assertEqual(store.decisions(self.root,self.first['run_id']),{})

    def test_scenario_switch_loads_a_distinct_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            ids={}
            for scenario in ['S1_5pct','S2_15pct']:
                generate_hospital(base/scenario,size=12,scenario=scenario)
                ids[scenario]=run(base/scenario)['run_id']
            with patch.dict(os.environ,{'MDM_WORKSPACE':str(base)}):
                app=self.app()
                self.assertFalse(app.exception)
                self.widget(app.sidebar.selectbox,'mdm_scenario').set_value('S2_15pct').run()
                self.assertFalse(app.exception)
                version=next(s for s in app.sidebar.selectbox if s.label=='Version du référentiel')
                self.assertEqual(version.value,ids['S2_15pct'])


if __name__=='__main__': unittest.main()
