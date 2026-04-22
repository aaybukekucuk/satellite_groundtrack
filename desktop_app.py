import sys
import os
import webview
import threading
import uvicorn
import time
import traceback

# --- HATA YAKALAYICI EKLENDİ ---
# Tüm çıktıları ve gizli hataları bir metin dosyasına yazdırıyoruz
# Böylece uygulama çökse bile neden çöktüğünü okuyabileceğiz!
log_dosyasi = open("hata_kaydi.txt", "w", encoding="utf-8")
sys.stdout = log_dosyasi
sys.stderr = log_dosyasi

print("🚀 Masaüstü Uygulaması Başlatılıyor...")

try:
    from src.api import app 
    print("✅ src.api başarıyla içe aktarıldı!")
except Exception as e:
    print("❌ API içe aktarılırken KRİTİK HATA:")
    traceback.print_exc()

def run_server():
    try:
        print("🌐 Uvicorn (FastAPI) sunucusu başlatılıyor...")
        # log_level="debug" yaparak uvicorn'un her adımını yazdırıyoruz
        uvicorn.run(app, host="127.0.0.1", port=8585, log_level="debug")
    except Exception as e:
        print("❌ Sunucu çalışırken HATA:")
        traceback.print_exc()

def main():
    # Sunucuyu başlat
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    
    print("⏳ Sunucunun ayağa kalkması ve verileri (SP3 vs) okuması için 8 saniye bekleniyor...")
    time.sleep(8) 

    print("🖥️ Pencere arayüzü çağrılıyor...")
    try:
        window = webview.create_window(
            title='GNSS Orbit Analysis Center', 
            url='http://127.0.0.1:8585',
            width=1280,
            height=800,
            min_size=(1024, 768)
        )
        webview.start()
    except Exception as e:
        print("❌ Pencere açılırken HATA:")
        traceback.print_exc()

if __name__ == '__main__':
    main()