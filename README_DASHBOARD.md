# Patient MDM — Dashboard de revue humaine

Prototype Streamlit en français pour le projet de Master Data Management patient.

## Fonctionnalités
- Vue d'ensemble et comparaison des scénarios S1, S2 et S3.
- Exploration des Golden Records et de leurs membres.
- Revue des paires en attente : `CONFIRM_MATCH`, `REJECT_MATCH` ou `ESCALATE`.
- Revue des conflits d'attributs avec sélection d'une valeur, acceptation ou escalade.
- Journal d'audit avec horodatage UTC, identifiant de réviseur et empreintes SHA-256 avant/après.
- Export CSV des Golden Records filtrés et du journal d'audit.

## Installation sous Windows (PowerShell)
1. Extraire complètement l'archive ZIP dans un dossier.
2. Ouvrir PowerShell dans le dossier `Patient_MDM_Dashboard`.
3. Créer un environnement virtuel :
   ```powershell
   python -m venv .venv
   ```
4. Activer l'environnement :
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   Si PowerShell bloque l'activation, utiliser cette commande dans la session courante :
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```
5. Installer les dépendances :
   ```powershell
   python -m pip install -r requirements.txt
   ```
6. Lancer l'application :
   ```powershell
   streamlit run app.py
   ```

Le navigateur s'ouvrira normalement automatiquement. Pour arrêter le serveur, faire `Ctrl+C` dans PowerShell.

## Où sont les données ?
Le dossier `patient_mdm_synthetic_dataset` est inclus dans cette archive. Les décisions sont sauvegardées dans :
- `patient_mdm_synthetic_dataset/human_review_queue.csv`
- `patient_mdm_synthetic_dataset/attribute_conflict_review_queue.csv`
- `patient_mdm_synthetic_dataset/mdm_audit_log.csv`

Faites une copie de sauvegarde du dossier de données avant une session de revue importante.

## Contrôles et limites
- Les décisions humaines sont persistées, mais ne modifient pas automatiquement les clusters ni les Golden Records. Une étape de réconciliation contrôlée devra être conçue séparément.
- Le fichier `ground_truth.csv`, `hard_nonmatch_evaluation.csv` et `reference_population_private.csv` restent des fichiers d'évaluation et ne sont jamais chargés par l'interface pour le matching ou la prise de décision.
- Le journal est append-only dans le flux normal de l'application, mais des fichiers CSV peuvent être modifiés manuellement. Ce prototype n'est pas un système de production.
- Jeu de données synthétique uniquement ; ne pas utiliser pour des décisions médicales ou avec des données personnelles réelles sans gouvernance, sécurité et conformité adaptées.

## Structure
```text
Patient_MDM_Dashboard/
├── app.py
├── requirements.txt
├── README_DASHBOARD.md
└── patient_mdm_synthetic_dataset/
    ├── human_review_queue.csv
    ├── attribute_conflict_review_queue.csv
    ├── mdm_audit_log.csv
    ├── S1_5pct/
    ├── S2_15pct/
    └── S3_30pct/
```


## Réconciliation contrôlée (v1)
L'onglet **Réconciliation** permet de préparer puis de créer une version réconciliée pour le scénario sélectionné. Seules les paires explicitement confirmées (`CONFIRM_MATCH` ou statut `REVIEWED_MATCH`) sont candidates. `REJECT_MATCH` et `ESCALATE` ne sont jamais fusionnés.

Les contrôles de la v1 empêchent les clusters contenant deux identités du même système source et les fusions dont les dates de naissance non vides se contredisent. Les sorties sont écrites dans `patient_mdm_synthetic_dataset/<SCENARIO>/reconciliation_v1/`; les fichiers Golden Record de référence ne sont pas écrasés.

**Limite connue :** la v1 choisit les attributs du Golden Record de référence le plus complet parmi les clusters réunis. Elle n'applique pas encore les décisions de revue des conflits d'attributs à la survivorship. Prototype pédagogique uniquement.


## Notebook complet de traitement des données
Le fichier `Patient_MDM_Traitement_Donnees.ipynb` documente le pipeline de bout en bout : inventaire, audit structurel, profilage, exploration des données standardisées, analyse des résultats de matching, exploration des Golden Records/memberships, revue humaine, audit et aperçu de réconciliation.

Pour installer les dépendances du notebook :
```powershell
python -m pip install -r requirements-notebook.txt
```
Puis lancer Jupyter depuis le dossier du projet :
```powershell
jupyter notebook Patient_MDM_Traitement_Donnees.ipynb
```
Le notebook recherche automatiquement le dossier `patient_mdm_synthetic_dataset` placé à côté de lui. Il lit les résultats de matching déjà calculés; il ne réexécute pas le moteur de matching baseline. La cellule qui écrit les fichiers de réconciliation est désactivée par défaut.


## Finalisation du dashboard — réconciliation
L'onglet **Réconciliation** utilise les champs exacts de `human_review_queue.csv` (`source_system_a`, `source_patient_id_a`, `source_system_b`, `source_patient_id_b`, `reviewer_decision`). Une fusion n'est candidate que si la décision explicite est `CONFIRM_MATCH`. Les rejets et escalades ne sont jamais fusionnés.

Chaque application crée une nouvelle version `reconciliation_v1`, `reconciliation_v2`, etc., sans écraser les versions précédentes ni le Golden Record baseline. Les sorties incluent les Golden Records réconciliés, la membership, le lineage, les décisions acceptées/refusées et un résumé.

### Tests automatisés
Depuis le dossier du projet :
```powershell
python -m pip install -r requirements-notebook.txt
python -m unittest discover -s tests -v
```
Les tests vérifient la fusion d'une paire confirmée, le blocage d'une date de naissance contradictoire, l'absence de fusion pour une paire non confirmée et la création de versions distinctes.
