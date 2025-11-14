def read_sp3(sp3_path):
    data = []
    with open(sp3_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        if line.startswith('*'):
            current_time = line[3:].strip()
        elif line.startswith('P'):
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
                "time": current_time
            })

    return data