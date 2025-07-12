# Cartographie des zones inondables d'Ouagadougou

## Installation

1. Extraire le dossier du projet.
2. Installer les dépendances :
    pip install -r requirements.txt
3. Lancer l'application :
    streamlit run app.py

## Structure

- `app.py` : code principal Streamlit.
- `data/` : fichiers géographiques et tabulaires.
- `tiles/` : tuiles de carte hors-ligne (OSM).
- `static/screenshots/` : captures d'écran.
- `static/icons/` : icônes UI.
- `images/` : captures d’écran et icônes.
- `requirements.txt` : bibliothèques Python requises.
- `README.md` : ce document.

## Description des cartes et couches

- **Carte de base** : fond OSM (en tuiles locales) centré sur Ouagadougou.
- **Zones inondables** : polygones bleus indiquant des zones propices aux inondations (données fictives).  
- **Zonage risques** : carte en choroplèthe illustrant le niveau de risque simulé par secteur.  
- **Planification** : localisation des infrastructures stratégiques (par ex. points de refuge).  
- **Sensibilisation** : icônes d’alerte (triangles danger) placées dans les zones inondables.  
- **Pluviométrie** : répartition spatiale des précipitations moyennes (carte thématique, palette de bleus).  

Les données proviennent de sources ouvertes ou sont simulées. La carte est construite avec Folium:contentReference[oaicite:14]{index=14} et intégrée dans Streamlit. Pour supporter le fonctionnement hors ligne, l’application est configurée pour utiliser des tuiles locales (`tiles=None`):contentReference[oaicite:15]{index=15} et exploite les données OpenStreetMap hors-ligne (projet OSM libre:contentReference[oaicite:16]{index=16}).
