from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import pandas as pd
import streamlit as st
from reconciliation import build_reconciliation, save_reconciliation

st.set_page_config(page_title="Patient MDM — Human Review", page_icon="🩺", layout="wide")

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "patient_mdm_synthetic_dataset"
SCENARIOS = ["S1_5pct", "S2_15pct", "S3_30pct"]

def load_csv(path, **kwargs):
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, **kwargs)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()

def save_csv(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8")

def stable_hash(row):
    payload = json.dumps({str(k): (None if pd.isna(v) else str(v)) for k, v in row.items()},
                         sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def append_audit(scenario, case_id, action, old_status, new_status, reviewer, decision, comment, before_hash, after_hash):
    path = DATA_DIR / "mdm_audit_log.csv"
    log = load_csv(path)
    if log.empty and not len(log.columns):
        log = pd.DataFrame(columns=[
            "audit_event_id", "timestamp_utc", "scenario", "case_id", "action",
            "previous_status", "new_status", "reviewer_id", "decision", "comment",
            "before_hash", "after_hash"
        ])
    event_id = f"AUD-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    entry = {
        "audit_event_id": event_id,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scenario": scenario, "case_id": case_id, "action": action,
        "previous_status": old_status, "new_status": new_status,
        "reviewer_id": reviewer, "decision": decision, "comment": comment,
        "before_hash": before_hash, "after_hash": after_hash
    }
    log = pd.concat([log, pd.DataFrame([entry])], ignore_index=True)
    save_csv(log, path)

def read_scenario_golden(scenario):
    return load_csv(DATA_DIR / scenario / "golden_record" / "golden_records.csv")

st.title("🩺 Patient Master Data Management")
st.caption("Prototype local de revue humaine, exploration des Golden Records et traçabilité des décisions.")
if not DATA_DIR.exists():
    st.error(f"Dossier de données introuvable : {DATA_DIR}. Placez le dossier patient_mdm_synthetic_dataset à côté de app.py.")
    st.stop()

with st.sidebar:
    st.header("Paramètres")
    scenario = st.selectbox("Scénario actif", SCENARIOS, index=0)
    reviewer = st.text_input("Identifiant du réviseur", placeholder="ex. HZBARI")
    st.info("Les décisions sont enregistrées dans les CSV locaux. Elles ne fusionnent pas automatiquement les Golden Records.")

summary = load_csv(DATA_DIR / "golden_record_summary.csv")
matching = load_csv(DATA_DIR / "matching_baseline_summary.csv")
review_queue = load_csv(DATA_DIR / "human_review_queue.csv")
conflict_queue = load_csv(DATA_DIR / "attribute_conflict_review_queue.csv")
audit_log = load_csv(DATA_DIR / "mdm_audit_log.csv")

tab_overview, tab_golden, tab_pairs, tab_conflicts, tab_audit, tab_reconciliation = st.tabs([
    "📊 Vue d'ensemble", "🗂️ Golden Records", "🔎 Revue des paires",
    "⚠️ Conflits d'attributs", "📜 Journal d'audit", "🔁 Réconciliation"
])

with tab_overview:
    st.subheader("Indicateurs clés")
    srow = summary[summary["scenario"] == scenario] if not summary.empty else pd.DataFrame()
    mrow = matching[matching["scenario"] == scenario] if not matching.empty else pd.DataFrame()
    rrow = review_queue[review_queue["scenario"] == scenario] if not review_queue.empty else pd.DataFrame()
    crow = conflict_queue[conflict_queue["scenario"] == scenario] if not conflict_queue.empty else pd.DataFrame()
    cols = st.columns(4)
    def first_value(frame, col, default=0):
        return frame.iloc[0][col] if not frame.empty and col in frame.columns else default
    cols[0].metric("Identités sources", f"{int(first_value(srow, 'input_identity_records')):,}")
    cols[1].metric("Golden Records", f"{int(first_value(srow, 'golden_records')):,}")
    cols[2].metric("Paires à examiner", f"{int((rrow['current_status'] == 'PENDING').sum()) if not rrow.empty else 0:,}")
    cols[3].metric("Conflits en attente", f"{int((crow['current_status'] == 'PENDING').sum()) if not crow.empty else 0:,}")
    st.markdown("### Comparaison des scénarios")
    if not summary.empty:
        show = summary.copy()
        if not matching.empty:
            show = show.merge(matching[["scenario", "candidate_pairs", "match_auto", "review", "non_match"]],
                              on="scenario", how="left")
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.warning("Résumé non trouvé.")
    st.markdown("### Répartition des décisions de matching")
    if not matching.empty:
        chart = matching.set_index("scenario")[["match_auto", "review", "non_match"]]
        st.bar_chart(chart)
    st.caption("Les métriques sont calculées sur le jeu synthétique. Les fichiers de vérité terrain sont réservés à l'évaluation et ne sont pas utilisés par cette interface pour prendre des décisions.")

with tab_golden:
    st.subheader(f"Explorateur des Golden Records — {scenario}")
    golden = read_scenario_golden(scenario)
    membership = load_csv(DATA_DIR / scenario / "golden_record" / "cluster_membership.csv")
    if golden.empty:
        st.warning("Fichier golden_records.csv absent ou vide.")
    else:
        q = st.text_input("Recherche (ID, nom, téléphone, adresse)", key="golden_search")
        min_sources = st.selectbox("Nombre minimum de systèmes sources", [1, 2, 3, 4, 5], index=0)
        filtered = golden.copy()
        if "source_count" in filtered:
            filtered = filtered[pd.to_numeric(filtered["source_count"], errors="coerce").fillna(0) >= min_sources]
        if q.strip():
            mask = filtered.astype(str).apply(lambda col: col.str.contains(q.strip(), case=False, na=False)).any(axis=1)
            filtered = filtered[mask]
        st.write(f"{len(filtered):,} résultat(s)")
        st.dataframe(filtered.head(1000), use_container_width=True, hide_index=True)
        if len(filtered) > 1000:
            st.caption("Affichage limité aux 1 000 premières lignes. Affinez la recherche pour retrouver un enregistrement.")
        if not filtered.empty and not membership.empty:
            chosen = st.selectbox("Afficher les membres du Golden Record", filtered["golden_record_id"].astype(str).tolist())
            members = membership[membership["golden_record_id"].astype(str) == chosen]
            st.markdown(f"**Membres de {chosen}**")
            st.dataframe(members, use_container_width=True, hide_index=True)
        st.download_button("Télécharger la sélection CSV", filtered.to_csv(index=False).encode("utf-8-sig"),
                           file_name=f"golden_records_{scenario}.csv", mime="text/csv")

with tab_pairs:
    st.subheader("Revue humaine des paires candidates")
    if review_queue.empty:
        st.warning("human_review_queue.csv introuvable ou vide.")
    else:
        scoped = review_queue[review_queue["scenario"] == scenario].copy()
        statuses = sorted(scoped["current_status"].fillna("PENDING").astype(str).unique().tolist())
        status_filter = st.multiselect("Filtrer par statut", statuses, default=["PENDING"] if "PENDING" in statuses else statuses)
        visible = scoped[scoped["current_status"].fillna("PENDING").astype(str).isin(status_filter)]
        st.write(f"{len(visible):,} cas affiché(s) sur {len(scoped):,}")
        cols = ["case_id", "source_system_a", "source_patient_id_a", "source_system_b", "source_patient_id_b",
                "score", "reason", "dob_exact", "phone_exact", "address_exact", "current_status", "reviewer_decision"]
        st.dataframe(visible[[c for c in cols if c in visible.columns]].head(500), use_container_width=True, hide_index=True)
        if len(visible) > 500:
            st.caption("Liste limitée à 500 lignes pour garder l'interface réactive. Utilisez le filtre ou l'ID de cas.")
        case_ids = visible["case_id"].astype(str).tolist()
        if case_ids:
            selected_case = st.selectbox("Cas à traiter", case_ids)
            record = review_queue[review_queue["case_id"].astype(str) == selected_case].iloc[0]
            with st.expander("Détails de la paire", expanded=True):
                st.json(record.where(pd.notna(record), None).to_dict())
            with st.form("pair_review_form"):
                decision = st.selectbox("Décision", ["CONFIRM_MATCH", "REJECT_MATCH", "ESCALATE"])
                comment = st.text_area("Commentaire / justification", max_chars=1000)
                submit = st.form_submit_button("Enregistrer la décision")
            if submit:
                if not reviewer.strip():
                    st.error("Saisissez votre identifiant de réviseur dans la barre latérale.")
                else:
                    idx = review_queue.index[review_queue["case_id"].astype(str) == selected_case][0]
                    old = review_queue.loc[idx].to_dict()
                    old_status = str(old.get("current_status", "PENDING"))
                    before = stable_hash(old)
                    new_status = {"CONFIRM_MATCH": "REVIEWED_MATCH", "REJECT_MATCH": "REVIEWED_NON_MATCH", "ESCALATE": "ESCALATED"}[decision]
                    review_queue.loc[idx, "current_status"] = new_status
                    review_queue.loc[idx, "reviewer_decision"] = decision
                    review_queue.loc[idx, "reviewer_id"] = reviewer.strip()
                    review_queue.loc[idx, "reviewed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    review_queue.loc[idx, "review_comment"] = comment.strip()
                    after = stable_hash(review_queue.loc[idx].to_dict())
                    save_csv(review_queue, DATA_DIR / "human_review_queue.csv")
                    append_audit(scenario, selected_case, "PAIR_REVIEW", old_status, new_status,
                                 reviewer.strip(), decision, comment.strip(), before, after)
                    st.success("Décision enregistrée et ajoutée au journal d'audit.")
                    st.rerun()

with tab_conflicts:
    st.subheader("Revue des conflits d'attributs")
    if conflict_queue.empty:
        st.warning("attribute_conflict_review_queue.csv introuvable ou vide.")
    else:
        scoped = conflict_queue[conflict_queue["scenario"] == scenario].copy()
        status_vals = sorted(scoped["current_status"].fillna("PENDING").astype(str).unique().tolist())
        status_filter = st.multiselect("Statuts à afficher", status_vals, default=status_vals, key="conflict_status")
        visible = scoped[scoped["current_status"].fillna("PENDING").astype(str).isin(status_filter)]
        st.dataframe(visible.head(500), use_container_width=True, hide_index=True)
        if len(visible) > 500:
            st.caption("Liste limitée à 500 lignes.")
        case_ids = visible["case_id"].astype(str).tolist()
        if case_ids:
            selected_case = st.selectbox("Conflit à traiter", case_ids, key="conflict_case")
            record = conflict_queue[conflict_queue["case_id"].astype(str) == selected_case].iloc[0]
            st.write(f"**Golden Record :** {record.get('golden_record_id', '')}  |  **Attribut :** {record.get('attribute', '')}")
            st.write(f"**Valeurs observées :** {record.get('values', '')}")
            selected_value = st.selectbox("Valeur retenue (si applicable)", [""] + [v.strip() for v in str(record.get("values", "")).split("||") if v.strip()])
            with st.form("conflict_review_form"):
                decision = st.selectbox("Décision", ["ACCEPT_SELECTED_VALUE", "SELECT_ALTERNATIVE_VALUE", "ESCALATE"])
                comment = st.text_area("Commentaire / justification", max_chars=1000, key="conflict_comment")
                submit = st.form_submit_button("Enregistrer le traitement")
            if submit:
                if not reviewer.strip():
                    st.error("Saisissez votre identifiant de réviseur dans la barre latérale.")
                elif decision == "SELECT_ALTERNATIVE_VALUE" and not selected_value:
                    st.error("Choisissez la valeur retenue avant de valider.")
                else:
                    idx = conflict_queue.index[conflict_queue["case_id"].astype(str) == selected_case][0]
                    old = conflict_queue.loc[idx].to_dict()
                    old_status = str(old.get("current_status", "PENDING"))
                    before = stable_hash(old)
                    new_status = {"ACCEPT_SELECTED_VALUE": "RESOLVED_ACCEPTED", "SELECT_ALTERNATIVE_VALUE": "RESOLVED_ALTERNATIVE", "ESCALATE": "ESCALATED"}[decision]
                    conflict_queue.loc[idx, "current_status"] = new_status
                    conflict_queue.loc[idx, "reviewer_decision"] = decision
                    conflict_queue.loc[idx, "reviewer_id"] = reviewer.strip()
                    conflict_queue.loc[idx, "reviewed_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
                    conflict_queue.loc[idx, "review_comment"] = comment.strip()
                    if selected_value:
                        conflict_queue.loc[idx, "selected_value"] = selected_value
                    after = stable_hash(conflict_queue.loc[idx].to_dict())
                    save_csv(conflict_queue, DATA_DIR / "attribute_conflict_review_queue.csv")
                    append_audit(scenario, selected_case, "ATTRIBUTE_CONFLICT_REVIEW", old_status, new_status,
                                 reviewer.strip(), decision, comment.strip(), before, after)
                    st.success("Traitement enregistré et ajouté au journal d'audit.")
                    st.rerun()

with tab_audit:
    st.subheader("Journal d'audit")
    current_log = load_csv(DATA_DIR / "mdm_audit_log.csv")
    if current_log.empty:
        st.info("Aucune décision humaine enregistrée pour le moment.")
    else:
        filt = current_log[current_log["scenario"] == scenario] if "scenario" in current_log.columns else current_log
        st.metric("Événements d'audit (tous scénarios)", len(current_log))
        st.dataframe(filt.sort_values("timestamp_utc", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("Télécharger le journal complet", current_log.to_csv(index=False).encode("utf-8-sig"),
                           file_name="mdm_audit_log.csv", mime="text/csv")
    st.warning("Le journal est append-only via l'interface, mais les CSV restent modifiables manuellement. Pour un environnement de production, utiliser une base de données, des permissions et des contrôles d'intégrité.")


with tab_reconciliation:
    st.subheader("Réconciliation contrôlée des Golden Records")
    st.warning("Seules les décisions humaines CONFIRM_MATCH et REVIEWED_MATCH sont candidates. REJECT_MATCH et ESCALATE ne déclenchent aucune fusion. Les Golden Records de référence ne sont jamais écrasés.")
    st.markdown("""
    **Contrôles appliqués avant chaque fusion :**
    - les deux identités doivent exister dans la membership de référence ;
    - un cluster ne peut pas contenir deux identités du même système source ;
    - les dates de naissance non vides doivent être compatibles ;
    - les paires déjà dans le même cluster ne provoquent pas de fusion supplémentaire.
    """)
    try:
        proposal = build_reconciliation(DATA_DIR, scenario)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Golden Records de référence", f"{proposal['baseline_golden_count']:,}")
        c2.metric("Golden Records proposés", f"{proposal['reconciled_golden_count']:,}")
        c3.metric("Décisions humaines confirmées", f"{proposal['confirmed_decisions_count']:,}")
        merged_count = int((proposal["accepted_decisions"].get("result", pd.Series(dtype=str)) == "MERGED").sum())
        c4.metric("Fusions proposées", f"{merged_count:,}")
        st.markdown("### Aperçu des décisions")
        if not proposal["accepted_decisions"].empty:
            st.write("Décisions acceptées / déjà reliées")
            st.dataframe(proposal["accepted_decisions"], use_container_width=True, hide_index=True)
        if not proposal["rejected_decisions"].empty:
            st.write("Fusions refusées par les contrôles")
            st.dataframe(proposal["rejected_decisions"], use_container_width=True, hide_index=True)
        st.info("La v1 conserve les attributs du Golden Record de référence le plus complet parmi les clusters réunis. Les décisions de conflits d'attributs ne sont pas encore appliquées aux valeurs métier.")
        if st.button("Créer la version de réconciliation v1", type="primary"):
            out_dir = save_reconciliation(proposal)
            append_audit(scenario, f"{scenario}_RECONCILIATION_V1", "RECONCILIATION_RUN",
                         "BASELINE", "RECONCILIATION_V1", reviewer.strip() or "UNSPECIFIED",
                         "CREATE_VERSION", "Version réconciliée créée; baseline conservée.",
                         stable_hash({"baseline_golden_count": proposal["baseline_golden_count"]}),
                         stable_hash({"reconciled_golden_count": proposal["reconciled_golden_count"],
                                      "merged": merged_count}))
            st.success(f"Version enregistrée : {out_dir.relative_to(DATA_DIR)}")
            st.rerun()
        version_dirs = sorted(
            [p for p in (DATA_DIR / scenario).glob("reconciliation_v*") if p.is_dir()],
            key=lambda p: int(p.name.removeprefix("reconciliation_v")) if p.name.removeprefix("reconciliation_v").isdigit() else 0
        )
        if version_dirs:
            st.success(f"{len(version_dirs)} version(s) de réconciliation déjà créée(s) pour ce scénario.")
            chosen_version = st.selectbox("Consulter une version existante", version_dirs, format_func=lambda p: p.name)
            summary_df = load_csv(chosen_version / "reconciliation_summary.csv")
            st.dataframe(summary_df, use_container_width=True, hide_index=True)
            st.download_button("Télécharger le résumé de réconciliation",
                               summary_df.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"reconciliation_summary_{scenario}_{chosen_version.name}.csv", mime="text/csv")
    except Exception as exc:
        st.error(f"Impossible de préparer la réconciliation : {exc}")

st.divider()
st.caption("Prototype pédagogique — ne pas utiliser pour des décisions médicales ou sur des données patients réelles.")
