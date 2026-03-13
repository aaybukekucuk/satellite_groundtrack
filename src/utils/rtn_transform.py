import numpy as np

def ecef_to_rtn_error(pos_ref, vel_ref, pos_brdc):
    """
    SP3 ve Broadcast ECEF koordinatları arasındaki farkı RTN bileşenlerine dönüştürür.
    Birimler metredir.
    """
    r = np.array(pos_ref, dtype=float)
    v = np.array(vel_ref, dtype=float)
    p_cmp = np.array(pos_brdc, dtype=float)
    
    delta_r = p_cmp - r
    
    r_norm = np.linalg.norm(r)
    if r_norm == 0:
        return {"Radial (m)": 0.0, "Along-track (m)": 0.0, "Cross-track (m)": 0.0}
        
    unit_R = r / r_norm
    
    ang_mom = np.cross(r, v)
    ang_norm = np.linalg.norm(ang_mom)
    if ang_norm == 0:
        return {"Radial (m)": 0.0, "Along-track (m)": 0.0, "Cross-track (m)": 0.0}
        
    unit_N = ang_mom / ang_norm
    unit_T = np.cross(unit_N, unit_R)
    
    R_mat = np.array([unit_R, unit_T, unit_N])
    rtn_error = np.dot(R_mat, delta_r)
    
    return {
        "Radial (m)": rtn_error[0],
        "Along-track (m)": rtn_error[1],
        "Cross-track (m)": rtn_error[2]
    }