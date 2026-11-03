from html import escape
import json
import pandas as pd
import altair as alt
import streamlit as st

FIELDS = {'family_name':'Nom', 'given_names':'Prénoms', 'birth_date':'Date de naissance', 'phone':'Téléphone',
          'email':'Courriel', 'address':'Adresse', 'professional_category':'Catégorie professionnelle',
          'preferred_name':'Désignation', 'category':'Famille', 'manufacturer':'Fabricant', 'model_reference':'Modèle',
          'dosage':'Dosage déclaré', 'form':'Forme', 'package_quantity':'Quantité / conditionnement', 'package_unit':'Unité',
          'sterile':'Stérilité déclarée', 'qualified_id':'Identifiant partagé', 'id_issuer':'Émetteur',
          'source':'Application', 'local_id':'Identifiant local', 'master_id':'Identifiant maître', 'service':'Service',
          'substance':'Substance', 'manifestation':'Manifestation déclarée', 'validation_status':'Validation',
          'source_count':'Applications', 'member_count':'Identités', 'lot':'Lot', 'quantity':'Quantité disponible',
          'expiry_date':'Date de péremption', 'location':'Emplacement', 'training_name':'Formation',
          'completion_date':'Réalisation', 'renewal_date':'Renouvellement', 'shift_date':'Date de garde',
          'shift_period':'Période', 'serial_number':'N° de série', 'next_maintenance':'Maintenance prévue'}
FIELDS.update({'field':'Attribut','value':'Valeur','selected_source':'Source retenue','selected_local_id':'Identifiant d’origine',
               'policy':'Règle de sélection','conflict':'Valeurs divergentes','candidates':'Valeurs observées',
               'contact_name':'Contact désigné','relationship':'Lien déclaré','role':'Fonction','start_date':'Début',
               'end_date':'Fin','establishment':'Établissement','status':'Statut déclaré','provenance':'Provenance',
               'reorder_level':'Seuil de réapprovisionnement','vigilance':'Point d’attention',
               'inventory_status':'État déclaré','last_maintenance':'Dernière maintenance',
               'reported_severity':'Sévérité déclarée','reported_at':'Date de déclaration','validated_by':'Validation par'})
STATUS = {'a_valider':'À vérifier', 'a_completer':'À compléter', 'confirmee':'Confirmée', 'ecartee':'Écartée',
          'PROPOSED':'Proposition automatique', 'RESOLVED':'Résolu', 'ESCALATED':'Escaladé',
          'AUTO':'Correspondance automatique', 'REVIEW':'Revue nécessaire', 'NO_MATCH':'Identités distinctes',
          'CONFIRM':'Confirmer', 'REJECT':'Rejeter', 'ESCALATE':'Escalader', 'SELECT_VALUE':'Retenir une valeur',
          'REFUTE':'Écarter la déclaration', 'REQUEST_INFO':'Demander un complément'}


def esc(value):
    return escape(str(value if value not in (None, '') else 'Non renseigné'))


def label(master):
    return (master.get('preferred_name') or ' '.join([master.get('given_names',''), master.get('family_name','')])).strip().title() or master['master_id'][:8]


def tag(text, style=''):
    return f'<span class="aa-tag {style}">{esc(text)}</span>'


def table(rows, fields=None, height=None):
    if not rows:
        st.caption('Aucun élément dans cette sélection.')
        return
    frame = pd.DataFrame(rows)
    if fields:
        frame = frame[[f for f in fields if f in frame]]
    for col in frame:
        if frame[col].map(lambda v: isinstance(v, (dict,list))).any():
            frame[col] = frame[col].map(lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v,(dict,list)) else v)
    frame = frame.rename(columns=FIELDS)
    st.dataframe(frame, width='stretch', hide_index=True, **({'height':height} if height else {}))


def details(row, fields):
    st.markdown(''.join(f'<div class="aa-detail"><span>{esc(FIELDS.get(f,f))}</span><b>{esc(row.get(f))}</b></div>' for f in fields), unsafe_allow_html=True)


def profile(master, badges=''):
    name = label(master)
    initials = ''.join(word[0] for word in name.split()[:2])
    st.markdown(f'<div class="aa-profile"><div class="aa-avatar">{esc(initials)}</div><div><h3>{esc(name)}</h3><p>Fiche {esc(master["master_id"][:8])} · {master["member_count"]} identités · {master["source_count"]} applications</p></div><div class="aa-tags">{badges}</div></div>', unsafe_allow_html=True)


def percent(value):
    return '—' if value is None else f'{value:.1%}'


def bars(rows, x, y, color=None):
    chart = alt.Chart(pd.DataFrame(rows)).mark_bar(cornerRadiusEnd=3, color='#118b91').encode(
        x=alt.X(f'{x}:Q', scale=alt.Scale(domainMin=0), title=None),
        y=alt.Y(f'{y}:N', sort=None, title=None), tooltip=list(rows[0]))
    if color:
        chart = chart.encode(color=alt.Color(f'{color}:N', scale=alt.Scale(range=['#168b90','#a0ccd0','#f0c779']), legend=alt.Legend(orient='bottom')))
    st.altair_chart(chart.properties(height=210), width='stretch')
