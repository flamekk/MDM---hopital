"""Évaluation séparée : ce module seul lit evaluation/truth.csv."""
from collections import Counter
from itertools import combinations
from .io import read_csv


def evaluate(path, rows, pairs, xrefs):
    labels = {(r['domain'], r['source'], r['local_id']): r['entity_id'] for r in read_csv(path)}
    truth = {r['rid']: labels.get((r['domain'], r['source'], r['local_id'])) for r in rows}
    if any(v is None for v in truth.values()):
        raise ValueError("Vérité terrain incomplète : évaluation refusée.")
    population = Counter(truth.values())
    true_pairs = sum(n * (n - 1) // 2 for n in population.values())
    candidate_true = sum(truth[p['a']] == truth[p['b']] for p in pairs)
    tp = sum(p['decision'] == 'AUTO' and truth[p['a']] == truth[p['b']] for p in pairs)
    fp = sum(p['decision'] == 'AUTO' and truth[p['a']] != truth[p['b']] for p in pairs)
    clusters = {}
    for r in xrefs:
        clusters.setdefault(r['master_id'], []).append(r['rid'])
    cluster_tp = cluster_fp = 0
    for members in clusters.values():
        counts = Counter(truth[r] for r in members)
        good = sum(n * (n - 1) // 2 for n in counts.values())
        cluster_tp += good
        cluster_fp += len(members) * (len(members) - 1) // 2 - good
    def ratio(a, b):
        return a / b if b else None
    return dict(true_pairs_total=true_pairs, candidate_true_pairs=candidate_true,
                blocking_recall=ratio(candidate_true, true_pairs),
                automatic_tp=tp, automatic_fp=fp, automatic_precision=ratio(tp, tp+fp),
                automatic_global_recall=ratio(tp, true_pairs),
                review_cases=sum(p['decision'] == 'REVIEW' for p in pairs),
                cluster_true_links=cluster_tp, cluster_false_links=cluster_fp,
                cluster_precision=ratio(cluster_tp, cluster_tp+cluster_fp), cluster_global_recall=ratio(cluster_tp, true_pairs),
                scope="jeu synthétique complet, descriptif ; aucun réglage sur ces étiquettes")
