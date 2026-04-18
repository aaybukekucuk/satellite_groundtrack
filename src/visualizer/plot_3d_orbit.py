"""
plot_3d_orbit_fixed.py
======================
GPS Konstellasyonu için doğru 3D yörünge çizimi.

Hocamızın belirttiği GPS yörünge geometrisi:
  - 6 yörünge düzlemi (A–F)
  - Eğim (inclination): i = 55°
  - RAAN aralığı: 60° (0, 60, 120, 180, 240, 300°)
  - Yarı-büyük eksen: a ≈ 26560 km

Teori (XYZ2KEPLER dokümanındaki Tablo 3.6 – Adım 3):
  q_s = R · r  burada R = R3(-Ω) · R1(-i) · R3(-ω)
"""

import numpy as np
import plotly.graph_objects as go
from typing import Optional


# ─────────────────────────────────────────────
# Rotasyon Matrisleri
# ─────────────────────────────────────────────

def R1(angle_rad: float) -> np.ndarray:
    """X ekseni etrafında rotasyon matrisi."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array([[1, 0, 0],
                     [0, c, -s],
                     [0, s,  c]])

def R3(angle_rad: float) -> np.ndarray:
    """Z ekseni etrafında rotasyon matrisi."""
    c, s = np.cos(angle_rad), np.sin(angle_rad)
    return np.array([[ c, -s, 0],
                     [ s,  c, 0],
                     [ 0,  0, 1]])


# ─────────────────────────────────────────────
# Kepler → XYZ dönüşümü  (Tablo 3.6, Adım 3)
# ─────────────────────────────────────────────

def kepler_to_xyz(a: float, e: float, i_deg: float,
                  raan_deg: float, omega_deg: float,
                  n_points: int = 360) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Kepler parametrelerinden yörünge noktalarını Kartezyen (XYZ) koordinatlarına dönüştürür.

    Parametreler
    ------------
    a       : Yarı-büyük eksen [km]
    e       : Eksantriklik
    i_deg   : Eğim açısı [derece]
    raan_deg: Sağ Yükselen Düğüm Boylam Ω [derece]
    omega_deg: Perigee argümanı ω [derece]
    n_points: Yörüngede hesaplanacak nokta sayısı

    Dönüş
    -----
    x, y, z : [km] cinsinden koordinat dizileri
    """
    i     = np.radians(i_deg)
    Omega = np.radians(raan_deg)
    omega = np.radians(omega_deg)

    # Rotasyon matrisi: R = R3(-Ω) · R1(-i) · R3(-ω)
    R = R3(-Omega) @ R1(-i) @ R3(-omega)

    # True anomaly v: 0 → 2π
    v_array = np.linspace(0, 2 * np.pi, n_points)

    # Perifocal koordinatlar (orbital düzlemde)
    p = a * (1 - e**2)            # semi-latus rectum
    r_array = p / (1 + e * np.cos(v_array))  # mesafe [km]

    x_orb = r_array * np.cos(v_array)  # perifocal X
    y_orb = r_array * np.sin(v_array)  # perifocal Y
    z_orb = np.zeros_like(v_array)     # perifocal Z (her zaman 0)

    # Yörünge düzleminden inertial (ECI) koordinatlara: q_s = R · r_perifocal
    xyz = R @ np.vstack([x_orb, y_orb, z_orb])

    return xyz[0], xyz[1], xyz[2]


# ─────────────────────────────────────────────
# GPS Konstellasyonu Tanımı
# ─────────────────────────────────────────────

# GPS nominal yörünge parametreleri
GPS_A     = 26560.0   # km  (yarı-büyük eksen)
GPS_E     = 0.01      # eksantriklik (nominalde ~0)
GPS_I_DEG = 55.0      # derece (eğim)

# 6 yörünge düzlemi: RAAN değerleri 60° aralıklı
GPS_PLANES = {
    "Plane A": {"raan": 0,   "color": "#00BFFF", "omega": 0},
    "Plane B": {"raan": 60,  "color": "#FF6B6B", "omega": 0},
    "Plane C": {"raan": 120, "color": "#90EE90", "omega": 0},
    "Plane D": {"raan": 180, "color": "#FFD700", "omega": 0},
    "Plane E": {"raan": 240, "color": "#FF69B4", "omega": 0},
    "Plane F": {"raan": 300, "color": "#DA70D6", "omega": 0},
}

# Gerçek GPS uydularının RAAN ve perigee argümanları (yaklaşık değerler)
# PRN → (plane, RAAN_offset, M0_deg)
GPS_SATELLITES = {
    # Plane A (RAAN ~ 0°)
    "G01": (0,   90),  "G03": (0,  30), "G08": (0, 150), "G14": (0, 210),
    # Plane B (RAAN ~ 60°)
    "G09": (60,  15),  "G27": (60,  75), "G10": (60, 135), "G30": (60, 195),
    # Plane C (RAAN ~ 120°)
    "G06": (120, 45),  "G19": (120, 105), "G24": (120, 165), "G11": (120, 225),
    # Plane D (RAAN ~ 180°)
    "G02": (180, 60),  "G17": (180, 120), "G28": (180, 180), "G20": (180, 240),
    # Plane E (RAAN ~ 240°)
    "G05": (240, 75),  "G18": (240, 135), "G21": (240, 195), "G15": (240, 255),
    # Plane F (RAAN ~ 300°)
    "G29": (300, 90),  "G07": (300, 150), "G26": (300, 210), "G12": (300, 270),
}

PLANE_COLORS = {
    0: "#00BFFF", 60: "#FF6B6B", 120: "#90EE90",
    180: "#FFD700", 240: "#FF69B4", 300: "#DA70D6"
}


def get_satellite_position(raan_deg: float, mean_anomaly_deg: float,
                           a: float = GPS_A, e: float = GPS_E,
                           i_deg: float = GPS_I_DEG,
                           omega_deg: float = 0.0) -> tuple[float, float, float]:
    """
    Verilen ortalama anomali için uydunun XYZ konumunu döndürür.
    Newton-Raphson ile eksantrik anomali E hesaplanır.
    """
    M = np.radians(mean_anomaly_deg)

    # Newton-Raphson: M = E - e·sin(E)
    E = M
    for _ in range(50):
        dE = (M - E + e * np.sin(E)) / (1 - e * np.cos(E))
        E += dE
        if abs(dE) < 1e-10:
            break

    # True anomaly
    v = 2 * np.arctan2(
        np.sqrt(1 + e) * np.sin(E / 2),
        np.sqrt(1 - e) * np.cos(E / 2)
    )

    r = a * (1 - e * np.cos(E))

    # Perifocal koordinatlar
    x_orb = r * np.cos(v)
    y_orb = r * np.sin(v)

    # ECI'ye dönüştür
    i     = np.radians(i_deg)
    Omega = np.radians(raan_deg)
    omega = np.radians(omega_deg)
    R = R3(-Omega) @ R1(-i) @ R3(-omega)

    pos = R @ np.array([x_orb, y_orb, 0.0])
    return float(pos[0]), float(pos[1]), float(pos[2])


# ─────────────────────────────────────────────
# Dünya'nın 3D yüzeyini çiz
# ─────────────────────────────────────────────

def earth_surface(r_earth: float = 6371.0, n: int = 60) -> go.Surface:
    """Dünya'nın yüzeyini temsil eden bir küre."""
    theta = np.linspace(0, 2 * np.pi, n)
    phi   = np.linspace(0, np.pi, n)
    x = r_earth * np.outer(np.cos(theta), np.sin(phi))
    y = r_earth * np.outer(np.sin(theta), np.sin(phi))
    z = r_earth * np.outer(np.ones(n),    np.cos(phi))
    return go.Surface(
        x=x, y=y, z=z,
        colorscale=[[0, "#1a5276"], [0.4, "#2471a3"],
                    [0.7, "#76b041"], [1, "#7dcea0"]],
        showscale=False,
        opacity=0.9,
        name="Dünya",
        hoverinfo="skip"
    )


# ─────────────────────────────────────────────
# Ana Çizim Fonksiyonu
# ─────────────────────────────────────────────

def plot_gps_constellation(
    selected_prns: Optional[list[str]] = None,
    show_all_planes: bool = True
) -> go.Figure:
    """
    GPS konstellasyonunu 3D olarak çizer.

    Parametreler
    ------------
    selected_prns   : Gösterilecek uydu listesi (None = hepsi)
    show_all_planes : Tüm yörünge düzlemlerini göster
    """
    fig = go.Figure()

    # 1. Dünya
    fig.add_trace(earth_surface())

    # 2. Yörünge düzlemleri (6 adet, 55° eğim, 60° RAAN aralığı)
    for plane_name, props in GPS_PLANES.items():
        x, y, z = kepler_to_xyz(
            a=GPS_A, e=GPS_E,
            i_deg=GPS_I_DEG,
            raan_deg=props["raan"],
            omega_deg=props["omega"]
        )
        fig.add_trace(go.Scatter3d(
            x=x, y=y, z=z,
            mode="lines",
            line=dict(color=props["color"], width=2, dash="dash"),
            name=plane_name,
            legendgroup=plane_name,
            hoverinfo="name"
        ))

    # 3. Uydu konumları
    for prn, (raan, m0) in GPS_SATELLITES.items():
        if selected_prns is not None and prn not in selected_prns:
            continue
        sx, sy, sz = get_satellite_position(raan_deg=raan, mean_anomaly_deg=m0)
        color = PLANE_COLORS[raan]
        fig.add_trace(go.Scatter3d(
            x=[sx], y=[sy], z=[sz],
            mode="markers+text",
            marker=dict(size=5, color=color, symbol="circle",
                        line=dict(color="white", width=1)),
            text=[prn],
            textposition="top center",
            textfont=dict(color="white", size=9),
            name=prn,
            legendgroup=f"RAAN_{raan}",
            showlegend=True,
            hovertemplate=(
                f"<b>{prn}</b><br>"
                f"RAAN: {raan}°<br>"
                f"X: {sx:.1f} km<br>"
                f"Y: {sy:.1f} km<br>"
                f"Z: {sz:.1f} km<br>"
                "<extra></extra>"
            )
        ))

    # 4. Layout
    axis_range = 32000
    fig.update_layout(
        title=dict(
            text="GPS Konstellasyonu – 3D Yörünge Görünümü<br>"
                 "<sup>i=55° | 6 Düzlem | RAAN: 0°,60°,120°,180°,240°,300°</sup>",
            font=dict(color="white", size=16)
        ),
        paper_bgcolor="#0a0a1a",
        scene=dict(
            bgcolor="#0a0a1a",
            xaxis=dict(title="X [km]", range=[-axis_range, axis_range],
                       showgrid=True, gridcolor="#1a2a3a",
                       tickfont=dict(color="#888")),
            yaxis=dict(title="Y [km]", range=[-axis_range, axis_range],
                       showgrid=True, gridcolor="#1a2a3a",
                       tickfont=dict(color="#888")),
            zaxis=dict(title="Z [km]", range=[-axis_range, axis_range],
                       showgrid=True, gridcolor="#1a2a3a",
                       tickfont=dict(color="#888")),
            aspectmode="cube",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=0.8)
            )
        ),
        legend=dict(
            font=dict(color="white", size=9),
            bgcolor="rgba(10,10,30,0.8)",
            bordercolor="#333",
            borderwidth=1
        ),
        margin=dict(l=0, r=0, t=60, b=0)
    )

    return fig


# ─────────────────────────────────────────────
# Mevcut arayüze entegrasyon için yardımcı fonksiyonlar
# ─────────────────────────────────────────────

def get_orbit_points_for_satellite(prn: str,
                                   raan_override: Optional[float] = None,
                                   omega_override: float = 0.0) -> dict:
    """
    Tek bir uydu için yörünge noktalarını döndürür.
    Mevcut arayüzün API'siyle uyumlu dict formatında.

    Dönüş
    ------
    {
        "prn": "G01",
        "x": [...], "y": [...], "z": [...],   # km
        "color": "#00BFFF",
        "plane": "A",
        "raan": 0.0,
        "inclination": 55.0
    }
    """
    if prn not in GPS_SATELLITES:
        raise ValueError(f"Bilinmeyen PRN: {prn}")

    raan, _ = GPS_SATELLITES[prn]
    if raan_override is not None:
        raan = raan_override

    x, y, z = kepler_to_xyz(
        a=GPS_A, e=GPS_E,
        i_deg=GPS_I_DEG,
        raan_deg=raan,
        omega_deg=omega_override
    )

    plane_letter = ["A", "B", "C", "D", "E", "F"][list(GPS_PLANES.keys()).index(
        next(k for k, v in GPS_PLANES.items() if v["raan"] == raan)
    )]

    return {
        "prn": prn,
        "x": x.tolist(),
        "y": y.tolist(),
        "z": z.tolist(),
        "color": PLANE_COLORS[raan],
        "plane": plane_letter,
        "raan": raan,
        "inclination": GPS_I_DEG
    }


def get_all_planes_data() -> list[dict]:
    """
    6 yörünge düzleminin tamamı için veri döndürür.
    Three.js / frontend'e JSON olarak gönderilebilir.
    """
    result = []
    for plane_name, props in GPS_PLANES.items():
        x, y, z = kepler_to_xyz(
            a=GPS_A, e=GPS_E,
            i_deg=GPS_I_DEG,
            raan_deg=props["raan"],
            omega_deg=props["omega"]
        )
        result.append({
            "plane": plane_name,
            "raan": props["raan"],
            "inclination": GPS_I_DEG,
            "color": props["color"],
            "x": x.tolist(),
            "y": y.tolist(),
            "z": z.tolist()
        })
    return result


# ─────────────────────────────────────────────
# Test: doğrudan çalıştır
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("GPS Konstellasyonu çiziliyor...")
    print(f"  Eğim (i)    : {GPS_I_DEG}°")
    print(f"  Düzlem sayısı: {len(GPS_PLANES)}")
    print(f"  RAAN aralığı : 60°")
    print()

    # Örnek: G01 için yörünge noktaları
    data = get_orbit_points_for_satellite("G01")
    print(f"G01 yörüngesi: {len(data['x'])} nokta, Düzlem {data['plane']}, RAAN={data['raan']}°")

    # Tüm düzlem verileri
    planes = get_all_planes_data()
    print(f"\nTüm düzlemler:")
    for p in planes:
        print(f"  {p['plane']}: RAAN={p['raan']}°, renk={p['color']}, nokta sayısı={len(p['x'])}")

    # Plotly ile görselleştir
    try:
        fig = plot_gps_constellation()
        fig.write_html("gps_constellation_3d.html")
        print("\n✅ gps_constellation_3d.html oluşturuldu.")
    except Exception as err:
        print(f"\n⚠️  Plotly çizimi: {err}")