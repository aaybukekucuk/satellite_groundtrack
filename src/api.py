from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Bulunduğumuz dizini (src) ve ana dizini dinamik olarak alıyoruz
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

# utils klasörüne erişim sağlamak için
sys.path.append(BASE_DIR)

from utils.read_sp3 import read_sp3
from utils.read_nav import read_nav_kepler
from utils.ecef_to_geodetic import ecef_to_geodetic

app = FastAPI(title="Satellite API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Eğer static klasörü yanlışlıkla silinirse veya yoksa, hata vermemesi için otomatik oluştursun
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    print(f"⚠️ Uyarı: '{STATIC_DIR}' klasörü yoktu, otomatik oluşturuldu. Lütfen index.html dosyasını içine koyun.")

# Artık 'static' kelimesi yerine dinamik ve kesin olan STATIC_DIR yolunu kullanıyoruz
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

SP3_DATA = []
KEPLER_DATA = {}

@app.on_event("startup")
def load_data():
    global SP3_DATA, KEPLER_DATA
    print("⏳ API Başlatılıyor... Veriler yükleniyor...")
    
    # Veri yollarını da ana dizindeki data klasörüne tam isabetle yönlendiriyoruz
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
    """Ana sayfaya girildiğinde tam yolu belirtilen index.html dosyasını gösterir."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        return {"hata": "index.html dosyasi static klasorunde bulunamadi!"}
    return FileResponse(index_path)

@app.get("/api/satellites")
def get_satellites(sats: str = "G01,G02"):
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
        response_data.append({
            "id": sat_id,
            "track": track_points,
            "kepler": kepler,
            "current_pos": track_points[0] if track_points else None
        })
        
    return {"status": "success", "data": response_data}