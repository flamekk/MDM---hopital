# Règles du baseline de rapprochement MDM Patient

## Entrées autorisées
Uniquement les fichiers `standardized/*_patients_standardized.csv` des scénarios S1, S2 et S3.
Les fichiers `ground_truth.csv`, `hard_nonmatch_evaluation.csv` et `reference_population_private.csv` ne sont jamais des entrées du matching. Ils servent uniquement à l'évaluation postérieure.

## Blocking (génération des candidats)
Une paire est candidate si elle partage au moins une clé parmi :
1. date de naissance normalisée + nom normalisé ;
2. téléphone normalisé (si présent) ;
3. prénom normalisé + nom normalisé.
Les paires provenant du même système source sont exclues de ce baseline inter-systèmes. Les doublons internes à une source seront traités dans une phase distincte.

## Score (0–100)
- Date de naissance identique : 25 points.
- Prénom : jusqu'à 20 points (similarité de chaînes).
- Nom : jusqu'à 25 points (similarité de chaînes).
- Téléphone identique : 20 points.
- Sexe identique : 5 points.
- Adresse identique : 5 points (uniquement si les deux valeurs sont disponibles).
Les attributs absents ne sont pas considérés comme des désaccords. Le score est ramené à 100 en fonction des poids effectivement comparables, afin de ne pas pénaliser mécaniquement les sources qui ne possèdent pas l'adresse.

## Décision initiale
- `MATCH_AUTO` : score >= 90 et date de naissance identique, plus au moins un des éléments suivants : téléphone identique ou prénom et nom très similaires.
- `REVIEW` : score >= 65, ou paire avec nom + date de naissance identiques mais signaux complémentaires insuffisants.
- `NON_MATCH` : autres paires candidates.
Les seuils sont un point de départ expérimental, pas une règle clinique définitive. Les décisions automatiques doivent être auditées avant production.

## Traçabilité
Chaque paire conserve les identifiants locaux, les systèmes sources, les indicateurs de comparaison, le score, la décision et les règles de blocking déclenchées.
Les valeurs brutes et les vues standardisées restent séparées.
