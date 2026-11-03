from datetime import datetime, timezone
import streamlit as st
from mdm.hospital import allergy_rows, stock_flags
from mdm import store
from .components import details, esc, label, profile, table, tag, STATUS


def related(data, name, master_id):
    return [r for r in data.get('related',{}).get(name,[]) if r['master_id']==master_id]


def allergies_panel(data, master_id, live=None):
    rows = [r for r in allergy_rows(data, live) if r['master_id']==master_id]
    if not rows:
        st.info("Aucune déclaration d’allergie rattachée à cette version. L’absence de déclaration ne prouve pas l’absence d’allergie.")
    for row in rows:
        status = row['validation_status']
        style = 'confirmed' if status=='confirmee' else ''
        st.markdown(f'<div class="aa-alert {style}"><h4>{esc(row["substance"])} {tag(STATUS.get(status,status), "amber" if status in {"a_valider","a_completer"} else "gray" if status=="ecartee" else "")}</h4><p>{esc(row.get("manifestation", "Manifestation non renseignée"))}</p><p>Source : {esc(row.get("provenance",row["source"]))} · Déclarée le {esc(row.get("reported_at"))}</p><p>Sévérité déclarée : {esc(row.get("reported_severity"))} · Validation : {esc(row.get("validated_by"))}</p></div>', unsafe_allow_html=True)
    st.caption('Déclarations cliniques sourcées. Elles ne participent jamais au rapprochement des identités.')
    return rows


def patient_profile(data, master, live):
    rows = [r for r in allergy_rows(data, live) if r['master_id']==master['master_id'] and r['validation_status']!='ecartee']
    profile(master, tag('Identité consolidée','blue') + (tag(f'{len(rows)} déclaration(s) d’allergie','amber') if rows else ''))
    identity, allergy, care, provenance = st.tabs(['Identité & contacts','Allergies & vigilances','Parcours de soins','Sources & provenance'])
    with identity:
        left,right=st.columns(2)
        with left:
            with st.container(border=True):
                st.markdown('#### Identité administrative')
                details(master,['given_names','family_name','birth_date','qualified_id'])
        with right:
            with st.container(border=True):
                st.markdown('#### Coordonnées & contact désigné')
                details(master,['phone','email','address'])
                table(related(data,'contacts_urgence.csv',master['master_id']),['contact_name','relationship','phone'])
    with allergy:
        allergies_panel(data, master['master_id'], live)
    with care:
        stays=related(data,'sejours.csv',master['master_id'])
        for row in sorted(stays,key=lambda r:r['admission_date'],reverse=True):
            st.markdown(f'<div class="aa-timeline"><strong>{esc(row["care_type"])} · {esc(row["service"])}</strong><p>Admission le {esc(row["admission_date"])} · Chambre {esc(row.get("room"))}, lit {esc(row.get("bed"))}</p><p>{"Séjour en cours dans la source" if row.get("care_status")=="en_cours" else "Parcours terminé dans la source"} · {esc(row["source"])}</p></div>',unsafe_allow_html=True)
        if not stays:
            st.caption('Aucun séjour rattaché dans les données de cette version.')
    with provenance:
        provenance_panel(data, master['master_id'])


def provenance_panel(data, master_id):
    st.markdown('#### Correspondances avec les applications sources')
    table([r for r in data['xrefs'] if r['master_id']==master_id],['source','local_id','master_id'])
    st.markdown('#### Origine des valeurs retenues')
    table([r for r in data['provenance'] if r['master_id']==master_id],['field','value','selected_source','selected_local_id','policy','conflict','candidates'])


def personnel_profile(data, master):
    profile(master, tag(master.get('professional_category','Personnel'),'blue'))
    identity, qualification, provenance=st.tabs(['Profil & affectations','Formations & gardes','Sources & provenance'])
    with identity:
        left,right=st.columns(2)
        with left:
            with st.container(border=True):
                details(master,['given_names','family_name','professional_category','email','phone'])
        with right:
            st.markdown('#### Affectations hospitalières')
            table(related(data,'affectations.csv',master['master_id']),['service','role','start_date','end_date','establishment'])
    with qualification:
        st.markdown('#### Formations déclarées')
        table(related(data,'formations.csv',master['master_id']),['training_name','completion_date','renewal_date','status','provenance'])
        st.markdown('#### Gardes & planning')
        table(related(data,'gardes.csv',master['master_id']),['service','shift_date','shift_period','provenance'])
        st.caption('Les formations et gardes sont des relations sourcées. Elles ne déterminent pas l’identité du professionnel.')
    with provenance:
        provenance_panel(data,master['master_id'])


def product_profile(data, master):
    profile(master,tag(master.get('category','Produit'),'blue'))
    reference, lots, biomedical, provenance=st.tabs(['Référence & conditionnement','Lots & disponibilités','Parc biomédical','Sources & provenance'])
    with reference:
        left,right=st.columns(2)
        with left:
            with st.container(border=True):
                details(master,['preferred_name','category','manufacturer','model_reference','qualified_id'])
        with right:
            with st.container(border=True):
                details(master,['dosage','form','package_quantity','package_unit','sterile'])
    with lots:
        rows=related(data,'stocks.csv',master['master_id'])
        enriched=[]
        today=datetime.now(timezone.utc).date()
        for row in rows:
            flags=stock_flags(row,today)
            enriched.append(dict(row, vigilance='Donnée à contrôler' if flags['invalid_expiry'] or flags['invalid_quantity'] else 'Date dépassée' if flags['expired'] else 'Sous le seuil déclaré' if flags['low_stock'] else 'Aucune alerte calculée'))
        table(enriched,['lot','quantity','reorder_level','expiry_date','location','vigilance'])
        st.caption('Alertes descriptives sur les dates et seuils saisis dans les sources ; aucune validation de délivrance ou d’utilisation.')
    with biomedical:
        table(related(data,'equipements.csv',master['master_id']),['serial_number','service','inventory_status','last_maintenance','next_maintenance','provenance'])
    with provenance:
        provenance_panel(data,master['master_id'])


def golden(data,domain,root):
    live=store.extra_decisions(root,data['run_id'],'clinical')
    masters=[r for r in data['masters'] if r['domain']==domain]
    left,right=st.columns([3,1])
    with left:
        query=st.text_input('Rechercher dans le référentiel',placeholder='Nom, identifiant ou référence…',key=f'search_{domain}')
    with right:
        maximum=max((r['source_count'] for r in masters),default=1)
        minimum=st.selectbox('Applications minimum',range(1,maximum+1),key=f'sources_{domain}')
    rows=[r for r in masters if r['source_count']>=minimum and query.casefold() in (' '.join(str(v) for v in r.values())).casefold()]
    if domain=='patient' and st.checkbox('Afficher les dossiers avec une allergie déclarée',key='allergy_filter'):
        ids={r['master_id'] for r in allergy_rows(data,live) if r['validation_status']!='ecartee'}
        rows=[r for r in rows if r['master_id'] in ids]
    rows.sort(key=label)
    st.caption(f'{len(rows)} fiche(s) · Les valeurs brutes et les autres identifiants restent consultables dans la provenance.')
    fields=['master_id','given_names','family_name','birth_date','professional_category','preferred_name','category','source_count','member_count']
    table(rows,fields,260)
    if rows:
        chosen=st.selectbox('Ouvrir une fiche',[r['master_id'] for r in rows],format_func=lambda mid:label(next(r for r in rows if r['master_id']==mid))+' · '+mid[:8],key=f'golden_{domain}')
        master=next(r for r in rows if r['master_id']==chosen)
        if domain=='patient': patient_profile(data,master,live)
        elif domain=='personnel': personnel_profile(data,master)
        else: product_profile(data,master)
    from mdm.io import csv_download
    st.download_button('Exporter les Golden Records filtrés',csv_download(rows),f'{domain}_golden_records.csv',key=f'export_{domain}')


def hospital_view(data,domain,root,reviewer):
    if domain!='patient':
        st.subheader('Organisation hospitalière' if domain=='personnel' else 'Stocks & parc hospitalier')
        cols=st.columns(3)
        if domain=='personnel':
            assignments=data.get('related',{}).get('affectations.csv',[])
            cols[0].metric('Services représentés',len({r['service'] for r in assignments}))
            cols[1].metric('Formations déclarées',len(data.get('related',{}).get('formations.csv',[])))
            cols[2].metric('Gardes planifiées',len(data.get('related',{}).get('gardes.csv',[])))
        else:
            flags=[stock_flags(r,datetime.now(timezone.utc).date()) for r in data.get('related',{}).get('stocks.csv',[])]
            cols[0].metric('Lots déclarés',len(flags))
            cols[1].metric('Dates dépassées',sum(r['expired'] for r in flags))
            cols[2].metric('Sous le seuil déclaré',sum(r['low_stock'] for r in flags))
        names=['affectations.csv','formations.csv','gardes.csv'] if domain=='personnel' else ['stocks.csv','equipements.csv']
        titles={'affectations.csv':'Affectations par service','formations.csv':'Formations suivies','gardes.csv':'Planning des gardes','stocks.csv':'Lots & stocks déclarés','equipements.csv':'Inventaire biomédical'}
        for name in names:
            with st.container(border=True):
                st.markdown(f'### {titles[name]}')
                table(data.get('related',{}).get(name,[]),[f for f in ['service','local_id','training_name','completion_date','shift_date','shift_period','lot','quantity','expiry_date','location','serial_number','next_maintenance','provenance']])
        return
    st.subheader('Vigilances & déclarations d’allergies')
    live=store.extra_decisions(root,data['run_id'],'clinical')
    rows=allergy_rows(data,live)
    cols=st.columns(3)
    cols[0].metric('Déclarations sourcées',len(rows))
    cols[1].metric('À vérifier / compléter',sum(r['validation_status'] in {'a_valider','a_completer'} for r in rows))
    cols[2].metric('Déclarations confirmées',sum(r['validation_status']=='confirmee' for r in rows))
    table(rows,['substance','manifestation','source','local_id','validation_status','validated_by'],260)
    if not rows: return
    masters={r['master_id']:r for r in data['masters']}
    selected=st.selectbox('Déclaration à examiner',[r['assertion_id'] for r in rows],format_func=lambda aid:next(f'{label(masters[r["master_id"]])} · {r["substance"]} · {r["source"]}' for r in rows if r['assertion_id']==aid),key='clinical_assertion')
    row=next(r for r in rows if r['assertion_id']==selected)
    master=masters[row['master_id']]
    profile(master,tag('Déclaration sourcée','amber'))
    details(row,['substance','manifestation','reported_severity','reported_at','provenance','validation_status'])
    with st.form('clinical_review'):
        st.markdown('#### Validation de la déclaration')
        role=st.selectbox('Fonction clinique déclarée',['Médecin','Pharmacien'],key='clinical_role')
        decision=st.selectbox('Décision clinique',['CONFIRM','REFUTE','REQUEST_INFO'],format_func=lambda v: {'CONFIRM':'Confirmer la déclaration','REFUTE':'Écarter la déclaration','REQUEST_INFO':'Demander un complément'}[v],key='clinical_decision')
        comment=st.text_area('Justification clinique',key='clinical_comment')
        submitted=st.form_submit_button('Enregistrer la validation clinique',type='primary')
    st.caption('Démonstration : la fonction du réviseur est déclarative. Une fusion d’identité ne valide jamais une allergie ; aucune recommandation thérapeutique n’est produite.')
    if submitted:
        try:
            store.clinical_review(root,data['run_id'],selected,decision,reviewer,role,comment)
            st.session_state['notice']='Validation enregistrée et tracée. Elle sera reprise dans la prochaine version.'
            st.rerun()
        except ValueError as exc: st.error(str(exc))
