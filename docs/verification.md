# Vérifications réalisées

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
