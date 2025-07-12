import folium
from folium.plugins import HeatMap
import geopandas as gpd
from shapely.geometry import Point

# Coordonnées GPS (lat, lon) des zones inondables
coords = [
    (12.286813, -1.612065),
    (12.324026, -1.609384),
    (12.320957, -1.615837),
    (12.342865, -1.596492),
    (12.350765, -1.587388),
    (12.335139, -1.616538),
    (12.367098, -1.638734)
]

# Charger les GeoJSON
rivers = gpd.read_file("data/hydrographie.geojson")
dams   = gpd.read_file("data/barrages.geojson")

# Créer la carte
m = folium.Map(location=[12.35, -1.61], zoom_start=12, tiles="CartoDB positron")

# Ajouter rivières et barrages
folium.GeoJson(rivers, name="Rivières",
               style_function=lambda f: {"color":"blue","weight":2}).add_to(m)
folium.GeoJson(dams, name="Barrages",
               style_function=lambda f: {"color":"darkred","fillOpacity":0.3}).add_to(m)

# Préparer heatmap des coordonnées
heat_data = [[lat, lon] for lat, lon in coords]
HeatMap(heat_data, radius=25, blur=15, max_zoom=13).add_to(m)

# Contrôle des couches
folium.LayerControl().add_to(m)

# Sauvegarder
m.save("heatmap_inondations_ouagadougou.html")
print("Heatmap générée : heatmap_inondations_ouagadougou.html")
