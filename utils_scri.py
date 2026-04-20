import sxs
import scri
from scri.asymptotic_bondi_data.map_to_superrest_frame import MT_to_WM, WM_to_MT

def strain_as_charges_and_fluxes(abd):
    h = MT_to_WM(2.0*abd.sigma.bar)
    psi2 = MT_to_WM(abd.psi2, dataType=scri.psi2)

    h_sxs = MT_to_WM(2.0*abd.sigma.bar, sxs_version=True)
    Psi2_sxs = MT_to_WM(abd.psi2, dataType=psi2, sxs_version=True)
    
    h_m = MT_to_WM(WM_to_MT(sxs.waveforms.memory.J_m(h_sxs, Psi2_sxs)))

    h_E = MT_to_WM(WM_to_MT(sxs.waveforms.memory.J_E(h_sxs)))
    h_E.data -= h_E.data[-1] - h.data[-1]

    h_N = MT_to_WM(WM_to_MT(sxs.waveforms.memory.J_Nhat(h_sxs, Psi2_sxs)))

    h_J = MT_to_WM(WM_to_MT(sxs.waveforms.memory.J_J(h_sxs)))

    return h, h_m, h_E, h_N, h_J
