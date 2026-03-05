import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def fix_wrap_around(lons, lats):
    """
    Boylam yırtılması (wrap-around) sorununu çözer.
    Ardışık iki nokta arasındaki boylam farkı 180 dereceden büyükse,
    araya 'NaN' (Not a Number) koyarak çizginin haritayı kesmesini engeller.
    """
    clean_lons, clean_lats = [], []
    for i in range(len(lons)):
        # Eğer bir önceki nokta ile boylam farkı çok büyükse (uydu haritanın diğer ucuna geçmişse)
        if i > 0 and abs(lons[i] - lons[i-1]) > 180:
            clean_lons.append(np.nan)
            clean_lats.append(np.nan)
            
        clean_lons.append(lons[i])
        clean_lats.append(lats[i])
        
    return clean_lons, clean_lats

def plot_ground_tracks(satellites_data):
    # Plate Carree (Coğrafi/Eşdikdörtgensel) projeksiyonu kullanıyoruz (WGS84'e en uygun standart)
    fig = plt.figure(figsize=(12, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Harita altlık özelliklerini ekleyelim (Kıyılar, Ülke sınırları, Okyanuslar)
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='azure')
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    # Harita sınırlarını tam dünya olarak belirle (-180 ile +180 boylam, -90 ile +90 enlem)
    ax.set_global()

    # Grid (Ağ) çizgilerini ve eksen etiketlerini ekle
    gl = ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False

    print(f"Haritaya çizilecek toplam uydu sayısı: {len(satellites_data)}")

    for sat_id, coords in satellites_data.items():
        if len(coords) == 0:
            continue

        # Veriyi çek
        if isinstance(coords[0], dict):
            lats = [c['lat'] for c in coords if 'lat' in c and 'lon' in c]
            lons = [c['lon'] for c in coords if 'lat' in c and 'lon' in c]
        else:
            lats = [c[0] for c in coords]
            lons = [c[1] for c in coords]

        # Yırtılma sorununu çözmek için filtreden geçir
        clean_lons, clean_lats = fix_wrap_around(lons, lats)

        # Dönüştürülmüş (temizlenmiş) veriyi çiz (transform=ccrs.PlateCarree() çok önemlidir!)
        ax.plot(clean_lons, clean_lats, label=sat_id, transform=ccrs.PlateCarree(), linewidth=2)
        
        # Uydunun yörüngesindeki İLK noktanın yerini belli etmek için bir işaretçi (marker) koyalım
        ax.plot(clean_lons[0], clean_lats[0], marker='o', markersize=5, transform=ccrs.PlateCarree(), color='red')

    plt.title("GPS Uyduları Ground Track (Yer İzi) Analizi - WGS84", fontsize=14, fontweight='bold', pad=15)
    
    # Sağ üstte lejant (hangi renk hangi uydu)
    plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1.0))
    plt.tight_layout()
    plt.show()