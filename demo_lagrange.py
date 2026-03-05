import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import lagrange
from src.utils.read_sp3 import read_sp3  # Sizin kendi modülünüzü kullanıyoruz

def demo_interpolation():
    # 1. Dosya Yolu (Sizin projenizdeki yol)
    sp3_path = os.path.join("data", "COD0MGXFIN_20240600000_01D_05M_ORB.SP3")
    
    # 2. Veriyi Oku (Sizin fonksiyonunuzla)
    print("Veri okunuyor...")
    data = read_sp3(sp3_path)
    
    # 3. Sadece bir uydunun (Örn: G01) ilk 10 verisini al (Örneklem)
    target_sat = "G01"
    sat_data = [d for d in data if d['id'] == target_sat][:10] # İlk 10 nokta
    
    # Zaman (epoch) ve X koordinatını alalım (Basitlik için sadece X ekseni)
    # SP3 verisinde zaman direkt yoksa, indexi zaman gibi kabul edelim (0, 15, 30...)
    times_known = np.array([i * 15 for i in range(len(sat_data))]) # Dakika cinsinden
    x_coords = np.array([d['x'] for d in sat_data])
    
    # 4. Lagrange Enterpolasyonu (Scipy ile prototip)
    # Raporun "Design" kısmında bu matematiği kullanacağımızı iddia ediyoruz.
    poly = lagrange(times_known, x_coords)
    
    # 5. Ara değerleri üret (Dakika dakika)
    times_new = np.linspace(min(times_known), max(times_known), 200)
    x_new = poly(times_new)
    
    # 6. Çizim (Profesyonel Görünüm)
    plt.figure(figsize=(10, 6))
    
    # Gerçek SP3 noktaları
    plt.plot(times_known, x_coords, 'ro', label='SP3 Known Epochs (15 min intervals)', markersize=8, zorder=5)
    
    # Enterpolasyon Eğrisi
    plt.plot(times_new, x_new, 'b--', label='Lagrange Interpolated Trajectory (Designed)', linewidth=2)
    
    plt.title(f'Visualization of Interpolation Logic (Sat: {target_sat})')
    plt.xlabel('Time (minutes from start)')
    plt.ylabel('ECEF X Coordinate (km)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.6)
    
    # Kaydet
    plt.savefig('lagrange_prototype_output.png', dpi=300)
    print("Grafik 'lagrange_prototype_output.png' olarak kaydedildi.")
    plt.show()

if __name__ == "__main__":
    demo_interpolation()