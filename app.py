# app.py
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap, MarkerCluster
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
import os
import warnings
import branca.colormap as cm

warnings.filterwarnings("ignore")

# Config page
st.set_page_config("Inondations Ouagadougou", layout="wide")
st.title("Carte optimisée – Zones inondables Ouagadougou")
st.sidebar.header("Sélection de la carte")

# 1. Points GPS
barrages = [(12.3662, -1.5270), (12.3461, -1.5457), (12.3386, -1.5229)]
obs_coords = [
    (12.286813, -1.612065), (12.324026, -1.609384), (12.320957, -1.615837),
    (12.342865, -1.596492), (12.350765, -1.587388), (12.335139, -1.616538),
    (12.367098, -1.638734),
    # + 7 nouvelles simulées
    (12.3675, -1.5280), (12.3455, -1.5460), (12.3388, -1.5232),
    (12.3530, -1.5800), (12.3580, -1.5750), (12.3500, -1.6500), (12.3440, -1.6450)
]
heat_data = barrages + obs_coords

# 2. Chargement GeoJSON locaux (fallback vide)
@st.cache_data
def load_layer(path):
    if os.path.exists(path):
        return gpd.read_file(path).to_crs(epsg=4326)
    return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")

commune = load_layer("data/communes.geojson")
roads   = load_layer("data/voirie.geojson")
water   = load_layer("data/hydrographie.geojson")
grid    = load_layer("data/zones_base.geojson")
zones14 = load_layer("data/zones_inond14.geojson")

# 3. Classification simple (si pas zones14)
if "zone14" not in zones14.columns and not grid.empty and not water.empty:
    grid["dist"] = grid.geometry.apply(lambda g: water.distance(g).min())
    grid["classe"] = grid["dist"].apply(lambda d: 5 if d<=200 else (3 if d<=400 else 1))

# 4. Fonctions Folium
def base_map():
    m = folium.Map(location=[12.35, -1.60], zoom_start=12, tiles="CartoDB positron")
    if not commune.empty:
        folium.GeoJson(commune, name="Commune", style_function=lambda f:{"color":"black"}).add_to(m)
    if not roads.empty:
        folium.GeoJson(roads, name="Voirie", style_function=lambda f:{"color":"grey","weight":1}).add_to(m)
    return m

def heatmap_map():
    m = base_map()
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    cluster = MarkerCluster(name="Inondations").add_to(m)
    for lat, lon in heat_data:
        folium.Marker([lat, lon], icon=folium.Icon(color="blue", icon="tint", prefix="fa")).add_to(cluster)
    folium.LayerControl().add_to(m)
    return m

def risk_map():
    m = base_map()
    if "classe" in grid.columns:
        folium.Choropleth(
            geo_data=grid.__geo_interface__,
            data=grid,
            columns=["id","classe"],
            key_on="feature.properties.id",
            fill_color="YlOrRd",
            legend_name="Risque (1-5)"
        ).add_to(m)
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    folium.LayerControl().add_to(m)
    return m

def zonage_map():
    m = base_map()
    if "classe" in grid.columns:
        pal = {1:"green",3:"orange",5:"red"}
        for _, r in grid.iterrows():
            c = pal.get(r["classe"], "gray")
            folium.GeoJson(r.geometry.__geo_interface__,
                style_function=lambda feat, color=c:{"fillColor":color,"fillOpacity":0.4,"color":color}
            ).add_to(m)
    folium.LayerControl().add_to(m)
    return m

def zones14_map():
    m = base_map()
    if "zone14" in zones14.columns:
        cmap = cm.linear.YlGnBu_09.scale(zones14.zone14.min(), zones14.zone14.max())
        cmap.caption = "Zone de risque (1–14)"
        cmap.add_to(m)
        for _, r in zones14.iterrows():
            color = cmap(r.zone14)
            folium.GeoJson(r.geometry.__geo_interface__,
                style_function=lambda feat, col=color:{"fillColor":col,"fillOpacity":0.5,"color":col,"weight":0.5}
            ).add_to(m)
        folium.LayerControl().add_to(m)
    else:
        st.info("14 zones non disponibles.")
    return m

def planning_map():
    m = risk_map()
    if not water.empty:
        buf = water.buffer(200)
        folium.GeoJson(buf.__geo_interface__, name="Servitudes",
            style_function=lambda f:{"color":"blue","fillOpacity":0.1}
        ).add_to(m)
        folium.LayerControl().add_to(m)
    return m

def awareness_map():
    m = base_map()
    cluster = MarkerCluster(name="Observations").add_to(m)
    for lat, lon in heat_data:
        folium.Marker([lat, lon], icon=folium.Icon(color="orange", icon="tint", prefix="fa")).add_to(cluster)
    folium.LayerControl().add_to(m)
    return m

def pluviometry_map():
    m = base_map()
    st.info("Pas de couche pluviométrie.")
    folium.LayerControl().add_to(m)
    return m

# 5. UI
maps = {
    "Base": base_map,
    "HeatMap": heatmap_map,
    "Risque": risk_map,
    "Zonage": zonage_map,
    "Zones14": zones14_map,
    "Planif": planning_map,
    "Sensib": awareness_map,
    "Pluvio": pluviometry_map
}
choice = st.sidebar.radio("Carte", list(maps.keys()))
st.subheader(choice)

m = maps[choice]()
st_folium(m, width=800, height=600)

if choice in ("HeatMap","Risque","Zones14"):
    st.subheader("Points inondations")
    st.dataframe(pd.DataFrame(heat_data, columns=["lat","lon"]))
