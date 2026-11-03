# Résultats mesurés du prototype

Version : `2c4b3399-2585-4c37-b0c5-2d0e6f8bfb18`. Exécutée le 2026-11-03T13:00:44.518504+00:00 (UTC). Règles 2.0.1, méthode weighted.

11 tables sources, 459 identités locales, 183 fiches maîtres, 42 anomalies.

| Domaine | Identités sources | Maîtres | Paires en revue |
| --- | ---: | ---: | ---: |
| patient | 127 | 61 | 24 |
| personnel | 132 | 59 | 15 |
| produit | 200 | 63 | 157 |

## Comparaison automatique, avant décisions humaines

| Domaine | Méthode | Précision auto | Rappel auto global | Rappel blocking | Faux liens de cluster | Revue |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| patient | exact | 100.00% | 70.00% | 100.00% | 0 | 33 |
| patient | weighted | 100.00% | 78.18% | 100.00% | 0 | 24 |
| patient | probabilistic | 100.00% | 78.18% | 100.00% | 0 | 23 |
| personnel | exact | 100.00% | 72.50% | 100.00% | 0 | 26 |
| personnel | weighted | 100.00% | 81.67% | 100.00% | 0 | 15 |
| personnel | probabilistic | 100.00% | 81.67% | 100.00% | 0 | 13 |
| produit | exact | 100.00% | 84.76% | 100.00% | 0 | 160 |
| produit | weighted | 100.00% | 85.67% | 100.00% | 0 | 157 |
| produit | probabilistic | 100.00% | 85.67% | 100.00% | 0 | 157 |

## Qualité

| Domaine | Complétude brute requise | Complétude valide | Validité des cellules fournies |
| --- | ---: | ---: | ---: |
| patient | 100.00% | 98.69% | 97.90% |
| personnel | 100.00% | 100.00% | 98.24% |
| produit | 100.00% | 100.00% | 100.00% |

## Interprétation et limites

Les chiffres proviennent du jeu synthétique déterministe. Ils ne mesurent pas la qualité d’un hôpital réel. Les contradictions injectées volontairement peuvent réduire le rappel : le moteur préfère conserver un fragment plutôt que fusionner des informations incompatibles.

Les trois méthodes emploient les mêmes candidats. Le rappel global tient compte des vraies paires absentes du blocking. Les scores probabilistes reposent sur des paramètres illustratifs ; aucune calibration ni validation sur un test indépendant n’est annoncée.

La vérité est lue après le matching par le module d’évaluation. Les tests vérifient qu’une modification des étiquettes ne modifie ni les paires, ni les maîtres, ni la provenance.

Les contrôles de groupe peuvent refuser des liens automatiques pourtant corrects pris individuellement. La table distingue ainsi les décisions par paire et les faux liens réellement présents dans les groupes.

PostgreSQL : schéma et export préparés. Son exécution doit être validée dans un serveur disponible ; le tableau de bord local utilise SQLite.

## Empreintes des sources

| Fichier | Lignes | SHA-256 |
| --- | ---: | --- |
| sources/patient/admission.csv | 48 | `7457ca440ec8a69bac70a3c74b8a0000266d1ceb4a966a95449d9fc24c190d78` |
| sources/patient/dpi.csv | 48 | `05882f052bd62c74069c00406892cc32ae0e0803732e2450616a286413d75464` |
| sources/patient/labo.csv | 31 | `287d5d92de60181ec1188e04347b470ebb6658192f57ae947141b71d74be2b83` |
| sources/personnel/formation.csv | 36 | `7de73b435ba565f022a774b42904d10b704a8ad1bb410cf32bd524a3a1d0dcac` |
| sources/personnel/planning.csv | 48 | `be2ac8f760cb6787e955d4639e3c5a8d613d54b5df5b0294324a0782d164c234` |
| sources/personnel/rh.csv | 48 | `f1529f8f2fbab8d3b67ab985a5c5a04868083d686bdf0f4bfb12395bad4ad4a3` |
| sources/produit/achats.csv | 33 | `65ad795d63710c16a3b248f9e50ec4171ed1a852567a2a9ee9f9eddb60396191` |
| sources/produit/biomedical.csv | 35 | `c26b53fa9e595a6c29b328bec5b6fa8769e0fce75ea21189d8bfe1b2b8f6b52f` |
| sources/produit/bloc.csv | 36 | `6af5d199156a263899789eca9d0e3bde5f6c3a904fdece35a310256116a1aadb` |
| sources/produit/labo.csv | 48 | `6f02a14319103fe7d0fb3ae50717d221d2ecfd231678ef53c29ec589f4530110` |
| sources/produit/pharmacie.csv | 48 | `553be7746c6e79701b1e3dfc012bd957827ab512766830762e8f8a6c7a2f6556` |
