# prepare_data.py
import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
import numpy as np    # <--- import numpy
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

# 0. Crée le dossier data
os.makedirs("data", exist_ok=True)

# 1. Limite administrative
city = ox.geocode_to_gdf("Ouagadougou, Burkina Faso")
city.to_crs(epsg=4326).to_file("data/communes.geojson", driver="GeoJSON")

# 2. Réseau routier (highway)
G = ox.graph_from_place("Ouagadougou, Burkina Faso", network_type="drive")
roads = ox.graph_to_gdfs(G, nodes=False, edges=True)
roads.to_crs(epsg=4326).to_file("data/voirie.geojson", driver="GeoJSON")

# 3. Cours d’eau (waterway)
tags_water = {"waterway": True}
water = ox.features_from_place("Ouagadougou, Burkina Faso", tags_water)
water = water[water.geometry.type.isin(["LineString","MultiLineString"])]
water.to_crs(epsg=4326).to_file("data/hydrographie.geojson", driver="GeoJSON")

# 4. Servitudes 200 m autour des cours d’eau
water_utm = water.to_crs(epsg=32630)
serv_buffer = water_utm.buffer(200)
serv = gpd.GeoDataFrame(geometry=serv_buffer, crs=water_utm.crs).to_crs(epsg=4326)
serv.to_file("data/servitudes.geojson", driver="GeoJSON")

# 5. Points barrages + observations
barrages = [(12.36620,-1.52700),(12.34610,-1.54570),(12.33860,-1.52290)]
obs = [
    (12.286813,-1.612065),(12.324026,-1.609384),(12.320957,-1.615837),
    (12.342865,-1.596492),(12.350765,-1.587388),(12.335139,-1.616538),
    (12.367098,-1.638734)
]
pts = barrages + obs
labels = ["barrage"]*len(barrages) + ["obs"]*len(obs)
gdf_pts = gpd.GeoDataFrame(
    {"type": labels},
    geometry=[Point(lon, lat) for lat, lon in pts],
    crs="EPSG:4326"
)
gdf_pts.to_file("data/poi.geojson", driver="GeoJSON")

# 6. Observations < 2 km des barrages
b_df = gdf_pts[gdf_pts.type=="barrage"].to_crs(epsg=32630)
o_df = gdf_pts[gdf_pts.type=="obs"].to_crs(epsg=32630)
union_buf = unary_union(b_df.geometry).buffer(2000)
o_within = o_df[o_df.geometry.within(union_buf)]
o_within.to_crs(epsg=4326).to_file("data/observations_2km.geojson", driver="GeoJSON")

# 7. zones_base grille 500 m
xmin, ymin, xmax, ymax = city.total_bounds
dx = dy = 0.005
cells, ids = [], []
i = 0
lat = ymin
while lat < ymax:
    lon = xmin
    while lon < xmax:
        cells.append(Polygon([
            (lon, lat),
            (lon+dx, lat),
            (lon+dx, lat+dy),
            (lon, lat+dy)
        ]))
        ids.append(i)
        i += 1
        lon += dx
    lat += dy

gpd.GeoDataFrame({"id": ids}, geometry=cells, crs=city.crs) \
   .to_file("data/zones_base.geojson", driver="GeoJSON")

# 8. MNT vide (à remplacer par ton MNT réel)
open("data/MNT.tif", "wb").close()

# 9. Simulation CSV pluviométrie
dfp = pd.DataFrame({
    "secteur": [f"S{i}" for i in range(len(cells))],
    "mm":       np.random.randint(50, 300, size=len(cells))  # <--- utilisation de numpy
})
dfp.to_csv("data/pluviometrie.csv", index=False)

print("✅ Données générées :")
for f in sorted(os.listdir("data")):
    print("  -", f)
