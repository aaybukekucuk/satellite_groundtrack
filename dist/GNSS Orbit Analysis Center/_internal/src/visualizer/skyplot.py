import matplotlib.pyplot as plt
import numpy as np

def plot_skyplot(visible_sats, lat_sta, lon_sta, time_str):
    # Grafiği biraz genişletelim ki metinler sığsın
    fig = plt.figure(figsize=(10, 8)) 
    ax = fig.add_subplot(111, polar=True)

    ax.set_theta_zero_location('N')
    ax.set_theta_direction(-1)
    ax.set_ylim(90, 0)
    ax.set_yticks([0, 30, 60, 90])
    ax.set_yticklabels(['0°', '30°', '60°', '90°'])

    count = 0
    for sat in visible_sats:
        az = sat['az']
        el = sat['el']
        sid = sat['id']
        vel = sat.get('vel', 0.0) # Ana programdan hızı çek (yoksa 0 al)

        if el > 0: 
            az_rad = np.radians(az)
            ax.plot(az_rad, el, 'o', markersize=12, label=sid)
            
            # Ekrana yazılacak dinamik metin (Uydu ID ve Altında Hızı)
            info_text = f" {sid}"
            if vel > 0:
                info_text += f"\n({vel:.2f} km/s)"
                
            ax.text(az_rad, el, info_text, fontsize=9, fontweight='bold', color='darkblue')
            count += 1

    plt.title(f"Sky Visibility Plot (Gökyüzü Görünürlüğü)\nİstasyon: {lat_sta:.2f}°, {lon_sta:.2f}° | Epoch: {time_str}\nGörünen Uydu Sayısı: {count}", va='bottom', fontsize=12)
    
    if count > 0:
        plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
    
    plt.tight_layout()
    plt.show()