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

# 2. Points de terrain enrichis
points = [
    {"lat":12.286813, "lon":-1.612065, "name":"Zone A : BOASSA", "contact":"M. Koulibaly", "comment":"Le marigot déborde chaque saison pluvieuse, inondant la rue principale.", "images":["images/boassa1.jpg","images/boassa2.jpg"]},
    {"lat":12.324026, "lon":-1.609384, "name":"Zone B : YOAGHIN", "contact":"Mme Sawadogo", "comment":"Après 30 min de pluie, la route devient impraticable.", "images":["images/yoaghin1.jpg","images/yoaghin2.jpg"]},
    {"lat":12.320957, "lon":-1.615837, "name":"Zone C : KANKAMSE", "contact":"M. Ouédraogo", "comment":"Les fondations se fissurent sous l'eau stagnante.", "images":["images/kankamse1.jpg","images/kankamse2.jpg"]},
    {"lat":12.342865, "lon":-1.596492, "name":"Zone D : ZONGO", "contact":"Mme Traoré", "comment":"Eaux stagnantes favorisent les moustiques.", "images":["images/zongo1.jpg","images/zongo2.jpg"]},
    {"lat":12.350765, "lon":-1.587388, "name":"Zone E : ST DOMINIQUE", "contact":"M. Dao", "comment":"Caniveaux débordés menaçant les rez‑de‑chaussée.", "images":["images/stdom1.jpg","images/stdom2.jpg"]},
    {"lat":12.335139, "lon":-1.616538, "name":"Zone F : ZAGTOULI", "contact":"Mme Kaboré", "comment":"Le mur de protection s'est affaissé en 2022.", "images":["images/zagtouli1.jpg","images/zagtouli2.jpg"]},
    {"lat":12.367098, "lon":-1.638734, "name":"Zone G : BASSEKO", "contact":"M. Ouahab", "comment":"Le seuil des fenêtres atteint un niveau critique lors des crues.", "images":["images/basseko1.jpg","images/basseko2.jpg"]},
    {"lat":12.322181, "lon":-1.579680, "name":"Zone Bonnaam 1", "contact":"M. Sawadogo", "comment":"4 photos d’inondation.", "images":["images/bonnaam1_1.jpg","images/bonnaam1_2.jpg","images/bonnaam1_3.jpg","images/bonnaam1_4.jpg"]},
    {"lat":12.320240, "lon":-1.579680, "name":"Zone Bonnaam 2", "contact":"Mme Kinda", "comment":"3 photos d’inondation.", "images":["images/bonnaam2_1.jpg","images/bonnaam2_2.jpg","images/bonnaam2_3.jpg"]},
    {"lat":12.313578, "lon":-1.572194, "name":"Zone Bonnaam 3", "contact":"M. Traoré", "comment":"4 photos d’inondation.", "images":["images/bonnaam3_1.jpg","images/bonnaam3_2.jpg","images/bonnaam3_3.jpg","images/bonnaam3_4.jpg"]},
    {"lat":12.313206, "lon":-1.574259, "name":"Zone Bonnaam 4", "contact":"Mme Zongo", "comment":"2 photos d’inondation.", "images":["images/bonnaam4_1.jpg","images/bonnaam4_2.jpg"]},
    {"lat":12.307954, "lon":-1.567229, "name":"Zone Bonnaam 5", "contact":"M. Ouédraogo", "comment":"10 ha inondés (superficie).", "images":["images/bonnaam5_1.jpg","images/bonnaam5_2.jpg"]},
    {"lat":12.306072, "lon":-1.566660, "name":"Zone Bonnaam 6", "contact":"Mme Balima", "comment":"2 photos d’inondation.", "images":["images/bonnaam6_1.jpg","images/bonnaam6_2.jpg"]},
    {"lat":12.304420, "lon":-1.569685, "name":"Zone Bonnaam 7", "contact":"M. Kaboré", "comment":"2 photos d’inondation.", "images":["images/bonnaam7_1.jpg","images/bonnaam7_2.jpg"]},
    {"lat":12.306373, "lon":-1.597861, "name":"Zone Sandogo 1", "contact":"Mme Sanon", "comment":"3 photos d’inondation.", "images":["images/sandogo1_1.jpg","images/sandogo1_2.jpg","images/sandogo1_3.jpg"]},
    {"lat":12.305514, "lon":-1.593024, "name":"Zone Sandogo 2", "contact":"M. Kinda", "comment":"3 photos d’inondation.", "images":["images/sandogo2_1.jpg","images/sandogo2_2.jpg","images/sandogo2_3.jpg"]},
    {"lat":12.305000, "lon":-1.595000, "name":"Zone Sandogo 3", "contact":"M. Zongo", "comment":"Coordonnée additionnelle.", "images":["images/sandogo3_1.jpg"]},
    {"lat":12.304000, "lon":-1.598000, "name":"Zone Sandogo 4", "contact":"Mme Ouédraogo", "comment":"Coordonnée additionnelle.", "images":["images/sandogo4_1.jpg"]},
    {"lat":12.337832, "lon":-1.5847228, "name":"Zone Yoaghin NE", "contact":"M. Traoré", "comment":"4 photos d’inondation.", "images":["images/yoaghin_ne1.jpg","images/yoaghin_ne2.jpg","images/yoaghin_ne3.jpg","images/yoaghin_ne4.jpg"]}
]

# 3. Chargement des couches géographiques Chargement des couches géographiques
@st.cache_data
def load_layer(path):
    if os.path.exists(path):
        return gpd.read_file(path).to_crs(epsg=4326)
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

commune = load_layer("data/communes.geojson")
roads   = load_layer("data/voirie.geojson")
water   = load_layer("data/hydrographie.geojson")
grid    = load_layer("data/zones_base.geojson")

# 4. Séries pluviométriques
@st.cache_data
def load_pluvio():
    path = "data/pluviometrie.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df[(df['year']>=2000)&(df['year']<=2024)]
    return pd.DataFrame(columns=['year','value','region'])
pluvio = load_pluvio()

@st.cache_data
def load_pluvio_mensuel():
    path = "data/pluvio_mensuel.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        if 'month' in df.columns:
            df = df.rename(columns={'month':'Mois'})
        return df
    return pd.DataFrame(columns=['Mois','value','region'])
pluvio_mensuel = load_pluvio_mensuel()

# 5. Encodage base64 pour images

def encode_img(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

# 6. Fond carto

def base_map():
    m = folium.Map(location=[12.35, -1.60], zoom_start=12, tiles="CartoDB positron")
    if not commune.empty:
        folium.GeoJson(commune.__geo_interface__, style_function=lambda f: {'fillColor':'#a8ddb5','fillOpacity':0.2,'color':'none'}).add_to(m)
    if not roads.empty:
        folium.GeoJson(roads.__geo_interface__, style_function=lambda f: {'color':'grey','weight':1}).add_to(m)
    return m

# 7. Zone de chaleur (cercles 1 km + halo 2 km)

def heatmap_map():
    m = base_map()
    HeatMap([(pt['lat'],pt['lon']) for pt in points], radius=25, blur=15).add_to(m)
    for pt in points:
        folium.Circle(location=[pt['lat'],pt['lon']], radius=1000, color='#de2d26', fill=True, fill_opacity=0.3).add_to(m)
        folium.Circle(location=[pt['lat'],pt['lon']], radius=2000, color='#feb24c', fill=True, fill_opacity=0.2).add_to(m)
        html = f"<h4>{pt['name']}</h4><p><i>{pt['contact']}</i><br>{pt['comment']}</p>"
        for img in pt['images']:
            if os.path.exists(img):
                b64 = encode_img(img)
                html += f"<img src='data:image/jpeg;base64,{b64}' width='150'><br>"
        folium.Marker(location=[pt['lat'],pt['lon']], icon=folium.Icon(color='red', icon='tint', prefix='fa'), popup=folium.Popup(html, max_width=300)).add_to(m)
    return m

# 8. Carte de risque

def risk_map():
    m = base_map()
    if 'classe' in grid.columns:
        folium.Choropleth(geo_data=grid.__geo_interface__, data=grid, columns=['id','classe'], key_on='feature.properties.id', fill_color='YlOrRd', legend_name='Niveau de risque').add_to(m)
    return m

# 9. Zonage simplifié

def zonage_map():
    m = base_map()
    if 'classe' in grid.columns:
        colors={1:'#31a354',3:'#fed976',5:'#de2d26'}
        for _,row in grid.iterrows():
            col=colors.get(row['classe'],'gray')
            folium.GeoJson(row.geometry.__geo_interface__, style_function=lambda f,c=col:{'fillColor':c,'fillOpacity':0.4,'color':'none'}).add_to(m)
    return m

# 10. UI avec onglets

tabs=['Zone de chaleur','Risque','Zonage','Pluviométrie']
choice=st.sidebar.radio('Onglet',tabs)
st.subheader(choice)

if choice=='Pluviométrie':
    if not pluvio.empty:
        st.subheader('Annuel (2000–2024)')
        st.line_chart(pluvio.set_index('year')['value'],height=300)
        st.line_chart(pluvio.set_index('year')['value'].rolling(3,center=True).mean(),height=300)
        dec=pluvio.set_index('year')['value'].groupby(lambda y:(y//10)*10).sum()
        st.bar_chart(dec,height=300)
        st.bar_chart(pluvio.set_index('year')['value']-pluvio['value'].mean(),height=300)
    else:
        st.info('Pas de données annuelles.')
    if not pluvio_mensuel.empty:
        st.subheader('Mensuel – Moyennes')
        chart=alt.Chart(pluvio_mensuel).mark_bar(color='#3182bd').encode(x=alt.X('Mois:O',sort=pluvio_mensuel['Mois'].tolist()),y='value:Q',tooltip=['Mois','value']).properties(height=300)
        st.altair_chart(chart,use_container_width=True)
    else:
        st.info('Pas de données mensuelles.')
else:
    mapper={'Zone de chaleur':heatmap_map,'Risque':risk_map,'Zonage':zonage_map}
    st_folium(mapper[choice](),width=800,height=600)
    if choice=='Zone de chaleur':
        df=pd.DataFrame(points)[['name','contact','comment']]
        st.subheader('Témoignages locaux')
        st.dataframe(df)

