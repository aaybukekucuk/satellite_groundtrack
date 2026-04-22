import numpy as np
import math

def datetime_to_mjd(dt):
    """ Python Datetime nesnesini Modified Julian Date (MJD) formatına çevirir """
    y, m = dt.year, dt.month
    d = dt.day + dt.hour / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
    
    if m <= 2:
        y -= 1
        m += 12
        
    A = math.floor(y / 100)
    B = 2 - A + math.floor(A / 4)
    
    JD = math.floor(365.25 * (y + 4716)) + math.floor(30.6001 * (m + 1)) + d + B - 1524.5
    MJD = JD - 2400000.5
    return MJD

def rotation(position, angle_deg, axis):
    """ Eksen etrafında 3D rotasyon matrisi uygular """
    angle_rad = np.radians(angle_deg)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    if axis == 1:
        rot = np.array([[1, 0, 0], [0, cos_a, sin_a], [0, -sin_a, cos_a]])
    elif axis == 2:
        rot = np.array([[cos_a, 0, -sin_a], [0, 1, 0], [sin_a, 0, cos_a]])
    elif axis == 3:
        rot = np.array([[cos_a, sin_a, 0], [-sin_a, cos_a, 0], [0, 0, 1]])
    else:
        raise ValueError("Axis must be 1, 2, or 3")
        
    pos_vec = np.array(position).reshape(3, 1)
    xout = rot @ pos_vec
    return xout.flatten()

def calc_sunpos(mjd):
    """
    Belirli bir MJD zamanında Güneş'in ECEF koordinatlarını (metre) hesaplar.
    MATLAB 'calc_sunpos.m' dosyasının Python karşılığıdır.
    """
    AU = 149597870700  # Astronomik Birim (Metre)
    
    fday = mjd - np.floor(mjd)
    JDN = mjd - 15019.5
    
    v1 = (279.696678 + 0.9856473354 * JDN) % 360
    gstr = (279.690983 + 0.9856473354 * JDN + 360 * fday + 180) % 360
    g = np.radians((358.475845 + 0.9856002670 * JDN) % 360)
    
    slong = v1 + (1.91946 - 0.004789 * JDN / 36525) * np.sin(g) + 0.020094 * np.sin(2 * g)
    obliq = np.radians(23.45229 - 0.0130125 * JDN / 36525)
    
    slp = np.radians(slong - 0.005686)
    snd = np.sin(obliq) * np.sin(slp)
    csd = np.sqrt(1 - snd**2)
    
    sdec = np.degrees(np.arctan2(snd, csd))
    sra = 180 - np.degrees(np.arctan2((snd / csd / np.tan(obliq)), (-np.cos(slp) / csd)))
    
    s_pos = np.array([
        np.cos(np.radians(sdec)) * np.cos(np.radians(sra)) * AU,
        np.cos(np.radians(sdec)) * np.sin(np.radians(sra)) * AU,
        np.sin(np.radians(sdec)) * AU
    ])
    
    s_pos_ecef = rotation(s_pos, gstr, 3)
    return s_pos_ecef

def calc_satapc(spos, sunpos, neu_l1, neu_l2):
    """
    Uydunun Kütle Merkezi (CoM) ile Anten Faz Merkezi (APC) arasındaki farkı vektörel hesaplar.
    MATLAB 'calc_satapc.m' dosyasının Python karşılığıdır.
    """
    # GPS L1 ve L2 Frekansları (Hz)
    f1 = 1575.42e6
    f2 = 1227.60e6
    
    a1 = (f1**2) / (f1**2 - f2**2)
    a2 = -(f2**2) / (f1**2 - f2**2)

    # L1 ve L2 İyonosfer-Free kombinasyonu (Milimetre -> Metre geçişi için sonda bölme var)
    de_if = a1 * np.array(neu_l1) + a2 * np.array(neu_l2)

    spos = np.array(spos)
    sunpos = np.array(sunpos)

    # Uydu Sabit Referans Sistemi
    k = -spos / np.linalg.norm(spos)
    rs = sunpos - spos
    e = rs / np.linalg.norm(rs)
    j = np.cross(k, e)
    j = j / np.linalg.norm(j)
    i = np.cross(j, k)
    
    sf = np.vstack((i, j, k))
    
    # ECEF sistemindeki Offset (Metre cinsinden)
    sapc = np.linalg.solve(sf, de_if) / 1000.0
    return sapc

def read_antex_gps(fname):
    """ IGS .atx dosyasını okur ve GPS uydularının anten kalibrasyon değerlerini döner """
    sat_offsets = {}
    try:
        with open(fname, 'r') as f:
            lines = f.readlines()
            
        i = 0
        while i < len(lines):
            line = lines[i]
            if "START OF ANTENNA" in line:
                i += 1
                type_line = lines[i]
                if "TYPE / SERIAL NO" in type_line and type_line[20] == 'G':
                    prn = int(type_line[21:24].strip())
                    neu_l1, neu_l2 = None, None
                    
                    while "END OF ANTENNA" not in lines[i]:
                        i += 1
                        freq_line = lines[i]
                        if "START OF FREQUENCY" in freq_line and "G01" in freq_line:
                            i += 1
                            if "NORTH / EAST / UP" in lines[i]:
                                neu_l1 = [float(x) for x in lines[i].split()[:3]]
                        elif "START OF FREQUENCY" in freq_line and "G02" in freq_line:
                            i += 1
                            if "NORTH / EAST / UP" in lines[i]:
                                neu_l2 = [float(x) for x in lines[i].split()[:3]]
                                
                    sat_offsets[prn] = {'L1': neu_l1, 'L2': neu_l2}
            i += 1
        return sat_offsets
    except Exception as e:
        print(f"ANTEX Okuma Hatası: {e}")
        return None