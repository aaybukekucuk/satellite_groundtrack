import os
import sys
from datetime import timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.read_sp3 import read_sp3
from utils.read_nav import read_nav
from utils.ecef_to_geodetic import ecef_to_geodetic
from utils.interpolation import lagrange_interpolate
from visualizer.plot_ground_tracks import plot_ground_tracks
from visualizer.animate_ground_tracks import animate_ground_tracks

def get_multi_satellite_positions(selected_sats, sp3_data):
    sat_positions = {}
    for sat_id in selected_sats:
        coords = [entry for entry in sp3_data if entry["id"] == sat_id]
        if coords:
            sat_positions[sat_id] = coords
    return sat_positions

def densify_satellite_data(sat_positions, interval_minutes=1):
    """Aralıklı SP3 verilerini Lagrange interpolasyonu ile istenilen dakikaya sıklaştırır."""
    dense_positions = {}
    for sat_id, coords in sat_positions.items():
        print(f"🔄 {sat_id} uydusu için Lagrange interpolasyonu hesaplanıyor (1 dakikalık aralıklarla)...")
        if len(coords) < 10:
            dense_positions[sat_id] = coords
            continue
        
        times = [c["time"] for c in coords]
        xs = [c["x"] for c in coords]
        ys = [c["y"] for c in coords]
        zs = [c["z"] for c in coords]
        
        start_time = times[0]
        end_time = times[-1]
        
        current_time = start_time
        dense_coords = []
        
        while current_time <= end_time:
            interp_x = lagrange_interpolate(current_time, times, xs, order=9)
            interp_y = lagrange_interpolate(current_time, times, ys, order=9)
            interp_z = lagrange_interpolate(current_time, times, zs, order=9)
            
            dense_coords.append({
                "id": sat_id,
                "x": interp_x,
                "y": interp_y,
                "z": interp_z,
                "time": current_time
            })
            current_time += timedelta(minutes=interval_minutes)
            
        dense_positions[sat_id] = dense_coords
        print(f"✅ {sat_id}: {len(coords)} nokta -> {len(dense_coords)} noktaya çıkarıldı.")
        
    return dense_positions

def main():
    print("🚀 Satellite Ground Track Visualizer başlatılıyor...")

    sp3_path = os.path.join("data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    nav_path = os.path.join("data", "BRDC00IGS_R_20240600000_01D_MN.rnx")

    print("📂 SP3 ve NAV dosyaları okunuyor...")
    sp3_data = read_sp3(sp3_path)
    # nav_data = read_nav(nav_path) # İleride parser yazana kadar şimdilik atlıyoruz

    satellites = sorted(set([sat["id"] for sat in sp3_data]))
    print(f"\n🌍 {len(satellites)} farklı uydu bulundu.")

    selected = input("\n🛰️ Lütfen uyduların ID’lerini virgülle ayırarak girin (örnek: G01,G05): ")
    selected_sats = [s.strip().upper() for s in selected.split(",") if s.strip().upper() in satellites]

    if not selected_sats:
        print("⚠️ Geçerli bir uydu ID’si girilmedi. Varsayılan olarak G01 seçildi.")
        selected_sats = ["G01"]

    # 1. Ham veriyi al
    multi_data = get_multi_satellite_positions(selected_sats, sp3_data)

    # 2. Veriyi İnterpolasyon ile Sıklaştır (Gerçek Jeodezik Adım)
    dense_multi_data = densify_satellite_data(multi_data, interval_minutes=1)

    # 3. Yoğunlaştırılmış veriyi ECEF'ten Geodetic'e çevir
    print("\n🌍 ECEF -> Geodetic dönüşümü yapılıyor...")
    for sat_id, coords in dense_multi_data.items():
        for entry in coords:
            lat, lon, h = ecef_to_geodetic(entry["x"], entry["y"], entry["z"])
            entry["lat"] = lat
            entry["lon"] = lon

    # 4. Çizdir
    animate_ground_tracks(dense_multi_data)
    plot_ground_tracks(dense_multi_data)

if __name__ == "__main__":
    main()