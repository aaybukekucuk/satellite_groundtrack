import matplotlib.pyplot as plt

def plot_ground_tracks(satellites_data):
    plt.figure(figsize=(10, 5))

    # 🟡 Debug: veri yapısını görmek için
    print(f"Total satellites to plot: {len(satellites_data)}")
    for sat_id, coords in satellites_data.items():
        print(f"{sat_id}: {len(coords)} points")
        if len(coords) > 0:
            print(f"First point sample: {coords[0]}")

    for sat_id, coords in satellites_data.items():
        # Eğer her eleman dict ise, 'lat' ve 'lon' anahtarlarını kullan
        if isinstance(coords[0], dict):
            lats = [c['lat'] for c in coords if 'lat' in c and 'lon' in c]
            lons = [c['lon'] for c in coords if 'lat' in c and 'lon' in c]
        else:
            # Tuple/list biçimindeyse ilk iki değeri al
            lats = [c[0] for c in coords]
            lons = [c[1] for c in coords]

        plt.plot(lons, lats, label=sat_id)

    plt.xlabel("Longitude (°)")
    plt.ylabel("Latitude (°)")
    plt.title("Satellite Ground Tracks")
    plt.legend()
    plt.grid(True)
    plt.show()