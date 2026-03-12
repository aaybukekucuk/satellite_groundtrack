from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Dosya yollarını dinamik ve kusursuz yapmak için (Pathing)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# utils klasörüne erişim sağlamak için
sys.path.append(BASE_DIR)

from utils.read_sp3 import read_sp3
from utils.read_nav import read_nav_kepler
from utils.ecef_to_geodetic import ecef_to_geodetic
# Önceki adımlarda yazdığımız Live Tracking özelliklerini entegre ediyoruz
from utils.velocity import calculate_orbital_velocity
from utils.topocentric import ecef_to_topocentric

app = FastAPI(title="OrbitalViz API | GNSS Ground Track Visualization")

# Güvenlik ve Arayüzle Haberleşme İzni (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static klasörü yoksa otomatik oluşturur (hata almamak için)
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    print(f"⚠️ Uyarı: '{STATIC_DIR}' klasörü yoktu, otomatik oluşturuldu. index.html'i içine koyun.")

# Arayüz dosyalarını sunma (Static Files serving)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Bellek önbelleği (Hızlı yanıt için)
SP3_DATA = []
KEPLER_DATA = {}

# Varsayılan Gözlem İstasyonu (Örn: Hacettepe Üniversitesi, Ankara)
# Toposentrik (Az/El) hesaplama bu noktaya göre yapılır
STATION = {
    "lat": 39.866,
    "lon": 32.736,
    "h": 100.0  # Elipsoid yüksekliği (m)
}

@app.on_event("startup")
def load_data():
    """Sunucu başlarken verileri sadece bir kere belleğe yükler."""
    global SP3_DATA, KEPLER_DATA
    print("⏳ API Startup: Loading SP3 and Broadcast Verileri...")
    
    # Ana dizindeki 'data' klasörüne tam isabetle yönlendirme
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
    """Yenilenen profesyonel Web Arayüzünü gösterir."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"hata": "index.html static klasorunde bulunamadi!"}
    return FileResponse(index_path)

@app.get("/api/satellites")
def get_satellites(sats: str = "G01,G02"):
    """
    Arayüzün veri istediği ana endpoint. Hem yörünge yollarını (track)
    hem de anlık teknik verileri (Hız, Az/El vb.) hesaplayıp gönderir.
    """
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
        
        # --- ANLIK TEKNİK VERİLERİ HESAPLAMA (DASHBOARD İÇİN) ---
        instant_data = None
        if coords:
            # Uydunun o anki (ilk epoch) konumunu baz alıyoruz
            current_epoch = coords[0] 
            
            # 1. Uzay Hızı Hesaplama (km/s) (Vis-viva ile)
            vel_kms = 0.0
            if kepler:
                a_meters = kepler["A (Yarı Büyük Eksen) [m]"]
                vel_kms = calculate_orbital_velocity(current_epoch["x"], current_epoch["y"], current_epoch["z"], a_meters)
            
            # 2. Toposentrik Dönüşüm (Azimut, Elevasyon)
            az, el, dist = ecef_to_topocentric(
                current_epoch["x"], current_epoch["y"], current_epoch["z"], 
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
            "instant_data": instant_data # Dinamik yörünge verileri
        })
        
    return {"status": "success", "data": response_data}