import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

import os
import sys
import warnings
from datetime import timedelta

# Gereksiz kütüphane uyarılarını gizler
warnings.filterwarnings("ignore", category=RuntimeWarning)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.read_sp3 import read_sp3
from utils.ecef_to_geodetic import ecef_to_geodetic
from utils.interpolation import lagrange_interpolate
from utils.topocentric import ecef_to_topocentric
from utils.read_nav import read_nav_kepler
from utils.velocity import calculate_orbital_velocity
from utils.velocity import calculate_orbital_velocity, calculate_sp3_velocity_from_positions
from utils.rtn_transform import ecef_to_rtn_error
from utils.satpos_utils import calculate_satpos_from_kepler

from visualizer.plot_ground_tracks import plot_ground_tracks
from visualizer.animate_ground_tracks import animate_ground_tracks
from visualizer.interactive_map import select_station_on_map
from visualizer.skyplot import plot_skyplot

def get_multi_satellite_positions(selected_sats, sp3_data):
    sat_positions = {}
    for sat_id in selected_sats:
        coords = [entry for entry in sp3_data if entry["id"] == sat_id]
        if coords:
            sat_positions[sat_id] = coords
    return sat_positions

def densify_satellite_data(sat_positions, interval_minutes=1):
    dense_positions = {}
    for sat_id, coords in sat_positions.items():
        if len(coords) < 10:
            dense_positions[sat_id] = coords
            continue
        
        times = [c["time"] for c in coords]
        xs, ys, zs = [c["x"] for c in coords], [c["y"] for c in coords], [c["z"] for c in coords]
        
        current_time = times[0]
        end_time = times[-1]
        dense_coords = []
        
        while current_time <= end_time:
            interp_x = lagrange_interpolate(current_time, times, xs, order=9)
            interp_y = lagrange_interpolate(current_time, times, ys, order=9)
            interp_z = lagrange_interpolate(current_time, times, zs, order=9)
            
            dense_coords.append({
                "id": sat_id, "x": interp_x, "y": interp_y, "z": interp_z, "time": current_time
            })
            current_time += timedelta(minutes=interval_minutes)
            
        dense_positions[sat_id] = dense_coords
        
    return dense_positions

def main():
    print("🚀 Satellite Ground Track & Sky Plot Visualizer")

    sp3_path = os.path.join("data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    sp3_data = read_sp3(sp3_path)
    # YENİ: NAV (Broadcast) verilerinden Kepler Parametrelerini okuma
    nav_path = os.path.join("data", "BRDC00IGS_R_20240600000_01D_MN.rnx")
    kepler_veri = read_nav_kepler(nav_path)
    satellites = sorted(set([sat["id"] for sat in sp3_data]))

    # Test etmek için tüm uyduları görmek istiyorsanız doğrudan çok sayıda ID girebilirsiniz (ör: G01,G05,G10,E02,E05)
    selected = input(f"🛰️ Lütfen virgülle uydu ID’si girin (G01,G05 vb.): ")
    selected_sats = [s.strip().upper() for s in selected.split(",") if s.strip().upper() in satellites]
    print("\n" + "="*70)
    print("🛰️ SEÇİLEN UYDULARIN KEPLER (YÖRÜNGE) PARAMETRELERİ (BRDC)")
    print("="*70)
    for sat in selected_sats:
        if sat in kepler_veri:
            k = kepler_veri[sat]
            print(f"Uydu: {sat}")
            print(f"  ➜ Dışmerkezlik (e)       : {k['e (Dışmerkezlik)']:.6f} (Tam daireye ne kadar yakın?)")
            print(f"  ➜ Yörünge Eğikliği (i0)  : {k['i0 (Yörünge Eğikliği)']:.6f} radyan")
            print(f"  ➜ Yarı Büyük Eksen (A)   : {k['A (Yarı Büyük Eksen) [m]']:,.2f} metre")
            print(f"  ➜ Yerberi Argümanı (w)   : {k['omega (Yerberi Argümanı)']:.6f} radyan")
            print("-" * 40)
        else:
            print(f"⚠️ {sat} uydusuna ait Kepler parametresi NAV dosyasında bulunamadı.")
    print("="*70 + "\n")

    if not selected_sats:
        selected_sats = ["G01", "G05", "G10"]

    multi_data = get_multi_satellite_positions(selected_sats, sp3_data)
    dense_multi_data = densify_satellite_data(multi_data, interval_minutes=1)

# --- YENİ EKLENEN RTN HATA ANALİZİ BÖLÜMÜ ---
    print("\n" + "="*70)
    print("📈 SP3 ve BROADCAST VERİLERİ İÇİN RTN HATA ANALİZİ HESAPLANIYOR")
    print("="*70)
    
    for sat_id, coords in dense_multi_data.items():
        if len(coords) < 3: continue
            
        # 1. SP3 için Hızları Hesapla (Sayısal Türev)
        sp3_velocities = calculate_sp3_velocity_from_positions(coords)
        
        # Referans Zamanı (t_zero) al (dt_seconds hesaplamak için)
        t_zero = coords[0]['time']
        
        print(f"\nUydu: {sat_id} (İlk 5 Epoch Örneği)")
        print(f"{'Zaman':<20} | {'Radial (m)':<12} | {'Along-track (m)':<15} | {'Cross-track (m)':<15}")
        print("-" * 70)
        
        # İlk 5 epoch'u ekrana basalım
        for i in range(min(5, len(coords))):
            t_epoch = coords[i]['time']
            dt_seconds = (t_epoch - t_zero).total_seconds()
            
            # SP3 Konum (Metre) ve Hız (m/s) Vektörleri
            pos_ref = [coords[i]['x'] * 1000.0, coords[i]['y'] * 1000.0, coords[i]['z'] * 1000.0]
            vel_ref = [sp3_velocities[i]['vx'], sp3_velocities[i]['vy'], sp3_velocities[i]['vz']]
            
            # BROADCAST ECEF KOORDİNATLARINI HESAPLA (YENİ FONKSİYON İLE)
            pos_brdc = [0.0, 0.0, 0.0]
            if sat_id in kepler_veri:
                pos_brdc = calculate_satpos_from_kepler(kepler_veri[sat_id], dt_seconds)
            
            # Eğer Broadcast verisi yoksa veya [0,0,0] döndüyse atla
            if pos_brdc == [0.0, 0.0, 0.0]:
                print(f"{t_epoch.strftime('%H:%M:%S'):<20} | HATA: Bu uydu için NAV verisi bulunamadı.")
                continue
                
            # RTN Dönüşümünü Yap
            rtn = ecef_to_rtn_error(pos_ref, vel_ref, pos_brdc)
            
            print(f"{t_epoch.strftime('%H:%M:%S'):<20} | {rtn['Radial (m)']:>10.3f} | {rtn['Along-track (m)']:>15.3f} | {rtn['Cross-track (m)']:>15.3f}")

    print("="*70 + "\n")
    
    for sat_id, coords in dense_multi_data.items():
        if len(coords) < 3: continue
            
        # 1. SP3 için Hızları Hesapla (Sayısal Türev)
        sp3_velocities = calculate_sp3_velocity_from_positions(coords)
        
        print(f"\nUydu: {sat_id} (İlk 3 Epoch Örneği)")
        print(f"{'Zaman':<20} | {'Radial (m)':<12} | {'Along-track (m)':<15} | {'Cross-track (m)':<15}")
        print("-" * 70)
        
        # Sadece örnek olsun diye ilk 3 epoch'u ekrana basalım
        for i in range(min(3, len(coords))):
            t_epoch = coords[i]['time']
            
            # SP3 Konum (Metre) ve Hız (m/s) Vektörleri
            pos_ref = [coords[i]['x'] * 1000.0, coords[i]['y'] * 1000.0, coords[i]['z'] * 1000.0]
            vel_ref = [sp3_velocities[i]['vx'], sp3_velocities[i]['vy'], sp3_velocities[i]['vz']]
            
            # NOT: Normalde burada Broadcast Kepler verisinden o anki (t_epoch) ECEF koordinatını 
            # hesaplayan fonksiyonunuzu çağırmalısınız. (Örn: satpos.py içindeki fonksiyon)
            # Şimdilik sistemin hata vermeden çalıştığını görmek için küçük bir sapma (gürültü) simüle ediyoruz.
            # İleride burası: pos_brdc = calculate_satpos(kepler_veri[sat_id], t_epoch) olacak.
            simulated_error_x = 2.5
            simulated_error_y = -1.2
            simulated_error_z = 3.8
            pos_brdc = [pos_ref[0] + simulated_error_x, pos_ref[1] + simulated_error_y, pos_ref[2] + simulated_error_z]
            
            # RTN Dönüşümünü Yap
            rtn = ecef_to_rtn_error(pos_ref, vel_ref, pos_brdc)
            
            print(f"{t_epoch.strftime('%H:%M:%S'):<20} | {rtn['Radial (m)']:>10.3f} | {rtn['Along-track (m)']:>15.3f} | {rtn['Cross-track (m)']:>15.3f}")

    print("="*70 + "\n")

    # --- YENİ EKLENEN SKY PLOT VE İSTASYON BÖLÜMÜ ---
    lat_sta, lon_sta = select_station_on_map()
    h_sta = 100.0 # İstasyon yüksekliği (100m varsayılan)

    visible_sats = []
    t_zero = None

    print("🔭 İstasyona göre Toposentrik koordinatlar ve Yörünge Hızı hesaplanıyor...")
    for sat_id, coords in dense_multi_data.items():
        if len(coords) > 0:
            first_epoch = coords[0] 
            if t_zero is None:
                t_zero = first_epoch["time"]
            
            # 1. Toposentrik Dönüşüm (Azimut, Elevasyon)
            az, el, dist = ecef_to_topocentric(
                first_epoch["x"], first_epoch["y"], first_epoch["z"], 
                lat_sta, lon_sta, h_sta
            )
            
            # 2. Vis-Viva Denklemi ile Hız Hesaplaması (YENİ EKLENEN KISIM)
            vel_kms = 0.0
            if sat_id in kepler_veri:
                a_meters = kepler_veri[sat_id]["A (Yarı Büyük Eksen) [m]"]
                vel_kms = calculate_orbital_velocity(first_epoch["x"], first_epoch["y"], first_epoch["z"], a_meters)
            
            # Tüm veriyi paketleyip grafik arayüzüne (Frontend) gönderiyoruz
            visible_sats.append({
                "id": sat_id, "az": az, "el": el, "vel": vel_kms
            })

    time_str = t_zero.strftime("%Y-%m-%d %H:%M:%S") if t_zero else "Bilinmiyor"
    
    # 1. Önce Sky Plot Gösterilir
    plot_skyplot(visible_sats, lat_sta, lon_sta, time_str)

    # 2. Sonra WGS84 Dönüşümü ve Harita Çizimleri Devam Eder
    print("🌍 ECEF -> Geodetic dönüşümü yapılıyor...")
    for sat_id, coords in dense_multi_data.items():
        for entry in coords:
            lat, lon, h = ecef_to_geodetic(entry["x"], entry["y"], entry["z"])
            entry["lat"], entry["lon"] = lat, lon

    animate_ground_tracks(dense_multi_data)
    plot_ground_tracks(dense_multi_data)

if __name__ == "__main__":
    main()