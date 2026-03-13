import math

# Sabitler (calc_brd.m dosyasındaki ile aynı)
MU = 3.986005e14           # m^3/s^2
WE = 7.2921151467e-5       # rad/s

def calculate_satpos_from_kepler(nav, tk):
    """
    Hocanın calc_brd.m (IS-GPS-200) algoritmasının birebir çevirisidir.
    16 parametre kullanarak harmonik yörünge perturbasyonlarını (sapmaları) düzeltir.
    tk: Referans zamandan (genellikle TOE) olan zaman farkı (saniye)
    """
    if not nav or "e" not in nav:
        return [0.0, 0.0, 0.0]

    A = nav['A']
    e = nav['e']
    M0 = nav['M0']
    
    # 1. Düzeltilmiş Ortalama Hareket (Corrected Mean Motion)
    n0 = math.sqrt(MU / (A**3))
    nm = n0 + nav['delta_n']
    
    # 2. Düzeltilmiş Ortalama Anomali
    Mk = M0 + nm * tk
    
    # 3. İterasyonla Eksantrik Anomali (Ek)
    E0 = Mk
    ni = 0
    while True:
        ni += 1
        Ek = Mk + e * math.sin(E0)
        dE = abs(Ek - E0)
        if dE < 1e-15 or ni > 15:
            break
        E0 = Ek
        
    # 4. Gerçek Anomali (True Anomaly - vk)
    vk = math.atan2((math.sqrt(1 - e**2) * math.sin(Ek)), (math.cos(Ek) - e))
    
    # 5. Enlem Argümanı (Argument of Latitude - fk)
    fk = vk + nav['omega']
    
    # 6. Harmonik Düzeltme Terimleri (IS-GPS-200 Perturbations)
    sin2f = math.sin(2 * fk)
    cos2f = math.cos(2 * fk)
    
    du = nav['cus'] * sin2f + nav['cuc'] * cos2f
    dr = nav['crs'] * sin2f + nav['crc'] * cos2f
    di = nav['cis'] * sin2f + nav['cic'] * cos2f
    
    # Düzeltilmiş Değerler
    uk = fk + du
    rk = A * (1 - e * math.cos(Ek)) + dr
    ik = nav['i0'] + di + (nav['idot'] * tk)
    
    # Yörünge Düzlemindeki Koordinatlar
    xkp = rk * math.cos(uk)
    ykp = rk * math.sin(uk)
    
    # 7. Çıkış Düğümü Boylamı (Longitude of Ascending Node)
    omega0 = nav['omega0']
    omgd = nav['omega_dot']
    toe = nav['toe']
    
    # omg = omg0 + (omgd - we)*tk - (we*toe);
    omg = omega0 + (omgd - WE) * tk - (WE * toe)
    
    # 8. ECEF (Dünya Merkezli Sabit) X, Y, Z Koordinatları
    X = xkp * math.cos(omg) - ykp * math.cos(ik) * math.sin(omg)
    Y = xkp * math.sin(omg) + ykp * math.cos(ik) * math.cos(omg)
    Z = ykp * math.sin(ik)
    
    return [X, Y, Z]