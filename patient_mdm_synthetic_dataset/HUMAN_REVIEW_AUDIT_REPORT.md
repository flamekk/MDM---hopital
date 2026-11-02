# File de validation humaine et audit MDM

La file est générée uniquement à partir des sorties de matching et des conflits des Golden Records. Aucune vérité terrain n'est utilisée pour construire les cas opérationnels.

## Volumes initiaux

| scenario   |   pair_review_cases |   attribute_conflict_cases |   conflicts_pending |   conflicts_monitor_only |   pair_cases_initially_pending |
|:-----------|--------------------:|---------------------------:|--------------------:|-------------------------:|-------------------------------:|
| S1_5pct    |                 978 |                        204 |                   0 |                      204 |                            978 |
| S2_15pct   |                2062 |                        481 |                  14 |                      467 |                           2062 |
| S3_30pct   |                3631 |                        744 |                  36 |                      708 |                           3631 |

## Fichiers
- `human_review_queue.csv` : une ligne par paire candidate classée REVIEW.
- `attribute_conflict_review_queue.csv` : conflits des Golden Records. Les cas marqués `PENDING` sont à examiner; `MONITOR` est une alerte informative selon les règles du prototype.
- `mdm_audit_log.csv` : modèle vide de journal d'audit append-only.
- `REVIEW_WORKFLOW.md` : étapes, décisions permises et contrôles.
- `review_queue_summary.csv` : synthèse des volumes.

## Important
Aucune décision humaine n'a été simulée. Tous les cas de matching démarrent en `PENDING`. Le journal d'audit est vide tant qu'aucun reviewer n'a réellement pris de décision. Les CSV ne fournissent pas à eux seuls une interface de validation multi-utilisateur.
