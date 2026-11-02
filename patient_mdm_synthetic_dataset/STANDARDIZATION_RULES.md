# Profilage et standardisation non destructive — Patient MDM

## Objectif
Préparer les attributs d'identité avant le rapprochement (entity resolution), sans modifier les fichiers sources. Les résultats sont des vues dérivées, pas des Golden Records.

## Règles appliquées
1. **Valeurs brutes conservées** : les colonnes d'origine sont copiées dans des colonnes `raw__*`; les CSV sources n'ont pas été écrasés.
2. **Prénoms/noms (`std__*`)** : suppression des espaces en début/fin et réduction des espaces successifs. La casse d'affichage est conservée.
3. **Clés de comparaison de noms (`match__*`)** : minuscules, suppression des diacritiques Unicode et espaces normalisés. Ces clés servent à générer des candidats, jamais à décider seules d'une identité.
4. **Date de naissance** : conversion des formats non ambigus `YYYY-MM-DD`, `DD/MM/YYYY` et `YYYY/MM/DD` vers `YYYY-MM-DD`. Les dates absentes ou non reconnues restent vides dans `std__date_of_birth`; `std__dob_parse_status` distingue `MISSING`, `OK` et `UNPARSEABLE`. Aucune date ambiguë n'est devinée.
5. **Téléphone** : seuls les caractères non numériques sont retirés; le résultat reste une chaîne pour préserver les zéros initiaux. Aucun indicatif pays n'est inventé et aucune longueur n'est forcée.
6. **Sexe (`std__sex`)** : normalisation prudente des valeurs reconnues vers `M`, `F` ou `X`; les valeurs inconnues deviennent vides dans le champ standardisé, tout en restant visibles dans le champ brut.
7. **Adresse** : espaces normalisés et casse de présentation en titre. Pas de géocodage, de correction d'orthographe ni de fusion d'adresses.
8. **Doublons potentiels** : les rapports comptent les répétitions de clé `nom normalisé + prénom normalisé + date de naissance normalisée` au sein d'une même source. Ce sont des candidats à examiner, pas des doublons confirmés.

## Limites importantes
- `ground_truth.csv`, `hard_nonmatch_evaluation.csv` et `reference_population_private.csv` sont des données d'évaluation et **ne doivent jamais être utilisées comme variables d'entrée du matching**.
- Les identifiants locaux et les champs de provenance sont conservés.
- Les statistiques `profile_field_metrics.csv` comparent les valeurs manquantes/invalides avant et après standardisation. Une hausse des valeurs vides après transformation signifie qu'une valeur brute n'a pas pu être normalisée de façon sûre; elle n'est pas supprimée de la colonne brute.
- La standardisation ne corrige pas les fautes d'identité et ne fusionne aucun enregistrement. La prochaine phase sera la conception des règles de matching et des seuils de décision.
