# Dictionnaire et contrat des CSV

## Extension Hôpital Al Amal

Les relations ajoutent `assertion_id` (empreinte de l’identifiant de déclaration qualifié par sa table et sa source), `source_hash` (SHA-256 du contenu source) et `source_record` (copie de la déclaration brute). Les huit tables liées sont `allergies`, `sejours`, `contacts_urgence`, `affectations`, `formations`, `gardes`, `stocks` et `equipements`.

| Relation / événement | Attributs complémentaires | Règles |
| --- | --- | --- |
| allergies | record_id, substance, allergy_category, manifestation, reported_severity, reported_at, provenance, clinical_status, validation_status | Statuts de revue : a_valider, confirmee, ecartee, a_completer ; aucune utilisation dans le matching |
| sejours | service, care_type, admission_date, discharge_date, room, bed, care_status | Relation patient / épisode déclaré par la source |
| contacts_urgence | contact_name, relationship, phone, provenance | Contact désigné distinct de l’identité patient |
| formations / gardes | training_name, completion_date, renewal_date / shift_date, shift_period, service | Relations professionnelles sourcées, pas des clés d’identité |
| stocks | lot, quantity, reorder_level, expiry_date, location | Quantités disponibles distinctes du conditionnement du produit maître |
| equipements | serial_number, service, inventory_status, last_maintenance, next_maintenance | Instances physiques liées à une référence de modèle |
| attribute_decisions | event_id, run_id, case_id, decision, selected_value, selected_source, selected_local_id, reviewer, comment, created_at | SELECT_VALUE ou ESCALATE ; candidat observé obligatoire ; publication dans une nouvelle version |
| clinical_decisions | event_id, run_id, assertion_id, source_hash, decision, reviewer, reviewer_role, comment, created_at | CONFIRM, REFUTE ou REQUEST_INFO ; Médecin / Pharmacien déclarés, justification obligatoire |

La provenance d’un attribut arbitré porte la règle `HUMAN_SELECTED_VALUE` et le statut `RESOLVED`. Les alternatives restent conservées. Une ancienne décision ne modifie pas un groupe dont l’UUID a changé. Les relations brutes ne sont pas réécrites par une décision ; la version conserve la décision et sa projection.

Les noms physiques du prototype sont anglais. Les champs texte sont normalisés sans accents et en minuscules pour comparer les valeurs. Les valeurs d’origine restent dans la zone brute. Les types ci-dessous décrivent la projection PostgreSQL ; SQLite conserve des snapshots JSON.

## Champs communs

| Champ | Type cible | Définition / contrainte | Origine et règle |
| --- | --- | --- | --- |
| run_id | UUID | Clé de la version ; obligatoire | Généré à chaque exécution |
| master_id | UUID | Clé maître dans une version | UUID v5 dérivé du domaine et des membres |
| domain | VARCHAR(20) | patient, personnel ou produit | Configuration de la table source |
| status | VARCHAR(20) | ACTIVE dans le prototype | Statut de publication |
| rules_version | VARCHAR(30) | Version des règles | `mdm/config.py` |
| created_at | TIMESTAMPTZ | Horodatage UTC de la version | Horloge d’exécution |
| source | VARCHAR(100) | Application d’origine | Nom du CSV sans extension |
| local_id | VARCHAR(150) | Identifiant local non vide ; unique par domaine/source | Source ; jamais utilisé seul comme identité globale |
| rid | VARCHAR(24) | Empreinte de la clé qualifiée | Calculée avant normalisation |
| qualified_id | VARCHAR(150) | Identifiant partagé vérifié dans le contexte de démo | Comparaison seulement avec le même émetteur |
| id_issuer | VARCHAR(150) | Émetteur de l’identifiant partagé | Indissociable de qualified_id |
| member_count / source_count | INTEGER | Nombre de lignes / d’applications du groupe | Calculé après rapprochement |

Une valeur vide ne vaut jamais accord. Les champs d’identifiant sont optionnels ; les identifiants globaux de la démo appartiennent à des registres simulés, pas à un système officiel. Dans un import réel il faudrait qualifier leur fiabilité avant d’appliquer ces règles.

## Patient maître

| Champ | Type cible | Définition / contraintes | Source prioritaire |
| --- | --- | --- | --- |
| family_name | VARCHAR(150) | Nom d’identité ; requis en qualité | admission, puis dpi, labo |
| given_names | VARCHAR(150) | Prénoms ; requis en qualité | Même priorité |
| birth_date | DATE | Date réelle, entre 1850 et le jour d’import ; requise en qualité | Même priorité ; toute contradiction connue bloque la fusion |
| phone | VARCHAR(32) | Téléphone marocain 05/06/07 sur 10 chiffres ; +212 normalisé | Même priorité |
| email | VARCHAR(254) | Adresse de contact syntaxiquement valide | Même priorité |
| address | VARCHAR(500) | Adresse déclarative ; non utilisée pour le score actuel | Même priorité |

Le prototype possède un seul champ family_name. La séparation nom de naissance / nom d’usage proposée dans le cadrage est une extension documentée, pas une fonctionnalité annoncée comme réalisée.

## Personnel maître

| Champ | Type cible | Définition / valeurs | Source prioritaire |
| --- | --- | --- | --- |
| family_name / given_names | VARCHAR(150) | Identité du professionnel ou stagiaire ; requise | rh, puis planning, formation |
| professional_category | VARCHAR(30) | medecin, infirmier, stagiaire, technicien, administratif, autre ; requise | Même priorité |
| email | VARCHAR(254) | Courriel professionnel ; critère exact | Même priorité |
| phone | VARCHAR(32) | Contact professionnel | Même priorité |

`email` et `phone` correspondent aux notions professional_email et professional_phone du texte de cadrage. Les affectations ne sont pas fusionnées dans l’identité.

## Produit maître

| Champ | Type cible | Définition / valeurs | Source prioritaire |
| --- | --- | --- | --- |
| preferred_name | VARCHAR(250) | Désignation préférée ; requise | pharmacie, labo, bloc, achats, biomedical |
| category | VARCHAR(30) | medicament, reactif, prelevement, consommable, dispositif, equipement ; requise | Même priorité |
| manufacturer | VARCHAR(200) | Fabricant déclaré ; requis pour preuve forte des équipements | Même priorité |
| model_reference | VARCHAR(100) | Référence de modèle ; requise pour preuve forte des équipements | Même priorité |
| dosage | VARCHAR(100) | Dosage textuel normalisé ; requis pour preuve forte des médicaments | Même priorité |
| form | VARCHAR(100) | Forme pharmaceutique ; requise pour preuve forte des médicaments | Même priorité |
| package_quantity | DECIMAL(12,3) | Quantité par conditionnement, strictement positive ; requise | Même priorité |
| package_unit | VARCHAR(20) | Unité normalisée ; requise | Même priorité |
| sterile | VARCHAR(20) | oui, non ou inconnu | Même priorité |

Les conversions entre dosages ou unités ne sont pas réalisées. Un « 0,5 g » et un « 500 mg » nécessitent une règle métier validée ; le moteur privilégie une séparation conservatrice. Les dimensions, compositions détaillées et normes d’équipement restent des extensions.

## Tables liées, qualité et traçabilité

| Table / sortie | Clé / champs principaux | Rôle |
| --- | --- | --- |
| xrefs | run_id + domain + source + local_id ; master_id | Une correspondance exactement par identité source |
| provenance | master_id + field ; value, selected_source, selected_local_id, candidates, policy, conflict | Valeur retenue et toutes les alternatives non vides |
| pairs | case_id ; a, b, score, coverage, features, decision, reason, cluster_result | Preuves de rapprochement ; AUTO, REVIEW, NO_MATCH |
| issues | domain, rid, field, code, raw_value | Erreurs syntaxiques et champs requis absents |
| quality | complétude brute/valide, validité, dénominateurs | Mesures calculées et interprétables |
| allergies | source, local_id, master_id, substance, clinical_status, validated_by, provenance | Déclaration clinique sourcée ; a_valider conservé |
| affectations | source, local_id, master_id, service, start_date | Relation personne/service |
| stocks | source, local_id, master_id, lot, quantity, location | Stock d’un lot, distinct du conditionnement |
| decisions | event_id, run_id, case_id, decision, reviewer, comment, created_at | CONFIRM, REJECT, ESCALATE ; justification obligatoire |
| audit | seq, event, previous_hash, event_hash | Journal chaîné, append-only dans l’application |
| lineage | previous_master_id, master_id, relationship | Correspondance entre deux versions |

Les contraintes de qualité « requis » n’empêchent pas la conservation d’une ligne incomplète. Elles produisent une anomalie et peuvent empêcher une fusion automatique. Les clés obligatoires et les références orphelines provoquent un échec d’import explicite.
