"""
satpos_utils.py
===============
IS-GPS-200 broadcast efemerisinden ECEF konum ve HIZ hesabı.

DÜZELTİLEN/EKLENEN:
  1. calculate_satvel_from_kepler() — broadcast hız vektörü (analitik türev)
     Hocanın istediği: "Broadcast'ten Q_dot (hız vektörü) hesaplanmalı"
  2. Sqrt(A) güvenlik kontrolü — RINEX nav. formatında 'sqrtA' saklanır;
     eğer read_nav 'A'yı kareköksüz vermişse burada yakalanır.
  3. Birim doğrulama — A < 1e6 ise sqrt(A) verilmiş demektir, otomatik düzeltilir.
"""

import math

MU = 3.986005e14       # Dünya çekim parametresi [m³/s²]
WE = 7.2921151467e-5   # Dünya dönüş hızı [rad/s]


def _compute_eccentric_anomaly(Mk, e, tol=1e-15, max_iter=15):
    """Newton-Raphson ile eksantrik anomali (Ek) hesabı."""
    E = Mk
    for _ in range(max_iter):
        dE = (Mk - E + e * math.sin(E)) / (1.0 - e * math.cos(E))
        E += dE
        if abs(dE) < tol:
            break
    return E


def _intermediate(nav, tk):
    """
    IS-GPS-200 ara değişkenleri: (uk, rk, ik, omg, xkp, ykp, dEk_dt)
    Hem pozisyon hem hız hesabı için ortak çekirdek.
    """
    # ── Güvenlik: sqrt(A) mı, A mı? ──────────────────────────────────────
    A = nav['A']
    if A < 1.0e6:
        # 5153 gibi bir değer geldi → sqrt(A) gelmiş, kareye al
        # Gerçek yarı-büyük eksen ≈ 26 560 km → A > 2.5e7 m
        A = A ** 2

    e   = nav['e']
    M0  = nav['M0']
    toe = nav['toe']

    # 1. Ortalama hareket
    n0 = math.sqrt(MU / A**3)
    nm = n0 + nav['delta_n']

    # 2. Ortalama anomali
    Mk = M0 + nm * tk

    # 3. Eksantrik anomali (Newton-Raphson)
    Ek = _compute_eccentric_anomaly(Mk, e)

    # 4. Gerçek anomali
    sin_vk = math.sqrt(1 - e**2) * math.sin(Ek) / (1 - e * math.cos(Ek))
    cos_vk = (math.cos(Ek) - e)                  / (1 - e * math.cos(Ek))
    vk     = math.atan2(sin_vk, cos_vk)

    # 5. Enlem argümanı
    fk = vk + nav['omega']

    sin2f = math.sin(2 * fk)
    cos2f = math.cos(2 * fk)

    # 6. Harmonik pertürbasyon düzeltmeleri
    du = nav['cus'] * sin2f + nav['cuc'] * cos2f
    dr = nav['crs'] * sin2f + nav['crc'] * cos2f
    di = nav['cis'] * sin2f + nav['cic'] * cos2f

    uk  = fk + du
    rk  = A * (1 - e * math.cos(Ek)) + dr
    ik  = nav['i0'] + di + nav['idot'] * tk

    xkp = rk * math.cos(uk)
    ykp = rk * math.sin(uk)

    # 7. Çıkış düğümü boylamı
    omg = nav['omega0'] + (nav['omega_dot'] - WE) * tk - WE * toe

    # 8. Hız hesabı için türevler
    dEk_dt = nm / (1 - e * math.cos(Ek))

    return A, e, Ek, vk, uk, rk, ik, omg, xkp, ykp, dEk_dt, sin2f, cos2f, nm


def calculate_satpos_from_kepler(nav, tk):
    """
    Broadcast efemerisinden IS-GPS-200 algoritmasıyla ECEF konum.

    Dönüş: [X, Y, Z] — metre cinsinden
    """
    if not nav or 'e' not in nav:
        return [0.0, 0.0, 0.0]

    try:
        _, _, _, _, _, _, ik, omg, xkp, ykp, _, _, _, _ = _intermediate(nav, tk)

        X = xkp * math.cos(omg) - ykp * math.cos(ik) * math.sin(omg)
        Y = xkp * math.sin(omg) + ykp * math.cos(ik) * math.cos(omg)
        Z = ykp * math.sin(ik)

        return [X, Y, Z]

    except Exception:
        return [0.0, 0.0, 0.0]


def calculate_satvel_from_kepler(nav, tk):
    """
    Broadcast efemerisinden IS-GPS-200 analitik türev ile ECEF hız vektörü.
    Hocanın istediği: "Broadcast'ten Q_dot hesaplanmalı."

    Dönüş: [Vx, Vy, Vz] — m/s cinsinden

    Analitik türev adımları (IS-GPS-200 §20.3.3.4.3):
      dEk/dt  = nm / (1 - e·cos(Ek))
      dvk/dt  = sin(Ek)·dEk/dt·√(1-e²) / (1 - e·cos(Ek))  [zincir kuralı]
      drk/dt  = A·e·sin(Ek)·dEk/dt + dCrs/dt
      duk/dt  = dvk/dt + harmonik türev
      dik/dt  = idot + harmonik türev
      domg/dt = omega_dot - WE
    """
    if not nav or 'e' not in nav:
        return [0.0, 0.0, 0.0]

    try:
        A, e, Ek, vk, uk, rk, ik, omg, xkp, ykp, dEk_dt, sin2f, cos2f, nm = _intermediate(nav, tk)

        fk   = vk + nav['omega']
        dfk_dt = dEk_dt * math.sqrt(1 - e**2) / (1 - e * math.cos(Ek))

        # Pertürbasyon türevleri
        d_sin2f_dt = 2 * math.cos(2 * fk) * dfk_dt
        d_cos2f_dt = -2 * math.sin(2 * fk) * dfk_dt

        du_dt = dfk_dt + nav['cus'] * d_sin2f_dt + nav['cuc'] * d_cos2f_dt
        dr_dt = A * e * math.sin(Ek) * dEk_dt \
                + nav['crs'] * d_sin2f_dt + nav['crc'] * d_cos2f_dt
        di_dt = nav['idot'] + nav['cis'] * d_sin2f_dt + nav['cic'] * d_cos2f_dt

        # Yörünge düzlemi hız
        dxkp_dt = dr_dt * math.cos(uk) - rk * math.sin(uk) * du_dt
        dykp_dt = dr_dt * math.sin(uk) + rk * math.cos(uk) * du_dt

        # Çıkış düğümü türevi
        domg_dt = nav['omega_dot'] - WE

        sin_omg = math.sin(omg)
        cos_omg = math.cos(omg)
        sin_ik  = math.sin(ik)
        cos_ik  = math.cos(ik)

        # ECEF hız (IS-GPS-200 denklemleri)
        Vx = (dxkp_dt * cos_omg
              - xkp * sin_omg * domg_dt
              - dykp_dt * cos_ik * sin_omg
              + ykp * (sin_ik * sin_omg * di_dt - cos_ik * cos_omg * domg_dt))

        Vy = (dxkp_dt * sin_omg
              + xkp * cos_omg * domg_dt
              + dykp_dt * cos_ik * cos_omg
              - ykp * (sin_ik * cos_omg * di_dt + cos_ik * sin_omg * domg_dt))

        Vz = (dykp_dt * sin_ik + ykp * cos_ik * di_dt)

        return [Vx, Vy, Vz]   # m/s

    except Exception:
        return [0.0, 0.0, 0.0]