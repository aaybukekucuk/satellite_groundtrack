import os
from datetime import datetime

def read_nav_kepler(filepath):
    """
    RINEX 3 NAV dosyasından uyduların gün içindeki tüm ephemeris 
    (yörünge parametre) setlerini okur ve listeler halinde kaydeder.
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
            
        # Sadece GPS(G) ve Galileo(E) verilerini okuyoruz
        if line.startswith("G") or line.startswith("E"): 
            sat_id = line[0:3].strip()
            
            try:
                # Başlangıç Tarihini (TOC) Pars Etme
                parts = line[3:23].split()
                year = int(parts[0])
                year = year + 2000 if year < 100 else year
                month, day, hour, minute = map(int, parts[1:5])
                sec = float(parts[5])
                toc_dt = datetime(year, month, day, hour, minute, int(sec))
                
                # Diğer 7 satırdaki parametreleri çekiyoruz
                l1 = lines[idx+1].ljust(80)
                l2 = lines[idx+2].ljust(80)
                l3 = lines[idx+3].ljust(80)
                l4 = lines[idx+4].ljust(80)
                l5 = lines[idx+5].ljust(80)
                
                crs       = float(l1[23:42].replace('D', 'E').strip())
                delta_n   = float(l1[42:61].replace('D', 'E').strip())
                m0        = float(l1[61:80].replace('D', 'E').strip())
                
                cuc       = float(l2[4:23].replace('D', 'E').strip())
                e         = float(l2[23:42].replace('D', 'E').strip())
                cus       = float(l2[42:61].replace('D', 'E').strip())
                sqrt_a    = float(l2[61:80].replace('D', 'E').strip())
                
                toe       = float(l3[4:23].replace('D', 'E').strip())
                cic       = float(l3[23:42].replace('D', 'E').strip())
                omega0    = float(l3[42:61].replace('D', 'E').strip())
                cis       = float(l3[61:80].replace('D', 'E').strip())
                
                i0        = float(l4[4:23].replace('D', 'E').strip())
                crc       = float(l4[23:42].replace('D', 'E').strip())
                omega     = float(l4[42:61].replace('D', 'E').strip())
                omega_dot = float(l4[61:80].replace('D', 'E').strip())
                
                idot      = float(l5[4:23].replace('D', 'E').strip())
                
                A = sqrt_a ** 2
                
                ephemeris = {
                    "toc_dt": toc_dt,
                    "crs": crs, "delta_n": delta_n, "M0": m0,
                    "cuc": cuc, "e": e, "cus": cus, "A": A,
                    "toe": toe, "cic": cic, "omega0": omega0, "cis": cis,
                    "i0": i0, "crc": crc, "omega": omega, "omega_dot": omega_dot,
                    "idot": idot,
                    
                    # UI Paneldeki kartlar için eski yapı
                    "A (Yarı Büyük Eksen) [m]": A,
                    "e (Dışmerkezlik)": e,
                    "i0 (Yörünge Eğikliği)": i0
                }
                
                if sat_id not in kepler_data:
                    kepler_data[sat_id] = []
                    
                # Uydunun gün içindeki tüm ephemeris setlerini listeye ekle
                kepler_data[sat_id].append(ephemeris)
                
            except Exception as ex:
                pass 
            
            idx += 8 
        else:
            idx += 1
            
    return kepler_data