import os

def read_nav_kepler(filepath):
    """
    RINEX 3 NAV dosyasından Multi-GNSS (GPS ve GALILEO) Kepler parametrelerini okur.
    GLONASS (R) uyduları Kepler yerine XYZ yayınladığı için bu aşamada atlanır.
    """
    kepler_data = {}
    
    if not os.path.exists(filepath):
        print(f"⚠️ HATA: NAV dosyası bulunamadı -> {filepath}")
        return kepler_data

    with open(filepath, "r") as file:
        lines = file.readlines()
        
    in_header = True
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        
        if in_header:
            if "END OF HEADER" in line:
                in_header = False
            idx += 1
            continue
            
        # YENİ: Hem GPS (G) hem de Galileo (E) uydularını kabul et
        if line.startswith("G") or line.startswith("E"): 
            sat_id = line[0:3].strip()
            
            try:
                l1 = lines[idx+1].ljust(80)
                l2 = lines[idx+2].ljust(80)
                l3 = lines[idx+3].ljust(80)
                l4 = lines[idx+4].ljust(80)
                
                m0 = float(l1[61:80].replace('D', 'E').strip())
                e = float(l2[23:42].replace('D', 'E').strip())
                sqrt_a = float(l2[61:80].replace('D', 'E').strip())
                omega0 = float(l3[42:61].replace('D', 'E').strip())
                i0 = float(l4[4:23].replace('D', 'E').strip())
                omega = float(l4[42:61].replace('D', 'E').strip())
                
                if sat_id not in kepler_data:
                    kepler_data[sat_id] = {
                        "M0 (Ort. Anomali)": m0, 
                        "e (Dışmerkezlik)": e, 
                        "A (Yarı Büyük Eksen) [m]": (sqrt_a ** 2),
                        "Omega0 (Çıkış Düğ. Boylamı)": omega0, 
                        "i0 (Yörünge Eğikliği)": i0, 
                        "omega (Yerberi Argümanı)": omega
                    }
            except Exception as e:
                pass 
            
            idx += 8 
        else:
            idx += 1
            
    return kepler_data