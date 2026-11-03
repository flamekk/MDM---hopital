# Historique des améliorations

## Version Hôpital Al Amal — 3 novembre 2026

- Restauration des six onglets du MDM patient initial, communs aux trois domaines, et des scénarios S1/S2/S3.
- Nouvelle interface claire, fiches détaillées, comparaison côte à côte et vocabulaire hospitalier.
- Arbitrage des attributs appliqué au Golden Record de la version suivante, avec la valeur et la source réellement choisies.
- Réconciliation en deux étapes : aperçu sans écriture puis publication d’un snapshot.
- Allergies structurées et sourcées, revue clinique déclarative indépendante des identités et invalidation d’une validation lorsque la déclaration source change.
- Séjours et contacts patients, affectations/formations/gardes du personnel, lots et parc biomédical.
- Huit tables liées et export de leurs données dans chaque version.
- Tests métier et interface étendus aux parcours d’arbitrage, de déclaration clinique et de changement de scénario.

## Version scolaire enrichie — 2 novembre 2026

Point de départ : dépôt `flamekk/MDM---hopital`, commit `070c381`.

- Extension du prototype patient aux domaines personnel et produits hospitaliers.
- Ajout d’un moteur reproductible depuis les CSV bruts : ingestion, contrôles, normalisation, blocking, matching et construction des maîtres.
- Comparaison des méthodes exacte, pondérée Jaro-Winkler et probabiliste illustrative, avec évaluation séparée.
- Contrôles de cohérence des groupes et respect des rejets humains, y compris par transitivité.
- Revue justifiée, snapshots SQLite, provenance par attribut, alternatives et lignage entre versions.
- Interface française de huit sections, exports CSV et API locale de consultation.
- Relations sourcées pour allergies, affectations et stocks.
- Projection PostgreSQL : schéma, export SQL et procédure Docker ; serveur non vérifié dans la session locale.
- Tests locaux : 25 réussis ; workflow GitHub Actions ajouté pour leur exécution sur les prochains envois.
- Guide de réalisation, rapport, dictionnaire, résultats exécutés, plan de soutenance et explication détaillée pour le professeur.

La base patient et son notebook sont conservés ; l’ancienne interface est disponible dans `legacy_app.py`. Les résultats complets de travail sont générés localement et exclus de Git ; des petits exports mesurés sont fournis dans `examples/`.
