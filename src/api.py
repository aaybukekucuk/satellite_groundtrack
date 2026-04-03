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
            
        kepler_list = KEPLER_DATA.get(sat_id, [])
        kepler = kepler_list[0] if kepler_list else {} # UI için ilk parametreyi al
        
        vel_kms = 0.0
        if len(coords) >= 2:
            p1, p2 = coords[0], coords[1]
            dt = (p2["time"] - p1["time"]).total_seconds()
            if dt > 0:
                vx = (p2["x"] - p1["x"]) * 1000 / dt 
                vy = (p2["y"] - p1["y"]) * 1000 / dt 
                vz = (p2["z"] - p1["z"]) * 1000 / dt 
                vel_kms = math.sqrt(vx**2 + vy**2 + vz**2) / 1000.0
        
        c0 = coords[0]
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
        
        # 1. SP3'ten gelen KÜTLE MERKEZİ (CoM) ECEF konumu ve Hızı
        pos_com = [coords[i]['x'] * 1000.0, coords[i]['y'] * 1000.0, coords[i]['z'] * 1000.0]
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)