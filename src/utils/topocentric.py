import math

def ecef_to_topocentric(x_sat, y_sat, z_sat, lat_sta, lon_sta, h_sta):
    """Uydunun ECEF koordinatlarını, İstasyonun konumuna göre Toposentrik (Azimut, Elevasyon, Mesafe) yapar."""
    a = 6378137.0
    f = 1 / 298.257223563
    e2 = f * (2 - f)

    lat_rad = math.radians(lat_sta)
    lon_rad = math.radians(lon_sta)

    N = a / math.sqrt(1 - e2 * math.sin(lat_rad)**2)
    x_sta = (N + h_sta) * math.cos(lat_rad) * math.cos(lon_rad)
    y_sta = (N + h_sta) * math.cos(lat_rad) * math.sin(lon_rad)
    z_sta = (N * (1 - e2) + h_sta) * math.sin(lat_rad)

    dx = x_sat - x_sta
    dy = y_sat - y_sta
    dz = z_sat - z_sta

    sin_lat = math.sin(lat_rad)
    cos_lat = math.cos(lat_rad)
    sin_lon = math.sin(lon_rad)
    cos_lon = math.cos(lon_rad)

    east  = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up    =  cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz

    distance = math.sqrt(east**2 + north**2 + up**2)
    azimuth_rad = math.atan2(east, north)
    elevation_rad = math.asin(up / distance)

    azimuth_deg = math.degrees(azimuth_rad)
    elevation_deg = math.degrees(elevation_rad)

    if azimuth_deg < 0:
        azimuth_deg += 360

    return azimuth_deg, elevation_deg, distance