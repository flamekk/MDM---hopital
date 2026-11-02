# Rapport d'audit initial — Patient MDM

## Périmètre
Audit des trois scénarios (`S1_5pct`, `S2_15pct`, `S3_30pct`) pour les cinq systèmes sources, sans effectuer de matching. Les données sont synthétiques.

## Résultats globaux
- Dossiers d'identité par scénario : **6,889**
- Enregistrements opérationnels par scénario : **8,944**
- Contrôles critiques échoués : **0**
- Avertissements : **0**
- Clés de vérité terrain dupliquées : **0**

## Contrôles
1. Présence des fichiers et conformité des schémas.
2. Unicité et présence des identifiants locaux.
3. Intégrité référentielle des fichiers opérationnels.
4. Unicité des identifiants d'événements.
5. Cohérence des volumes entre scénarios.
6. Couverture de la vérité terrain.
7. Valeurs manquantes et formats des dates de naissance.
8. Taux d'anomalies observés.

## Interprétation importante
Les anomalies de format de date (`YYYY-MM-DD` et `DD/MM/YYYY`) sont intentionnelles pour tester la standardisation. Les valeurs manquantes sont également attendues. Un dossier dupliqué est une anomalie métier intentionnelle et ne signifie pas que les identifiants locaux sont dupliqués : chaque enregistrement conserve un identifiant local distinct.

## Fichiers produits
- `audit_schema_and_counts.csv`
- `audit_event_integrity.csv`
- `audit_data_quality_metrics.csv`
- `audit_ground_truth_summary.csv`
- `audit_findings.csv`

## Recommandation
Lire `audit_findings.csv` et les métriques qualité avant d'entamer la standardisation et le matching. Le ground truth et la population privée restent réservés à l'évaluation, jamais aux entrées du matching.
