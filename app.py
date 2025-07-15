# app.py
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap
import geopandas as gpd
import pandas as pd
import os
import warnings
from shapely.geometry import Point
import altair as alt

warnings.filterwarnings("ignore")

# Page config
st.set_page_config("Zones inondables & Pluviométrie – Ouagadougou", layout="wide")
st.title("Zones inondables & Pluviométrie – Ouagadougou")
st.sidebar.header("Sélection de l'onglet")

# 1. Points terrain
points = [
    {"lat":12.286813, "lon":-1.612065, "name":"Zone A : BOASSA", 
     "images":["images/boassa1.jpg","images/boassa2.jpg"], 
     "comment":"Le marigot déborde chaque année."},
    {"lat":12.324026, "lon":-1.609384, "name":"Zone B : YOAGHIN", 
     "images":["images/yoaghin1.jpg","images/yoaghin2.jpg"],
     "comment":"Routes impraticables."},
    {"lat":12.320957, "lon":-1.615837, "name":"Zone C : KANKAMSE", 
     "images":["images/kankamse1.jpg","images/kankamse2.jpg"],
     "comment":"Fondations fragiles."},
    {"lat":12.342865, "lon":-1.596492, "name":"Zone D : ZONGO", 
     "images":["images/zongo1.jpg","images/zongo2.jpg"],
     "comment":"Eaux stagnantes."},
    {"lat":12.350765, "lon":-1.587388, "name":"Zone E : ST DOMINIQUE", 
     "images":["images/stdom1.jpg","images/stdom2.jpg"],
     "comment":"Caniveaux débordés."},
    {"lat":12.335139, "lon":-1.616538, "name":"Zone F : ZAGTOULI", 
     "images":["images/zagtouli1.jpg","images/zagtouli2.jpg"],
     "comment":"Murs de protection."},
    {"lat":12.367098, "lon":-1.638734, "name":"Zone G : BASSEKO", 
     "images":["images/basseko1.jpg","images/basseko2.jpg"],
     "comment":"Seuil des fenêtres atteint."}
]
heat_data = [(pt['lat'], pt['lon']) for pt in points]

# 2. Chargement couches géo
@st.cache_data
def load_layer(path):
    if os.path.exists(path):
        return gpd.read_file(path).to_crs(epsg=4326)
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

commune = load_layer("data/communes.geojson")
roads   = load_layer("data/voirie.geojson")
water   = load_layer("data/hydrographie.geojson")
grid    = load_layer("data/zones_base.geojson")

# 3a. Pluviométrie annuelle
@st.cache_data
def load_pluvio():
    path = "data/pluviometrie.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        return df[(df['year']>=2000)&(df['year']<=2024)]
    return pd.DataFrame(columns=['year','value','region'])
pluvio = load_pluvio()

# 3b. Pluviométrie mensuelle
@st.cache_data
def load_pluvio_mensuel():
    path = "data/pluvio_mensuel.csv"
    if os.path.exists(path):
        df = pd.read_csv(path)
        # mois en int ou string
        return df
    return pd.DataFrame(columns=['Mois','value','region'])
pluvio_mensuel = load_pluvio_mensuel()

# 4. Fonctions de rendu

def base_map():
    m = folium.Map(location=[12.35, -1.60], zoom_start=12, tiles="CartoDB positron")
    if not commune.empty:
        folium.GeoJson(
            commune.__geo_interface__,
            style_function=lambda f: {'fillColor':'#a8ddb5','fillOpacity':0.2,'color':'none'}
        ).add_to(m)
    if not roads.empty:
        folium.GeoJson(
            roads.__geo_interface__,
            style_function=lambda f: {'color':'grey','weight':1}
        ).add_to(m)
    return m


def heatmap_map():
    m = base_map()
    HeatMap(heat_data, radius=25, blur=15).add_to(m)
    for pt in points:
        html = f"<h4>{pt['name']}</h4><p>{pt['comment']}</p>"
        for img in pt['images']:
            if os.path.exists(img): html += f"<img src='{img}' width='150'><br>"
        folium.CircleMarker(
            location=[pt['lat'],pt['lon']], radius=10, color='red', fill=True, fillOpacity=0.7,
            popup=folium.Popup(html, max_width=300)
        ).add_to(m)
    return m


def risk_map():
    m = base_map()
    if 'classe' in grid.columns:
        folium.Choropleth(
            geo_data=grid.__geo_interface__, data=grid,
            columns=['id','classe'], key_on='feature.properties.id',
            fill_color='YlOrRd', legend_name='Risque (1-5)'
        ).add_to(m)
    return m


def zonage_map():
    m = base_map()
    if 'classe' in grid.columns:
        cols = {1:'#31a354', 3:'#fed976', 5:'#de2d26'}
        for _,r in grid.iterrows():
            folium.GeoJson(
                r.geometry.__geo_interface__,
                style_function=lambda f, c=cols[r['classe']]: {'fillColor':c,'fillOpacity':0.4,'color':'none'}
            ).add_to(m)
    return m

# 5. UI
tabs = ['Zone de chaleur','Risque','Zonage','Pluviométrie']
choice = st.sidebar.radio('Onglet', tabs)
st.subheader(choice)

if choice == 'Pluviométrie':
    if not pluvio.empty:
        st.subheader('Données annuelles')
        st.dataframe(pluvio)
        st.markdown('**Évolution (2000-2024)**')
        st.line_chart(pluvio.set_index('year')['value'])
        st.markdown('**Moyenne mobile 3 ans**')
        st.line_chart(pluvio.set_index('year')['value'].rolling(3, center=True).mean())
        st.markdown('**Histogramme par décennie**')
        dec = pluvio.set_index('year')['value'].groupby(lambda y: (y//10)*10).sum()
        st.bar_chart(dec)
        st.markdown('**Anomalies annuelles**')
        anomalies = pluvio.set_index('year')['value'] - pluvio['value'].mean()
        st.bar_chart(anomalies)
    else:
        st.info("Pas de données annuelles.")

    if not pluvio_mensuel.empty:
        st.subheader('Moyennes mensuelles (1991-2020)')
        chart = alt.Chart(pluvio_mensuel).mark_bar().encode(
            x=alt.X('Mois:N', sort=pluvio_mensuel['Mois']),
            y='value:Q',
            color=alt.value('#3182bd')
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Pas de données mensuelles.")

else:
    func_map = {'Zone de chaleur':heatmap_map,
                'Risque':risk_map,
                'Zonage':zonage_map}
    st_folium(func_map[choice](), width=800, height=600)

if choice == 'Zone de chaleur':
    df = pd.DataFrame(points)[['name','comment']]
    st.subheader('Informations terrain')
    st.dataframe(df)
