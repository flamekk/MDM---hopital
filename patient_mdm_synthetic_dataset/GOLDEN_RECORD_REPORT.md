# Golden Record — consolidation conservatrice

## Objectif
Transformer les décisions de matching en clusters de patients et en fiches Golden Record explicables, sans utiliser la vérité terrain pour former les clusters.

## Garde-fous appliqués
- Seuls les `MATCH_AUTO` du baseline ont servi à proposer des fusions.
- Les arêtes sont traitées par score décroissant.
- Une fusion est refusée si elle introduit deux identifiants du même système dans un cluster.
- Une fusion est refusée si les clusters ont des dates de naissance non vides contradictoires.
- Les cas `REVIEW` ne sont pas fusionnés automatiquement.
- Tous les enregistrements restent présents dans `cluster_membership.csv`, y compris les singletons.

## Survivance des attributs
Pour chaque attribut non vide, la valeur est choisie selon : priorité de source documentée, complétude du record, date de mise à jour/création, puis valeur lexicographique comme départage déterministe. Cette priorité est un choix expérimental à valider avec les responsables métier.
Les valeurs brutes et standardisées restent inchangées. `golden_record_lineage.csv` trace la source et l'identifiant local ayant fourni chaque valeur retenue.

## Fichiers produits dans chaque dossier `*/golden_record/`
- `golden_records.csv` : une ligne par Golden Record.
- `cluster_membership.csv` : rattachement de chaque enregistrement source à un cluster.
- `golden_record_lineage.csv` : provenance par attribut.
- `attribute_conflicts_review_queue.csv` : valeurs non vides contradictoires et proposition de mise en revue.
- `cluster_merge_rejections.csv` : fusions candidates refusées par les garde-fous.

## Résultats

### Résumé de consolidation

| scenario   |   input_identity_records |   golden_records |   multi_source_clusters |   singleton_clusters |   auto_match_edges_considered |   edges_accepted_or_already_connected |   cluster_merge_rejections |   attribute_conflict_rows |   conflicts_flagged_for_review |
|:-----------|-------------------------:|-----------------:|------------------------:|---------------------:|------------------------------:|--------------------------------------:|---------------------------:|--------------------------:|-------------------------------:|
| S1_5pct    |                     6889 |             2759 |                    1864 |                  895 |                          7750 |                                  7405 |                        345 |                       204 |                              0 |
| S2_15pct   |                     6889 |             2941 |                    1832 |                 1109 |                          7282 |                                  6953 |                        329 |                       481 |                             14 |
| S3_30pct   |                     6889 |             3224 |                    1785 |                 1439 |                          6491 |                                  6212 |                        279 |                       744 |                             36 |

### Évaluation après construction des clusters

| scenario   |   pairwise_cluster_precision |   pairwise_cluster_recall |   pairwise_cluster_f1 |   true_positive_pairs |   false_positive_pairs |   false_negative_pairs | evaluation_used_truth_only_after_clusters_saved   |
|:-----------|-----------------------------:|--------------------------:|----------------------:|----------------------:|-----------------------:|-----------------------:|:--------------------------------------------------|
| S1_5pct    |                       1      |                    0.8517 |                0.9199 |                  7406 |                      0 |                   1290 | True                                              |
| S2_15pct   |                       1      |                    0.803  |                0.8907 |                  6983 |                      0 |                   1713 | True                                              |
| S3_30pct   |                       0.9984 |                    0.7242 |                0.8395 |                  6298 |                     10 |                   2398 | True                                              |

## Limites
- La priorité des sources est provisoire et doit être validée par les métiers.
- Le matching automatique n'est pas une preuve d'identité. Les décisions de revue restent non fusionnées.
- L'évaluation pairwise peut être coûteuse, mais elle est calculée ici sur le jeu synthétique de taille limitée.
- Le Golden Record est un artefact de démonstration; il ne doit pas être utilisé en contexte clinique réel sans validation, contrôles et gouvernance.
