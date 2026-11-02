# Réaliser et présenter le projet, étape par étape

## 1. Valider le sujet avec le formateur

Sujet proposé : **Conception d’une plateforme MDM hospitalière pour l’unification, la qualité et la gouvernance des données du personnel, des patients et des produits et matériels hospitaliers.**

Problématique : comment maintenir des référentiels fiables à partir de sources hétérogènes, sans provoquer de fausses fusions ? Compléter le numéro du groupe et les noms des trois membres. Le texte joint est conservé dans `docs/cadrage_fourni.txt`. La validation du formateur reste à obtenir.

Livrable : périmètre validé, responsables des données et critères de réussite.

## 2. Installer et lancer

Ouvrir PowerShell dans le dossier `MDM---hopital`, avec Python 3.13 installé :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m mdm demo
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ouvrir `http://127.0.0.1:8501`. L’activation de l’environnement n’est pas nécessaire. La commande `demo` se lance une seule fois par dossier : elle refuse d’écraser des sources existantes. Ensuite utiliser `python -m mdm run` avec le Python de l’environnement. Le raccourci `powershell -File .\lancer.ps1 -Installer` réalise aussi l’installation et le lancement.

## 3. Comprendre les sources et le modèle

Ouvrir **Catalogue & modèle**, puis `docs/architecture.md` et `docs/dictionnaire.md`.

Les trois domaines couvrent 11 sources simulées : admissions/DPI/laboratoire, RH/planning/formation, pharmacie/laboratoire/bloc/achats/biomédical. Les allergies, affectations et stocks sont des tables rattachées. La démo couvre six familles de produits, sans prétendre représenter tous leurs attributs métier.

Livrables : catalogue calculé `workspace/runs/<version>/catalogue.csv`, dictionnaire et modèle PostgreSQL dans `sql/schema.sql`.

## 4. Mesurer et nettoyer

Dans **Sources & qualité**, comparer les données brutes et normalisées. Montrer une date impossible, un téléphone invalide et un nom avec des accents ou des espaces.

La complétude valide peut diminuer après nettoyage : une valeur remplie mais invalide devient vide. Elle n’est jamais inventée. Une valeur syntaxiquement valide peut rester inexacte.

Livrables : `issues.csv`, `quality.csv` et `standardized_<domaine>.csv`.

## 5. Comparer les trois méthodes

Dans **Matching & évaluation**, comparer exact, pondéré Jaro-Winkler et rapport de vraisemblance probabiliste. Expliquer le blocking et distinguer précision, rappel global et erreurs de clusters. Les paramètres et seuils sont définis dans `mdm/config.py` et inclus dans le snapshot.

Les étiquettes de `evaluation/truth.csv` ne sont lues que par le module d’évaluation. Pour démontrer cette séparation :

```powershell
.\.venv\Scripts\python.exe -m mdm run --no-evaluation
```

Livrable : `metrics.csv`. Les mesures sont descriptives sur le jeu synthétique, sans prétention de généralisation.

## 6. Traiter un cas comme Data Steward

Dans **Revue humaine**, sélectionner une paire, lire les deux identités et les similarités, saisir un identifiant de réviseur et une justification, puis confirmer, rejeter ou escalader.

Pour appliquer : laisser **Reprendre les décisions de cette version** coché et cliquer **Exécuter le pipeline**. La décision est enregistrée immédiatement ; la fusion est appliquée dans la nouvelle version après les contrôles de groupe. Un rejet ou une escalade interdit aussi une fusion indirecte de la paire. Les contradictions critiques doivent être corrigées dans les sources, même après confirmation humaine.

Livrables : journal SQLite, `events.csv`, nouveaux maîtres et lignage.

## 7. Vérifier le Golden Record et la provenance

Dans **Référentiels**, rechercher une personne ou un produit. Afficher les identités sources et le choix de chaque attribut. La priorité est explicitement RH avant planning/formation, admission avant DPI/labo, pharmacie avant les autres sources produits ; ces choix sont pédagogiques et doivent être validés par les Data Owners.

Les candidats écartés restent visibles dans la provenance. Les allergies restent déclarées « à valider » : un rapprochement d’identité ne réalise aucune validation clinique.

## 8. Tester, exporter et préparer PostgreSQL

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m mdm verify
.\.venv\Scripts\python.exe scripts\bilan.py
.\.venv\Scripts\python.exe scripts\export_postgres.py
.\.venv\Scripts\python.exe -m mdm api --port 8080
```

L’API est consultable sur `http://127.0.0.1:8080/api/health`. Les autres routes sont dans le README. SQLite exécute la démo sans serveur. PostgreSQL est une étape de migration préparée, indépendante de l’interface actuelle ; son exécution nécessite PostgreSQL ou Docker. Consulter `docs/postgresql.md`.

Pour reprendre les CSV patients originaux du dépôt, sans utiliser leurs résultats pré-calculés :

```powershell
.\.venv\Scripts\python.exe -m mdm import-patients --workspace workspace_patients --scenario S1_5pct
```

Ce dossier distinct contient uniquement le domaine patient des cinq applications historiques. L’ancienne interface reste disponible : `python -m streamlit run legacy_app.py --server.port 8502`.

## 9. Préparer la soutenance et rendre

Lire `docs/rapport.md`, `docs/soutenance.md` et le bilan généré `docs/resultats_mesures.md`. Adapter la présentation au temps accordé et compléter les membres du groupe. Régénérer les livrables après une modification du moteur :

```powershell
.\.venv\Scripts\python.exe -m mdm run
.\.venv\Scripts\python.exe scripts\bilan.py
.\.venv\Scripts\python.exe scripts\empaqueter.py
```

L’archive `dist/MDM-hopital-projet-scolaire.zip` exclut l’environnement virtuel et les bases de travail ; elle contient le code, le guide, les données historiques et les résultats de référence. Le destinataire recrée la démo avec la même graine. La publication GitHub et la remise à l’enseignant sont à réaliser depuis votre compte.
