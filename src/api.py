from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import math
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
sys.path.append(BASE_DIR)

from utils.read_sp3 import read_sp3
from utils.read_nav import read_nav_kepler
from utils.ecef_to_geodetic import ecef_to_geodetic
from utils.topocentric import ecef_to_topocentric
from utils.state_to_kepler import calculate_kepler_from_state
from utils.velocity import calculate_sp3_velocity_from_positions
from utils.rtn_transform import ecef_to_rtn_error
from utils.satpos_utils import calculate_satpos_from_kepler
from utils.apc_utils import read_antex_gps, datetime_to_mjd, calc_sunpos, calc_satapc
from utils.compare_kepler import analyze_kepler_errors
from visualizer.plot_3d_orbit import (
    get_all_planes_data,
    get_orbit_points_for_satellite,
    GPS_SATELLITES,
    GPS_PLANES,
    GPS_A, GPS_E, GPS_I_DEG,
    kepler_to_xyz,
    get_satellite_position,
)

from contextlib import asynccontextmanager
import uvicorn # En alta uvicorn ile çalıştırma kodu ekleyeceğiz

# --- GLOBAL DEĞİŞKENLER ---
SP3_DATA = []
KEPLER_DATA = {}
ANTEX_DATA = {}
STATION = {"lat": 39.866, "lon": 32.736, "h": 100.0}

# --- YENİ MODERN VERİ YÜKLEME YAPISI (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global SP3_DATA, KEPLER_DATA, ANTEX_DATA
    print("⏳ API Startup: Loading SP3, Broadcast ve ANTEX Verileri...")
    
    root_dir = os.path.dirname(BASE_DIR)
    sp3_path = os.path.join(root_dir, "data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    nav_path = os.path.join(root_dir, "data", "BRDC00IGS_R_20240600000_01D_MN.rnx")
    atx_path = os.path.join(root_dir, "brdc and sp3 pos and clck", "igs20.atx") 
    
    if os.path.exists(sp3_path):
        SP3_DATA = read_sp3(sp3_path)
    if os.path.exists(nav_path):
        KEPLER_DATA = read_nav_kepler(nav_path)
    if os.path.exists(atx_path):
        ANTEX_DATA = read_antex_gps(atx_path) 
        
    print("✅ Veriler API'ye başarıyla yüklendi!")
    yield # API burada çalışmaya başlar

# FastAPI Uygulamasını yeni lifespan yapısıyla başlatıyoruz
app = FastAPI(title="OrbitalViz API", lifespan=lifespan)

# --- AYARLAR ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# (Buradan aşağısı app.get("/") ve get_kepler_analysis kodlarınla aynı şekilde devam ediyor...)

def load_data():
    global SP3_DATA, KEPLER_DATA, ANTEX_DATA
    print("⏳ API Startup: Loading SP3, Broadcast ve ANTEX Verileri...")
    
    root_dir = os.path.dirname(BASE_DIR)
    sp3_path = os.path.join(root_dir, "data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    nav_path = os.path.join(root_dir, "data", "BRDC00IGS_R_20240600000_01D_MN.rnx")
    
    # YENİ: Hocanın gönderdiği igs20.atx dosyasının yolu
    atx_path = os.path.join(root_dir, "brdc and sp3 pos and clck", "igs20.atx") 
    
    if os.path.exists(sp3_path):
        SP3_DATA = read_sp3(sp3_path)
    if os.path.exists(nav_path):
        KEPLER_DATA = read_nav_kepler(nav_path)
    if os.path.exists(atx_path):
        ANTEX_DATA = read_antex_gps(atx_path) # ANTEX okuyucuyu çalıştır
        
    print("✅ Veriler API'ye başarıyla yüklendi!")

@app.get("/")
def serve_home():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))

@app.get("/api/satellites")
def get_satellites(sats: str = "G01"):
    selected = [s.strip().upper() for s in sats.split(",")]
    response_data = []
    
    for sat_id in selected:
        coords = [entry for entry in SP3_DATA if entry["id"] == sat_id]
        if not coords: continue
            
        track_points = []
        for c in coords:
            lat, lon, h = ecef_to_geodetic(c["x"], c["y"], c["z"])
            track_points.append({"lat": lat, "lon": lon, "alt": h, "time": c["time"].isoformat()})
            
        c0 = coords[0]
        
        # Hız Vektörleri (vx, vy, vz) ve Skaler Hız (vel_kms) Hesaplama
        vel_kms = 0.0
        vx, vy, vz = 0.0, 0.0, 0.0
        if len(coords) >= 2:
            p1, p2 = coords[0], coords[1]
            dt = (p2["time"] - p1["time"]).total_seconds()
            if dt > 0:
                # read_sp3 zaten metre döndürür → dx[m]/dt[s] = m/s (×1000 YOK)
                vx = (p2["x"] - p1["x"]) / dt   # m/s
                vy = (p2["y"] - p1["y"]) / dt   # m/s
                vz = (p2["z"] - p1["z"]) / dt   # m/s
                vel_kms = math.sqrt(vx**2 + vy**2 + vz**2) / 1000.0  # km/s (~3.9)
        
        # =====================================================================
        # DİNAMİK DÖNÜŞÜM MOTORU ENTEGRASYONU (HOCANIN İSTEDİĞİ KISIM)
        # =====================================================================
        kepler_list = KEPLER_DATA.get(sat_id, [])
        kepler = {}
        
        # Eğer uydu GLONASS ('R') ise Kepler parametrelerini ANLIK hesapla!
        if sat_id.startswith("R"):
            if len(coords) >= 2:
                # read_sp3 zaten metre → ×1000 YOK
                r_vec = [c0["x"], c0["y"], c0["z"]]  # [m]
                v_vec = [vx, vy, vz]                 # [m/s]
                
                # Sizin yazdığınız state_to_kepler fonksiyonunu çağırıyoruz
                kepler = calculate_kepler_from_state(r_vec, v_vec)
        else:
            # GPS ve Galileo için Broadcast dosyasından statik okumaya devam et
            kepler = kepler_list[0] if kepler_list else {}
        # =====================================================================

        az, el, dist = ecef_to_topocentric(c0["x"], c0["y"], c0["z"], STATION["lat"], STATION["lon"], STATION["h"])
        
        instant_data = {
            "velocity_kms": vel_kms,
            "topocentric": {"azimuth": az, "elevation": el, "distance_m": dist}
        }

        response_data.append({"id": sat_id, "track": track_points, "kepler": kepler, "instant_data": instant_data})
        
    return {"status": "success", "data": response_data}

# -- ZAMAN DÖNÜŞÜM YARDIMCISI --
def get_tk(t_epoch, toe):
    """ SP3 zamanı ile Broadcast TOE (Time of Ephemeris) arasındaki saniye farkını hesaplar """
    gps_epoch = datetime(1980, 1, 6)
    delta = t_epoch - gps_epoch
    sec_of_week = (delta.days % 7) * 86400 + delta.seconds
    tk = sec_of_week - toe
    
    # Hafta atlaması (Crossover) düzeltmesi (IS-GPS-200)
    if tk > 302400:
        tk -= 604800
    elif tk < -302400:
        tk += 604800
    return tk

@app.get("/api/analysis")
@app.get("/api/analysis")
def get_kepler_analysis(sat: str = "G01"):
    sat_id = sat.strip().upper()
    coords = [entry for entry in SP3_DATA if entry["id"] == sat_id]
    brdc_list = KEPLER_DATA.get(sat_id, [])
    
    if len(coords) < 3 or not brdc_list:
        return {"status": "error", "message": f"{sat_id} için yeterli SP3/Broadcast verisi yok."}
    
    sp3_velocities = calculate_sp3_velocity_from_positions(coords)
    
    times_str, radial_err, along_err, cross_err = [], [], [], []

    for i in range(len(coords)):
        t_epoch = coords[i]['time']
        
        # read_sp3.py zaten km→m dönüşümü yapıyor (×1000 orada var)
        # Burada tekrar ×1000 YAPILMAZ — aksi hâlde 26.5 milyar metre olur
        pos_com = [coords[i]['x'], coords[i]['y'], coords[i]['z']]  # [m]
        vel_ref = [sp3_velocities[i]['vx'], sp3_velocities[i]['vy'], sp3_velocities[i]['vz']]
        
        # 2. ANTEN FAZ MERKEZİ (APC) DÜZELTMESİ
        prn_num = int(sat_id.replace("G", ""))
        pos_ref = pos_com 
        
        if ANTEX_DATA and prn_num in ANTEX_DATA:
            mjd = datetime_to_mjd(t_epoch)
            sunpos = calc_sunpos(mjd)
            neu_l1 = ANTEX_DATA[prn_num].get('L1')
            neu_l2 = ANTEX_DATA[prn_num].get('L2')
            
            if neu_l1 and neu_l2:
                sapc_offset = calc_satapc(pos_com, sunpos, neu_l1, neu_l2)
                pos_ref = [pos_com[0] + sapc_offset[0], 
                           pos_com[1] + sapc_offset[1], 
                           pos_com[2] + sapc_offset[2]]
        
        # O anki SP3 saatine EN YAKIN (Geçerli) yörünge parametresini bul
        best_eph = None
        min_abs_tk = float('inf')
        best_tk = 0
        
        for eph in brdc_list:
            current_tk = get_tk(t_epoch, eph['toe'])
            if abs(current_tk) < min_abs_tk:
                min_abs_tk = abs(current_tk)
                best_eph = eph
                best_tk = current_tk
                
        if best_eph:
            # Geçerli yörünge seti ve doğru zaman farkı ile ECEF hesapla
            pos_brdc = calculate_satpos_from_kepler(best_eph, best_tk)
            
            if pos_brdc != [0.0, 0.0, 0.0]:
                rtn = ecef_to_rtn_error(pos_ref, vel_ref, pos_brdc)
                times_str.append(t_epoch.strftime('%H:%M'))
                radial_err.append(round(rtn['Radial (m)'], 3))
                along_err.append(round(rtn['Along-track (m)'], 3))
                cross_err.append(round(rtn['Cross-track (m)'], 3))

    return {"status": "success", "sat_id": sat_id, "analysis": {
        "times": times_str, "radial": radial_err, "along": along_err, "cross": cross_err
    }}

@app.get("/api/kepler_errors")
def get_kepler_errors(sat: str = "G01"):
    sat_id = sat.strip().upper()
    coords = [entry for entry in SP3_DATA if entry["id"] == sat_id]
    brdc_list = KEPLER_DATA.get(sat_id, [])

    if len(coords) < 3 or not brdc_list:
        return {"status": "error", "message": f"{sat_id} için yeterli SP3/Broadcast verisi bulunamadı."}

    # Günün ortasına en yakın broadcast efemerisini referans al
    mid_time = coords[len(coords) // 2]["time"]
    best_eph = min(brdc_list, key=lambda eph: abs(get_tk(mid_time, eph["toe"])))

    error_series = analyze_kepler_errors(coords, best_eph)

    if not error_series:
        return {"status": "error", "message": "Kepler hata serisi hesaplanamadı. Veri yetersiz olabilir."}

    times   = [e["time"][11:16] for e in error_series]   # sadece HH:MM
    delta_a = [e["delta_A_meters"] for e in error_series]
    delta_e = [e["delta_E"]        for e in error_series]
    delta_i = [e["delta_I_deg"]    for e in error_series]

    # Özet istatistikler
    def stats(lst):
        if not lst: return {}
        import statistics
        return {
            "mean":  round(statistics.mean(lst), 6),
            "std":   round(statistics.stdev(lst), 6) if len(lst) > 1 else 0,
            "max":   round(max(lst), 6),
            "min":   round(min(lst), 6),
        }

    return {
        "status": "success",
        "sat_id": sat_id,
        "brdc_toe": best_eph.get("toe", 0),
        "kepler_errors": {
            "times":   times,
            "delta_A": delta_a,
            "delta_E": delta_e,
            "delta_I": delta_i,
        },
        "stats": {
            "delta_A": stats(delta_a),
            "delta_E": stats(delta_e),
            "delta_I": stats(delta_i),
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# 3D YÖRÜNGE / KONSTELASYONendpointleri
# plot_3d_orbit.py ile entegrasyon — Three.js frontend'inin tükettiği veriler
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/constellation/planes")
def get_constellation_planes():
    """
    GPS'in 6 yörünge düzlemini döndürür.
    Her düzlem: RAAN (60° aralıklı), i=55°, 360 noktalı XYZ listesi.
    Three.js'de TubeGeometry veya Line ile doğrudan çizilebilir.
    """
    try:
        planes = get_all_planes_data()
        return {
            "status": "success",
            "meta": {
                "inclination_deg": GPS_I_DEG,
                "semi_major_axis_km": GPS_A,
                "eccentricity": GPS_E,
                "plane_count": len(planes),
                "raan_spacing_deg": 60
            },
            "planes": planes
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@app.get("/api/constellation/orbit/{prn}")
def get_single_orbit(prn: str, raan: float = None, omega: float = 0.0):
    """
    Tek bir uyduya ait yörünge noktalarını döndürür.

    Query parametreleri (isteğe bağlı):
      raan  : RAAN açısını manuel override et (derece)
      omega : Perigee argümanını override et (derece)

    Kullanım:
      GET /api/constellation/orbit/G01
      GET /api/constellation/orbit/G01?raan=45&omega=10
    """
    prn_upper = prn.strip().upper()
    try:
        data = get_orbit_points_for_satellite(
            prn=prn_upper,
            raan_override=raan,
            omega_override=omega
        )
        return {"status": "success", "orbit": data}
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}


@app.get("/api/constellation/satellites")
def get_constellation_satellites(sats: str = None):
    """
    SP3 verisiyle uyumlu anlık uydu konumlarını döndürür.
    RAAN ve Kepler tabanlı nominal konumları içerir.

    Query parametresi:
      sats : Virgülle ayrılmış PRN listesi. Boş bırakılırsa tüm GPS (G01-G32).

    Her uydu için döner:
      prn, x, y, z (km), color, plane (A-F), raan, inclination
      + SP3'ten gelen gerçek anlık konum (eğer mevcutsa)
    """
    if sats:
        selected = [s.strip().upper() for s in sats.split(",")]
    else:
        selected = list(GPS_SATELLITES.keys())

    result = []
    for prn in selected:
        if prn not in GPS_SATELLITES:
            continue

        raan_deg, m0_deg = GPS_SATELLITES[prn]

        # Nominal (Kepler tabanlı) konum
        nx, ny, nz = get_satellite_position(raan_deg=raan_deg, mean_anomaly_deg=m0_deg)

        # SP3 gerçek konum (varsa — ECEF km)
        sp3_entry = next((e for e in SP3_DATA if e["id"] == prn), None)
        sp3_pos = None
        if sp3_entry:
            sp3_pos = {
                "x_km": sp3_entry["x"],
                "y_km": sp3_entry["y"],
                "z_km": sp3_entry["z"],
                "time": sp3_entry["time"].isoformat()
            }

        plane_letters = ["A", "B", "C", "D", "E", "F"]
        plane_raans   = [0, 60, 120, 180, 240, 300]
        plane_letter  = plane_letters[plane_raans.index(raan_deg)] if raan_deg in plane_raans else "?"

        from visualizer.plot_3d_orbit import PLANE_COLORS
        result.append({
            "prn": prn,
            "plane": plane_letter,
            "raan_deg": raan_deg,
            "inclination_deg": GPS_I_DEG,
            "color": PLANE_COLORS.get(raan_deg, "#ffffff"),
            "nominal_position_km": {"x": nx, "y": ny, "z": nz},
            "sp3_position": sp3_pos
        })

    return {
        "status": "success",
        "count": len(result),
        "satellites": result
    }


# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# SKYPLOT — Her uydu için tam gün Az/El ark verisi
# ═══════════════════════════════════════════════════════════════════════════

# Bilinen IGS referans istasyonları (Türkiye ve çevresi)
IGS_STATIONS = {
    "ANKR": {"lat": 39.887472, "lon": 32.758667, "h": 975.0,  "city": "Ankara"},
    "ISTA": {"lat": 41.104722, "lon": 29.020833, "h": 174.0,  "city": "Istanbul"},
    "TUBI": {"lat": 40.786944, "lon": 31.374167, "h": 1005.0, "city": "Gebze"},
    "IZMI": {"lat": 38.394722, "lon": 27.075833, "h": 117.0,  "city": "Izmir"},
    "ERZR": {"lat": 39.901944, "lon": 41.277222, "h": 1868.0, "city": "Erzurum"},
}

@app.get("/api/skyplot")
def get_skyplot_arcs(
    sats: str = "G01",
    station: str = "ANKR",
    lat: float = None,
    lon: float = None,
    h: float = None
):
    """
    Seçili uydular için tüm SP3 epoch'larında azimut/elevasyon arkını döndürür.
    Yalnızca el > 0° (ufkun üstü) noktaları dahil edilir.

    Parametreler
    ------------
    sats    : Virgülle ayrılmış PRN listesi  (örn. "G01,G09,G12")
    station : IGS istasyon kodu              (ANKR, ISTA, TUBI, IZMI, ERZR)
    lat/lon/h: Özel koordinat (station yerine)
    """
    selected = [s.strip().upper() for s in sats.split(",")]

    # İstasyon koordinatlarını belirle
    if lat is not None and lon is not None:
        sta_lat, sta_lon, sta_h = lat, lon, (h or 100.0)
        sta_name = f"CUSTOM ({lat:.3f}°N, {lon:.3f}°E)"
        sta_city = "Custom"
    elif station.upper() in IGS_STATIONS:
        s = IGS_STATIONS[station.upper()]
        sta_lat, sta_lon, sta_h = s["lat"], s["lon"], s["h"]
        sta_name = station.upper()
        sta_city = s["city"]
    else:
        # Fallback: ANKR
        s = IGS_STATIONS["ANKR"]
        sta_lat, sta_lon, sta_h = s["lat"], s["lon"], s["h"]
        sta_name = "ANKR"
        sta_city = s["city"]

    arcs = []
    for sat_id in selected:
        coords = [e for e in SP3_DATA if e["id"] == sat_id]
        if not coords:
            continue

        arc_pts = []
        prev_visible = False
        segment = []

        for c in coords:
            az, el, dist = ecef_to_topocentric(
                c["x"], c["y"], c["z"],
                sta_lat, sta_lon, sta_h
            )
            visible = el > 0.0

            if visible:
                segment.append({
                    "az": round(az, 2),
                    "el": round(el, 2),
                    "t":  c["time"].strftime("%H:%M")
                })
            else:
                if segment:
                    arc_pts.append(segment)   # ufkun altına inince segmenti kapat
                    segment = []

        if segment:
            arc_pts.append(segment)           # gün sonu kalan segment

        if arc_pts:
            arcs.append({
                "id":       sat_id,
                "segments": arc_pts           # birden fazla geçiş olabilir
            })

    return {
        "status": "success",
        "station": {
            "name": sta_name,
            "city": sta_city,
            "lat":  sta_lat,
            "lon":  sta_lon,
            "h":    sta_h
        },
        "arcs": arcs,
        "available_stations": list(IGS_STATIONS.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)