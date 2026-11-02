# Validation humaine et audit MDM

## Objectif
Fournir une file de travail contrôlée pour les cas incertains de matching et les conflits d'attributs. Les fichiers sont des files de revue, pas une interface interactive : les décisions doivent être saisies par un reviewer autorisé puis validées par un processus d'application.

## Files créées
- `human_review_queue.csv` : paires classées `REVIEW`, avec score et signaux comparatifs.
- `attribute_conflict_review_queue.csv` : conflits d'attributs remontés par les Golden Records.
- `mdm_audit_log.csv` : journal append-only vide, avec schéma des événements attendus.
- `REVIEW_WORKFLOW.md` : cycle de vie, valeurs permises et règles de sécurité.
- `review_queue_summary.csv` : volume par scénario et statut initial.

## Cycle de vie recommandé
1. `PENDING` : cas en attente.
2. Le reviewer ouvre les deux enregistrements sources, vérifie les attributs et consulte la provenance.
3. Pour les paires : choisir `CONFIRM_MATCH`, `REJECT_MATCH` ou `ESCALATE`.
4. Pour les conflits : choisir `ACCEPT_SELECTED_VALUE`, `SELECT_ALTERNATIVE_VALUE` ou `ESCALATE`.
5. Saisir `reviewer_id`, `reviewed_at` (UTC), et un commentaire motivant la décision.
6. Un processus d'application contrôlé met à jour les liens/clusters et écrit un événement dans `mdm_audit_log.csv`. Ne pas modifier directement les fichiers sources.
7. Les événements d'audit sont append-only : ne pas supprimer ni réécrire les décisions précédentes; corriger en ajoutant un nouvel événement qui référence la décision antérieure.

## Contrôles obligatoires
- Aucun auto-validation sur les cas `PENDING`.
- Séparation des rôles : le reviewer ne modifie pas les données sources.
- Toute décision doit avoir un identifiant de reviewer, horodatage UTC et justification.
- Les changements de Golden Record doivent conserver la provenance avant/après.
- Les désaccords sensibles (date de naissance contradictoire, fusion à fort impact) doivent être escaladés.
- La vérité terrain synthétique n'est jamais exposée dans la file opérationnelle ni utilisée pour décider les cas.

## Valeurs de décision
- Paire : `CONFIRM_MATCH`, `REJECT_MATCH`, `ESCALATE`.
- Conflit : `ACCEPT_SELECTED_VALUE`, `SELECT_ALTERNATIVE_VALUE`, `ESCALATE`.
- Statut de file : `PENDING`, `IN_REVIEW`, `RESOLVED`, `ESCALATED`, `MONITOR`.

## Limites
Les CSV constituent un prototype batch auditable, pas une application multi-utilisateur. Le journal est un modèle vide à remplir par le processus d'application. Un véritable déploiement nécessiterait authentification, autorisation, verrouillage concurrent, stockage transactionnel et traçabilité inviolable.
