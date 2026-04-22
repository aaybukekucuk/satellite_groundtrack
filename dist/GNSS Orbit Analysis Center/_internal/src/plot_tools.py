# plot_tools.py
import matplotlib.pyplot as plt
from utils.satpos_utils import ecef_to_geodetic

def plot_ground_track(sp3_data, sat_id):
    """Belirtilen uydu için ground track (yörünge izi) çizer"""
    from utils.satpos_utils import get_satellite_positions

    sat_positions = get_satellite_positions(sp3_data, sat_id)

    if len(sat_positions) == 0:
        print(f"{sat_id} uydusu SP3 verisinde bulunamadı.")
        return

    lats, lons = [], []
    for (x, y, z) in sat_positions:
        lat, lon, _ = ecef_to_geodetic(x, y, z)
        lats.append(lat)
        lons.append(lon)

    plt.figure(figsize=(10, 5))
    plt.title(f"Ground Track of {sat_id}")
    plt.xlabel("Longitude (°)")
    plt.ylabel("Latitude (°)")
    plt.grid(True)
    plt.plot(lons, lats, ".", markersize=1, color="blue")
    plt.xlim(-180, 180)
    plt.ylim(-90, 90)
    plt.show()