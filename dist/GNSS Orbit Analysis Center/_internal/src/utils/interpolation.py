import numpy as np
from datetime import datetime

def lagrange_interpolate(target_time, times, values, order=9):
    """
    Hedeflenen bir 'target_time' için, eldeki bilinen 'times' ve 'values' 
    değerlerini kullanarak yüksek dereceli Lagrange interpolasyonu yapar.
    """
    if len(times) < order + 1:
        return values[0]  # Yeterli veri yoksa hata vermemesi için

    # Zamanları 'saniye' cinsinden ondalık sayılara çevir (Fark hesaplayabilmek için)
    base_time = times[0]
    t_points = np.array([(t - base_time).total_seconds() for t in times])
    t_target = (target_time - base_time).total_seconds()

    # Hedef zamana en yakın 'order + 1' adet noktayı bul
    idx = np.argsort(np.abs(t_points - t_target))[:order+1]
    t_sel = t_points[idx]
    v_sel = np.array(values)[idx]

    # Lagrange Formülü
    result = 0.0
    for i in range(len(t_sel)):
        term = v_sel[i]
        for j in range(len(t_sel)):
            if i != j:
                term = term * (t_target - t_sel[j]) / (t_sel[i] - t_sel[j])
        result += term
        
    return float(result)