import os

def read_nav_kepler(filepath):
    """
    RINEX 3 NAV dosyasından Kepler parametrelerini okur.
    Uluslararası 19 karakterlik blok standardına tam uyumludur.
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
            
        # RINEX 3 GPS uyduları
        if line.startswith("G"): 
            sat_id = line[0:3].strip()
            
            try:
                # Satırları garanti olması için 80 karaktere tamamlıyoruz
                l1 = lines[idx+1].ljust(80)
                l2 = lines[idx+2].ljust(80)
                l3 = lines[idx+3].ljust(80)
                l4 = lines[idx+4].ljust(80)
                
                # Doğru RINEX Sütun İndeksleri: (4:23), (23:42), (42:61), (61:80)
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
                # Eğer veri gerçekten bozuksa atla, terminali kirletme
                pass 
            
            idx += 8 
        else:
            idx += 1
            
    return kepler_data