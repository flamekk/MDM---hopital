RULE_VERSION = "2.0.1"
DOMAINS = {
    "patient": {
        "label": "Patients", "sources": ["admission", "dpi", "labo"],
        "owner": "Responsable des admissions", "classification": "Restreint",
        "fields": ["family_name", "given_names", "birth_date", "phone", "email", "address", "qualified_id", "id_issuer"],
        "required": ["family_name", "given_names", "birth_date"],
        "weights": {"family_name": .28, "given_names": .22, "birth_date": .30, "phone": .15, "email": .05},
        "critical": ["birth_date"],
    },
    "personnel": {
        "label": "Personnel", "sources": ["rh", "planning", "formation"],
        "owner": "Responsable RH", "classification": "Restreint",
        "fields": ["family_name", "given_names", "professional_category", "email", "phone", "qualified_id", "id_issuer"],
        "required": ["family_name", "given_names", "professional_category"],
        "weights": {"family_name": .35, "given_names": .25, "email": .30, "phone": .10},
        "critical": [],
    },
    "produit": {
        "label": "Produits et matériels", "sources": ["pharmacie", "labo", "bloc", "achats", "biomedical"],
        "owner": "Responsables pharmacie / achats / biomédical", "classification": "Interne",
        "fields": ["preferred_name", "category", "manufacturer", "model_reference", "dosage", "form", "package_quantity", "package_unit", "sterile", "qualified_id", "id_issuer"],
        "required": ["preferred_name", "category", "package_quantity", "package_unit"],
        "weights": {"preferred_name": .35, "manufacturer": .10, "model_reference": .15, "dosage": .15, "form": .10, "package_quantity": .10, "package_unit": .05},
        "critical": ["category", "model_reference", "dosage", "form", "package_quantity", "package_unit", "sterile"],
    },
}
METHODS = ("exact", "weighted", "probabilistic")
# Paramètres illustratifs de rapport de vraisemblance, non appris sur la vérité.
FS = {"prior": .02, "agreement_match": .90, "agreement_nonmatch": .05,
      "partial_match": .08, "partial_nonmatch": .15,
      "disagreement_match": .02, "disagreement_nonmatch": .80}
THRESHOLDS = {"weighted": (.70, .93), "probabilistic": (.20, .98)}
