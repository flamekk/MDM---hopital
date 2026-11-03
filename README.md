# Hôpital Al Amal — trois référentiels MDM

Plateforme locale en français pour **Patients**, **Personnel** et **Produits et matériels hospitaliers**. Elle importe des CSV, mesure leur qualité, compare trois méthodes de matching, construit les Golden Records et trace la revue humaine dans des versions distinctes.

La version hospitalière conserve les **six onglets du premier MDM patient**, communs aux trois domaines, et les scénarios S1/S2/S3. Les fiches ajoutent allergies, séjours et contacts, affectations et formations, lots et équipements biomédicaux. Voir [le guide Hôpital Al Amal](docs/hopital_al_amal.md).

Le projet enrichit [flamekk/MDM---hopital](https://github.com/flamekk/MDM---hopital), importé au commit `070c381`. Les données historiques, le notebook et le moteur de réconciliation initial sont conservés ; l’ancienne interface est `legacy_app.py`. La personnalisation hospitalière est regroupée dans la branche `hopital-al-amal`, après intégration de la première version enrichie.

**Pour la soutenance : lire [l’explication pour le professeur](docs/explication_professeur.md)** — améliorations réalisées, introduction orale, démonstration écran par écran, résultats et questions/réponses. [L’historique des changements](CHANGELOG.md) résume les apports techniques.

## Démarrer sous Windows

Dans PowerShell ouvert dans ce dossier, avec Python 3.13 :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m mdm hospital-demo --workspace workspace_hospital
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
- Arbitrage des conflits d’attributs, appliqué à la prochaine publication avec sa provenance.
- Préparation de réconciliation sans écriture, puis publication contrôlée.
- Maîtres UUID, XREF, provenance par attribut, alternatives et lignage.
- Huit tables liées : allergies, séjours, contacts d’urgence, affectations, formations, gardes, stocks et équipements.
- Revue clinique déclarative des allergies, distincte du rapprochement d’identité et protégée par l’empreinte de la déclaration.
- Audit transactionnel SQLite, vérification des empreintes, exports CSV et API locale.
- Comparaison mesurée des méthodes ; vérité terrain isolée du moteur.
- Schéma PostgreSQL typé et générateur d’export SQL pour une migration distincte.

## Commandes utiles

```powershell
# Recalculer sans écraser les anciennes versions
.\.venv\Scripts\python.exe -m mdm run --workspace workspace_hospital/S1_5pct --method weighted

# Reprendre les décisions de la version choisie
.\.venv\Scripts\python.exe -m mdm run --workspace workspace_hospital/S1_5pct --base-run <run_id>

# Fonctionner sans lire la vérité terrain
.\.venv\Scripts\python.exe -m mdm run --workspace workspace_hospital/S1_5pct --no-evaluation

# Recalculer depuis les CSV patients originaux, dans un dossier distinct
.\.venv\Scripts\python.exe -m mdm import-patients --workspace workspace_patients --scenario S1_5pct

# Tester, contrôler et préparer la remise
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m mdm verify --workspace workspace_hospital/S1_5pct
.\.venv\Scripts\python.exe scripts\bilan.py --workspace workspace_hospital/S1_5pct
.\.venv\Scripts\python.exe scripts\export_postgres.py --workspace workspace_hospital/S1_5pct
.\.venv\Scripts\python.exe scripts\empaqueter.py
```

`hospital-demo` prépare les trois scénarios dans `workspace_hospital`, le dossier lu par défaut par l’interface. `demo` conserve la petite démo générique précédente et refuse de remplacer des sources existantes. Pour une autre population, utiliser `--workspace workspace_autre --size 80`. Pour consulter un autre dossier, définir `$env:MDM_WORKSPACE = 'chemin absolu du dossier'` avant de lancer Streamlit.

Pour charger vos propres CSV, utiliser `sources/<patient|personnel|produit>/<application>.csv` dans un nouveau workspace et respecter [le contrat des champs](docs/dictionnaire.md). Un identifiant local absent ou dupliqué provoque un échec explicite. Sans fichier `evaluation/truth.csv`, aucune précision ou rappel n’est calculé.

## Livrables à lire

| Document | Utilité |
| --- | --- |
| [Guide](docs/guide_etape_par_etape.md) | Neuf étapes de réalisation et de démonstration |
| [Hôpital Al Amal](docs/hopital_al_amal.md) | Six onglets communs, allergies, organisation et stocks |
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
.\.venv\Scripts\python.exe -m mdm api --workspace workspace_hospital/S1_5pct --port 8080
```

Routes : `/api/health`, `/api/runs`, puis `/api/runs/<run_id>/masters`, `/xrefs`, `/catalogue`, `/quality`, `/metrics`. L’API écoute uniquement sur `127.0.0.1`. Les routes de ressources se placent toutes après l’identifiant de version. Aucun endpoint d’écriture n’est exposé.

## Organisation

```text
app.py                 tableau de bord des trois domaines
ui/                    composants visuels, fiches hospitalières et six onglets communs
mdm/                   ingestion, matching, clustering, versions, audit, API
tests/                 tests métier, pipeline et interface ; tests initiaux conservés
docs/                  guide, dictionnaire, rapport, soutenance et résultats
examples/              petits exports de référence calculés
sql/schema.sql         projection relationnelle PostgreSQL
scripts/               bilan, export SQL et empaquetage
workspace_hospital/    scénarios S1/S2/S3, SQLite et versions générées (ignorés Git)
legacy_app.py           ancienne interface patient
patient_mdm_synthetic_dataset/   données patients historiques conservées
```

## Limites et protocole

Prototype scolaire sur données synthétiques, sans authentification ni connecteurs hospitaliers réels. Le réviseur est déclaratif. Le score probabiliste n’est pas calibré et les mesures ne revendiquent aucun test indépendant. Les priorités de sources et seuils nécessitent une validation métier. Les UUID restent stables si l’appartenance au groupe est inchangée ; une fusion ou défusion crée un UUID et son lignage.

L’application utilise **SQLite** ; PostgreSQL est une projection préparée et documentée, pas un backend actif. La chaîne de hachage détecte une altération partielle mais n’empêche pas un administrateur local de réécrire l’ensemble. Une déclaration d’allergie exige une revue distincte, avec fonction clinique déclarée ; le moteur de matching ne la valide jamais. Les noms de naissance et d’usage séparés, conversions d’unités et caractéristiques produits détaillées restent des extensions.

Références techniques : [Jaro-Winkler / RapidFuzz](https://rapidfuzz.github.io/RapidFuzz/Usage/distance/JaroWinkler.html), [tests Streamlit](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest), [contraintes PostgreSQL](https://www.postgresql.org/docs/17/ddl-constraints.html).
