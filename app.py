"""Hôpital Al Amal : le parcours patient d'origine, partagé par trois MDM."""
from pathlib import Path
import json
import os
import streamlit as st
from mdm.config import DOMAINS, RULE_VERSION
from mdm.hospital import HOSPITAL_NAME, SCENARIOS, generate_hospital
from mdm.io import digest, csv_download
from mdm.pipeline import run
from mdm import store
from ui.components import esc, table
from ui.profiles import golden, hospital_view
from ui.workflow import TABS, overview, pairs_view, conflicts_view, audit_view, reconciliation_view, quality_view

ROOT=Path(__file__).resolve().parent
BASE=Path(os.environ.get('MDM_WORKSPACE',ROOT/'workspace_hospital'))
st.set_page_config(page_title=f'{HOSPITAL_NAME} | Référentiels MDM',page_icon='🏥',layout='wide')
st.html(ROOT/'ui/styles.css')
single=(BASE/'sources').exists()
single_scenario='S1_5pct'
if single and (BASE/'hospital.json').exists():
    single_scenario=json.loads((BASE/'hospital.json').read_text(encoding='utf-8')).get('scenario',single_scenario)
    if single_scenario not in SCENARIOS: single_scenario='S1_5pct'
with st.sidebar:
    st.markdown('<div class="aa-brand"><div class="aa-cross"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M9 3h6v6h6v6h-6v6H9v-6H3V9h6z" fill="currentColor"/></svg></div><div><strong>Hôpital Al Amal</strong><small>Référentiels hospitaliers</small></div></div>',unsafe_allow_html=True)
    st.caption('RÉFÉRENTIELS')
    domain=st.radio('Référentiel actif',list(DOMAINS),format_func=lambda d:DOMAINS[d]['label'],key='mdm_domain',label_visibility='collapsed')
    st.divider()
    scenario=st.selectbox('Scénario actif',[single_scenario] if single else list(SCENARIOS),format_func=lambda s:SCENARIOS[s],key='mdm_scenario')
    work=BASE if single else BASE/scenario
    runs=store.list_runs(work)
    if not runs:
        st.info('Préparez les données hospitalières pour commencer.')
        if st.button('Initialiser ce scénario',type='primary'):
            try:
                with st.spinner('Préparation des sources et des référentiels…'):
                    if not (work/'sources').exists(): generate_hospital(work,scenario=scenario)
                    run(work)
                st.rerun()
            except (ValueError,OSError) as exc: st.error(str(exc))
        st.stop()
    version_key='version_'+digest(str(work))[:10]
    requested=st.session_state.pop('requested_version',None)
    if requested and requested in [r['run_id'] for r in runs]: st.session_state[version_key]=requested
    selected=st.selectbox('Version du référentiel',[r['run_id'] for r in runs],format_func=lambda rid:next(r['created_at'][:16].replace('T',' ')+' UTC · '+rid[:8] for r in runs if r['run_id']==rid),key=version_key)
    st.divider()
    section=st.radio('Espace de travail',['Référentiel MDM','Vue hospitalière','Qualité & méthodes','Catalogue & aide'],key='workspace_section')
    st.divider()
    reviewer=st.text_input('Identifiant du réviseur',placeholder='Nom ou identifiant professionnel',key='reviewer')
    st.caption('Les décisions exigent un réviseur et une justification. La fonction clinique reste déclarative dans la démo.')

try:
    data=store.load_run(work,selected)
except ValueError as exc:
    st.error(str(exc))
    st.stop()

context=f'{work}/{selected}/{domain}'
if st.session_state.get('ui_context')!=context:
    for key in ['pair_case','attribute_case','attribute_value','clinical_assertion','golden_patient','golden_personnel','golden_produit','reconciliation_method']:
        st.session_state.pop(key,None)
    st.session_state['ui_context']=context
if not data['standardized'].get(domain):
    st.info('Ce jeu ne contient pas ce domaine. Sélectionnez un référentiel disponible.')
    st.stop()

titles={'patient':('Référentiel patients','Une identité commune, des déclarations sourcées et un parcours de soins traçable.'),
        'personnel':('Référentiel du personnel','Des professionnels identifiés au-delà des matricules, services et affectations.'),
        'produit':('Référentiel produits & matériels','Des références communes pour la pharmacie, les achats et les services hospitaliers.')}
title,subtitle=titles[domain]
st.markdown(f'<div class="aa-breadcrumb">{esc(HOSPITAL_NAME)} <span>/</span> Gouvernance des données <span>/</span> <b>{esc(DOMAINS[domain]["label"])}</b></div><div class="aa-head"><div><h1>{esc(title)}</h1><p>{esc(subtitle)}</p></div><div class="aa-version"><span class="aa-dot"></span>Version publiée · {esc(selected[:8])}<br>{esc(SCENARIOS[scenario])}</div></div>',unsafe_allow_html=True)
if 'notice' in st.session_state: st.success(st.session_state.pop('notice'))

if section=='Référentiel MDM':
    tabs=st.tabs(TABS,key=f'mdm_tabs_{domain}')
    with tabs[0]:
        comparison=[]
        for name in ([scenario] if single else SCENARIOS):
            path=work if single else BASE/name
            if not (path/'mdm.sqlite3').exists():
                comparison.append({'Scénario':SCENARIOS[name],'État':'À initialiser'})
                continue
            try:
                snapshot=data if name==scenario else store.load_run(path)
                comparison.append({'Scénario':SCENARIOS[name],'Identités sources':len(snapshot['standardized'][domain]),'Golden Records':sum(r['domain']==domain for r in snapshot['masters']),'Paires en revue':sum(r['domain']==domain and r['decision']=='REVIEW' for r in snapshot['pairs'])})
            except ValueError: comparison.append({'Scénario':SCENARIOS[name],'État':'À initialiser'})
        overview(data,domain,work,comparison)
    with tabs[1]: golden(data,domain,work)
    with tabs[2]: pairs_view(data,domain,work,reviewer)
    with tabs[3]: conflicts_view(data,domain,work,reviewer)
    with tabs[4]: audit_view(data,work)
    with tabs[5]: reconciliation_view(data,work,domain)
elif section=='Vue hospitalière':
    hospital_view(data,domain,work,reviewer)
elif section=='Qualité & méthodes':
    quality_view(data,domain)
else:
    catalogue,guide,architecture=st.tabs(['Catalogue des sources','Guide de présentation','Architecture & dictionnaire'])
    with catalogue:
        table([r for r in data['catalogue'] if r['domain']==domain])
        st.download_button('Exporter le catalogue',csv_download(data['catalogue']),'catalogue_hospitalier.csv')
        st.markdown('### Relations hospitalières chargées')
        table(data.get('related_manifest',[]))
    with guide:
        path=ROOT/'docs/hopital_al_amal.md'
        st.markdown(path.read_text(encoding='utf-8') if path.exists() else (ROOT/'docs/guide_etape_par_etape.md').read_text(encoding='utf-8'))
    with architecture:
        for filename,title in [('architecture.md','Architecture du hub'),('dictionnaire.md','Dictionnaire des données')]:
            with st.expander(title): st.markdown((ROOT/'docs'/filename).read_text(encoding='utf-8'))
        st.caption(f'Règles {RULE_VERSION} · Interface locale sur SQLite · Projection PostgreSQL disponible dans le dossier du projet.')

st.markdown(f'<div class="aa-foot"><span>{esc(HOSPITAL_NAME)} · Démonstration sur données synthétiques</span><span>Chargement : {esc(data["created_at"][:16].replace("T"," "))} UTC</span></div>',unsafe_allow_html=True)
