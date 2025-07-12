# app.py
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import HeatMap, MarkerCluster
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point, Polygon
import os
import osmnx as ox
import warnings

warnings.filterwarnings("ignore")

# Configuration de la page
st.set_page_config("Inondations Ouagadougou", layout="wide")
st.title("Carte optimisée – Zones inondables Ouagadougou")
st.sidebar.header("Sélection de la carte")

# 1. Points GPS (barrages + observations existantes + nouvelles observations)
barrages = [(12.3662, -1.5270), (12.3461, -1.5457), (12.3386, -1.5229)]
obs_coords = [
    (12.286813, -1.612065), (12.324026, -1.609384), (12.320957, -1.615837),
    (12.342865, -1.596492), (12.350765, -1.587388), (12.335139, -1.616538),
    (12.367098, -1.638734)
]
# +7 nouvelles coordonnées simulées le long du réseau hydrographique
extra_coords = [
    # Proches des barrages 1, 2, 3
    (12.3675, -1.5280),  # aval barrage 1
    (12.3455, -1.5460),  # aval barrage 2
    (12.3388, -1.5232),  # aval barrage 3
    # Quartier Nagrin (secteur sud-est)
    (12.3530, -1.5800),
    (12.3580, -1.5750),
    # Quartier Tampouy (ouest)
    (12.3500, -1.6500),
    (12.3440, -1.6450)
]
# Fusionner toutes les observations
heat_data = barrages + obs_coords + extra_coords

# 2. Chargements différés et simplification des couches
@st.cache_data
def load_commune():
    g = ox.geocode_to_gdf("Ouagadougou, Burkina Faso").to_crs(epsg=4326)
    g.geometry = g.geometry.simplify(0.001)
    return g

@st.cache_data
def load_roads():
    tags = {"highway": ["motorway", "primary", "secondary", "trunk"]}
    g = ox.features_from_place("Ouagadougou, Burkina Faso", tags)
    g = g[g.geometry.type.isin(["LineString", "MultiLineString"])].to_crs(epsg=4326)
    g.geometry = g.geometry.simplify(0.001)
    return g

@st.cache_data
def load_water():
    tags = {"waterway": True}
    w = ox.features_from_place("Ouagadougou, Burkina Faso", tags)
    w = w[w.geometry.type.isin(["LineString", "MultiLineString"])].to_crs(epsg=4326)
    w.geometry = w.geometry.simplify(0.001)
    return w

@st.cache_data
def load_grid():
    city = load_commune()
    xmin, ymin, xmax, ymax = city.total_bounds
    dx = dy = 0.01  # maille ~1km
    cells, ids = [], []
    idx = 0
    y = ymin
    while y < ymax:
        x = xmin
        while x < xmax:
            cells.append(Polygon([(x,y), (x+dx,y), (x+dx,y+dy), (x,y+dy)]))
            ids.append(idx)
            idx += 1
            x += dx
        y += dy
    grid = gpd.GeoDataFrame({"id": ids}, geometry=cells, crs=city.crs)
    grid.geometry = grid.geometry.simplify(0.002)
    return grid

# 3. Classification simple en 3 classes
@st.cache_data
def classify_grid():
    grid = load_grid()
    water = load_water().to_crs(grid.crs)
    if grid.empty or water.empty:
        return grid
    grid = grid.copy()
    grid['dist'] = grid.geometry.apply(lambda g: water.distance(g).min())
    grid['classe'] = grid['dist'].apply(lambda d: 5 if d <=200 else (3 if d<=400 else 1))
    return grid

# 4. Chargement des 14 zones issues de compute_zones14.py
@st.cache_data
def load_zones14():
    path = 'data/zones_inond14.geojson'
    if os.path.exists(path):
        z = gpd.read_file(path).to_crs(epsg=4326)
        return z
    return gpd.GeoDataFrame(geometry=[], crs='EPSG:4326')

# 5. Fonctions de rendu Folium

def base_map():
    m = folium.Map(location=[12.35, -1.60], zoom_start=12, tiles='CartoDB positron')
    comm = load_commune()
    roads = load_roads()
    if not comm.empty:
        folium.GeoJson(comm, name='Commune', style_function=lambda f: {'color':'black'}).add_to(m)
    if not roads.empty:
        folium.GeoJson(roads, name='Voirie', style_function=lambda f: {'color':'grey','weight':1}).add_to(m)
    return m


def heatmap_map():
    m = base_map()
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    cluster = MarkerCluster(name='Observations').add_to(m)
    for lat, lon in obs_coords:
        folium.Marker([lat, lon], icon=folium.Icon(color='blue', icon='tint', prefix='fa')).add_to(cluster)
    folium.LayerControl().add_to(m)
    return m


def risk_map():
    m = base_map()
    grid = classify_grid()
    if not grid.empty:
        folium.Choropleth(
            geo_data=grid.__geo_interface__,
            data=grid,
            columns=['id','classe'],
            key_on='feature.properties.id',
            fill_color='YlOrRd',
            legend_name='Risque (1-5)'
        ).add_to(m)
    HeatMap(heat_data, radius=15, blur=10).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def zonage_map():
    m = base_map()
    grid = classify_grid()
    pal = {1:'green',3:'orange',5:'red'}
    for _, r in grid.iterrows():
        c = pal.get(r['classe'],'gray')
        folium.GeoJson(r.geometry.__geo_interface__,
                       style_function=lambda feat, color=c: {'fillColor':color,'fillOpacity':0.4,'color':color}
        ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def zones14_map():
    m = base_map()
    zones14 = load_zones14()
    if zones14.empty or 'zone14' not in zones14.columns:
        st.info('Zones14 non disponibles ou mal définies.')
        return m
    # Créer une colormap
    import branca.colormap as cm
    colormap = cm.linear.YlGnBu_09.scale(1, 14)
    colormap.caption = 'Zone de risque (1–14)'
    colormap.add_to(m)
    # Ajouter chaque zone
    for _, row in zones14.iterrows():
        z = int(row['zone14'])
        color = colormap(z)
        folium.GeoJson(
            row.geometry.__geo_interface__,
            style_function=lambda feat, c=color: {'fillColor':c, 'fillOpacity':0.5, 'color':c, 'weight':0.3}
        ).add_to(m)
    folium.LayerControl().add_to(m)
    return m


def planning_map():
    m = risk_map()
    serv = load_water().buffer(200)
    if hasattr(serv, '__geo_interface__'):
        folium.GeoJson(serv.__geo_interface__, name='Servitudes', style_function=lambda f: {'color':'blue','fillOpacity':0.1}).add_to(m)
        folium.LayerControl().add_to(m)
    return m


def awareness_map():
    m = base_map()
    cluster = MarkerCluster(name='Inondations').add_to(m)
    for lat, lon in heat_data:
        folium.Marker([lat, lon], icon=folium.Icon(color='orange', icon='tint', prefix='fa')).add_to(cluster)
    folium.LayerControl().add_to(m)
    return m


def pluviometry_map():
    m = base_map()
    st.info('Pas de couche pluviométrie actuellement implémentée.')
    folium.LayerControl().add_to(m)
    return m

# 6. Interface utilisateur
maps = {
    'Base': base_map,
    'HeatMap': heatmap_map,
    'Risque': risk_map,
    'Zonage': zonage_map,
    'Zones14': zones14_map,
    'Planif': planning_map,
    'Sensib': awareness_map,
    'Pluvio': pluviometry_map
}
choice = st.sidebar.radio('Carte', list(maps.keys()))
st.subheader(choice)

m = maps[choice]()
st_folium(m, width=800, height=600)

if choice in ['HeatMap','Risque','Zones14']:
    st.subheader('Points inondations')
    st.dataframe(pd.DataFrame(heat_data, columns=['lat','lon']))
