import math

# WGS84 elipsoidi parametreleri
a = 6378137.0  # yarıçap (m)
f = 1 / 298.257223563
e2 = f * (2 - f)

def ecef_to_geodetic(x, y, z):
    """ECEF (X,Y,Z) -> enlem (lat), boylam (lon), yükseklik (h) dönüşümü"""
    lon = math.atan2(y, x)
    r = math.sqrt(x ** 2 + y ** 2)
    lat = math.atan2(z, r * (1 - e2))
    lat_prev = 0
    while abs(lat - lat_prev) > 1e-12:
        lat_prev = lat
        N = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
        h = r / math.cos(lat) - N
        lat = math.atan2(z, r * (1 - e2 * (N / (N + h))))
    h = r / math.cos(lat) - N
    lat_deg = math.degrees(lat)
    lon_deg = math.degrees(lon)

    # 🔹 Boylamı -180° ile 180° arasına normalleştir
    if lon_deg > 180:
        lon_deg -= 360
    elif lon_deg < -180:
        lon_deg += 360

    return lat_deg, lon_deg, h