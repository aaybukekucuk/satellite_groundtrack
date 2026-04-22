from datetime import datetime

def read_sp3(sp3_path):
    data = []
    current_time = None
    
    with open(sp3_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith('*'):
            # Örnek satır: * 2024  6  1  0  0  0.00000000
            parts = line[1:].split()
            year, month, day, hour, minute = map(int, parts[0:5])
            second = float(parts[5])
            
            sec_int = int(second)
            microsec = int((second - sec_int) * 1e6)
            
            # Zamanı matematiksel bir objeye çeviriyoruz
            current_time = datetime(year, month, day, hour, minute, sec_int, microsec)
            
        elif line.startswith('P') and current_time is not None:
            sat_id = line[1:4].strip()
            x = float(line[4:18]) * 1000  # km -> m
            y = float(line[18:32]) * 1000
            z = float(line[32:46]) * 1000
            clock = float(line[46:60])
            data.append({
                "id": sat_id,
                "x": x,
                "y": y,
                "z": z,
                "clock": clock,
                "time": current_time  # Artık zaman bilgisini de sözlüğe ekledik
            })

    return data