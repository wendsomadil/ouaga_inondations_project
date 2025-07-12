# compute_zones14.py
"""
Génère un GeoJSON de 14 zones d'inondation pour Ouagadougou
en combinant distance à l'eau, pente (optionnelle) et historique.
"""
import os
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from shapely.ops import unary_union
from sklearn.cluster import KMeans

# 1. Charger la grille de base
grid_path = "data/zones_base.geojson"
if not os.path.exists(grid_path):
    raise FileNotFoundError(f"Grille manquante: {grid_path}")
grid = gpd.read_file(grid_path).to_crs(epsg=32630)

# 2. Charger hydrographie et calculer distance minimale
hydro_path = "data/hydrographie.geojson"
hydro = gpd.read_file(hydro_path).to_crs(epsg=32630) if os.path.exists(hydro_path) else gpd.GeoDataFrame(geometry=[], crs="EPSG:32630")
grid["dist"] = grid.geometry.apply(lambda poly: hydro.distance(poly).min() if not hydro.empty else np.nan)

# 3. Calcul pente si MNT valide
mnt_path = "data/MNT.tif"
def calc_slope(poly, dem):
    try:
        window = rasterio.windows.from_bounds(*poly.bounds, transform=dem.transform)
        data = dem.read(1, window=window)
        gy, gx = np.gradient(data.astype(float), dem.res[1], dem.res[0])
        return np.nanmean(np.sqrt(gx**2 + gy**2)) * 100
    except Exception:
        return np.nan
if os.path.exists(mnt_path) and os.path.getsize(mnt_path) > 1024:
    dem = rasterio.open(mnt_path)
    grid["slope"] = grid.geometry.apply(lambda poly: calc_slope(poly, dem))
else:
    grid["slope"] = np.nan

# 4. Charger historique inondations (facultatif)
histo_path = "data/histo_inondations.csv"
if os.path.exists(histo_path):
    histo = pd.read_csv(histo_path)
    # s'assurer que les colonnes existent
    if "id_zone" in histo.columns and "n_events" in histo.columns:
        histo = histo.rename(columns={"id_zone": "id", "n_events": "freq"})
        grid = grid.merge(histo[["id","freq"]], on="id", how="left")
    else:
        grid["freq"] = 0
else:
    grid["freq"] = 0

# 5. Normalisation (0-1)
for col in ["dist","slope","freq"]:
    if grid[col].notna().any():
        mn, mx = grid[col].min(), grid[col].max()
        grid[f"{col}_norm"] = (grid[col] - mn) / (mx - mn) if mx > mn else 0
    else:
        grid[f"{col}_norm"] = 0

# 6. Calcul indice de risque (pondération) w1=dist, w2=slope, w3=freq
grid["risk_index"] = (
    0.5 * (1 - grid["dist_norm"]) +
    0.3 * grid["slope_norm"] +
    0.2 * grid["freq_norm"]
)

# 7. Clustering en 14 zones
kmeans = KMeans(n_clusters=14, random_state=42)
grid["zone14"] = kmeans.fit_predict(grid[["risk_index"]]) + 1

# 8. Export
out_path = "data/zones_inond14.geojson"
grid.to_crs(epsg=4326).to_file(out_path, driver="GeoJSON")
print(f"✅ Exporté 14 zones dans {out_path}")
