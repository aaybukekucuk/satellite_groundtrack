import numpy as np
import math

def calculate_kepler_from_state(r_vec, v_vec):
    """Konum ve Hızdan güvenli Kepler dönüşümü"""
    r = np.array(r_vec, dtype=float)
    v = np.array(v_vec, dtype=float)
    mu = 3.986004418e14  # m^3/s^2
    
    r_norm = np.linalg.norm(r)
    v_norm = np.linalg.norm(v)
    
    c_vec = np.cross(r, v)
    c_norm = np.linalg.norm(c_vec)
    
    # a (Yarı Büyük Eksen)
    a = 1.0 / (2.0 / r_norm - (v_norm**2) / mu)
    
    # e (Dışmerkezlik) - Eksi kök hatasını önlemek için max(0) eklendi
    p = (c_norm**2) / mu
    e_sq = 1.0 - p / a
    e = math.sqrt(max(0.0, e_sq))
    
    # i (Yörünge Eğikliği) - Acos çökmesini önlemek için Clamping
    cos_i = c_vec[2] / c_norm
    cos_i = max(-1.0, min(1.0, cos_i)) 
    i = math.acos(cos_i)
    
    Omega = math.atan2(c_vec[0], -c_vec[1])
    
    e_vec = (np.cross(v, c_vec) / mu) - (r / r_norm)
    e_norm = np.linalg.norm(e_vec)
    
    if e_norm > 1e-12:
        cos_V = np.dot(e_vec, r) / (e_norm * r_norm)
        cos_V = max(-1.0, min(1.0, cos_V))
        V = math.acos(cos_V)
        if np.dot(r, v) < 0:
            V = 2 * math.pi - V
            
        n_vec = np.array([-c_vec[1], c_vec[0], 0])
        n_norm = np.linalg.norm(n_vec)
        if n_norm > 1e-12:
            cos_omega = np.dot(n_vec, e_vec) / (n_norm * e_norm)
            cos_omega = max(-1.0, min(1.0, cos_omega))
            omega = math.acos(cos_omega)
            if e_vec[2] < 0:
                omega = 2 * math.pi - omega
        else:
            omega = 0.0
    else:
        V = 0.0
        omega = 0.0
        
    val = (1 - e) / (1 + e)
    tan_E_half = math.sqrt(max(0.0, val)) * math.tan(V / 2.0)
    E = 2.0 * math.atan(tan_E_half)
    
    M = E - e * math.sin(E)
    
    return {
        "A (Yarı Büyük Eksen) [m]": a,
        "e (Dışmerkezlik)": e,
        "i0 (Yörünge Eğikliği)": i,
        "Omega0 (Çıkış Düğ. Boylamı)": Omega,
        "omega (Yerberi Argümanı)": omega,
        "M0 (Ortalama Anomali)": M
    }