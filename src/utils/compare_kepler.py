import math
import numpy as np
from .state_to_kepler import calculate_kepler_from_state

# Dünya'nın açısal dönüş hızı ve Kütleçekim Sabiti
OMEGA_E = 7.2921151467e-5 
MU = 3.986004418e14

def rotate_z(vec, angle):
    """ Vektörü Z ekseni etrafında Dünya'nın dönüşü kadar döndürür. """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return np.array([
        vec[0]*cos_a - vec[1]*sin_a,
        vec[0]*sin_a + vec[1]*cos_a,
        vec[2]
    ])

def gibbs_method(r1, r2, r3, mu):
    """ GIBBS YÖNTEMİ: Zaman türevi olmadan, 3 Konum Vektöründen Kesin Hız Bulur """
    r1_mag = np.linalg.norm(r1)
    r2_mag = np.linalg.norm(r2)
    r3_mag = np.linalg.norm(r3)

    # Vektörel çapraz çarpımlar (Yörünge düzlemi hesabı)
    c12 = np.cross(r1, r2)
    c23 = np.cross(r2, r3)
    c31 = np.cross(r3, r1)

    D = c12 + c23 + c31
    N = r3_mag * c12 + r1_mag * c23 + r2_mag * c31
    S = (r2_mag - r3_mag)*r1 + (r3_mag - r1_mag)*r2 + (r1_mag - r2_mag)*r3

    D_mag = np.linalg.norm(D)
    N_mag = np.linalg.norm(N)

    if D_mag == 0 or N_mag == 0:
        return np.array([0.0, 0.0, 0.0])

    B = np.cross(D, r2) / r2_mag
    L = math.sqrt(mu / (N_mag * D_mag))
    
    # Tam r2 anındaki kusursuz ECI hız vektörü
    v2 = L * (B + S)
    return v2

def analyze_kepler_errors(sp3_coords, brdc_kepler):
    error_series = []
    
    if not brdc_kepler or "A (Yarı Büyük Eksen) [m]" not in brdc_kepler:
        return error_series
        
    brdc_a = brdc_kepler.get("A (Yarı Büyük Eksen) [m]", 0)
    brdc_e = brdc_kepler.get("e (Dışmerkezlik)", 0)
    brdc_i = brdc_kepler.get("i0 (Yörünge Eğikliği)", 0)

    # Gibbs için 3 nokta yeterli (Geçmiş, Şimdi, Gelecek)
    for idx in range(1, len(sp3_coords) - 1):
        p1 = sp3_coords[idx-1]
        p2 = sp3_coords[idx]
        p3 = sp3_coords[idx+1]
        
        dt1 = (p2["time"] - p1["time"]).total_seconds()
        dt3 = (p3["time"] - p2["time"]).total_seconds()
        
        if dt1 <= 0 or dt3 <= 0:
            continue
            
        # 1. ECEF Konumları (Metre)
        r1_ecef = np.array([p1["x"]*1000.0, p1["y"]*1000.0, p1["z"]*1000.0])
        r2_ecef = np.array([p2["x"]*1000.0, p2["y"]*1000.0, p2["z"]*1000.0])
        r3_ecef = np.array([p3["x"]*1000.0, p3["y"]*1000.0, p3["z"]*1000.0])
        
        # 2. ECEF'ten ECI'ye (Sabit Uzay) Dönüşüm
        # Merkez nokta (p2) referans alınarak Dünya'nın 15 dakikalık dönüşü ileri/geri sarılır
        r1_eci = rotate_z(r1_ecef, OMEGA_E * dt1)
        r2_eci = r2_ecef  # Referans anı
        r3_eci = rotate_z(r3_ecef, -OMEGA_E * dt3)
        
        try:
            # 3. GIBBS İLE KUSURSUZ FİZİKSEL HIZ
            v2_eci = gibbs_method(r1_eci, r2_eci, r3_eci, MU)
            
            # 4. Hız ve Konumu kitaptaki formüle yolla
            sp3_kep = calculate_kepler_from_state(r2_eci, v2_eci)
            
            # Milyonluk farkların yok oluşunu izle
            delta_a = sp3_kep["A (Yarı Büyük Eksen) [m]"] - brdc_a
            delta_e = sp3_kep["e (Dışmerkezlik)"] - brdc_e
            delta_i = math.degrees(sp3_kep["i0 (Yörünge Eğikliği)"] - brdc_i)
            
            error_series.append({
                "time": p2["time"].isoformat(),
                "delta_A_meters": round(delta_a, 3),
                "delta_E": round(delta_e, 9),
                "delta_I_deg": round(delta_i, 6)
            })
            
        except Exception as e:
            pass
            
    return error_series