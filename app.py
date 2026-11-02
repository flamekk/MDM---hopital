from pathlib import Path
import os
import json
import pandas as pd
import altair as alt
import streamlit as st
from mdm.config import DOMAINS, RULE_VERSION
from mdm.demo import generate
from mdm.pipeline import run
from mdm.io import csv_download
from mdm import store

st.set_page_config(page_title="Hospital MDM | Gouvernance", page_icon="🏥", layout="wide")
ROOT = Path(__file__).resolve().parent
WORK = Path(os.environ.get('MDM_WORKSPACE', ROOT / 'workspace'))
st.markdown("""<style>
.stApp {background:#f6f8fb} [data-testid="stSidebar"] {background:#102b3a}
[data-testid="stSidebar"] * {color:#f1f6fa}
[data-testid="stSidebar"] input {color:#102b3a}
h1,h2,h3 {color:#123b4a;letter-spacing:-.025em}
[data-testid="stMetric"] {background:white;border:1px solid #dce6ec;border-radius:12px;padding:18px}
.hero {background:#123b4a;color:white;border-radius:16px;padding:28px 32px;margin-bottom:24px}
.hero h1 {color:white;margin:8px 0;font-size:2.2rem}.hero p {color:#c5e0e5;margin:0}
.eyebrow {font-size:12px;letter-spacing:.17em;color:#6fe0cb}
</style>""", unsafe_allow_html=True)

with st.sidebar:
    st.title("🏥 Hospital MDM")
    st.caption("QUALITÉ · IDENTITÉ · GOUVERNANCE")
    page = st.radio("Navigation", ['Pilotage', 'Sources & qualité', 'Référentiels', 'Revue humaine', 'Matching & évaluation', 'Catalogue & modèle', 'Historique & API', 'Parcours scolaire'])
    st.divider()
    runs = store.list_runs(WORK)
    if not runs:
        st.info("Initialisez les trois domaines pour commencer.")
        if st.button('Initialiser la démonstration', type='primary'):
            try:
                if not (WORK / 'sources').exists():
                    generate(WORK)
                run(WORK)
                st.rerun()
            except (ValueError, OSError) as exc:
                st.error(str(exc))
        st.stop()
    selected = st.selectbox('Version consultée', [r['run_id'] for r in runs], format_func=lambda v: next(r['created_at'][:19].replace('T', ' ') + ' UTC · ' + v[:8] for r in runs if r['run_id'] == v))
    method = st.selectbox('Méthode de la prochaine exécution', ['weighted', 'exact', 'probabilistic'])
    inherit = st.checkbox('Reprendre les décisions de cette version', value=True)
    if st.button('Exécuter le pipeline', type='primary'):
        try:
            with st.spinner('Normalisation, matching et création du référentiel…'):
                run(WORK, method, selected if inherit else None)
            st.rerun()
        except (ValueError, OSError) as exc:
            st.error(str(exc))
    st.caption(f'Règles {RULE_VERSION} · Démonstration locale')

try:
    data = store.load_run(WORK, selected)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

st.markdown('<div class="hero"><span class="eyebrow">PLATEFORME DE DONNÉES HOSPITALIÈRES</span><h1>Des sources multiples. Une identité maîtrisée.</h1><p>Patients, personnel et produits : comprendre, rapprocher et tracer chaque décision.</p></div>', unsafe_allow_html=True)
st.caption(f"Version {selected[:8]} · {data['created_at'][:19]} UTC · Méthode {data['method']} · Sources synthétiques")


def table(rows, height=None):
    if not rows:
        st.info('Aucun enregistrement dans cette sélection.')
        return
    kwargs = dict(width='stretch', hide_index=True)
    if height:
        kwargs['height'] = height
    frame = pd.DataFrame(rows)
    for col in frame.columns:
        if frame[col].map(lambda x: isinstance(x, (dict, list))).any():
            frame[col] = frame[col].map(lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, (list, dict)) else x)
    st.dataframe(frame, **kwargs)


def domain_picker(key):
    present = [d for d in DOMAINS if data['standardized'][d]]
    return st.selectbox('Domaine', present, format_func=lambda d: DOMAINS[d]['label'], key=key)


def percent(value):
    return '—' if value is None else f'{value:.1%}'


if page == 'Pilotage':
    st.subheader('Le référentiel en un regard')
    pending = [p for p in data['pairs'] if p['decision'] == 'REVIEW' and not p['review_decision']]
    c = st.columns(4)
    c[0].metric('Identités sources', len(data['xrefs']))
    c[1].metric('Fiches maîtres', len(data['masters']))
    c[2].metric('Paires à examiner dans cette version', len(pending))
    c[3].metric('Anomalies détectées', len(data['issues']))
    left, right = st.columns([1.3, 1])
    with left:
        st.markdown('### Couverture des trois domaines')
        counts = [{'Domaine': spec['label'], 'Sources': len(data['standardized'][d]), 'Maîtres': sum(r['domain'] == d for r in data['masters'])} for d, spec in DOMAINS.items()]
        chart_data = pd.DataFrame(counts).melt(id_vars='Domaine', var_name='Type', value_name='Nombre')
        chart = alt.Chart(chart_data).mark_bar(cornerRadiusEnd=3).encode(
            y=alt.Y('Domaine:N', sort=None, title=None), x=alt.X('Nombre:Q', scale=alt.Scale(domainMin=0)),
            color=alt.Color('Type:N', scale=alt.Scale(range=['#087f8c', '#95c9d0'])),
            yOffset='Type:N', tooltip=['Domaine', 'Type', 'Nombre']).properties(height=250)
        st.altair_chart(chart, width='stretch')
    with right:
        st.markdown('### Circuit de gouvernance')
        st.markdown('1. **Importer** les sources et conserver leur empreinte.\n2. **Contrôler** les données et isoler les anomalies.\n3. **Rapprocher** les identités avec des preuves explicites.\n4. **Valider** les cas ambigus avec un Data Steward.\n5. **Publier une version** avec provenance et historique.')
        (st.success if store.verify(WORK) else st.error)('Intégrité locale du journal vérifiée.' if store.verify(WORK) else 'Intégrité invalide : consulter le journal.')
    st.info("Les identités restent séparées en présence de contradictions critiques. Les allergies, affectations et stocks sont rattachés par correspondance, hors des critères de matching.")

elif page == 'Sources & qualité':
    domain = domain_picker('source_domain')
    q = next(q for q in data['quality'] if q['domain'] == domain)
    c = st.columns(3)
    c[0].metric('Complétude brute des champs requis', percent(q['raw_completeness']))
    c[1].metric('Complétude valide après contrôle', percent(q['valid_required_completeness']))
    c[2].metric('Validité syntaxique des valeurs fournies', percent(q['validity']))
    st.caption(q['note'])
    a, b, ctab = st.tabs(['Données brutes', 'Données normalisées', 'Anomalies et remédiation'])
    with a:
        table(data['raw'][domain], 360)
    with b:
        table(data['standardized'][domain], 360)
        st.download_button('Exporter les données normalisées', csv_download(data['standardized'][domain]), f'{domain}_standardized.csv')
    with ctab:
        issues = [r for r in data['issues'] if r['domain'] == domain]
        table(issues)
        st.caption('Une date impossible ou un contact invalide devient une valeur vide. Corriger la source, puis créer une nouvelle exécution ; la valeur brute reste conservée.')

elif page == 'Référentiels':
    domain = domain_picker('master_domain')
    query = st.text_input('Rechercher un nom, une référence ou un identifiant')
    rows = [r for r in data['masters'] if r['domain'] == domain and query.casefold() in json.dumps(r, ensure_ascii=False).casefold()]
    table(rows, 330)
    st.download_button('Exporter la sélection', csv_download(rows), f'{domain}_masters.csv')
    if rows:
        chosen = st.selectbox('Fiche à examiner', [r['master_id'] for r in rows])
        a, b, c = st.tabs(['Identités sources', 'Provenance des attributs', 'Tables rattachées'])
        with a:
            table([r for r in data['xrefs'] if r['master_id'] == chosen])
        with b:
            table([r for r in data['provenance'] if r['master_id'] == chosen])
        with c:
            related = [dict(r, table=name) for name, records in data['related'].items() for r in records if r['master_id'] == chosen]
            table(related)
            st.caption('Une allergie déclarée « a_valider » reste non validée après le rapprochement des identités.')

elif page == 'Revue humaine':
    if 'review_notice' in st.session_state:
        st.success(st.session_state.pop('review_notice'))
    domain = domain_picker('review_domain')
    latest_decisions = store.decisions(WORK, selected)
    status = st.selectbox('Afficher', ['À examiner', 'Contradictions critiques', 'Toutes les paires'])
    scoped = [p for p in data['pairs'] if p['domain'] == domain]
    if status == 'À examiner':
        scoped = [p for p in scoped if (p['decision'] == 'REVIEW' or p['cluster_result'].startswith('BLOCKED')) and p['case_id'] not in latest_decisions and not p['review_decision']]
    elif status == 'Contradictions critiques':
        scoped = [p for p in scoped if p['critical_conflicts']]
    st.write(f'{len(scoped)} paire(s)')
    table([{k: p[k] for k in ['case_id', 'source_a', 'local_id_a', 'source_b', 'local_id_b', 'score', 'decision', 'reason', 'cluster_result']} for p in scoped[:300]])
    if scoped:
        case_id = st.selectbox('Cas à traiter', [p['case_id'] for p in scoped])
        pair = next(p for p in scoped if p['case_id'] == case_id)
        records = {r['rid']: r for r in data['standardized'][domain]}
        a, b = st.columns(2)
        with a:
            st.markdown('**Identité A**')
            st.json(records[pair['a']])
        with b:
            st.markdown('**Identité B**')
            st.json(records[pair['b']])
        with st.expander('Comprendre le score'):
            st.json(dict(similarities=pair['features'], observed_weight=pair['coverage'], reason=pair['reason']))
        if pair['critical_conflicts']:
            st.warning('Confirmation bloquée : corriger les contradictions dans les sources avant un nouveau traitement.')
        with st.form('human_review'):
            reviewer = st.text_input('Identifiant du Data Steward')
            options = ['REJECT', 'ESCALATE'] if pair['critical_conflicts'] else ['CONFIRM', 'REJECT', 'ESCALATE']
            decision = st.selectbox('Décision', options)
            comment = st.text_area('Justification obligatoire')
            submitted = st.form_submit_button('Enregistrer la décision')
        if submitted:
            try:
                store.review(WORK, selected, case_id, decision, reviewer, comment)
                st.session_state['review_notice'] = 'Décision enregistrée. Exécutez le pipeline en reprenant cette version pour appliquer la décision.'
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))
    st.markdown('### Décisions enregistrées depuis cette version')
    table(list(latest_decisions.values()))
    st.caption('La version consultée reste un snapshot immuable. La décision prend effet dans la prochaine version, après contrôle de cohérence du groupe entier.')

elif page == 'Matching & évaluation':
    st.subheader('Comparer les méthodes sur une même population')
    baseline = [r for r in data['metrics'] if r['stage'] == 'automatic_baseline']
    table(baseline)
    if baseline:
        frame = pd.DataFrame(baseline)
        frame['Méthode'] = frame['domain'] + ' / ' + frame['method']
        st.bar_chart(frame.set_index('Méthode')[['automatic_precision', 'automatic_global_recall', 'blocking_recall']])
    else:
        st.info("Pas de vérité terrain fournie : aucun chiffre de précision ou de rappel n'est inventé.")
    st.markdown('**Précision** : part des rapprochements automatiques corrects. **Rappel global** : part de toutes les vraies paires retrouvées, y compris celles perdues au blocking. **Liens faux de cluster** : erreurs après fermeture transitive.')
    st.warning("Le score probabiliste utilise des paramètres illustratifs et une hypothèse d'indépendance. Il ne constitue pas une probabilité calibrée. Les résultats sont descriptifs sur un jeu synthétique ; aucun jeu de test indépendant n'est revendiqué.")
    st.markdown('### Résultat de la version courante, après décisions reprises')
    table([r for r in data['metrics'] if r['stage'] == 'current_version'])
    st.download_button('Exporter les mesures', csv_download(data['metrics']), 'evaluation.csv')

elif page == 'Catalogue & modèle':
    st.subheader('Catalogue des sources réellement chargées')
    table(data['catalogue'])
    st.download_button('Exporter le catalogue', csv_download(data['catalogue']), 'catalogue.csv')
    st.markdown('### Modèle et responsabilités')
    st.graphviz_chart('digraph { rankdir=LR; Sources -> Brut -> Normalisation -> Matching; Matching -> Revue; Matching -> Masters; Revue -> Masters; Masters -> XREF; Masters -> Provenance; Masters -> Relations; }')
    st.markdown('**Data Owner** : définit le sens des attributs et approuve les règles. **Data Steward** : contrôle les cas et justifie les décisions. **Équipe technique** : maintient les imports, les versions et les sauvegardes.')
    st.caption('Le prototype actif utilise SQLite. Le schéma PostgreSQL et son export SQL sont fournis pour l’étape de migration décrite dans le guide.')
    for label, filename in [('Dictionnaire des données', 'dictionnaire.md'), ('Architecture et décisions', 'architecture.md')]:
        with st.expander(label):
            st.markdown((ROOT / 'docs' / filename).read_text(encoding='utf-8'))

elif page == 'Historique & API':
    st.subheader('Versions et audit')
    table(runs)
    valid = store.verify(WORK)
    (st.success if valid else st.error)('Empreintes et chaîne d’audit valides.' if valid else 'Altération détectée.')
    st.caption('Cette chaîne détecte des modifications accidentelles ou partielles. Un administrateur local peut réécrire la base et toute la chaîne ; ce mécanisme ne fournit pas de signature externe.')
    table(store.audit_log(WORK), 330)
    st.markdown('### Lignage de la version')
    table(data['lineage'])
    st.markdown('### API locale de consultation')
    st.code('.\\.venv\\Scripts\\python.exe -m mdm api --port 8080\n# GET http://127.0.0.1:8080/api/runs\n# GET http://127.0.0.1:8080/api/runs/<run_id>/masters', language='powershell')
    st.caption('Pour revenir à une ancienne version, sélectionnez-la dans la barre latérale. Aucun ancien snapshot n’est écrasé.')

else:
    st.subheader('Votre parcours, étape par étape')
    st.markdown((ROOT / 'docs' / 'guide_etape_par_etape.md').read_text(encoding='utf-8'))

st.divider()
st.caption('Projet scolaire · Données entièrement synthétiques · Validation des règles et du périmètre à soumettre au formateur')
