# Vérifications réalisées

## Hôpital Al Amal — 3 novembre 2026

- **39 tests réussis** : les six onglets du projet patient sont présents dans chacun des trois domaines ; les cinq tests d’interface couvrent aussi les arbitrages, la publication et la revue des déclarations d’allergies.
- La préparation de réconciliation ne crée ni snapshot ni événement de publication. L’arbitrage d’un attribut conserve le candidat et sa source ; une validation d’allergie ne modifie ni les paires ni les correspondances d’identité.
- Une modification de la déclaration source empêche la reprise de sa validation précédente. La copie source brute reste conservée dans `source_record`.
- Trois scénarios de 459 identités : S1 produit 183 maîtres, S2 en produit 251 et S3 en produit 349 avant décisions humaines.
- Huit tables rattachées : 16 déclarations d’allergies, 48 séjours, 24 contacts désignés, 48 affectations, 48 formations, 48 gardes, 48 lignes de stock et 8 équipements dans le jeu initial S1.
- Les données de travail précédentes et l’interface `legacy_app.py` sont conservées. Le nouveau jeu utilise `workspace_hospital`.
- Export SQL PostgreSQL généré à partir du snapshot hospitalier ; exécution serveur toujours distincte et non vérifiée dans cette session.

## Première version enrichie — 2 novembre 2026

Vérifications locales du 2 novembre 2026, Python 3.13, versions des paquets dans `requirements-lock.txt`.

| Contrôle | Résultat |
| --- | --- |
| Tests automatisés | 25 tests réussis : normalisation, matching, transitivité, rejets, conservation des versions, absence de fuite de vérité, audit et interface |
| Navigation Streamlit | Huit sections exécutées par AppTest, sans exception |
| Parcours de revue | Décision justifiée persistée puis reprise dans une nouvelle version lors du test d’interface |
| Démonstration des trois domaines | 11 tables, 459 identités, 183 maîtres, 42 anomalies ; détails dans le bilan mesuré |
| Données patients historiques, scénario S1 | 6 889 identités brutes retraitées ; 2 662 maîtres ; 1 389 paires en revue avec la méthode pondérée |
| Évaluation historique pondérée | Précision auto 100 %, rappel auto global 89,37 %, rappel blocking 99,84 %, aucun faux lien de cluster mesuré sur ce jeu synthétique |
| HTTP tableau de bord | Réponse 200 sur 127.0.0.1:8501 |
| API de consultation | Santé ok, intégrité vraie ; route maîtres retourne 183 fiches |
| Audit | Empreintes des snapshots et chaîne d’événements vérifiées |
| Conservation des sources initiales | Aucun changement Git dans les données historiques, le notebook, reconciliation.py ou les tests initiaux |
| Aperçu visuel | Page de pilotage inspectée dans le navigateur intégré ; image dans `docs/images/tableau_de_bord.jpg` |
| PostgreSQL | Schéma et SQL générés ; exécution serveur non vérifiée car Docker Desktop ne fonctionne pas dans la session |

Commande de tests :

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Le moteur AppTest doit disposer des permissions locales normales de Python. Dans la session d’exécution restreinte utilisée pour construire le projet, les tests ont été lancés avec les permissions locales nécessaires et les temporaires placés dans le dossier `tmp` du projet. Cela ne nécessite aucune modification des permissions de votre machine pour l’usage normal.

Les chiffres historiques sont distincts de la petite démo des trois domaines. Ces deux jeux sont synthétiques. Les résultats ne prouvent aucune performance sur des données hospitalières réelles.
