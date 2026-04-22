"""
compare_kepler.py
=================
SP3 yörünge verilerinden Gibbs yöntemiyle Kepler parametrelerini hesaplar
ve Broadcast efemerisi ile karşılaştırır.

DÜZELTİLEN HATALAR:
  ❌ ESKİ KOD: r1_eci = rotate_z(r1_ecef, +OMEGA_E * dt1)   ← YANLIŞ YÖNDE DÖNÜŞ!
               r3_eci = rotate_z(r3_ecef, -OMEGA_E * dt3)   ← YANLIŞ YÖNDE DÖNÜŞ!

  ✅ YENİ KOD:  r1_eci = rotate_z(r1_ecef, -OMEGA_E * dt1)
               r3_eci = rotate_z(r3_ecef, +OMEGA_E * dt3)

  Mantık:
    ECI (inertial) sabit durur, Dünya döner.
    p2 referans an olarak alındığında:
      - p1, p2'den dt1 ÖNCE gerçekleşti.
        ECEF'teki p1, o sırada Dünya daha az dönmüştü (OMEGA_E * dt1 kadar geri).
        ECI'ya çevirmek için p1_ecef'i -OMEGA_E * dt1 kadar döndürürüz.
      - p3, p2'den dt3 SONRA gerçekleşti.
        ECEF'teki p3, Dünya fazladan döndükten sonra kaydedildi.
        ECI'ya çevirmek için p3_ecef'i +OMEGA_E * dt3 kadar döndürürüz.

  Bu hata, Gibbs'in ürettiği hız vektörünü tamamen bozuyor ve
  state_to_kepler'da semi-major axis'i milyar metre hatalı hesaplatıyordu.

NOT: SP3 verisindeki koordinatlar kilometre cinsindendir; metreye çevrilir.
"""

import math
import numpy as np
from .state_to_kepler import calculate_kepler_from_state

# Dünya'nın açısal dönüş hızı ve Kütle-Çekim Sabiti
OMEGA_E = 7.2921151467e-5   # [rad/s]
MU      = 3.986004418e14    # [m³/s²]


def rotate_z(vec, angle):
    """
    Vektörü Z ekseni etrafında 'angle' [rad] kadar döndürür.
    Pozitif angle → Dünya dönüşüyle aynı yön (Doğuya doğru).
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return np.array([
        vec[0] * cos_a - vec[1] * sin_a,
        vec[0] * sin_a + vec[1] * cos_a,
        vec[2]
    ])


def gibbs_method(r1, r2, r3, mu):
    """
    Gibbs Yöntemi: 3 ECI konum vektöründen r2 anındaki hız vektörünü türetir.
    Tüm vektörler aynı koordinat çerçevesinde (ECI) ve metre cinsinden olmalı.
    """
    r1_mag = np.linalg.norm(r1)
    r2_mag = np.linalg.norm(r2)
    r3_mag = np.linalg.norm(r3)

    c12 = np.cross(r1, r2)
    c23 = np.cross(r2, r3)
    c31 = np.cross(r3, r1)

    D = c12 + c23 + c31
    N = r3_mag * c12 + r1_mag * c23 + r2_mag * c31
    S = (r2_mag - r3_mag) * r1 + (r3_mag - r1_mag) * r2 + (r1_mag - r2_mag) * r3

    D_mag = np.linalg.norm(D)
    N_mag = np.linalg.norm(N)

    if D_mag < 1e-12 or N_mag < 1e-12:
        return np.array([0.0, 0.0, 0.0])

    B = np.cross(D, r2) / r2_mag
    L = math.sqrt(mu / (N_mag * D_mag))

    v2 = L * (B + S)
    return v2


def _get_brdc_param(brdc_kepler, *keys):
    """Birden fazla olası anahtar ismini dener, ilk bulunanı döndürür."""
    for k in keys:
        if k in brdc_kepler:
            return brdc_kepler[k]
    return None


def analyze_kepler_errors(sp3_coords, brdc_kepler):
    """
    SP3 konum serisi ve tek bir Broadcast efemerisi alarak
    her SP3 epoch'unda Kepler parametre hatalarını hesaplar.

    Parametreler
    ------------
    sp3_coords  : [{"x": km, "y": km, "z": km, "time": datetime}, ...]
    brdc_kepler : read_nav_kepler'dan gelen tek broadcast efemerisi dict'i

    Dönüş
    -----
    list of dict: [{"time", "delta_A_meters", "delta_E", "delta_I_deg"}, ...]
    """
    error_series = []

    # ── Broadcast parametrelerini esnek key isimleriyle çek ──────────────
    brdc_a = _get_brdc_param(brdc_kepler,
        "A (Yarı Büyük Eksen) [m]", "sqrtA", "a", "semi_major_axis")
    brdc_e = _get_brdc_param(brdc_kepler,
        "e (Dışmerkezlik)", "e", "eccentricity")
    brdc_i = _get_brdc_param(brdc_kepler,
        "i0 (Yörünge Eğikliği)", "i0", "inclination")

    if brdc_a is None or brdc_e is None or brdc_i is None:
        return error_series

    # sqrtA ise kareye al (RINEX nav. sqrtA = √a cinsinden saklar)
    if "sqrtA" in brdc_kepler and "A (Yarı Büyük Eksen) [m]" not in brdc_kepler:
        brdc_a = brdc_a ** 2

    # ── Her orta noktası için Gibbs hesabı ───────────────────────────────
    for idx in range(1, len(sp3_coords) - 1):
        p1 = sp3_coords[idx - 1]
        p2 = sp3_coords[idx]
        p3 = sp3_coords[idx + 1]

        # p2 referans anına göre zaman farkları
        dt1 = (p2["time"] - p1["time"]).total_seconds()   # p1'in p2'den ne kadar önce olduğu
        dt3 = (p3["time"] - p2["time"]).total_seconds()   # p3'ün p2'den ne kadar sonra olduğu

        if dt1 <= 0 or dt3 <= 0:
            continue

        # read_sp3.py zaten km→m dönüşümü yapıyor
        # Burada ×1000 YAPILMAZ — aksi hâlde ΔA 26.5 milyar metre çıkar
        r1_ecef = np.array([p1["x"], p1["y"], p1["z"]])  # [m]
        r2_ecef = np.array([p2["x"], p2["y"], p2["z"]])  # [m]
        r3_ecef = np.array([p3["x"], p3["y"], p3["z"]])  # [m]

        # 2. ECEF → ECI dönüşümü (p2 anı referans)
        #
        # ✅ DOĞRU MANTIK:
        #    p1, p2'den dt1 saniye ÖNCE gerçekleşti.
        #    O anda Dünya henüz (OMEGA_E * dt1) kadar dönmemişti.
        #    → p1_ecef'i ECI'ya çevirmek için -OMEGA_E * dt1 kadar döndür.
        #
        #    p3, p2'den dt3 saniye SONRA gerçekleşti.
        #    O anda Dünya fazladan (OMEGA_E * dt3) kadar dönmüştü.
        #    → p3_ecef'i ECI'ya çevirmek için +OMEGA_E * dt3 kadar döndür.
        #
        r1_eci = rotate_z(r1_ecef, -OMEGA_E * dt1)   # ← DÜZELTİLDİ (eski: +dt1)
        r2_eci = r2_ecef.copy()                       # Referans an — dönüşüm yok
        r3_eci = rotate_z(r3_ecef, +OMEGA_E * dt3)   # ← DÜZELTİLDİ (eski: -dt3)

        try:
            # 3. Gibbs ile ECI hız vektörü
            v2_eci = gibbs_method(r1_eci, r2_eci, r3_eci, MU)

            # Hız vektörü sıfır veya çok küçükse (ortak düzlem sorunu) atla
            if np.linalg.norm(v2_eci) < 100:
                continue

            # 4. ECI konum + hız → Kepler parametreleri
            sp3_kep = calculate_kepler_from_state(r2_eci.tolist(), v2_eci.tolist())

            # 5. Farklar
            delta_a = sp3_kep["A (Yarı Büyük Eksen) [m]"] - brdc_a
            delta_e = sp3_kep["e (Dışmerkezlik)"]          - brdc_e
            delta_i = math.degrees(sp3_kep["i0 (Yörünge Eğikliği)"] - brdc_i)

            error_series.append({
                "time":           p2["time"].isoformat(),
                "delta_A_meters": round(delta_a, 3),
                "delta_E":        round(delta_e, 9),
                "delta_I_deg":    round(delta_i, 6)
            })

        except Exception:
            continue

    return error_series