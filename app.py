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
from folium.plugins import Fullscreen

warnings.filterwarnings("ignore")

# 1. Configuration principale
st.set_page_config(page_title="Zones inondables & Pluviométrie – Ouagadougou", layout="wide")
st.title("📍 Cartographie participative des zones inondables de Ouagadougou")
st.sidebar.header("🔍 Sélection de l'onglet")

# 2. Points de terrain enrichis
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
     "comment":"Mur de protection fissuré en 2022.","images":["images/zagtouli1.jpg","images/zagtouli2.jpg"]},
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

    # Yoaghin NE & SE
    {"lat":12.337832,"lon":-1.5847228,"name":"Yoaghin NE","contact":"M. Traoré",
     "comment":"Crue soudaine à 1,0 m en bordure de canal.","images":["images/yoaghin_ne1.jpg","images/yoaghin_ne2.jpg","images/yoaghin_ne3.jpg","images/yoaghin_ne4.jpg"]},
    {"lat":12.338500,"lon":-1.582500,"name":"Yoaghin SE","contact":"Mme Salif",
     "comment":"Glissement de berge observé à 0,6 m.","images":["images/yoaghin_se1.jpg","images/yoaghin_se2.jpg","images/yoaghin_se3.jpg"]},

    # Saonre (17 repères)
   {"lat":12.286258,"lon":-1.559080,"name":"Saonre 1","contact":"M. Nikiema",
     "comment":"Seuil d’eau à 0,5 m.","images":["images/saonre1_1.jpg","images/saonre1_2.jpg"]},
    {"lat":12.286834,"lon":-1.558946,"name":"Saonre 2","contact":"Mme Bouda",
     "comment":"Sédiments observés.","images":["images/saonre2_1.jpg","images/saonre2_2.jpg"]},
    {"lat":12.282990,"lon":-1.559539,"name":"Saonre 3","contact":"M. Sawadogo",
     "comment":"Érosion de sol.","images":["images/saonre3_1.jpg","images/saonre3_2.jpg"]},
    {"lat":12.277612,"lon":-1.562369,"name":"Saonre 4","contact":"Mme Zida",
     "comment":"Montée lente des eaux.","images":["images/saonre4_1.jpg","images/saonre4_2.jpg"]},
    {"lat":12.277772,"lon":-1.564359,"name":"Saonre 5","contact":"M. Ouédraogo",
     "comment":"Ruissellement important.","images":["images/saonre5_1.jpg","images/saonre5_2.jpg"]},
    {"lat":12.282271,"lon":-1.572650,"name":"Saonre 6","contact":"Mme Traoré",
     "comment":"Inondation ponctuelle.","images":["images/saonre6_1.jpg","images/saonre6_2.jpg"]},
    {"lat":12.282962,"lon":-1.561369,"name":"Saonre 7","contact":"M. Kaboré",
     "comment":"Accumulation d'eau.","images":["images/saonre7_1.jpg","images/saonre7_2.jpg"]},
    {"lat":12.288230,"lon":-1.559163,"name":"Saonre 8","contact":"Mme Diallo",
     "comment":"Étiage bas.","images":["images/saonre8_1.jpg","images/saonre8_2.jpg"]},
    {"lat":12.296193,"lon":-1.560334,"name":"Saonre 9","contact":"M. Banon",
     "comment":"Crue brève.","images":["images/saonre9_1.jpg","images/saonre9_2.jpg"]},
    {"lat":12.292403,"lon":-1.585354,"name":"Saonre 10","contact":"Mme Kaboré",
     "comment":"Terrain saturé.","images":["images/saonre10_1.jpg","images/saonre10_2.jpg"]},
    {"lat":12.298594,"lon":-1.564698,"name":"Saonre 11","contact":"M. Nikiema",
     "comment":"Ruissellement fort.","images":["images/saonre11_1.jpg","images/saonre11_2.jpg"]},
    {"lat":12.292286,"lon":-1.558426,"name":"Saonre 12","contact":"Mme Sawadogo",
     "comment":"Eau stagnante.","images":["images/saonre12_1.jpg","images/saonre12_2.jpg"]},
    {"lat":12.289775,"lon":-1.559813,"name":"Saonre 13","contact":"M. Dao",
     "comment":"Sol boueux.","images":["images/saonre13_1.jpg","images/saonre13_2.jpg"]},
    {"lat":12.298575,"lon":-1.569577,"name":"Saonre 14","contact":"Mme Balima",
     "comment":"Importante crue.","images":["images/saonre14_1.jpg","images/saonre14_2.jpg"]},
    {"lat":12.296347,"lon":-1.581075,"name":"Saonre 15","contact":"M. Traoré",
     "comment":"Pont submergé.","images":["images/saonre15_1.jpg","images/saonre15_2.jpg"]},
    {"lat":12.296772,"lon":-1.576165,"name":"Saonre 16","contact":"Mme Sanon",
     "comment":"Route coupée.","images":["images/saonre16_1.jpg","images/saonre16_2.jpg"]},
    {"lat":12.285145,"lon":-1.561207,"name":"Saonre 17","contact":"M. Salif",
     "comment":"Digue perforée.","images":["images/saonre17_1.jpg","images/saonre17_2.jpg"]},

     # — Naab‑Pougo (3 repères) avec commentaires uniques
    {"lat":12.369183,"lon":-1.574075,"name":"Naab‑Pougo 1","contact":"M. Traoré",
    "comment":"Rivière débordante sous les latérites.","images":["images/naab1_1.jpg","images/naab1_2.jpg"]},
    {"lat":12.369156,"lon":-1.574081,"name":"Naab‑Pougo 2","contact":"Mme Salif",
    "comment":"Infiltrations sous la passerelle.","images":["images/naab2_1.jpg","images/naab2_2.jpg"]},
    {"lat":12.370153,"lon":-1.575372,"name":"Naab‑Pougo 3","contact":"M. Dao",
    "comment":"Plaine inondée jusqu’au sentier.","images":["images/naab3_1.jpg","images/naab3_2.jpg"]},

    # — Noncin (3 repères)
    {"lat":12.369922,"lon":-1.578133,"name":"Noncin 1","contact":"Mme Zida",
    "comment":"Canal artificiel saturé.","images":["images/noncin1_1.jpg","images/noncin1_2.jpg"]},
    {"lat":12.369925,"lon":-1.578319,"name":"Noncin 2","contact":"M. Ouédraogo",
    "comment":"Boue collante après la pluie.","images":["images/noncin2_1.jpg","images/noncin2_2.jpg"]},
    {"lat":12.361122,"lon":-1.584544,"name":"Noncin 3","contact":"Mme Balima",
    "comment":"Talus érodé par le ruissellement.","images":["images/noncin3_1.jpg","images/noncin3_2.jpg"]},

    # — Basseko (6 repères)
    {"lat":12.361122,"lon":-1.584553,"name":"Basseko 1","contact":"M. Nikiema",
    "comment":"Accès barré par la flaque.","images":["images/basseko1_1.jpg","images/basseko1_2.jpg"]},
    {"lat":12.361144,"lon":-1.584461,"name":"Basseko 2","contact":"Mme Sawadogo",
    "comment":"Zones marécageuses persistantes.","images":["images/basseko2_1.jpg","images/basseko2_2.jpg"]},
    {"lat":12.360361,"lon":-1.589486,"name":"Basseko 3","contact":"M. Traoré",
    "comment":"Route secondaire inondée.","images":["images/basseko3_1.jpg","images/basseko3_2.jpg"]},
    {"lat":12.357653,"lon":-1.589600,"name":"Basseko 4","contact":"Mme Zongo",
    "comment":"Station de bus impraticable.","images":["images/basseko4_1.jpg","images/basseko4_2.jpg"]},
    {"lat":12.353017,"lon":-1.586556,"name":"Basseko 5","contact":"M. Sawadogo",
    "comment":"Niveau d’eau à 30 cm sous trottoir.","images":["images/basseko5_1.jpg","images/basseko5_2.jpg"]},
    {"lat":12.352989,"lon":-1.586633,"name":"Basseko 6","contact":"Mme Kaboré",
    "comment":"Fissures sur le parapet.","images":["images/basseko6_1.jpg","images/basseko6_2.jpg"]},
]
 
# 3. Chargement des couches GeoJSON
@st.cache_data
def load_layer(path):
    if os.path.exists(path):
        return gpd.read_file(path).to_crs(epsg=4326)
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

commune = load_layer("data/communes.geojson")
roads   = load_layer("data/voirie.geojson")
water   = load_layer("data/hydrographie.geojson")
grid    = load_layer("data/zones_base.geojson")

# 4. Chargement des données pluviométrie
@st.cache_data
def load_pluvio():
    path = "data/pluviometrie.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df[(df.year>=2000)&(df.year<=2024)]
    return pd.DataFrame(columns=['year','value'])

@st.cache_data
def load_pluvio_mensuel():
    path = "data/pluvio_mensuel.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        if 'month' in df.columns:
            df.rename(columns={'month':'Mois'}, inplace=True)
        return df
    return pd.DataFrame(columns=['Mois','value'])

pluvio = load_pluvio()
pluvio_mensuel = load_pluvio_mensuel()

# 5. Helper pour images
def encode_img(path):
    with open(path,'rb') as f:
        return base64.b64encode(f.read()).decode()

# 6. Fonction de base_map avec bouton plein écran + limites/voirie/hydro
def base_map():
    m = folium.Map(location=[12.35, -1.60], zoom_start=13, tiles="CartoDB positron")
    Fullscreen(
        position="topright",
        title="Afficher plein écran",
        title_cancel="Quitter plein écran",
        force_separate_button=True
    ).add_to(m)
    # Limite
    folium.GeoJson(commune,
        style_function=lambda f: {"fillColor":"#a8ddb5","fillOpacity":0.2,"color":"none"}
    ).add_to(m)
    # Voirie (toggleable)
    folium.GeoJson(roads,
        name="Voirie", show=False,
        style_function=lambda f: {"color":"grey","weight":1}
    ).add_to(m)
    # Hydrographie (toggleable)
    folium.GeoJson(water,
        name="Hydrographie", show=False,
        style_function=lambda f: {"color":"blue","weight":1}
    ).add_to(m)
    return m

# 7. Heatmap
def heatmap_map():
    m = base_map()
    HeatMap([(p['lat'],p['lon']) for p in points],
            name="HeatMap", show=True, radius=25, blur=15
    ).add_to(m)
    # Cercles 1km
    for pt in points:
        folium.Circle(
            location=[pt['lat'],pt['lon']], radius=1000,
            color='#de2d26', fill=True, fill_opacity=0.3
        ).add_to(m)
    # Halo 2km
    for pt in points:
        folium.Circle(
            location=[pt['lat'],pt['lon']], radius=2000,
            color='#feb24c', fill=True, fill_opacity=0.2
        ).add_to(m)
    # Popups
    for pt in points:
        html = f"<h4>{pt['name']}</h4><i>{pt['contact']}</i><br>{pt['comment']}<br>"
        for img in pt['images']:
            if os.path.exists(img):
                b64 = encode_img(img)
                html += f"<img src='data:image/jpeg;base64,{b64}' width='150'><br>"
        folium.Marker(
            [pt['lat'],pt['lon']],
            popup=folium.Popup(html, max_width=300),
            icon=folium.Icon(color='red', icon='tint', prefix='fa')
        ).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)
    m.fit_bounds([[pt['lat'],pt['lon']] for pt in points])
    return m

# 8. Onglet Sensibilisation
def sensibilisation_tab():
    st.subheader("📘 Sensibilisation & Bonnes pratiques")
    st.markdown("""
    **Pourquoi se préparer aux inondations ?**  
    - Réduire les dégâts matériels  
    - Protéger la vie et la santé  
    - Limiter les déplacements d'urgence  
    """)
    st.markdown("### 🕰️ Avant la saison des pluies")
    st.markdown("""
    1. Vérifiez l’état de vos caniveaux et gouttières.  
    2. Scellez les fissures de sous‑sol avec un mortier hydrofuge.  
    3. Stockez vos biens de valeur en hauteur.  
    4. Préparez un kit d’urgence (lampe, eau, pharmacie).  
    """)
    st.markdown("### 🌧️ En période de fortes pluies")
    st.markdown("""
    - Évitez de traverser un gué submergé (1 m d’eau suffit pour emporter un véhicule).  
    - Coupez l’électricité si l’eau monte au ras des prises.  
    - Restez informé·e via la radio locale ou les réseaux officiels.  
    """)
    st.markdown("### 💧 Après l’inondation")
    st.markdown("""
    - N’utilisez pas l’eau du robinet tant que le réseau n’a pas été déclaré potable.  
    - Débarrassez‑vous des objets imbibés d’eau pour éviter moisissure.  
    - Vérifiez la solidité des murs et fondations avant de revenir.  
    """)
    st.markdown("### 🔗 Liens & Contacts")
    st.markdown("""
    - **Service d’Assainissement Municipal** : +226 25 30 40 50  
    - **Protection Civile** : +226 15 20 30 40  
    - [Guide INDC-BF (PDF)](https://example.org/guide-indc-bf.pdf)  
    """)

    # Construire la carte
    m = base_map()
    # Réappliquer l’ancienne vue si présente
    if st.session_state.map_bounds:
        sw, ne = st.session_state.map_bounds
        m.fit_bounds([sw, ne])

    # Ajouter grille de risque
    if not grid.empty and 'classe' in grid.columns:
        folium.Choropleth(
            geo_data=grid, data=grid,
            columns=['id','classe'], key_on='feature.properties.id',
            fill_color='YlOrRd', legend_name='Risque (1–5)'
        ).add_to(m)

    # Optionnel : montrer les relevés terrain
    if st.checkbox("Afficher les relevés de terrain (avec photos)"):
        for pt in points:
            html = f"<h4>{pt['name']}</h4><i>{pt['contact']}</i><br>{pt['comment']}<br>"
            for img in pt['images']:
                if os.path.exists(img):
                    b64 = encode_img(img)
                    html += f"<img src='data:image/jpeg;base64,{b64}' width='150'><br>"
            folium.Marker(
                [pt['lat'],pt['lon']],
                popup=folium.Popup(html, max_width=300),
                icon=folium.Icon(color='green', icon='info-sign')
            ).add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)

    # Afficher et récupérer les nouvelles bounds
    ret = st_folium(m, width=1200, height=700, returned_objects=['bounds'])
    if ret and ret.get('bounds'):
        SW = [ret['bounds']['southWest']['lat'], ret['bounds']['southWest']['lng']]
        NE = [ret['bounds']['northEast']['lat'], ret['bounds']['northEast']['lng']]
        st.session_state.map_bounds = (SW, NE)

# 9. Onglet Contribution
def contribution_tab():
    st.subheader("📝 Contribution citoyenne")
    if 'reports' not in st.session_state:
        st.session_state.reports = []
    with st.form("report_form", clear_on_submit=True):
        lat     = st.number_input("Latitude", format="%.6f")
        lon     = st.number_input("Longitude", format="%.6f")
        contact = st.text_input("Votre nom")
        comment = st.text_area("Votre remarque")
        imgs    = st.file_uploader("Photos (max 3)", type=['jpg','png'], accept_multiple_files=True)
        if st.form_submit_button("Publier"):
            enc = [f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
                   for f in imgs[:3]]
            st.session_state.reports.append({
                'lat':lat,'lon':lon,'contact':contact,
                'comment':comment,'images':enc
            })
            st.success("Merci pour votre contribution !")

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
    st_folium(m, width=800, height=600)

# 10. Onglet Pluviométrie
def pluviometrie_tab():
    st.subheader("☔ Pluviométrie")
    if not pluvio.empty:
        st.markdown("**Évolution annuelle (2000–2024)**")
        st.line_chart(pluvio.set_index('year')['value'])
    else:
        st.info("Pas de données annuelles.")
    if not pluvio_mensuel.empty:
        st.markdown("**Moyennes mensuelles**")
        chart = alt.Chart(pluvio_mensuel).mark_bar().encode(
            x=alt.X('Mois:O', sort=list(pluvio_mensuel['Mois'])),
            y='value:Q', tooltip=['Mois','value']
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Pas de données mensuelles.")

# === SWITCH ONGLET ===
tabs = ['Zone de chaleur','Sensibilisation','Contribution','Pluviométrie']
choice = st.sidebar.radio('Onglet', tabs)

if choice == 'Zone de chaleur':
    st.subheader("🌡️ Zone de chaleur")
    st_folium(heatmap_map(), width=800, height=600)
    df = pd.DataFrame(points)[['name','contact','comment']]
    st.markdown("### Témoignages et contacts locaux")
    st.dataframe(df, height=250)

elif choice == 'Sensibilisation':
    sensibilisation_tab()

elif choice == 'Contribution':
    contribution_tab()

else:
    pluviometrie_tab()
    
