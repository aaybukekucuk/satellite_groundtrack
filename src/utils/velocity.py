"""
velocity.py
===========
SP3 konum serisinden sayısal türev ile hız vektörü hesabı.

KRİTİK BİRİM NOTU:
  read_sp3.py koordinatları KİLOMETRE [km] cinsinden döndürür.
  api.py'de pozisyon için coords[i]['x'] * 1000 yapılıyor (km→m).
  Hız için de aynı dönüşüm şart:
      dx [km] / dt [s] = vx [km/s]  →  × 1000  →  vx [m/s]

  Önceki kodda "SP3 zaten metre" yorumu YANLIŞ'tı.
  Bu hata hız vektörünü 1000x küçültüyordu.
  RTN dönüşümünde Q × Q̇ cross product'ı bozuluyordu,
  E3 (normal) yanlış hesaplanıyor, tüm RTN çerçevesi çöküyordu.
  Sonuç: Radyal grafik ~-26.5 milyar metre gösteriyordu (GPS orbit yarıçapı).
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

    Giriş  : coords[i] = {'x': km, 'y': km, 'z': km, 'time': datetime}
                          ^^^ SP3 KİLOMETRE cinsinden döndürür
    Çıkış  : [{'time', 'vx', 'vy', 'vz'}]  ---  m/s

    DÜZELTİLEN HATA:
      dx [km] / dt [s] = km/s  --x1000-->  m/s
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
            # Merkezi Fark --- O(h2) hassasiyet
            dt = (coords[i+1]['time'] - coords[i-1]['time']).total_seconds()
            dx = coords[i+1]['x'] - coords[i-1]['x']
            dy = coords[i+1]['y'] - coords[i-1]['y']
            dz = coords[i+1]['z'] - coords[i-1]['z']

        if dt == 0:
            velocities.append({'time': coords[i]['time'],
                                'vx': 0.0, 'vy': 0.0, 'vz': 0.0})
            continue

        # SP3 km cinsinden: dx/dt = km/s --> x1000 --> m/s
        velocities.append({
            'time': coords[i]['time'],
            'vx': dx / dt * 1000.0,
            'vy': dy / dt * 1000.0,
            'vz': dz / dt * 1000.0
        })

    return velocities