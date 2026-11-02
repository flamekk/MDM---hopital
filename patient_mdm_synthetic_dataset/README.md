# Patient MDM — jeu de données synthétiques

## Contenu
- `S1_5pct/`, `S2_15pct/`, `S3_30pct/` : les cinq systèmes sources, chacun avec un fichier d'identité et un fichier opérationnel, plus un rapport qualité.
- `ground_truth.csv` : correspondance indépendante entre chaque dossier source et son identité fictive de référence. Réservé à l'évaluation, jamais comme entrée du matching.
- `reference_population_private.csv` : population fictive de génération; à garder hors des entrées du matching.
- `source_metadata.csv` : description des systèmes et profils de qualité.
- `generation_config.json` : paramètres et graine de génération.
- `validation_report.csv` : contrôles automatiques.

## Sources
ADMISSION_SYS, LAB_SYS, RADIOLOGY_SYS, CONSULTATION_SYS, BILLING_SYS.

## Important
Toutes les données sont fictives. Aucun dossier réel n'est utilisé.
Les scénarios partagent les mêmes identités et la même répartition des dossiers entre sources; les perturbations varient selon le scénario. Les taux observés peuvent dépasser les taux cibles parce que les perturbations propres aux sources et les changements temporels s'ajoutent à la perturbation générale.

## Limites et transparence
Les identifiants `PERSON-*` et `SOLO-*` ne figurent pas dans les fichiers sources. Les identifiants locaux sont indépendants par système. Les anomalies sont synthétiques et ne prétendent pas représenter une clinique réelle.

- `hard_nonmatch_evaluation.csv` : paires d'évaluation difficiles (homonymes synthétiques), à ne pas fournir au matching.


## Étape Golden Record
Consulter `GOLDEN_RECORD_REPORT.md` pour la consolidation, les règles de survivance, la provenance et l'évaluation. Les résultats détaillés sont dans chaque dossier de scénario `golden_record/`.

## Validation humaine et audit
Voir `HUMAN_REVIEW_AUDIT_REPORT.md` et `REVIEW_WORKFLOW.md`. Les files de revue et le journal d'audit sont des prototypes batch; aucune décision de reviewer n'a été inventée.
