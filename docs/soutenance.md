# Déroulé de soutenance — proposition de 10 minutes

Lire aussi [l’explication détaillée pour le professeur](explication_professeur.md) : discours d’introduction, changements réalisés, démonstration commentée et questions/réponses.

| Temps | Message | Démonstration / preuve |
| --- | --- | --- |
| 0:00–1:00 | Problème hospitalier et trois domaines | Donner un exemple de doublon et de conditionnement contradictoire |
| 1:00–2:00 | Architecture et séparation identité/transactions | Catalogue & modèle ; allergies, affectations, stocks |
| 2:00–3:00 | Qualité : ne pas inventer une valeur manquante | Montrer une date impossible et son anomalie |
| 3:00–4:30 | Trois méthodes et blocking | Comparer les mesures exécutées, expliquer le rappel global |
| 4:30–6:00 | Revue humaine contrôlée | Saisir une décision et sa justification ; exécuter une nouvelle version |
| 6:00–7:00 | Provenance et réversibilité | Ouvrir une fiche maître et une ancienne version |
| 7:00–8:00 | Tests et intégrité | Présenter les tests de transitivité, rejet et altération |
| 8:00–9:00 | Résultats et limites | Lire le bilan mesuré ; expliquer le score non calibré |
| 9:00–10:00 | Perspectives et bilan des contributions | PostgreSQL, corpus indépendant, authentification et connecteurs |

Répartition possible pour trois membres : 1) cadrage, sources et qualité ; 2) modèle, matching et évaluation ; 3) interface, gouvernance, tests et limites. Répartir les questions de façon à ce que chacun sache expliquer une fusion et une non-fusion.

Questions à préparer :

- Pourquoi ne pas fusionner deux patients qui ont seulement le même nom ?
- Comment une chaîne A–B–C peut-elle créer une erreur alors que chaque lien paraît plausible ?
- Pourquoi les allergies sont-elles exclues des critères d’identité ?
- Quelle différence entre le taux de doublons et une précision mesurée avec une vérité terrain ?
- Pourquoi une complétude après nettoyage peut-elle être plus faible ?
- Quand un identifiant maître change-t-il et comment informer un consommateur ?
- Quelles décisions relèvent du Data Owner, du Steward et de l’équipe technique ?
- Pourquoi SQLite aujourd’hui et PostgreSQL comme étape distincte ?
- Quelle limite reste-t-il à une chaîne de hachage stockée sur le même ordinateur ?

Avant la présentation, lancer les tests, vérifier les ports disponibles et préparer une copie du dossier de démonstration. Ne pas annoncer une validation du formateur, une conformité réglementaire ou des performances sur un hôpital réel qui n’ont pas été obtenues.
