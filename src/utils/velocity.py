import math

def calculate_orbital_velocity(x, y, z, a_meters):
    """ECEF koordinatları ve Yarı Büyük Eksen (A) ile anlık yörünge hızını (km/s) hesaplar."""
    mu = 3.986004418e14  # Dünya'nın yerçekimi sabiti (m^3/s^2)
    
    # Uydunun Dünya merkezine uzaklığı (r)
    r = math.sqrt(x**2 + y**2 + z**2)
    
    if a_meters <= 0 or r <= 0:
        return 0.0
        
    # Vis-Viva Denklemi (Sonuç saniyede metre çıkar)
    v_mps = math.sqrt(mu * ((2.0 / r) - (1.0 / a_meters)))
    
    # km/s cinsine çevir (MEO GPS uyduları için genelde ~3.8 - 3.9 km/s çıkar)
    return v_mps / 1000.0