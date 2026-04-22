"""
rtn_transform.py
================
SP3 (referans) ile Broadcast (karşılaştırılan) arasındaki farkı
RTN (Radyal–Teğetsel–Normal) bileşenlerine dönüştürür.

Hocanın istediği matematiksel adımlar (IS-GPS-200 / IGS konvansiyonu):
  E1 (Radyal)   = Q / |Q|              [konum yönü]
  E3 (Normal)   = (Q × Q̇) / |Q × Q̇|   [açısal momentum → yörünge düzlemine dik]
  E2 (Teğetsel) = E3 × E1             [uçuş yönü]

Birim uyarısı:
  pos_ref, pos_brdc → metre [m]
  vel_ref           → metre/saniye [m/s]

DÜZELTİLEN:
  Eski velocity.py km/s döndürüyordu → velocity.py düzeltildi.
  RTN matematiği zaten doğruydu (E1, E2=E3×E1, E3).
"""

import numpy as np


def ecef_to_rtn_error(pos_ref, vel_ref, pos_brdc):
    """
    SP3 ile Broadcast arasındaki ECEF konumlarını RTN hata bileşenlerine dönüştürür.

    Parametreler
    ------------
    pos_ref  : SP3 referans konumu [m]  (APC düzeltmesi uygulanmış olmalı)
    vel_ref  : SP3 hız vektörü [m/s]
    pos_brdc : Broadcast ECEF konumu [m]

    Dönüş
    -----
    dict : {'Radial (m)', 'Along-track (m)', 'Cross-track (m)'}
    """
    Q     = np.array(pos_ref,  dtype=float)
    Qdot  = np.array(vel_ref,  dtype=float)
    Q_brd = np.array(pos_brdc, dtype=float)

    # Sağlık kontrolü: GPS uydusu için |Q| ≈ 26 560 km = 2.656e7 m
    Q_norm = np.linalg.norm(Q)
    if Q_norm < 1e6:
        # Konum çok küçük — büyük ihtimalle birim hatası (km yerine m verildi)
        raise ValueError(
            f"pos_ref normu {Q_norm:.1f} m — GPS uydusu için beklenen ≈ 2.6e7 m. "
            "SP3 birimi kontrol edilmeli (km → m dönüşümü yapılmalı)."
        )

    # ── E1: Radyal (konum yönü) ──────────────────────────────────────────
    E1 = Q / Q_norm                           # R

    # ── E3: Normal (açısal momentum, yörünge düzlemine dik) ──────────────
    h      = np.cross(Q, Qdot)               # h = Q × Q̇
    h_norm = np.linalg.norm(h)
    if h_norm < 1e-12:
        raise ValueError("Hız vektörü sıfır veya konuma paralel — RTN hesaplanamaz.")
    E3 = h / h_norm                           # N

    # ── E2: Teğetsel (uçuş yönü = E3 × E1) ─────────────────────────────
    E2 = np.cross(E3, E1)                     # T  (normalize gerekmez: |E3|=|E1|=1 → |E2|=1)

    # ── Hata vektörü: Broadcast − SP3 ───────────────────────────────────
    delta = Q_brd - Q                         # [m]

    # ── RTN bileşenlerine projeksiyon ────────────────────────────────────
    R_mat    = np.array([E1, E2, E3])         # 3×3 dönüşüm matrisi
    rtn      = R_mat @ delta                  # [m]

    return {
        "Radial (m)":      float(rtn[0]),
        "Along-track (m)": float(rtn[1]),
        "Cross-track (m)": float(rtn[2])
    }


def validate_inputs(pos_ref, vel_ref, pos_brdc, label=""):
    """
    RTN hesabı öncesi birim/büyüklük sağlık kontrolü.
    Geliştirme sırasında çağrılabilir.
    """
    Q    = np.linalg.norm(pos_ref)
    Qbrd = np.linalg.norm(pos_brdc)
    V    = np.linalg.norm(vel_ref)

    issues = []
    if Q < 1e6:
        issues.append(f"pos_ref normu {Q:.0f} m — GPS için ≈2.6e7 m beklenir (km/m birim hatası?)")
    if Qbrd < 1e6:
        issues.append(f"pos_brdc normu {Qbrd:.0f} m — Broadcast yanlış (sqrt_A sorunu?)")
    if V < 100:
        issues.append(f"vel_ref normu {V:.2f} — GPS hızı ≈3800 m/s beklenir (km/s → m/s dönüşümü yapılmalı)")
    if abs(Q - Qbrd) > 1e6:
        issues.append(f"SP3 ile Broadcast yarıçap farkı {abs(Q-Qbrd)/1000:.0f} km — birim hatası olabilir")

    return issues