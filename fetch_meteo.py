# fetch_meteo.py

from datetime import datetime
import pandas as pd
from meteostat import Point, Daily
import os

# 1) Définir la position de Ouagadougou
loc = Point(12.37, -1.53, 310)  # lat, lon, altitude

# 2) Période 2000–2024
start = datetime(2000, 1, 1)
end   = datetime(2024, 12, 31)

# 3) Récupérer les données journalières
daily = Daily(loc, start, end)
df_daily = daily.fetch()  # colonnes : prcp (mm), tavg, etc.

if 'prcp' not in df_daily:
    raise RuntimeError("Aucune donnée de précipitations journalières disponible pour cette localisation")

# 4) Agréger en pluviométrie annuelle
annual = df_daily['prcp'].resample('Y').sum().rename('value').reset_index()
annual['year']   = annual['time'].dt.year
annual['region'] = 'Ouagadougou'
annual = annual[['year','value','region']]

# 5) Calculer la moyenne multi-annuelle par mois
monthly = df_daily['prcp'].resample('M').sum().rename('value').reset_index()
monthly['month'] = monthly['time'].dt.month
monthly_mean = monthly.groupby('month')['value'].mean().reset_index()
monthly_mean['region'] = 'Ouagadougou'
monthly_mean = monthly_mean[['month','value','region']]

# 6) Sauvegarder les CSV
os.makedirs('data', exist_ok=True)
annual.to_csv('data/pluviometrie.csv',      index=False)  # cumuls annuels 2000–2024
monthly_mean.to_csv('data/pluvio_mensuel.csv', index=False)  # moyennes mensuelles

print("✅ Fichiers générés :")
print(" • data/pluviometrie.csv      →", annual.head())
print(" • data/pluvio_mensuel.csv    →", monthly_mean.head())
