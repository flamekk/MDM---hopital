from collections import Counter
import json
import streamlit as st
from mdm.config import DOMAINS
from mdm.hospital import attribute_conflicts, allergy_rows
from mdm.io import csv_download, digest
from mdm.pipeline import run
from mdm import store
from .components import FIELDS, STATUS, bars, details, esc, label, percent, profile, table, tag

TABS=['Vue d’ensemble','Golden Records','Revue des paires','Conflits d’attributs','Journal d’audit','Réconciliation']


def pending_pairs(data,domain,live):
    return [p for p in data['pairs'] if p['domain']==domain and (p['decision']=='REVIEW' or p['cluster_result'].startswith('BLOCKED')) and not p.get('review_decision') and p['case_id'] not in live]


def overview(data,domain,root,comparison):
    live=store.decisions(root,data['run_id'])
    attr_live=store.extra_decisions(root,data['run_id'],'attribute')
    conflicts=[r for r in attribute_conflicts(data) if r['domain']==domain]
    pending_conflicts=[r for r in conflicts if r['resolution_status']=='PROPOSED' and r['case_id'] not in attr_live]
    cols=st.columns(4)
    cols[0].metric('Identités sources',len(data['standardized'][domain]))
    cols[1].metric('Golden Records',sum(r['domain']==domain for r in data['masters']))
    cols[2].metric('Paires à examiner',len(pending_pairs(data,domain,live)))
    cols[3].metric('Conflits à arbitrer',len(pending_conflicts))
    st.markdown('<div class="aa-banner"><b>Un parcours commun aux trois MDM.</b> Explorer les fiches, examiner les paires et les conflits, puis publier une version réconciliée.</div>',unsafe_allow_html=True)
    left,right=st.columns([1.35,1])
    with left:
        with st.container(border=True):
            st.markdown('### Les applications qui alimentent le référentiel')
            counts=Counter(r['source'] for r in data['standardized'][domain])
            bars([{'Identités':n,'Application':s.replace('_',' ').title()} for s,n in counts.items()],'Identités','Application')
    with right:
        with st.container(border=True):
            st.markdown('### Qualité & points d’attention')
            q=next(r for r in data['quality'] if r['domain']==domain)
            details({'Complétude valide':percent(q['valid_required_completeness']),'Validité syntaxique':percent(q['validity']),'Anomalies à la source':sum(r['domain']==domain for r in data['issues']),'Applications contributrices':len(counts)},['Complétude valide','Validité syntaxique','Anomalies à la source','Applications contributrices'])
            if domain=='patient':
                allergies=allergy_rows(data,store.extra_decisions(root,data['run_id'],'clinical'))
                st.markdown(tag(f'{len(allergies)} déclarations d’allergies','amber')+tag('Validation séparée des identités','blue'),unsafe_allow_html=True)
            elif domain=='personnel':
                st.caption('Affectations, formations et gardes sont rattachées aux professionnels sans devenir des critères d’identité.')
            else:
                st.caption('Un dosage, un modèle ou un conditionnement contradictoire empêche la fusion, même en présence d’une référence identique.')
    with st.container(border=True):
        st.markdown('### Comparaison des scénarios')
        table(comparison)
        st.caption('S1, S2 et S3 conservent la même population synthétique, avec des profils de qualité différents. Les valeurs affichées sont calculées après exécution.')


def pairs_view(data,domain,root,reviewer):
    live=store.decisions(root,data['run_id'])
    status=st.selectbox('File de revue',['En attente','Déjà traitées','Toutes les paires'],key='pair_status')
    scoped=[p for p in data['pairs'] if p['domain']==domain]
    if status=='En attente': scoped=pending_pairs(data,domain,live)
    elif status=='Déjà traitées': scoped=[p for p in scoped if p['case_id'] in live or p.get('review_decision')]
    st.caption(f'{len(scoped)} paire(s) · Les confirmations sont appliquées lors de la réconciliation.')
    table([{'Cas':p['case_id'][:8],'Source A':p['source_a'],'Identité A':p['local_id_a'],'Source B':p['source_b'],'Identité B':p['local_id_b'],'Score':p['score'],'Proposition':STATUS.get(p['decision'],p['decision'])} for p in scoped[:250]],height=250)
    if not scoped:
        st.success('Aucune paire dans cette file pour le domaine et la version choisis.')
        return
    selected=st.selectbox('Cas à traiter',[p['case_id'] for p in scoped],format_func=lambda cid:next(f'{p["local_id_a"]} ↔ {p["local_id_b"]} · {p["score"]:.3f}' for p in scoped if p['case_id']==cid),key='pair_case')
    pair=next(p for p in scoped if p['case_id']==selected)
    records={r['rid']:r for r in data['standardized'][domain]}
    for column,rid in zip(st.columns(2),[pair['a'],pair['b']]):
        with column:
            with st.container(border=True):
                record=records[rid]
                st.markdown('### '+esc(record['source'].replace('_',' ').title()))
                details(record,DOMAINS[domain]['fields'])
                st.caption(record['local_id'])
    with st.expander('Indices de rapprochement et motif de la proposition'):
        table([{'Attribut':FIELDS.get(f,f),'Similarité':f'{v:.3f}' if v is not None else 'Non comparable'} for f,v in pair['features'].items()])
        st.caption(f'Couverture des champs : {percent(pair["coverage"])} · {pair["reason"]}')
    if pair['critical_conflicts']:
        st.warning('Confirmation bloquée : les sources présentent des contradictions critiques. Demandez leur correction avant un nouveau traitement.')
    with st.form('pair_review'):
        decision=st.selectbox('Décision',['REJECT','ESCALATE'] if pair['critical_conflicts'] else ['CONFIRM','REJECT','ESCALATE'],format_func=lambda v:STATUS[v],key='pair_decision')
        comment=st.text_area('Justification de la décision',key='pair_comment')
        submitted=st.form_submit_button('Enregistrer la décision',type='primary')
    if submitted:
        try:
            store.review(root,data['run_id'],selected,decision,reviewer,comment)
            st.session_state['notice']='Décision enregistrée. Préparez la réconciliation pour l’appliquer dans une nouvelle version.'
            st.rerun()
        except ValueError as exc: st.error(str(exc))


def conflicts_view(data,domain,root,reviewer):
    live=store.extra_decisions(root,data['run_id'],'attribute')
    rows=[r for r in attribute_conflicts(data) if r['domain']==domain]
    mode=st.selectbox('Conflits à afficher',['À arbitrer','Tous les conflits'],key='attribute_status')
    if mode=='À arbitrer': rows=[r for r in rows if r['resolution_status']=='PROPOSED' and r['case_id'] not in live]
    table([{'Cas':r['case_id'][:8],'Fiche':r['master_id'][:8],'Attribut':FIELDS.get(r['field'],r['field']),'Valeur proposée':r['value'],'Source retenue':r['selected_source'],'Statut':STATUS.get(r['resolution_status'],r['resolution_status'])} for r in rows],height=250)
    if not rows:
        st.success('Aucun conflit en attente dans cette sélection.')
        return
    chosen=st.selectbox('Conflit à traiter',[r['case_id'] for r in rows],format_func=lambda cid:next(FIELDS.get(r['field'],r['field'])+' · '+r['master_id'][:8] for r in rows if r['case_id']==cid),key='attribute_case')
    conflict=next(r for r in rows if r['case_id']==chosen)
    st.info('La priorité de source propose une valeur. Vous pouvez retenir une autre valeur observée et en conserver la justification dans la prochaine version.')
    table(conflict['candidates'],['value','source','local_id'])
    blocked=conflict['field'] in DOMAINS[domain]['critical']+['qualified_id','id_issuer']
    with st.form('attribute_review'):
        candidate=st.selectbox('Valeur retenue',range(len(conflict['candidates'])),format_func=lambda i:f'{conflict["candidates"][i]["value"]} · {conflict["candidates"][i]["source"]} / {conflict["candidates"][i]["local_id"]}',key='attribute_value')
        decision=st.selectbox('Décision sur l’attribut',['ESCALATE'] if blocked else ['SELECT_VALUE','ESCALATE'],format_func=lambda v:STATUS[v],key='attribute_decision')
        comment=st.text_area('Justification de l’arbitrage',key='attribute_comment')
        submitted=st.form_submit_button('Enregistrer l’arbitrage',type='primary')
    if submitted:
        try:
            store.attribute_review(root,data['run_id'],chosen,decision,reviewer,comment,conflict['candidates'][candidate] if decision=='SELECT_VALUE' else None)
            st.session_state['notice']='Arbitrage enregistré. La réconciliation appliquera la valeur retenue et sa provenance.'
            st.rerun()
        except ValueError as exc: st.error(str(exc))


def audit_view(data,root):
    rows=store.audit_log(root)
    valid=store.verify(root)
    cols=st.columns(3)
    cols[0].metric('Événements conservés',len(rows))
    cols[1].metric('Versions du référentiel',len(store.list_runs(root)))
    cols[2].metric('Intégrité locale','Vérifiée' if valid else 'À contrôler')
    display=[]
    for row in reversed(rows):
        event=json.loads(row['event'])
        display.append({'Date UTC':event.get('created_at',''),'Événement':{'PIPELINE_RUN':'Publication de version','REVIEW':'Revue de paire','ATTRIBUTE_REVIEW':'Arbitrage d’attribut','CLINICAL_REVIEW':'Validation d’une déclaration clinique'}.get(event['action'],event['action']),'Réviseur':event.get('reviewer','Moteur MDM'),'Décision':event.get('decision',''),'Justification':event.get('comment',''),'Empreinte':row['event_hash'][:16]})
    table(display,height=340)
    st.download_button('Exporter le journal d’audit',csv_download(rows),'journal_audit.csv')
    st.caption('Écritures transactionnelles et empreintes chaînées. La fonction du réviseur reste déclarative ; une preuve externe d’intégrité et une authentification seraient nécessaires en production.')


def reconciliation_view(data,root,domain):
    pairs=store.decisions(root,data['run_id'])
    attributes=store.extra_decisions(root,data['run_id'],'attribute')
    clinical=store.extra_decisions(root,data['run_id'],'clinical')
    st.markdown('### Préparer, vérifier, puis publier')
    st.caption('La réconciliation traite les décisions des trois domaines et conserve toutes les versions précédentes.')
    cols=st.columns(3)
    cols[0].metric('Décisions sur les paires',len(pairs))
    cols[1].metric('Arbitrages d’attributs',len(attributes))
    cols[2].metric('Validations d’allergies',len(clinical))
    method=st.selectbox('Technique de matching',['weighted','exact','probabilistic'],index=['weighted','exact','probabilistic'].index(data['method']),format_func=lambda v:{'weighted':'Similarité pondérée','exact':'Correspondance exacte','probabilistic':'Rapport de vraisemblance illustratif'}[v],key='reconciliation_method')
    signature=digest([str(root),data['run_id'],method,pairs,attributes,clinical])
    if st.button('Préparer la réconciliation',type='primary',key='prepare_reconciliation'):
        try:
            with st.spinner('Vérification des groupes, des arbitrages et des déclarations…'):
                proposal=run(root,method,base_run=data['run_id'],persist=False)
            st.session_state['reconciliation_proposal']=(signature,proposal)
        except (ValueError,OSError) as exc: st.error(str(exc))
    saved=st.session_state.get('reconciliation_proposal')
    if saved and saved[0]==signature:
        proposal=saved[1]
        changes=[]
        for d,spec in DOMAINS.items():
            changes.append({'Domaine':spec['label'],'Maîtres actuels':sum(r['domain']==d for r in data['masters']),'Maîtres proposés':sum(r['domain']==d for r in proposal['masters']),'Fusions appliquées':sum(e['domain']==d and e['result'].startswith('MERGED') for e in proposal['events'])})
        table(changes)
        blocked=[r for r in proposal['events'] if r['result'].startswith('BLOCKED')]
        if blocked:
            st.warning(f'{len(blocked)} rapprochement(s) bloqué(s) par les contrôles de groupe.')
            table(blocked)
        st.success('Proposition prête : les contradictions critiques et les rejets restent contrôlés.')
        if st.button('Publier la version réconciliée',type='primary',key='publish_reconciliation'):
            try:
                published=run(root,method,base_run=data['run_id'])
                st.session_state.pop('reconciliation_proposal',None)
                st.session_state['requested_version']=published['run_id']
                st.session_state['notice']='Nouvelle version publiée. Les versions précédentes restent consultables.'
                st.rerun()
            except (ValueError,OSError) as exc: st.error(str(exc))
    st.markdown('#### Lignage de la version consultée')
    table(data.get('lineage',[])[:100])
    st.caption('Une confirmation de paire ne valide jamais une déclaration clinique. Une correction de source invalide les décisions de rapprochement reprises depuis une autre empreinte.')


def quality_view(data,domain):
    q=next(r for r in data['quality'] if r['domain']==domain)
    cols=st.columns(3)
    cols[0].metric('Complétude brute',percent(q['raw_completeness']))
    cols[1].metric('Complétude valide',percent(q['valid_required_completeness']))
    cols[2].metric('Validité syntaxique',percent(q['validity']))
    raw,clean,issues,metrics=st.tabs(['Sources brutes','Normalisation','Anomalies','Comparaison des méthodes'])
    with raw: table(data['raw'][domain],['source','local_id']+DOMAINS[domain]['fields'],350)
    with clean:
        table(data['standardized'][domain],['source','local_id']+DOMAINS[domain]['fields'],350)
        st.download_button('Exporter les données normalisées',csv_download(data['standardized'][domain]),f'{domain}_standardized.csv')
    with issues:
        table([r for r in data['issues'] if r['domain']==domain])
        st.caption('Une valeur invalide devient vide ; la donnée brute reste conservée. La complétude valide peut donc diminuer après le contrôle.')
    with metrics:
        table([r for r in data['metrics'] if r['domain']==domain])
        st.caption('Évaluation descriptive sur des sources synthétiques. Le rappel global inclut les paires perdues au blocking. Les paramètres probabilistes ne sont pas calibrés sur un corpus indépendant.')
