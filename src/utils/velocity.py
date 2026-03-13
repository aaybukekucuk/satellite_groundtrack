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


def calculate_sp3_velocity_from_positions(dense_coords):
    """
    1 dakikalık sıklaştırılmış SP3 konum verilerinden (X, Y, Z - metre) 
    sayısal türev (Merkezi Farklar yöntemi) ile Hız (Vx, Vy, Vz - m/s) vektörlerini hesaplar.
    """
    velocities = []
    n = len(dense_coords)
    
    if n < 3:
        return velocities # Türev için en az 3 nokta lazım
        
    for i in range(n):
        # Sınır koşulları: İlk noktada İleri Fark (Forward Difference)
        if i == 0:
            dt = (dense_coords[1]['time'] - dense_coords[0]['time']).total_seconds()
            vx = (dense_coords[1]['x'] - dense_coords[0]['x']) / dt
            vy = (dense_coords[1]['y'] - dense_coords[0]['y']) / dt
            vz = (dense_coords[1]['z'] - dense_coords[0]['z']) / dt
            
        # Sınır koşulları: Son noktada Geri Fark (Backward Difference)
        elif i == n - 1:
            dt = (dense_coords[i]['time'] - dense_coords[i-1]['time']).total_seconds()
            vx = (dense_coords[i]['x'] - dense_coords[i-1]['x']) / dt
            vy = (dense_coords[i]['y'] - dense_coords[i-1]['y']) / dt
            vz = (dense_coords[i]['z'] - dense_coords[i-1]['z']) / dt
            
        # Ara noktalar: Merkezi Fark (Central Difference) -> En hassas yöntem
        else:
            dt = (dense_coords[i+1]['time'] - dense_coords[i-1]['time']).total_seconds()
            vx = (dense_coords[i+1]['x'] - dense_coords[i-1]['x']) / dt
            vy = (dense_coords[i+1]['y'] - dense_coords[i-1]['y']) / dt
            vz = (dense_coords[i+1]['z'] - dense_coords[i-1]['z']) / dt
            
        velocities.append({
            'time': dense_coords[i]['time'],
            'vx': vx,
            'vy': vy,
            'vz': vz
        })
        
    return velocities