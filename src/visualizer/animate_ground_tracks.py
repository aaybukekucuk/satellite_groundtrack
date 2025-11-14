import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.animation import FuncAnimation

def animate_ground_tracks(satellites_data):
    fig = plt.figure(figsize=(12, 6))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.set_extent([-180, 180, -90, 90], crs=ccrs.PlateCarree())
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    ax.add_feature(cfeature.BORDERS, linestyle=':')

    colors = plt.cm.get_cmap('tab10', len(satellites_data))
    lines, points = {}, {}

    # Her uydu için çizgi ve nokta objesi oluştur
    for i, (sat_id, coords) in enumerate(satellites_data.items()):
        lats = [c['lat'] for c in coords]
        lons = [c['lon'] for c in coords]
        line, = ax.plot([], [], label=sat_id, color=colors(i))
        point, = ax.plot([], [], 'o', color=colors(i), markersize=4)
        lines[sat_id] = {'line': line, 'lons': lons, 'lats': lats}
        points[sat_id] = point

    time_text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12)

    def init():
        for item in lines.values():
            item['line'].set_data([], [])
        for point in points.values():
            point.set_data([], [])
        time_text.set_text('')
        return [item['line'] for item in lines.values()] + list(points.values()) + [time_text]

    # 🔹 Animasyon güncelleme fonksiyonu
    def update(frame):
        for sat_id, item in lines.items():
            lons, lats = item['lons'], item['lats']
            item['line'].set_data(lons[:frame], lats[:frame])
            if frame < len(lons):
                points[sat_id].set_data(lons[frame], lats[frame])
        return [item['line'] for item in lines.values()] + list(points.values())

    frames = len(list(satellites_data.values())[0])
    ani = FuncAnimation(fig, update, frames=frames, init_func=init, interval=80, blit=True, repeat=True)

    plt.legend()
    plt.title("Animated Satellite Ground Tracks")
    plt.show()