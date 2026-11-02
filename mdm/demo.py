"""Sources synthétiques déterministes ; la vérité est isolée dans evaluation/."""
import random
from pathlib import Path
from .config import DOMAINS
from .io import write_csv


def generate(root, size=48, seed=42):
    if size < 12:
        raise ValueError("Au moins 12 entités par domaine sont nécessaires.")
    root = Path(root)
    # Ne jamais remplacer silencieusement des sources ou une vérité existante.
    if (root / "sources").exists() or (root / "evaluation").exists():
        raise ValueError("Sources déjà présentes. Choisir un autre dossier pour une nouvelle démonstration.")
    rng = random.Random(seed)
    truth, allergies, assignments, stocks = [], [], [], []
    families = ["El Amrani", "Bennani", "Alaoui", "Idrissi", "Berrada", "Tazi", "Mansouri", "Saidi"]
    given = ["Imane", "Anas", "Salma", "Youssef", "Nadia", "Omar"]
    categories = ["medicament", "reactif", "prelevement", "consommable", "dispositif", "equipement"]
    labels = ["Paracétamol", "Réactif glucose", "Tube de prélèvement", "Gants examen", "Pince chirurgicale", "Moniteur patient"]
    for domain, spec in DOMAINS.items():
        by_source = {s: [] for s in spec["sources"]}
        for i in range(size):
            if domain == "produit":
                cat = categories[i % 6]
                base = dict(preferred_name=f"{labels[i % 6]} série {i // 6 + 1}", category=cat,
                            manufacturer=f"Fabricant démo {i % 4}", model_reference=f"MOD-{i:04}" if cat == "equipement" else "",
                            dosage="500 mg" if cat == "medicament" else "", form="comprime" if cat == "medicament" else "",
                            package_quantity=str(10 + i // 6), package_unit="unite", sterile="oui" if cat in ("prelevement", "dispositif") else "non",
                            qualified_id=f"P{i:05}", id_issuer="CATALOGUE_DEMO")
            else:
                base = dict(family_name=families[i % 8], given_names=given[(i // 8) % 6],
                            phone=f"06{i + 10000000:08}", email=f"demo.{domain}.{i}@example.org",
                            qualified_id=f"{domain.upper()}-{i:05}", id_issuer=f"REGISTRE_{domain.upper()}_DEMO")
                if domain == "patient":
                    base.update(birth_date=f"{1960 + i % 40}-{1 + i % 12:02}-{1 + i % 27:02}", address=f"{i + 1} rue Démonstration")
                else:
                    base.update(professional_category=["medecin", "infirmier", "stagiaire"][i % 3])
            for si, source in enumerate(spec["sources"]):
                if si > 1 and rng.random() < .25:
                    continue
                local_id = f"{source}-{i:04}"
                row = dict(base, local_id=local_id, updated_at=f"2026-10-{10 + si:02}T12:00:00Z")
                # Erreurs reproductibles : accents, blancs, dates et contacts invalides.
                if si == 1 and i % 4 == 0:
                    field = "preferred_name" if domain == "produit" else "family_name"
                    row[field] = "  " + row[field].upper() + "  "
                if si == 1 and i % 7 == 0:
                    field = "preferred_name" if domain == "produit" else "given_names"
                    row[field] = row[field][:-1] + "x"
                    row["qualified_id"] = ""
                if si == 2 and i % 5 == 0:
                    row["qualified_id"] = ""
                    if domain != "produit":
                        row["phone"], row["email"] = "123", "adresse-invalide"
                if domain == "patient" and si == 1 and i % 11 == 0:
                    row["birth_date"] = "2026-02-30"
                # Contradiction critique volontaire, même référence mais conditionnement différent.
                if domain == "produit" and si == 1 and i % 13 == 0:
                    row["package_quantity"] = "999"
                if domain == "personnel" and si == 2 and i % 11 == 0:
                    row["qualified_id"] = "AUTRE-" + str(i)
                by_source[source].append(row)
                truth.append(dict(domain=domain, source=source, local_id=local_id, entity_id=f"{domain}-{i:04}"))
                if domain == "patient" and source == "dpi" and i % 8 == 0:
                    allergies.append(dict(source=source, local_id=local_id, substance="pénicilline", clinical_status="a_valider", provenance="dpi.allergie_patient", validated_by=""))
                if domain == "personnel" and source == "rh":
                    assignments.append(dict(source=source, local_id=local_id, service=["urgences", "pediatrie", "laboratoire"][i % 3], start_date="2026-09-01"))
                if domain == "produit" and source == "achats":
                    stocks.append(dict(source=source, local_id=local_id, lot=f"LOT-{i}", quantity=str(i + 20), location="magasin_demo"))
        for source, rows in by_source.items():
            write_csv(root / "sources" / domain / f"{source}.csv", rows)
    write_csv(root / "evaluation" / "truth.csv", truth)
    write_csv(root / "related" / "allergies.csv", allergies)
    write_csv(root / "related" / "affectations.csv", assignments)
    write_csv(root / "related" / "stocks.csv", stocks)


def import_legacy(root, legacy, scenario):
    """Adapte les CSV bruts patients du dépôt, jamais les Golden Records calculés."""
    import json
    from .io import read_csv
    root, legacy = Path(root), Path(legacy)
    if scenario not in ("S1_5pct", "S2_15pct", "S3_30pct"):
        raise ValueError("Scénario patient inconnu.")
    if (root / "sources").exists():
        raise ValueError("Le dossier cible contient déjà des sources.")
    config = json.loads((legacy / "generation_config.json").read_text(encoding="utf-8"))
    for source, spec in config["source_systems"].items():
        records = []
        for r in read_csv(legacy / scenario / spec["identity_file"]):
            records.append(dict(local_id=r[spec["local_patient_id_column"]], family_name=r.get("last_name", ""),
                                given_names=r.get("first_name", ""), birth_date=r.get("date_of_birth", ""),
                                phone=r.get("phone", ""), address=r.get("address", ""),
                                updated_at=r.get("record_updated_at", "")))
        write_csv(root / "sources" / "patient" / f"{source}.csv", records)
    truth = [dict(domain="patient", source=r["source_system"], local_id=r["source_patient_id"], entity_id=r["synthetic_person_id"])
             for r in read_csv(legacy / "ground_truth.csv")]
    write_csv(root / "evaluation" / "truth.csv", truth)
