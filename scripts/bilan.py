"""Génère un bilan académique uniquement depuis une exécution vérifiée."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from mdm import store


def build(root, project):
    if not store.verify(root):
        raise ValueError('Journal altéré : bilan refusé.')
    p = store.load_run(root)
    def fmt(value):
        return 'non définie' if value is None else f'{value:.2%}'
    lines = ['# Résultats mesurés du prototype', '',
             f"Version : `{p['run_id']}`. Exécutée le {p['created_at']} (UTC). Règles {p['rules_version']}, méthode {p['method']}.", '',
             f"{len(p['catalogue'])} tables sources, {len(p['xrefs'])} identités locales, {len(p['masters'])} fiches maîtres, {len(p['issues'])} anomalies.", '',
             '| Domaine | Identités sources | Maîtres | Paires en revue |', '| --- | ---: | ---: | ---: |']
    for d in ('patient', 'personnel', 'produit'):
        lines.append(f"| {d} | {sum(r['domain']==d for r in p['xrefs'])} | {sum(r['domain']==d for r in p['masters'])} | {sum(r['domain']==d and r['decision']=='REVIEW' for r in p['pairs'])} |")
    lines += ['', '## Comparaison automatique, avant décisions humaines', '',
              '| Domaine | Méthode | Précision auto | Rappel auto global | Rappel blocking | Faux liens de cluster | Revue |',
              '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for r in p['metrics']:
        if r['stage'] == 'automatic_baseline':
            lines.append(f"| {r['domain']} | {r['method']} | {fmt(r['automatic_precision'])} | {fmt(r['automatic_global_recall'])} | {fmt(r['blocking_recall'])} | {r['cluster_false_links']} | {r['review_cases']} |")
    lines += ['', '## Qualité', '', '| Domaine | Complétude brute requise | Complétude valide | Validité des cellules fournies |', '| --- | ---: | ---: | ---: |']
    for q in p['quality']:
        lines.append(f"| {q['domain']} | {fmt(q['raw_completeness'])} | {fmt(q['valid_required_completeness'])} | {fmt(q['validity'])} |")
    lines += ['', '## Interprétation et limites', '',
              'Les chiffres proviennent du jeu synthétique déterministe. Ils ne mesurent pas la qualité d’un hôpital réel. Les contradictions injectées volontairement peuvent réduire le rappel : le moteur préfère conserver un fragment plutôt que fusionner des informations incompatibles.', '',
              'Les trois méthodes emploient les mêmes candidats. Le rappel global tient compte des vraies paires absentes du blocking. Les scores probabilistes reposent sur des paramètres illustratifs ; aucune calibration ni validation sur un test indépendant n’est annoncée.', '',
              'La vérité est lue après le matching par le module d’évaluation. Les tests vérifient qu’une modification des étiquettes ne modifie ni les paires, ni les maîtres, ni la provenance.', '',
              'Les contrôles de groupe peuvent refuser des liens automatiques pourtant corrects pris individuellement. La table distingue ainsi les décisions par paire et les faux liens réellement présents dans les groupes.', '',
              'PostgreSQL : schéma et export préparés. Son exécution doit être validée dans un serveur disponible ; le tableau de bord local utilise SQLite.', '',
              '## Empreintes des sources', '', '| Fichier | Lignes | SHA-256 |', '| --- | ---: | --- |']
    for r in p['manifest']:
        lines.append(f"| {r['path']} | {r['rows']} | `{r['sha256']}` |")
    docs, examples = project / 'docs', project / 'examples'
    docs.mkdir(exist_ok=True)
    examples.mkdir(exist_ok=True)
    (docs / 'resultats_mesures.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    source = root / 'runs' / p['run_id']
    for name in ('quality', 'catalogue', 'metrics', 'issues'):
        shutil.copyfile(source / f'{name}.csv', examples / f'{name}.csv')
    print(f"Bilan créé : {docs / 'resultats_mesures.md'}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--workspace', type=Path, default=Path('workspace'))
    args = parser.parse_args()
    build(args.workspace, Path(__file__).resolve().parents[1])
