import matplotlib.pyplot as plt
import numpy as np

def plot_skyplot(visible_sats, lat_sta, lon_sta, time_str):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, polar=True)

    # Jeodezi standardı: Kuzey yukarıda (0 derece), saat yönünde artar
    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)

    # Merkez Zenith (90 derece), dış çember Ufuk (0 derece)
    ax.set_ylim(90, 0)
    ax.set_yticks([0, 30, 60, 90])
    ax.set_yticklabels(['0°', '30°', '60°', '90°'])

    count = 0
    for sat in visible_sats:
        az = sat['az']
        el = sat['el']
        sid = sat['id']

        # Sadece ufkun üzerindeki (0 dereceden yüksek) uyduları çiz
        if el > 0: 
            az_rad = np.radians(az)
            ax.plot(az_rad, el, 'o', markersize=12, label=sid)
            ax.text(az_rad, el, f" {sid}", fontsize=11, fontweight='bold')
            count += 1

    plt.title(f"Sky Visibility Plot (Gökyüzü Görünürlüğü)\nİstasyon: {lat_sta:.2f}°, {lon_sta:.2f}° | Epoch: {time_str}\nGörünen Uydu Sayısı: {count}", va='bottom', fontsize=12)
    
    if count > 0:
        plt.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    
    plt.tight_layout()
    plt.show()