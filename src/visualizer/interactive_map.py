import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def select_station_on_map():
    print("\n🗺️ İstasyon konumunu belirlemek için açılan harita üzerinde bir noktaya TIKLAYIN...")
    fig = plt.figure(figsize=(10, 5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()
    ax.add_feature(cfeature.LAND, facecolor='lightgray')
    ax.add_feature(cfeature.OCEAN, facecolor='azure')
    ax.coastlines(linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':')
    
    plt.title("İstasyon Seçimi: Lütfen Haritada Gözlem Noktanıza Tıklayın", fontsize=14, fontweight='bold')
    
    station = []
    
    def onclick(event):
        if event.xdata is not None and event.ydata is not None:
            station.append((event.ydata, event.xdata)) # Enlem, Boylam
            print(f"📍 İstasyon seçildi! Enlem: {event.ydata:.2f}, Boylam: {event.xdata:.2f}")
            plt.close(fig) # Tıklayınca harita otomatik kapanır
            
    fig.canvas.mpl_connect('button_press_event', onclick)
    plt.show()
    
    if station:
        return station[0][0], station[0][1]
    else:
        print("⚠️ Haritaya tıklanmadı. Varsayılan (Hacettepe Üniversitesi) seçiliyor...")
        return 39.866, 32.736