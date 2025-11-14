# satpos.py
import numpy as np
from pyproj import Transformer

def ecef_to_geodetic(x, y, z):
    """ECEF (m) → Enlem, boylam, yükseklik (derece, derece, m)"""
    transformer = Transformer.from_crs("epsg:4978", "epsg:4326", always_xy=True)
    lon, lat, alt = transformer.transform(x, y, z)
    return lat, lon, alt

def get_satellite_positions(sp3_data, sat_id):
    """Verilen uydu ID'sine ait tüm ECEF konumlarını döndürür"""
    positions = []
    for sat, x, y, z in sp3_data:
        if sat_id in sat:
            positions.append((x, y, z))
    return np.array(positions)