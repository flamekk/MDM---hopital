import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from mdm.demo import generate
from mdm.pipeline import run
from mdm import store


class InterfaceTests(unittest.TestCase):
    def test_review_saves_then_publishes_new_version(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(root, size=12)
            first = run(root)
            with patch.dict(os.environ, {'MDM_WORKSPACE': tmp}):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
                app.sidebar.radio[0].set_value('Revue humaine').run()
                self.assertFalse(app.exception)
                if not app.text_input:
                    self.fail('La démo doit proposer un cas de revue.')
                app.text_input[0].set_value('STEWARD_TEST')
                app.text_area[0].set_value('Cas vérifié pendant le test de parcours')
                # Une escalade est une décision traçable et ne force aucune fusion.
                next(s for s in app.selectbox if s.label == 'Décision').set_value('ESCALATE')
                next(b for b in app.button if b.label == 'Enregistrer la décision').click().run()
                self.assertFalse(app.exception)
                self.assertEqual(len(store.decisions(root, first['run_id'])), 1)
                app.sidebar.button[0].click().run()
                self.assertFalse(app.exception)
                self.assertEqual(len(store.list_runs(root)), 2)
                second = store.load_run(root)
                self.assertEqual(second['parent_run'], first['run_id'])
                self.assertEqual(len(second['applied_decisions']), 1)

    def test_all_sections_render(self):
        from streamlit.testing.v1 import AppTest
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            generate(root, size=12)
            run(root)
            with patch.dict(os.environ, {'MDM_WORKSPACE': tmp}):
                app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=30).run()
                self.assertFalse(app.exception)
                for page in ['Sources & qualité', 'Référentiels', 'Revue humaine', 'Matching & évaluation', 'Catalogue & modèle', 'Historique & API', 'Parcours scolaire']:
                    app.sidebar.radio[0].set_value(page).run()
                    self.assertFalse(app.exception, f'Échec de la page {page}')


if __name__ == '__main__':
    unittest.main()
