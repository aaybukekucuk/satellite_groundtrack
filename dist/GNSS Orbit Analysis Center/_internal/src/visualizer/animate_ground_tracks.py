import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.animation import FuncAnimation
import numpy as np

def fix_wrap_around(lons, lats):
    """Animasyon sırasında boylam yırtılmalarını engeller."""
    clean_lons, clean_lats = [], []
    for i in range(len(lons)):
        if i > 0 and abs(lons[i] - lons[i-1]) > 180:
            clean_lons.append(np.nan)
            clean_lats.append(np.nan)
        clean_lons.append(lons[i])
        clean_lats.append(lats[i])
    return clean_lons, clean_lats

def animate_ground_tracks(satellites_data):
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='azure')
    ax.coastlines(linewidth=0.8)
    ax.gridlines(draw_labels=True, linestyle='--', alpha=0.5)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)

    colors = plt.colormaps.get_cmap('tab10')
    lines, points = {}, {}

    # En uzun veri setinin uzunluğunu bul (animasyonun kaç kare süreceğini belirlemek için)
    max_frames = max([len(v) for v in satellites_data.values()])

    # Her uydu için çizgi ve nokta objesi oluştur
    for i, (sat_id, coords) in enumerate(satellites_data.items()):
        if isinstance(coords[0], dict):
            lats = [c['lat'] for c in coords if 'lat' in c and 'lon' in c]
            lons = [c['lon'] for c in coords if 'lat' in c and 'lon' in c]
        else:
            lats = [c[0] for c in coords]
            lons = [c[1] for c in coords]

        # Yırtılma düzeltmesini uygula
        clean_lons, clean_lats = fix_wrap_around(lons, lats)
        
        # transform=ccrs.PlateCarree() EKLENMESİ ZORUNLUDUR!
        line, = ax.plot([], [], label=sat_id, color=colors(i % 10), transform=ccrs.PlateCarree(), linewidth=2)
        point, = ax.plot([], [], 'o', color=colors(i % 10), markersize=6, transform=ccrs.PlateCarree())
        
        lines[sat_id] = {'line': line, 'lons': clean_lons, 'lats': clean_lats}
        points[sat_id] = point

    def init():
        for item in lines.values():
            item['line'].set_data([], [])
        for point in points.values():
            point.set_data([], [])
        return [item['line'] for item in lines.values()] + list(points.values())

    def update(frame):
        for sat_id, item in lines.items():
            lons, lats = item['lons'], item['lats']
            
            # Eğer uydunun verisi bittiyse hata vermemesi için kontrol
            if frame < len(lons):
                item['line'].set_data(lons[:frame], lats[:frame])
                # Liste formatında veri vermek zorunludur: [lons[frame]]
                points[sat_id].set_data([lons[frame]], [lats[frame]]) 
                
        return [item['line'] for item in lines.values()] + list(points.values())

    # blit=False yapıldı çünkü Cartopy ile animasyonlarda arka plan çakışması yapabiliyor
    ani = FuncAnimation(fig, update, frames=max_frames, init_func=init, interval=50, blit=False, repeat=True)

    # Lejantı haritanın dışına, sağ üst köşeye alalım
    plt.legend(loc='upper right', bbox_to_anchor=(1.15, 1.0))
    plt.title("Animasyonlu Uydu Yörüngeleri - Ground Tracks", fontsize=14, fontweight='bold', pad=15)
    plt.tight_layout()
    plt.show()