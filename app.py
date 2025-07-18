# app.py
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import geopandas as gpd
import pandas as pd
import os
import warnings
import base64
import altair as alt

warnings.filterwarnings("ignore")

# 1. Configuration principale
st.set_page_config(page_title="Zones inondables & Pluviométrie – Ouagadougou", layout="wide")
st.title("📍 Cartographie participative des zones inondables de Ouagadougou")
st.sidebar.header("🔍 Sélection de l'onglet")

# 2. Points de terrain enrichis (Zones A à G, Bonnaam, Sandogo, Yoaghin, Saonre)
points = [
    # A–G
    {"lat":12.286813,"lon":-1.612065,"name":"Zone A : BOASSA","contact":"M. Koulibaly",
     "comment":"Le marigot déborde chaque saison pluvieuse.","images":["images/boassa1.jpg","images/boassa2.jpg"]},
    {"lat":12.324026,"lon":-1.609384,"name":"Zone B : YOAGHIN","contact":"Mme Sawadogo",
     "comment":"Accès impraticable après 30 min de pluie.","images":["images/yoaghin1.jpg","images/yoaghin2.jpg"]},
    {"lat":12.320957,"lon":-1.615837,"name":"Zone C : KANKAMSE","contact":"M. Ouédraogo",
     "comment":"Fondations fissurées par l’eau stagnante.","images":["images/kankamse1.jpg","images/kankamse2.jpg"]},
    {"lat":12.342865,"lon":-1.596492,"name":"Zone D : ZONGO","contact":"Mme Traoré",
     "comment":"Eaux stagnantes attirent moustiques.","images":["images/zongo1.jpg","images/zongo2.jpg"]},
    {"lat":12.350765,"lon":-1.587388,"name":"Zone E : ST DOMINIQUE","contact":"M. Dao",
     "comment":"Caniveaux débordés menaçant rez‑de‑chaussée.","images":["images/stdcdom1.jpg","images/stdcdom2.jpg"]},
    {"lat":12.335139,"lon":-1.616538,"name":"Zone F : ZAGTOULI","contact":"Mme Kaboré",
     "comment":"Mur de protection fissuré en 2022.","images":["images/zagtouli1.jpg","images/zagtouli2.jpg"]},
    {"lat":12.367098,"lon":-1.638734,"name":"Zone G : BASSEKO","contact":"M. Ouahab",
     "comment":"Seuil des fenêtres critique lors des crues.","images":["images/basseko1.jpg","images/basseko2.jpg"]},
    # Bonnaam (7 repères)
    {"lat":12.322181,"lon":-1.579680,"name":"Bonnaam 1","contact":"M. Sawadogo",
     "comment":"Hauteur de crue atteignant 1,2 m.","images":["images/bonnaam1_1.jpg","images/bonnaam1_2.jpg","images/bonnaam1_3.jpg","images/bonnaam1_4.jpg"]},
    {"lat":12.320240,"lon":-1.579680,"name":"Bonnaam 2","contact":"Mme Kinda",
     "comment":"Eau stagnante jusqu’à 0,8 m.","images":["images/bonnaam2_1.jpg","images/bonnaam2_2.jpg","images/bonnaam2_3.jpg"]},
    {"lat":12.313578,"lon":-1.572194,"name":"Bonnaam 3","contact":"M. Traoré",
     "comment":"Inondation sur 1,5 ha du quartier.","images":["images/bonnaam3_1.jpg","images/bonnaam3_2.jpg","images/bonnaam3_3.jpg","images/bonnaam3_4.jpg"]},
    {"lat":12.313206,"lon":-1.574259,"name":"Bonnaam 4","contact":"Mme Zongo",
     "comment":"Eau atteignant 0,5 m le long de la route.","images":["images/bonnaam4_1.jpg","images/bonnaam4_2.jpg"]},
    {"lat":12.307954,"lon":-1.567229,"name":"Bonnaam 5","contact":"M. Ouédraogo",
     "comment":"Secteur de 10 ha submergé pendant 48 h.","images":["images/bonnaam5_1.jpg","images/bonnaam5_2.jpg"]},
    {"lat":12.306072,"lon":-1.566660,"name":"Bonnaam 6","contact":"Mme Balima",
     "comment":"Points bas inondés jusqu’à 0,6 m.","images":["images/bonnaam6_1.jpg","images/bonnaam6_2.jpg"]},
    {"lat":12.304420,"lon":-1.569685,"name":"Bonnaam 7","contact":"M. Kaboré",
     "comment":"Crue atteignant les clôtures de jardin.","images":["images/bonnaam7_1.jpg","images/bonnaam7_2.jpg"]},
    # Sandogo (4 repères)
    {"lat":12.306373,"lon":-1.597861,"name":"Sandogo 1","contact":"Mme Sanon",
     "comment":"Inondation localisée à 0,9 m autour du puits.","images":["images/sandogo1_1.jpg","images/sandogo1_2.jpg","images/sandogo1_3.jpg"]},
    {"lat":12.305514,"lon":-1.593024,"name":"Sandogo 2","contact":"M. Kinda",
     "comment":"Eaux à 0,7 m au marché.","images":["images/sandogo2_1.jpg","images/sandogo2_2.jpg","images/sandogo2_3.jpg"]},
    {"lat":12.305000,"lon":-1.595000,"name":"Sandogo 3","contact":"M. Zongo",
     "comment":"Débordement mineur, profondeur faible.","images":["images/sandogo3_1.jpg"]},
    {"lat":12.304000,"lon":-1.598000,"name":"Sandogo 4","contact":"Mme Ouédraogo",
     "comment":"Zone périphérique légèrement inondée.","images":["images/sandogo4_1.jpg"]},
    # Yoaghin NE & SE (b1/b2)
    {"lat":12.337832,"lon":-1.584723,"name":"Yoaghin NE","contact":"M. Traoré",
     "comment":"Crue soudaine à 1,0 m en bordure de canal.","images":["images/yoaghin_ne1.jpg","images/yoaghin_ne2.jpg","images/yoaghin_ne3.jpg","images/yoaghin_ne4.jpg"]},
    {"lat":12.338500,"lon":-1.582500,"name":"Yoaghin SE","contact":"Mme Salif",
     "comment":"Glissement de berge observé à 0,6 m.","images":["images/yoaghin_se1.jpg","images/yoaghin_se2.jpg","images/yoaghin_se3.jpg"]},
    # Saonre (exemple: 1 seul, les suivants à recopier)
    {"lat":12.286258,"lon":-1.559080,"name":"Saonre 1","contact":"M. Nikiema",
     "comment":"Seuil d’eau à 0,5 m.","images":[]},
]

# 3. Chargement GeoJSON
@st.cache_data
def load_layer(path):
    if os.path.exists(path):
        return gpd.read_file(path).to_crs(epsg=4326)
    else:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

commune = load_layer("data/communes.geojson")
roads   = load_layer("data/voirie.geojson")
grid    = load_layer("data/zones_base.geojson")

# 4. Pluviométrie CSV
@st.cache_data
def load_pluvio():
    if os.path.exists("data/pluviometrie.csv"):
        df = pd.read_csv("data/pluviometrie.csv")
        return df[(df.year>=2000)&(df.year<=2024)]
    return pd.DataFrame(columns=['year','value'])

@st.cache_data
def load_pluvio_mensuel():
    if os.path.exists("data/pluvio_mensuel.csv"):
        df = pd.read_csv("data/pluvio_mensuel.csv")
        if 'month' in df.columns:
            df.rename(columns={'month':'Mois'}, inplace=True)
        return df
    return pd.DataFrame(columns=['Mois','value'])

pluvio         = load_pluvio()
pluvio_mensuel = load_pluvio_mensuel()

# 5. Encode Base64
def encode_img(path):
    with open(path,'rb') as f:
        return base64.b64encode(f.read()).decode()

# 6. Fond de carte
def base_map():
    m = folium.Map(location=[12.35, -1.60], zoom_start=13, tiles="CartoDB positron")
    if not commune.empty:
        folium.GeoJson(commune, style_function=lambda f:{'fillColor':'#a8ddb5','fillOpacity':0.2,'color':'none'}).add_to(m)
    if not roads.empty:
        folium.GeoJson(roads, style_function=lambda f:{'color':'grey','weight':1}).add_to(m)
    return m

# 7. Zone de chaleur (halo jaune 2 km)
def heatmap_map():
    m = base_map()
    HeatMap([(p['lat'],p['lon']) for p in points], radius=25, blur=15).add_to(m)
    for pt in points:
        folium.Circle(
            location=[pt['lat'],pt['lon']],
            radius=2000,
            color='#feb24c',
            fill=True,
            fill_opacity=0.2
        ).add_to(m)
        html = f"<h4>{pt['name']}</h4><i>{pt['contact']}</i><br>{pt['comment']}<br>"
        for img in pt['images']:
            if os.path.exists(img):
                b64 = encode_img(img)
                html += f"<img src='data:image/jpeg;base64,{b64}' width='150'><br>"
        folium.Marker(
            [pt['lat'],pt['lon']],
            popup=folium.Popup(html, max_width=300),
            icon=folium.Icon(color='orange', icon='tint', prefix='fa')
        ).add_to(m)
    return m

# 8. Carte de risque
def risk_map():
    m = base_map()
    if 'classe' in grid.columns:
        folium.Choropleth(
            geo_data=grid, data=grid,
            columns=['id','classe'], key_on='feature.properties.id',
            fill_color='YlOrRd', legend_name='Niveau de risque (1–5)'
        ).add_to(m)
    return m

# 9. Contribution (remplace Zonage)
def contribution_map():
    if 'reports' not in st.session_state:
        st.session_state.reports = []

    with st.form('report_form'):
        st.markdown("### Soumettre un rapport de terrain")
        lat     = st.number_input('Latitude', format="%.6f")
        lon     = st.number_input('Longitude', format="%.6f")
        contact = st.text_input('Votre nom')
        comment = st.text_area('Commentaire')
        imgs    = st.file_uploader('Photos (max 3)', type=['jpg','png'], accept_multiple_files=True)
        if st.form_submit_button('Envoyer'):
            encoded = [f"data:image/jpeg;base64,{base64.b64encode(img.read()).decode()}" for img in imgs[:3]]
            st.session_state.reports.append({'lat':lat,'lon':lon,'contact':contact,'comment':comment,'images':encoded})
            st.success("Rapport ajouté.")

    m = base_map()
    for rpt in st.session_state.reports:
        html = f"<b>{rpt['contact']}</b><br>{rpt['comment']}<br>"
        for src in rpt['images']:
            html += f"<img src='{src}' width='150'><br>"
        folium.Marker(
            [rpt['lat'], rpt['lon']],
            popup=folium.Popup(html, max_width=300),
            icon=folium.Icon(color='blue', icon='comment', prefix='fa')
        ).add_to(m)
    return m

# 10. Interface onglets
tabs = ['Zone de chaleur','Risque','Contribution','Pluviométrie']
choice = st.sidebar.radio('Onglet', tabs)
st.subheader(choice)

if choice == 'Zone de chaleur':
    st_folium(heatmap_map(), width=800, height=600)
    df = pd.DataFrame(points)[['name','contact','comment']]
    st.markdown("### Témoignages et contacts locaux")
    st.dataframe(df, height=250)

elif choice == 'Risque':
    st_folium(risk_map(), width=800, height=600)

elif choice == 'Contribution':
    st_folium(contribution_map(), width=800, height=600)

elif choice == 'Pluviométrie':
    st.markdown("### Évolution annuelle (2000–2024)")
    if not pluvio.empty:
        st.line_chart(pluvio.set_index('year')['value'])
    else:
        st.info("Pas de données annuelles.")
    st.markdown("### Moyennes mensuelles")
    if not pluvio_mensuel.empty:
        chart = alt.Chart(pluvio_mensuel).mark_bar(color='#3182bd').encode(
            x=alt.X('Mois:O', sort=list(pluvio_mensuel['Mois'])),
            y='value:Q', tooltip=['Mois','value']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Pas de données mensuelles.")
