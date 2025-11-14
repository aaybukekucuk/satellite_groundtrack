import matplotlib.pyplot as plt
import numpy as np

def plot_ground_tracks(multi_data):
    """
    Birden fazla uydunun ground track'ini çizer.
    multi_data: { "G01": [pos1, pos2, ...], "G02": [...], ... }
    """

    plt.figure(figsize=(10, 6))
    plt.title("🌍 Multi-Satellite Ground Tracks")
    plt.xlabel("Longitude (°)")
    plt.ylabel("Latitude (°)")
    plt.grid(True)

    colors = plt.cm.get_cmap("tab10", len(multi_data))  # farklı renkler

    for i, (sat_id, data) in enumerate(multi_data.items()):
        lats = [p["lat"] for p in data]
        lons = [p["lon"] for p in data]
        lons = np.unwrap(np.radians(lons))
        lons = np.degrees(lons)
        plt.plot(lons, lats, label=sat_id, color=colors(i))

    plt.legend(title="Satellites")
    plt.tight_layout()
    plt.show()