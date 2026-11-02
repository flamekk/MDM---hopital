# Baseline de rapprochement des patients

## Méthode
Le baseline compare uniquement les identités standardisées des cinq systèmes, et uniquement entre systèmes distincts.
Blocking : date de naissance + nom, téléphone, ou prénom + nom. Les paires candidates sont scorées sur la date de naissance, prénom, nom, téléphone, sexe et adresse si disponible.
Décisions : `MATCH_AUTO`, `REVIEW`, `NON_MATCH`. Les seuils et limites sont documentés dans `MATCHING_RULES.md`.

## Résultats par scénario
| scenario   |   source_identity_records |   candidate_pairs |   match_auto |   review |   non_match | blocking_method                     | input_files                     | truth_used_during_matching   |
|:-----------|--------------------------:|------------------:|-------------:|---------:|------------:|:------------------------------------|:--------------------------------|:-----------------------------|
| S1_5pct    |                      6889 |             28953 |         7750 |      978 |       20225 | DOB+last name OR phone OR full name | standardized identity CSVs only | False                        |
| S2_15pct   |                      6889 |             28217 |         7282 |     2062 |       18873 | DOB+last name OR phone OR full name | standardized identity CSVs only | False                        |
| S3_30pct   |                      6889 |             27128 |         6491 |     3631 |       17006 | DOB+last name OR phone OR full name | standardized identity CSVs only | False                        |

## Évaluation postérieure au matching
La vérité terrain a été chargée seulement après la génération des paires et décisions. Les métriques mesurent la précision/rappel des `MATCH_AUTO` sur toutes les paires positives inter-systèmes présentes dans la vérité terrain.
| scenario   |   auto_match_true_positives |   auto_match_false_positives |   auto_match_precision |   auto_match_recall_all_cross_source_truth_pairs |   auto_match_f1 |   true_pairs_sent_to_review |   false_pairs_sent_to_review |   total_cross_source_truth_pairs |   hard_nonmatch_pairs_in_eval_file |   hard_nonmatch_false_auto_matches | evaluation_note                                                                                                             |
|:-----------|----------------------------:|-----------------------------:|-----------------------:|-------------------------------------------------:|----------------:|----------------------------:|-----------------------------:|---------------------------------:|-----------------------------------:|-----------------------------------:|:----------------------------------------------------------------------------------------------------------------------------|
| S1_5pct    |                        7747 |                            3 |                 0.9996 |                                           0.9088 |          0.9521 |                         590 |                          388 |                             8524 |                                 75 |                                  0 | Ground truth and hard homonyms used only after candidate predictions were written; same-source homonyms excluded by design. |
| S2_15pct   |                        7279 |                            3 |                 0.9996 |                                           0.8539 |          0.921  |                        1060 |                         1002 |                             8524 |                                 75 |                                  0 | Ground truth and hard homonyms used only after candidate predictions were written; same-source homonyms excluded by design. |
| S3_30pct   |                        6478 |                           13 |                 0.998  |                                           0.76   |          0.8629 |                        1855 |                         1776 |                             8524 |                                 75 |                                  0 | Ground truth and hard homonyms used only after candidate predictions were written; same-source homonyms excluded by design. |

## Limites à garder en tête
- Baseline déterministe, sans apprentissage automatique ni calibration probabiliste.
- Les doublons intra-système sont exclus pour cette première phase.
- Le blocking peut manquer des paires si tous les attributs de blocking sont perturbés ou absents.
- Le score est un indicateur explicable, pas une preuve d'identité.
- Le jeu des homonymes difficiles est actuellement constitué de paires au sein d'un même système; il ne permet donc pas de mesurer directement les faux matchs inter-systèmes de ce baseline.
- Avant d'utiliser le Golden Record, il faudra traiter les groupes/clusterings de correspondances, les conflits d'attributs, la provenance et les validations humaines.