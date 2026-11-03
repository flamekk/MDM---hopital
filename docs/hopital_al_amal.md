# Hôpital Al Amal — guide de la version hospitalière

Le principe du premier MDM patient est conservé : **scénarios, Golden Records, revue des paires, arbitrage des attributs, journal d’audit et réconciliation contrôlée**. Le personnel et les produits utilisent exactement le même parcours.

## Démarrer

Depuis la racine du projet :

```powershell
.\.venv\Scripts\python.exe -m mdm hospital-demo --workspace workspace_hospital
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Le script `lancer.ps1` prépare aussi cette démonstration si elle n’existe pas. Les dossiers de travail initiaux `workspace`, `workspace_patients` et les CSV historiques sont conservés. Le nouveau tableau de bord utilise `workspace_hospital` ; définir `MDM_WORKSPACE` permet de choisir un autre dossier.

Le générateur crée 48 identités de référence par domaine et 459 enregistrements sources au total, répartis dans 11 tables. Les trois scénarios partagent la même population et la même couverture des sources ; des erreurs supplémentaires sont injectées dans S2 et S3. Les suffixes historiques `5pct`, `15pct`, `30pct` sont des noms de profils : aucun taux exact de cellules erronées n’est garanti par ces noms.

## Les six onglets, pour chacun des trois domaines

| Onglet | Utilisation |
| --- | --- |
| Vue d’ensemble | Indicateurs du domaine, contributions des sources, qualité et comparaison des scénarios |
| Golden Records | Recherche, filtre sur le nombre de sources, fiche détaillée et provenance des valeurs |
| Revue des paires | Comparaison côte à côte, indices du score, confirmation, rejet ou escalade justifiés |
| Conflits d’attributs | Choix d’une valeur réellement observée, avec source et justification, ou escalade |
| Journal d’audit | Décisions de rapprochement, arbitrages, validations de déclarations et publications |
| Réconciliation | Préparation sans écriture, aperçu des groupes, puis publication d’une nouvelle version |

L’identifiant du réviseur se renseigne dans la barre latérale. Les décisions de rapprochement et les arbitrages prennent effet dans la nouvelle version. Les contrôles de groupe continuent de bloquer les contradictions critiques et les rejets indirects.

L’arbitrage manuel ne permet pas de fabriquer une valeur absente des sources. Les identifiants qualifiés et attributs critiques demandent une correction de la source. Si les membres d’un groupe changent, son nouvel UUID ne récupère pas automatiquement l’arbitrage d’une ancienne fiche.

## Patients : identité, allergies et parcours

La fiche patient possède quatre vues :

- **Identité & contacts** : identité administrative, coordonnées et contact désigné.
- **Allergies & vigilances** : substance, catégorie, manifestation rapportée, sévérité renseignée par la source, origine et validation.
- **Parcours de soins** : séjour ou consultation, service, date d’admission, chambre et lit déclarés.
- **Sources & provenance** : identifiants locaux, valeurs retenues et alternatives.

Dans les Golden Records, cocher « Afficher les dossiers avec une allergie déclarée » permet de retrouver rapidement une fiche de démonstration.

L’espace **Vue hospitalière** permet d’examiner une déclaration d’allergie. Le réviseur renseigne une fonction clinique déclarée (Médecin ou Pharmacien), choisit Confirmer, Écarter ou Demander un complément, puis justifie la décision. La décision est enregistrée et visible dans la vue de revue ; elle est intégrée au snapshot à la prochaine publication.

Une déclaration ne devient **jamais confirmée parce que deux identités ont été fusionnées**. La validation concerne une déclaration et son empreinte de source. Si la substance ou un autre contenu de la déclaration change, l’ancienne validation n’est pas réappliquée automatiquement. Plusieurs déclarations restent séparées, même lorsqu’elles mentionnent la même substance.

La fonction du réviseur est déclarative dans ce prototype sans authentification. Il ne fournit ni prescription, ni analyse d’interaction médicamenteuse, ni décision thérapeutique. L’absence de déclaration rattachée ne prouve pas l’absence d’allergie.

## Personnel : professionnels et organisation

La fiche professionnelle réunit l’identité, la catégorie, les contacts et les identifiants partagés. Les affectations par service, les formations suivies et les gardes sont rattachées comme des relations distinctes. Leur provenance reste affichée.

Les formations de démonstration portent sur l’identitovigilance, l’hygiène et la traçabilité. Le tableau ne délivre pas une habilitation réelle : il restitue une information sourcée.

## Produits : références, lots et biomédical

La fiche produit conserve la désignation, la famille, le fabricant, le modèle, le dosage, la forme, le conditionnement et la stérilité déclarée. Le dosage, le modèle et le conditionnement restent des critères de cohérence qui peuvent bloquer une fusion.

Les lots portent la quantité disponible, un seuil de réapprovisionnement, une date de péremption et un emplacement. Des points d’attention descriptifs signalent une date dépassée ou une quantité inférieure au seuil fourni. Ils ne constituent pas une autorisation de délivrance ou d’utilisation.

Le parc biomédical conserve le numéro de série, le service, l’état déclaré et les dates de maintenance. Une référence maître correspond à un modèle ; plusieurs instances physiques peuvent lui être rattachées.

## Démonstration au professeur — proposition de 5 minutes

1. Montrer les six onglets du domaine patient et expliquer qu’ils sont identiques pour le personnel et les produits.
2. Ouvrir une fiche patient avec une allergie déclarée ; retrouver son application d’origine et son statut « À vérifier ».
3. Comparer une paire et enregistrer une escalade justifiée. Montrer ensuite un conflit d’attributs et une valeur candidate sourcée.
4. Préparer la réconciliation : aucun snapshot n’est encore créé. Publier après lecture de la proposition et revenir à une ancienne version.
5. Passer au personnel pour montrer affectations et formations, puis aux produits pour montrer conditionnement, lot et équipement.

Phrase d’introduction : « Nous avons conservé le workflow de revue du MDM patient et l’avons rendu commun à trois référentiels hospitaliers. Les informations métier sont rattachées aux identités, avec leurs sources et leurs validations propres. »

## Résultats initiaux de la nouvelle démo

| Scénario | Identités sources, trois domaines | Maîtres, trois domaines |
| --- | ---: | ---: |
| S1 — qualité élevée | 459 | 183 |
| S2 — qualité intermédiaire | 459 | 251 |
| S3 — qualité dégradée | 459 | 349 |

Ces résultats proviennent de la méthode pondérée, avec la graine 42 et sans décisions humaines. Une dégradation des données peut fragmenter les groupes : le moteur conserve des identités séparées lorsqu’il manque des preuves. Ces nombres ne mesurent pas un hôpital réel et peuvent évoluer après revue.

## Vérifier et exporter

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m mdm verify --workspace workspace_hospital/S1_5pct
.\.venv\Scripts\python.exe scripts/bilan.py --workspace workspace_hospital/S1_5pct
.\.venv\Scripts\python.exe scripts/export_postgres.py --workspace workspace_hospital/S1_5pct
.\.venv\Scripts\python.exe scripts/empaqueter.py
```

SQLite reste le stockage actif. L’export PostgreSQL conserve les huit tables liées dans la projection générique des relations et les décisions appliquées dans le snapshot JSON. L’exécution sur un serveur PostgreSQL reste une vérification distincte.
