# Hospital MDM — projet scolaire

Plateforme locale en français pour **Patients**, **Personnel** et **Produits et matériels hospitaliers**. Elle importe des CSV, mesure leur qualité, compare trois méthodes de matching, construit les Golden Records et trace la revue humaine dans des versions distinctes.

Le projet enrichit [flamekk/MDM---hopital](https://github.com/flamekk/MDM---hopital), importé au commit `070c381`. Les données historiques, le notebook et le moteur de réconciliation initial sont conservés ; l’ancienne interface est `legacy_app.py`. La version enrichie est regroupée dans la branche `amelioration-projet-scolaire`.

**Pour la soutenance : lire [l’explication pour le professeur](docs/explication_professeur.md)** — améliorations réalisées, introduction orale, démonstration écran par écran, résultats et questions/réponses. [L’historique des changements](CHANGELOG.md) résume les apports techniques.

## Démarrer sous Windows

Dans PowerShell ouvert dans ce dossier, avec Python 3.13 :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m mdm demo
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ouvrir [le tableau de bord local](http://127.0.0.1:8501). Aucun serveur de base de données n’est nécessaire. Pour les démarrages suivants : `powershell -File .\lancer.ps1`. Le script accepte `-Installer` pour installer les dépendances. Sous Linux/macOS : utiliser `python3 -m venv .venv` puis `.venv/bin/python` dans les commandes.

**Commencer par [le guide étape par étape](docs/guide_etape_par_etape.md).** Le sujet et les noms du groupe doivent être complétés et validés avec le formateur.

## Ce qui fonctionne

- 11 tables sources simulées et reproductibles ; six familles de produits.
- Conservation du brut, empreintes des sources, contrôles et normalisation.
- Blocking multi-clés ; exact, pondéré Jaro-Winkler, rapport de vraisemblance illustratif.
- Contrôles au niveau des groupes : contradictions critiques et rejets transitifs.
- Revue humaine justifiée ; CONFIRM, REJECT, ESCALATE ; application dans une nouvelle version.
- Maîtres UUID, XREF, provenance par attribut, alternatives et lignage.
- Allergies, affectations et stocks liés sans être utilisés comme preuves d’identité.
- Audit transactionnel SQLite, vérification des empreintes, exports CSV et API locale.
- Comparaison mesurée des méthodes ; vérité terrain isolée du moteur.
- Schéma PostgreSQL typé et générateur d’export SQL pour une migration distincte.

## Commandes utiles

```powershell
# Recalculer sans écraser les anciennes versions
.\.venv\Scripts\python.exe -m mdm run --method weighted

# Reprendre les décisions de la version choisie
.\.venv\Scripts\python.exe -m mdm run --base-run <run_id>

# Fonctionner sans lire la vérité terrain
.\.venv\Scripts\python.exe -m mdm run --no-evaluation

# Recalculer depuis les CSV patients originaux, dans un dossier distinct
.\.venv\Scripts\python.exe -m mdm import-patients --workspace workspace_patients --scenario S1_5pct

# Tester, contrôler et préparer la remise
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m mdm verify
.\.venv\Scripts\python.exe scripts\bilan.py
.\.venv\Scripts\python.exe scripts\export_postgres.py
.\.venv\Scripts\python.exe scripts\empaqueter.py
```

`demo` refuse de remplacer des sources existantes. Pour une autre population, utiliser `--workspace workspace_autre --size 80`. Le tableau de bord lit `workspace` par défaut ; pour consulter un autre dossier, définir `$env:MDM_WORKSPACE = 'chemin absolu du dossier'` avant de le lancer.

Pour charger vos propres CSV, utiliser `sources/<patient|personnel|produit>/<application>.csv` dans un nouveau workspace et respecter [le contrat des champs](docs/dictionnaire.md). Un identifiant local absent ou dupliqué provoque un échec explicite. Sans fichier `evaluation/truth.csv`, aucune précision ou rappel n’est calculé.

## Livrables à lire

| Document | Utilité |
| --- | --- |
| [Guide](docs/guide_etape_par_etape.md) | Neuf étapes de réalisation et de démonstration |
| [Architecture](docs/architecture.md) | Modèle, choix et responsabilités |
| [Dictionnaire](docs/dictionnaire.md) | Champs, types, contraintes et provenance |
| [Rapport](docs/rapport.md) | Texte académique à personnaliser |
| [Bilan mesuré](docs/resultats_mesures.md) | Résultats réellement exécutés |
| [Vérifications](docs/verification.md) | Tests, parcours contrôlés et limite PostgreSQL |
| [Soutenance](docs/soutenance.md) | Proposition de déroulé de dix minutes |
| [Explication au professeur](docs/explication_professeur.md) | Avant/après, discours, démonstration et réponses aux questions |
| [PostgreSQL](docs/postgresql.md) | Chargement relationnel avec Docker ou psql |
| [Cadrage fourni](docs/cadrage_fourni.txt) | Texte joint d’origine |

## API de lecture

```powershell
.\.venv\Scripts\python.exe -m mdm api --port 8080
```

Routes : `/api/health`, `/api/runs`, puis `/api/runs/<run_id>/masters`, `/xrefs`, `/catalogue`, `/quality`, `/metrics`. L’API écoute uniquement sur `127.0.0.1`. Les routes de ressources se placent toutes après l’identifiant de version. Aucun endpoint d’écriture n’est exposé.

## Organisation

```text
app.py                 tableau de bord des trois domaines
mdm/                   ingestion, matching, clustering, versions, audit, API
tests/                 tests métier, pipeline et interface ; tests initiaux conservés
docs/                  guide, dictionnaire, rapport, soutenance et résultats
examples/              petits exports de référence calculés
sql/schema.sql         projection relationnelle PostgreSQL
scripts/               bilan, export SQL et empaquetage
workspace/             sources synthétiques, SQLite et versions générées (ignorés Git)
legacy_app.py           ancienne interface patient
patient_mdm_synthetic_dataset/   données patients historiques conservées
```

## Limites et protocole

Prototype scolaire sur données synthétiques, sans authentification ni connecteurs hospitaliers réels. Le réviseur est déclaratif. Le score probabiliste n’est pas calibré et les mesures ne revendiquent aucun test indépendant. Les priorités de sources et seuils nécessitent une validation métier. Les UUID restent stables si l’appartenance au groupe est inchangée ; une fusion ou défusion crée un UUID et son lignage.

L’application utilise **SQLite** ; PostgreSQL est une projection préparée et documentée, pas un backend actif. La chaîne de hachage détecte une altération partielle mais n’empêche pas un administrateur local de réécrire l’ensemble. Les allergies ne sont pas validées cliniquement par le moteur. Les noms de naissance et d’usage séparés, conversions d’unités et caractéristiques produits détaillées restent des extensions.

Références techniques : [Jaro-Winkler / RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html), [tests Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), [contraintes PostgreSQL](https://www.postgresql.org/docs/17/ddl-constraints.html).
