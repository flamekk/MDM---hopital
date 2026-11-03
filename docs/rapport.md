# Plateforme MDM hospitalière — rapport de projet

La version **Hôpital Al Amal** reprend le parcours initial en six onglets pour les patients, le personnel et les produits. Elle ajoute une revue des conflits d’attributs effectivement appliquée lors de la publication, une préparation de réconciliation sans écriture et huit tables hospitalières liées. Voir le [guide de la version hospitalière](hopital_al_amal.md).

**Groupe et membres : à compléter. Validation du sujet : à obtenir auprès du formateur.**

## Contexte et objectifs

Un hôpital conserve des informations communes dans plusieurs applications : identité patient dans l’admission, le laboratoire et le DPI ; identité professionnelle dans les RH, le planning et les formations ; références produits dans la pharmacie, les achats et les services techniques. Des doublons et contradictions apparaissent quand ces applications évoluent séparément.

Le projet construit un hub de consolidation pour trois domaines. Il vise une identité maître traçable, une mesure explicite de la qualité et une gestion des ambiguïtés. Les sources sont simulées : aucun accès à un système hospitalier réel n’est nécessaire.

## Réalisation

Le moteur importe les CSV, conserve leurs valeurs brutes et calcule une empreinte SHA-256. Il normalise les noms, dates, contacts et quantités, puis signale les champs manquants ou invalides. Des clés de blocking réduisent la recherche de paires candidates. Trois méthodes produisent une classification : exacte, similarité pondérée Jaro-Winkler et rapport de vraisemblance avec paramètres illustratifs.

La fusion automatique demande des preuves minimales en plus du score. Les patients nécessitent des noms proches, une date compatible et un contact ou identifiant partagé. Le personnel nécessite des noms proches et un courriel ou identifiant partagé. Les produits exigent une cohérence de catégorie et de conditionnement, complétée par les attributs propres aux médicaments et équipements.

Les contrôles portent sur le groupe entier, afin d’éviter une incohérence introduite par transitivité. Une confirmation humaine ne contourne jamais une contradiction critique. Le Data Steward doit demander la correction de la source ; ses rejets et escalades interdisent également un lien indirect entre les identités concernées.

## Gouvernance et traçabilité

Chaque version conserve les paires et scores, les données normalisées, les maîtres, les correspondances, la provenance des attributs et les anomalies. Les décisions humaines sont justifiées et horodatées dans une transaction SQLite qui ajoute aussi l’événement d’audit. Une nouvelle exécution applique ces décisions sans écraser le snapshot précédent. Le lignage relie les anciens et nouveaux UUID.

La survivorship suit une priorité par application documentée. Une valeur retenue ne devient pas nécessairement exacte : les alternatives restent consultables. Les allergies conservent leur provenance et leur statut de validation clinique. Affectations et stocks restent des relations séparées.

## Évaluation

Les résultats exécutés sont dans `docs/resultats_mesures.md` et `examples/metrics.csv`. Le protocole distingue la précision automatique, le rappel global incluant les pertes de blocking, la charge de revue et les faux liens après clustering. Un dénominateur nul produit une mesure absente, pas un résultat parfait.

La vérité terrain synthétique est isolée du moteur de décision. Les trois méthodes sont comparées sur la même population et les mêmes candidats. Les paramètres ne sont pas appris sur ces étiquettes. Le protocole reste descriptif : aucun test indépendant ni calibration probabiliste n’est revendiqué.

## Apports et limites

Le projet rend reproductible la chaîne de traitement, étend le dépôt patient aux domaines personnel et produits, fournit une interface de revue, une API locale et des exports de versions. Le schéma PostgreSQL prépare une projection du hub dans une base serveur, sans annoncer que l’interface utilise déjà ce serveur.

Les limites principales sont l’absence d’authentification et de contrôle des rôles, le volume pédagogique, les paramètres de matching illustratifs, l’absence de connecteurs hospitaliers et la couverture limitée des caractéristiques produits. Un nom de réviseur reste déclaratif. La chaîne d’audit protège contre certaines altérations locales mais ne remplace pas une preuve externe d’intégrité.

Les étapes suivantes seraient une validation des règles par les Data Owners, un corpus annoté indépendant, la calibration des seuils, une gestion des droits, puis des imports incrémentaux et une diffusion versionnée vers des consommateurs autorisés.
