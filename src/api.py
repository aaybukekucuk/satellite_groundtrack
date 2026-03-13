from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import math

# Dosya yollarını dinamik ve kusursuz yapmak için (Pathing)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# utils klasörüne erişim sağlamak için (ÖNCE YOLU TANITIYORUZ)
sys.path.append(BASE_DIR)

# ŞİMDİ UTILS İÇİNDEKİLERİ İMPORT EDEBİLİRİZ:
from utils.read_sp3 import read_sp3
from utils.read_nav import read_nav_kepler
from utils.ecef_to_geodetic import ecef_to_geodetic
from utils.topocentric import ecef_to_topocentric
from utils.state_to_kepler import calculate_kepler_from_state
from utils.compare_kepler import analyze_kepler_errors # <--- DOĞRU YERİ BURASI

app = FastAPI(title="OrbitalViz API | Multi-GNSS Ground Track Visualization")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    print(f"⚠️ Uyarı: '{STATIC_DIR}' klasörü yoktu, otomatik oluşturuldu.")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SP3_DATA = []
KEPLER_DATA = {}
STATION = {
    "lat": 39.866,
    "lon": 32.736,
    "h": 100.0  
}

@app.on_event("startup")
def load_data():
    global SP3_DATA, KEPLER_DATA
    print("⏳ API Startup: Loading SP3 and Broadcast Verileri...")
    
    root_dir = os.path.dirname(BASE_DIR)
    sp3_path = os.path.join(root_dir, "data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    nav_path = os.path.join(root_dir, "data", "BRDC00IGS_R_20240600000_01D_MN.rnx")
    
    if os.path.exists(sp3_path):
        SP3_DATA = read_sp3(sp3_path)
    if os.path.exists(nav_path):
        KEPLER_DATA = read_nav_kepler(nav_path)
    print("✅ Veriler API'ye yüklendi!")

@app.get("/")
def serve_home():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"hata": "index.html static klasorunde bulunamadi!"}
    return FileResponse(index_path)

@app.get("/api/satellites")
def get_satellites(sats: str = "G01"):
    selected = [s.strip().upper() for s in sats.split(",")]
    response_data = []
    
    for sat_id in selected:
        coords = [entry for entry in SP3_DATA if entry["id"] == sat_id]
        if not coords:
            continue
            
        track_points = []
        for c in coords:
            lat, lon, h = ecef_to_geodetic(c["x"], c["y"], c["z"])
            track_points.append({"lat": lat, "lon": lon, "alt": h, "time": c["time"].isoformat()})
            
        kepler = KEPLER_DATA.get(sat_id, {})
        instant_data = None
        vel_kms = 0.0
        
        # --- 3 BOYUTLU VEKTÖR MATEMATİĞİ VE KEPLER ÜRETİMİ ---
        if len(coords) >= 2:
            p1 = coords[0]
            p2 = coords[1]
            dt = (p2["time"] - p1["time"]).total_seconds()
            
            if dt > 0:
                # DÜZELTME: SP3 verisi KM ise METRE'ye çeviriyoruz (* 1000)
                # Formüllerin çökmemesi için bu şart!
                rx1, ry1, rz1 = p1["x"] * 1000, p1["y"] * 1000, p1["z"] * 1000
                rx2, ry2, rz2 = p2["x"] * 1000, p2["y"] * 1000, p2["z"] * 1000
                
                vx = (rx2 - rx1) / dt # m/s
                vy = (ry2 - ry1) / dt # m/s
                vz = (rz2 - rz1) / dt # m/s
                
                # Arayüz için km/s'ye geri çevir
                vel_kms = math.sqrt(vx**2 + vy**2 + vz**2) / 1000.0
                
                if not kepler:
                    r_vec = [rx1, ry1, rz1]
                    v_vec = [vx, vy, vz]
                    try:
                        # GLONASS ve Galileo için Kepler parametrelerini kitaptaki fonksiyonla üret
                        kepler = calculate_kepler_from_state(r_vec, v_vec)
                    except Exception as e:
                        print(f"Kepler hesaplama hatası ({sat_id}): {e}")
        
        if coords:
            c0 = coords[0]
            az, el, dist = ecef_to_topocentric(
                c0["x"], c0["y"], c0["z"], 
                STATION["lat"], STATION["lon"], STATION["h"]
            )
            
            instant_data = {
                "velocity_kms": vel_kms,
                "topocentric": {
                    "azimuth": az,
                    "elevation": el,
                    "distance_m": dist
                }
            }

        response_data.append({
            "id": sat_id,
            "track": track_points,
            "kepler": kepler,
            "instant_data": instant_data
        })
        
    return {"status": "success", "data": response_data}

# Yeni yazdığımız analiz modülünü en üste import etmeyi unutma:
# from utils.compare_kepler import analyze_kepler_errors

@app.get("/api/analysis")
def get_kepler_analysis(sat: str = "G01"):
    """
    SP3 ve Broadcast verilerini karşılaştırarak,
    arayüzdeki hata grafikleri (Error Charts) için zaman serisi datası yollar.
    """
    sat_id = sat.strip().upper()
    
    # İlgili uydunun SP3 noktalarını filtrele
    coords = [entry for entry in SP3_DATA if entry["id"] == sat_id]
    
    # Uydunun RINEX (Broadcast) Kepler verisini al
    brdc_kepler = KEPLER_DATA.get(sat_id, {})
    
    if not coords or not brdc_kepler:
        return {"status": "error", "message": f"{sat_id} için yeterli SP3 veya Broadcast verisi bulunamadı. Lütfen bir GPS uydusu seçin."}
    
    # Fonksiyonumuzu çağırıp Günlük Hata Serisini üretiyoruz
    error_series = analyze_kepler_errors(coords, brdc_kepler)
    
    return {"status": "success", "sat_id": sat_id, "analysis": error_series}