"""
velocity.py
===========
SP3 konum serisinden sayısal türev ile hız vektörü hesabı.

KRİTİK BİRİM NOTU:
  read_sp3.py satır 17: x = float(...) * 1000  # km → m
  Yani coords[i]['x'] ZATEN METRE cinsinden gelir.
  
  Doğru türev: dx [m] / dt [s] = vx [m/s]  — çarpan gerekmez.
  
  YANLIŞ (eski kod): dx / dt * 1000  → m/s zannedip tekrar ×1000 → 1000× fazla hız
  DOĞRU  (bu kod)  : dx / dt         → m/s (çarpan yok)
"""

import math


def calculate_orbital_velocity(x, y, z, a_meters):
    """
    Vis-Viva denklemiyle anlık yörünge hızı.
    x, y, z : ECEF [m] | a_meters : yarı-büyük eksen [m]
    Dönüş   : skaler hız [km/s]
    """
    MU = 3.986004418e14
    r = math.sqrt(x**2 + y**2 + z**2)
    if a_meters <= 0 or r <= 0:
        return 0.0
    return math.sqrt(MU * (2.0 / r - 1.0 / a_meters)) / 1000.0


def calculate_sp3_velocity_from_positions(coords):
    """
    SP3 konum serisinden Merkezi Fark yöntemiyle hız vektörü.

    Giriş  : coords[i] = {'x': m, 'y': m, 'z': m, 'time': datetime}
              (read_sp3.py km→m dönüşümü zaten yapar)
    Çıkış  : [{'time', 'vx', 'vy', 'vz'}]  →  m/s
    """
    velocities = []
    n = len(coords)
    if n < 3:
        return velocities

    for i in range(n):
        if i == 0:
            dt = (coords[1]['time'] - coords[0]['time']).total_seconds()
            dx = coords[1]['x'] - coords[0]['x']
            dy = coords[1]['y'] - coords[0]['y']
            dz = coords[1]['z'] - coords[0]['z']
        elif i == n - 1:
            dt = (coords[i]['time'] - coords[i-1]['time']).total_seconds()
            dx = coords[i]['x'] - coords[i-1]['x']
            dy = coords[i]['y'] - coords[i-1]['y']
            dz = coords[i]['z'] - coords[i-1]['z']
        else:
            # Merkezi Fark — O(h²) hassasiyet
            dt = (coords[i+1]['time'] - coords[i-1]['time']).total_seconds()
            dx = coords[i+1]['x'] - coords[i-1]['x']
            dy = coords[i+1]['y'] - coords[i-1]['y']
            dz = coords[i+1]['z'] - coords[i-1]['z']

        if dt == 0:
            velocities.append({'time': coords[i]['time'],
                                'vx': 0.0, 'vy': 0.0, 'vz': 0.0})
            continue

        # coords zaten metre → dx[m]/dt[s] = m/s  (×1000 YAPILMAZ)
        velocities.append({
            'time': coords[i]['time'],
            'vx': dx / dt,   # m/s
            'vy': dy / dt,   # m/s
            'vz': dz / dt    # m/s
        })

    return velocities