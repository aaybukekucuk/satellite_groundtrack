import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.read_sp3 import read_sp3
from utils.read_nav import read_nav
from utils.ecef_to_geodetic import ecef_to_geodetic
from visualizer.plot_ground_tracks import plot_ground_tracks
from visualizer.animate_ground_tracks import animate_ground_tracks


def get_multi_satellite_positions(selected_sats, sp3_data):
    """Seçilen uyduların SP3 verilerini filtreler."""
    sat_positions = {}
    for sat_id in selected_sats:
        coords = [entry for entry in sp3_data if entry["id"] == sat_id]
        sat_positions[sat_id] = coords
    return sat_positions


def main():
    print("🚀 Satellite Ground Track Visualizer başlatılıyor...")

    # Veri yolları
    sp3_path = os.path.join("data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    nav_path = os.path.join("data", "BRDC00IGS_R_20240600000_01D_MN.rnx")

    # SP3 ve NAV verilerini oku
    print("SP3 ve NAV dosyaları okunuyor...")
    sp3_data = read_sp3(sp3_path)
    nav_data = read_nav(nav_path)
    print(f"SP3 verileri: {len(sp3_data)}")
    print(f"NAV verileri: {len(nav_data)}")

    # Mevcut SP3 dosyasındaki tüm uydu ID'lerini listele
    satellites = sorted(set([sat["id"] for sat in sp3_data]))
    print("\nMevcut uydular:")
    print(", ".join(satellites))

    # Kullanıcıdan birden fazla uydu seçmesini iste
    selected = input("\nLütfen görüntülemek istediğiniz uyduların ID’lerini virgülle ayırarak girin (örnek: G01,G02,G05): ")
    selected_sats = [s.strip().upper() for s in selected.split(",") if s.strip().upper() in satellites]

    if not selected_sats:
        print("⚠️ Geçerli bir uydu ID’si girilmedi. Varsayılan olarak G01 seçildi.")
        selected_sats = ["G01"]

    # Seçilen uyduların verilerini filtrele
    multi_data = get_multi_satellite_positions(selected_sats, sp3_data)

    # ECEF -> Lat/Lon dönüşümü
    for sat_id, coords in multi_data.items():
        for entry in coords:
            lat, lon, h = ecef_to_geodetic(entry["x"], entry["y"], entry["z"])
            entry["lat"] = lat
            entry["lon"] = lon
            entry["h"] = h

    # ✅ Koordinat aralıklarını yazdır
    print("\n📊 Uydu koordinat aralıkları:")
    for sat_id, coords in multi_data.items():
        lats = [c["lat"] for c in coords]
        lons = [c["lon"] for c in coords]
        print(f"{sat_id} -> Lat range: {min(lats):.2f} to {max(lats):.2f}, Lon range: {min(lons):.2f} to {max(lons):.2f}")

    # Her uydunun konum sayısını ekrana yaz
    print("\n📈 Konum sayıları:")
    for sat, data in multi_data.items():
        print(f"{sat}: {len(data)} positions")

    # Ground track çizimi
    animate_ground_tracks(multi_data)
    plot_ground_tracks(multi_data)


if __name__ == "__main__":
    main()