# fetch_data.py
import os
import requests
import zipfile
import io
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon

os.makedirs("data", exist_ok=True)

# 1. Requête Overpass pour obtenir la limite et les routes
overpass_url = "http://overpass-api.de/api/interpreter"
# a) Limite admin d'Ouagadougou
query_boundary = """
[out:json];
relation["boundary"="administrative"]["name"="Ouagadougou"];
out geom;
"""
# b) Réseau routier (highway) dans la même zone
query_highways = """
[out:json][timeout:25];
area[name="Ouagadougou"]->.a;
way(area.a)["highway"];
(._;>;);
out geom;
"""

def overpass_to_gdf(query, geom_type):
    resp = requests.post(overpass_url, data={'data': query})
    data = resp.json()
    # Rassembler en GeoDataFrame
    features = []
    for el in data['elements']:
        if el['type'] == 'way' and 'geometry' in el:
            coords = [(pt['lon'], pt['lat']) for pt in el['geometry']]
            if geom_type == 'LineString':
                geom = Point(coords[0]).buffer(0) if len(coords)<2 else Polygon(coords) if coords[0]==coords[-1] else gpd.GeoSeries().geometry.unary_union # fallback
            else:
                from shapely.geometry import LineString
                geom = LineString(coords)
            features.append({'geometry': geom, 'tags': el.get('tags', {})})
    return gpd.GeoDataFrame(features, crs="EPSG:4326")

# Récupérer et sauvegarder
# a) Limite communale
resp = requests.post(overpass_url, data={'data': query_boundary})
boundary_data = resp.json()
# Extraire l'objet multipolygon
from shapely.geometry import Polygon, MultiPolygon
polys = []
for el in boundary_data['elements']:
    if el['type']=='relation' and 'members' in el:
        for mem in el['members']:
            if mem['type']=='way' and mem.get('role')=='outer':
                coords = [(pt['lon'], pt['lat']) for pt in mem['geometry']]
                polys.append(Polygon(coords))
boundary = MultiPolygon(polys)
gpd.GeoDataFrame({'geometry':[boundary]}, crs="EPSG:4326") \
    .to_file("data/communes.geojson", driver="GeoJSON")

# b) Voirie
# Pour simplifier, on utilise la même zone pour roads via aires lat/lon
# Ici, on réutilise query_highways
gdf_roads = overpass_to_gdf(query_highways, geom_type='LineString')
gdf_roads.to_file("data/voirie.geojson", driver="GeoJSON")

# 2. zones_base : découpage en grilles de 1km
city = gpd.read_file("data/communes.geojson")
xmin, ymin, xmax, ymax = city.total_bounds
dx = dy = 0.01  # env. 1km
cells = []
ids = []
i = 0
y = ymin
while y < ymax:
    x = xmin
    while x < xmax:
        cells.append(Polygon([(x,y),(x+dx,y),(x+dx,y+dy),(x,y+dy)]))
        ids.append(i); i+=1
        x += dx
    y += dy
gpd.GeoDataFrame({'id':ids}, geometry=cells, crs=city.crs) \
   .to_file("data/zones_base.geojson", driver="GeoJSON")

# 3. Cours d’eau (waterway) et servitudes 200m
query_rivers = """
[out:json][timeout:25];
area[name="Ouagadougou"]->.a;
way(area.a)["waterway"];
(._;>;);
out geom;
"""
gdf_riv = overpass_to_gdf(query_rivers, geom_type='LineString')
gdf_riv.to_file("data/hydrographie.geojson", driver="GeoJSON")
# Buffer servitudes
serv = gdf_riv.to_crs(epsg=32630).buffer(200).to_crs(epsg=4326)
gpd.GeoDataFrame(geometry=serv, crs="EPSG:4326") \
   .to_file("data/servitudes.geojson", driver="GeoJSON")

# 4. Points inondation + barrage
barrages = [(12.36620,-1.52700),(12.34610,-1.54570),(12.33860,-1.52290)]
obs = [
    (12.286813,-1.612065),(12.324026,-1.609384),(12.320957,-1.615837),
    (12.342865,-1.596492),(12.350765,-1.587388),(12.335139,-1.616538),
    (12.367098,-1.638734)
]
pts = barrages + obs
types = ['barrage']*len(barrages) + ['obs']*len(obs)
gdf_pts = gpd.GeoDataFrame({'type':types},
                           geometry=[Point(lon,lat) for lat,lon in pts],
                           crs="EPSG:4326")
gdf_pts.to_file("data/poi.geojson", driver="GeoJSON")

# Points à moins de 2km de barrage
b_df = gdf_pts[gdf_pts['type']=='barrage'].to_crs(epsg=32630)
o_df = gdf_pts[gdf_pts['type']=='obs'].to_crs(epsg=32630)
mask = o_df.geometry.apply(lambda x: b_df.distance(x).min() <= 2000)
o_df[mask].to_crs(epsg=4326).to_file("data/observations_2km.geojson", driver="GeoJSON")

print("✅ Data initiale générée dans le dossier data/ :")
for f in os.listdir("data"):
    print("  •", f)
