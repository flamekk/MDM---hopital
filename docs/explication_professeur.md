# Comprendre le projet et l’expliquer au professeur

Ce document complète le [rapport](rapport.md), le [guide pratique](guide_etape_par_etape.md) et le [déroulé de soutenance](soutenance.md). Les chiffres cités viennent des exécutions consignées dans le dépôt. Compléter les noms du groupe et présenter la répartition réelle du travail.

## 1. Le projet en une phrase

**Nous construisons un hub MDM hospitalier qui rapproche les identités de plusieurs applications, mesure leur qualité et conserve la justification de chaque décision pour les patients, le personnel et les produits.**

MDM signifie Master Data Management : gestion des données de référence communes à plusieurs systèmes. Une fiche maître, ou Golden Record, rassemble les attributs retenus d’une même identité. Elle conserve des liens vers les enregistrements d’origine ; elle ne remplace pas les applications de soins, de RH ou de stock.

## 2. Ce qui a été amélioré

| Point | Base importée | Version enrichie |
| --- | --- | --- |
| Périmètre | Patients, avec scénarios et résultats déjà présents | Patients, personnel et six familles de produits et matériels |
| Traitement | Exploration des résultats patients et réconciliation | Pipeline reproductible qui repart des CSV bruts |
| Qualité | Fichiers de contrôle et de profilage historiques | Normalisation et anomalies recalculées dans chaque version |
| Matching | Résultats historiques consultables | Trois méthodes exécutables et comparées sur les mêmes candidats |
| Fusion | Réconciliation patient avec contrôles propres à la base | Contrôles des contradictions sur tous les membres du groupe, y compris les liens indirects |
| Revue | Interface patient de décision | Revue des trois domaines ; décisions justifiées, reprises dans une nouvelle version |
| Survivorship | Attributs du Golden Record de référence sélectionné | Choix par attribut, priorité de source explicite et conservation des alternatives |
| Traçabilité | CSV d’audit et versions de réconciliation | Snapshots SQLite, événements transactionnels, empreintes et lignage |
| Relations | Données opérationnelles patients historiques | Exemples d’allergies, d’affectations et de stocks rattachés aux identités |
| Restitution | Dashboard et notebook patients | Dashboard des trois domaines, CSV, API de lecture et dossier de soutenance |
| Base serveur | Sans nouvelle projection relationnelle | Schéma PostgreSQL et générateur d’export SQL ; interface active sur SQLite |
| Vérification | Quatre tests de réconciliation initiaux | 25 tests locaux, dont les huit sections et un parcours complet de revue |

Le commit initial `070c381` permet de retrouver la base. Les ajouts sont regroupés dans la branche `amelioration-projet-scolaire`. `legacy_app.py` conserve l’ancienne interface ; le notebook et les données historiques restent disponibles.

## 3. Introduction orale à adapter — environ 90 secondes

> Notre projet répond à un problème de cohérence des données dans un hôpital. Un patient peut avoir plusieurs dossiers dans les admissions, le laboratoire et le dossier patient. Le même problème existe pour le personnel et pour les références produits.
>
> Nous avons construit un hub de consolidation pour ces trois domaines. Il importe les données, conserve leur origine, vérifie leur qualité et normalise les valeurs. Il recherche ensuite les identités qui pourraient correspondre, puis compare trois méthodes de rapprochement.
>
> Une fusion demande des preuves suffisantes. Un score élevé ne permet pas de contourner une date de naissance contradictoire ou un conditionnement produit différent. Les cas ambigus sont soumis à un Data Steward, qui explique sa décision.
>
> Chaque exécution produit une nouvelle version des fiches maîtres, avec les correspondances sources et la provenance de chaque attribut. Nous pouvons donc expliquer une valeur retenue et retrouver une version précédente.
>
> La démonstration utilise des données synthétiques. Nous avons aussi retraité les CSV patients du dépôt initial. Les tests vérifient notamment les fusions indirectes, les rejets humains et la séparation entre matching et vérité d’évaluation. SQLite permet un lancement local ; la projection PostgreSQL constitue l’étape serveur préparée.

## 4. Démonstration commentée, écran par écran

Lancer l’application avec les commandes du README, puis suivre cet ordre.

### Pilotage — expliquer le résultat global

Dire : « Nous avons 11 tables simulées, représentant 459 identités locales. Le moteur construit 183 fiches maîtres. Une fiche maître peut regrouper plusieurs identités locales, mais certains fragments restent volontairement séparés faute de preuve ou à cause d’une contradiction. »

Montrer les trois domaines et les 42 anomalies de la démo de référence. Ne pas confondre une anomalie d’attribut, une paire à examiner et une personne distincte : ces unités de mesure sont différentes.

### Sources & qualité — montrer une correction contrôlée

Choisir Patients. Montrer une date comme `2026-02-30`, puis la ligne `INVALID_DATE`. Expliquer : « La valeur brute reste conservée. La date normalisée devient vide parce que le calendrier la rend impossible. Nous n’inventons pas une date de remplacement. »

Montrer aussi la suppression des espaces superflus et la normalisation d’un nom. La normalisation rend les valeurs comparables ; elle ne prouve pas que les deux lignes décrivent la même personne.

### Matching & évaluation — expliquer la décision

Dire : « Nous commençons par le blocking pour éviter de comparer toutes les lignes. Ensuite nous comparons les paires candidates par égalité, similarité pondérée et rapport de vraisemblance illustratif. »

Pour la méthode pondérée, le seuil bas est 0,70 et le seuil haut 0,93. Le seuil haut ne suffit pas : le moteur demande aussi une couverture minimale des champs et des preuves adaptées au domaine. Pour un patient, les noms doivent être proches, la date égale et un contact ou identifiant partagé présent. Une contradiction critique bloque la fusion.

Montrer la précision et le rappel, puis dire : « Une précision élevée ne veut pas dire que tous les doublons ont été retrouvés. Nous mesurons aussi les paires perdues au blocking, les cas en revue et les faux liens après regroupement. »

### Revue humaine — montrer une décision qui a un effet traçable

1. Choisir une paire à examiner et comparer ses deux identités.
2. Lire les caractéristiques du score et le motif.
3. Saisir un identifiant de Steward et une justification.
4. Enregistrer CONFIRM, REJECT ou ESCALATE selon les preuves disponibles.
5. Garder « Reprendre les décisions de cette version » coché et exécuter le pipeline.
6. Consulter la nouvelle version et son lignage.

Dire : « La décision est enregistrée immédiatement. Son application crée une nouvelle version ; elle ne réécrit pas la version consultée. Une confirmation ne contourne jamais une contradiction critique. »

Pour une démonstration sans ambiguïté métier, enregistrer une escalade justifiée et montrer sa reprise dans la version suivante. Pour montrer une fusion, examiner un cas compatible : ne pas confirmer une paire uniquement pour faire diminuer le nombre de maîtres.

### Référentiels — expliquer d’où vient une valeur

Ouvrir une fiche maître, ses identités sources et la provenance d’un attribut. Dire : « Cette valeur vient de cette application et de cet identifiant local. Les autres valeurs candidates restent visibles. La priorité de source est une règle de gouvernance à valider avec le Data Owner. »

Pour un patient avec une allergie, montrer que le statut `a_valider` reste présent. La consolidation de l’identité n’effectue aucune validation clinique.

### Historique & API — montrer la preuve de traçabilité

Afficher les versions et les événements d’audit. Revenir à une ancienne version via la sélection latérale. Expliquer que le journal et les empreintes servent à détecter une altération partielle ; ils ne constituent pas une preuve externe contre un administrateur qui réécrirait toute la base.

## 5. Les résultats à commenter correctement

| Population | Résultat exécuté | Interprétation |
| --- | --- | --- |
| Démo des trois domaines | 459 identités, 183 maîtres, 42 anomalies | Taille du prototype, pas volume d’un hôpital réel |
| Patients de la petite démo, méthode pondérée | Précision auto 100 %, rappel global 78,18 % | Les liens automatiques mesurés sont corrects ; une partie des vraies paires reste séparée ou en revue |
| Personnel de la petite démo, méthode pondérée | Précision auto 100 %, rappel global 81,67 % | Résultat descriptif sur les données générées |
| Produits de la petite démo, méthode pondérée | Précision auto 100 %, rappel global 85,67 % | Les contradictions injectées limitent volontairement les regroupements |
| Patients historiques S1 | 6 889 identités, 2 662 maîtres | Recalcul depuis cinq applications du jeu initial |
| Patients historiques S1, méthode pondérée | Précision auto 100 %, rappel global 89,37 %, rappel blocking 99,84 % | Des vraies paires sont manquées ; le résultat ne généralise pas à des données réelles |

Les mesures détaillées sont dans [le bilan mesuré](resultats_mesures.md), [les vérifications](verification.md) et `examples/metrics.csv`. Les jeux sont synthétiques, les paramètres probabilistes sont illustratifs et aucun test indépendant n’est revendiqué. Ne pas présenter un score probabiliste de 0,98 comme une certitude clinique à 98 %.

## 6. Questions possibles et réponses courtes

**Pourquoi un MDM plutôt qu’un simple fichier fusionné ?**

Un fichier assemblé ne suffit pas à résoudre les doublons et contradictions. Le hub conserve aussi l’identité maître, les correspondances sources, les règles de choix, les décisions et les versions.

**Quelle différence entre nettoyage et matching ?**

Le nettoyage rend les valeurs exploitables et comparables. Le matching évalue si deux enregistrements décrivent la même identité. Deux noms normalisés égaux ne constituent pas une preuve suffisante.

**Pourquoi le nom seul ne suffit-il pas ?**

Des personnes différentes peuvent partager les mêmes noms. Le moteur demande d’autres indices compatibles et contrôle les contradictions.

**Qu’est-ce que le blocking ?**

C’est une présélection des paires à comparer grâce à plusieurs clés, comme un contact ou une partie de l’identité. Elle réduit les calculs mais peut manquer des correspondances ; son rappel est donc mesuré.

**Qu’est-ce qu’une erreur transitive ?**

Si A ressemble à B et B ressemble à C, on pourrait former A–B–C alors que A et C ont des dates contradictoires. Le moteur vérifie toutes les paires entre les groupes avant de les réunir.

**Un rejet humain peut-il être contourné par un autre lien ?**

Le moteur l’interdit. Il refuse aussi une fusion indirecte qui placerait les deux identités rejetées dans le même groupe. Un test couvre ce comportement.

**Comment choisissez-vous la valeur maître ?**

Une priorité d’application est définie par domaine, puis une règle déterministe départage les lignes. Toutes les valeurs candidates non vides et leur origine restent dans la provenance. Cette priorité doit être approuvée par le responsable métier.

**Pourquoi séparer allergies, affectations et stocks ?**

Ces informations décrivent des relations ou transactions. Une allergie n’est pas une clé d’identité, une affectation peut changer et un stock ne définit pas une référence produit.

**Les identifiants maîtres sont-ils toujours stables ?**

Ils sont stables lorsque les membres du groupe sont identiques. Une fusion ou défusion produit un autre UUID ; le lignage relie les versions. Une diffusion vers d’autres applications devrait appliquer ces correspondances.

**Comment savez-vous que l’évaluation ne décide pas des fusions ?**

Le moteur ne lit pas les étiquettes de vérité. Le module d’évaluation les lit après les décisions. Un test modifie ces étiquettes et vérifie que les paires, maîtres et provenances ne changent pas. Le mode `--no-evaluation` permet aussi d’exécuter le traitement sans cette lecture.

**Pourquoi SQLite si le cadrage cite PostgreSQL ?**

SQLite rend la démo reproductible sans installer un serveur. Un schéma typé et un export transactionnel PostgreSQL sont fournis. L’interface utilise encore SQLite ; l’exécution serveur reste à vérifier dans un environnement disponible.

**Peut-on déployer ce prototype avec de vrais patients ?**

Le prototype démontre les mécanismes MDM. Un usage réel demanderait notamment une validation métier et clinique, des identités sources qualifiées, des droits d’accès, des connecteurs, des sauvegardes et une évaluation indépendante adaptée.

## 7. Où lire le code pour pouvoir répondre

| Fichier | Ce qu’il faut comprendre |
| --- | --- |
| `mdm/demo.py` | Génération déterministe des sources et isolation de la vérité synthétique |
| `mdm/config.py` | Champs, poids, priorités, seuils et contradictions par domaine |
| `mdm/engine.py` | Ingestion, normalisation, blocking, scores, contrôles des groupes et choix des valeurs |
| `mdm/pipeline.py` | Enchaînement du traitement, reprise des décisions et création des versions |
| `mdm/evaluation.py` | Dénominateurs des métriques, précision, rappel global et faux liens de clusters |
| `mdm/store.py` | Transactions, décisions, audit chaîné et vérification des snapshots |
| `app.py` | Consultation et parcours du Steward dans Streamlit |
| `tests/test_mdm.py` | Cas métier : données invalides, contradictions, rejets indirects et altération |
| `tests/test_interface.py` | Navigation et décision reprise dans une nouvelle version |
| `sql/schema.sql` | Modèle relationnel proposé pour PostgreSQL |

Pour préparer la discussion, chaque membre devrait pouvoir expliquer un cas accepté, un cas refusé et une valeur maître dont il retrouve la provenance. Répéter le parcours complet avec les données synthétiques, puis adapter le discours à ce qui a réellement été observé.
