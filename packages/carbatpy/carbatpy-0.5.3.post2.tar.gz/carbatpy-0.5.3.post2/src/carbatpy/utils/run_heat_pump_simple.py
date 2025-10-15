# -*- coding: utf-8 -*-
"""
Created on Mon Nov 13 09:47:06 2023

@author: atakan
"""

import carbatpy as cb


_RESULTS_ = cb._RESULTS_DIR 


FLUID = "Propane * Ethane * Pentane *Isobutane"
#comp = [.75, 0.05, 0.15, 0.05]
x1 =0.25
x2 =0.05
x3 =0.05
x4 = 1- x1-x2-x3
comp = [x1,x2, x3, x4]  # [0.164,.3330,.50300,0.0]
print(f"{FLUID}, composition:\n{comp}")
T_SUR =273.15+20
FLS = "Water"  #
FLCOLD = "Methanol"  # "Water"  #

flm = cb.fprop.FluidModel(FLUID)
myFluid = cb.fprop.Fluid(flm, comp)

secFlm = cb.fprop.FluidModel(FLS)
secFluid = cb.fprop.Fluid(secFlm, [1.])

coldFlm = cb.fprop.FluidModel(FLCOLD)
coldFluid = cb.fprop.Fluid(coldFlm, [1.])

# Condenser(c) and storage (s), secondary fluids fix all, temperatures(T in K),
# pressures (p in Pa)
_ETA_S_ = 0.57  # interesting when changed from 0.69 to 0.65, the efficiency
# decreases, the reason is the low quality along throtteling then
_STORAGE_T_IN_ = T_SUR
_COLD_STORAGE_T_IN_ = T_SUR
_STORAGE_T_OUT_ = 273.15 + 60  # 395.0
_COLD_STORAGE_T_OUT_ = 284.15
_STORAGE_P_IN_ = 5e5
_COLD_STORAGE_P_IN_ = 5e5
_Q_DOT_MIN_ = 1e3  # and heat_flow rate (W)
_D_T_SUPER_ = 15  # super heating of working fluid
_D_T_MIN_ = 4.  # minimum approach temperature (pinch point)
# high T-storages
state_sec_out = secFluid.set_state([_STORAGE_T_OUT_, _STORAGE_P_IN_], "TP")
state_sec_in = secFluid.set_state([_STORAGE_T_IN_, _STORAGE_P_IN_], "TP")

#  low T sorages:
state_cold_out = coldFluid.set_state(
    [_COLD_STORAGE_T_OUT_, _COLD_STORAGE_P_IN_], "TP")
state_cold_in = coldFluid.set_state(
    [_COLD_STORAGE_T_IN_, _COLD_STORAGE_P_IN_], "TP")

# working fluid
T_DEW = _STORAGE_T_OUT_ #+ _D_T_MIN_
state_in_cond = myFluid.set_state([T_DEW, 1.], "TQ")  # find high pressure
state_out_cond = myFluid.set_state([_STORAGE_T_IN_ + _D_T_MIN_,
                                    state_in_cond[1]], "TP")
state_satv_evap = myFluid.set_state(
    [_STORAGE_T_IN_-_D_T_MIN_-_D_T_SUPER_, 1.], "TQ")  # find minimum pressure
p_low = state_satv_evap[1]

T_IN = _STORAGE_T_IN_ - _D_T_MIN_

state_out_evap = myFluid.set_state([p_low,
                                    T_IN], "PT")

FIXED_POINTS = {"eta_s": _ETA_S_,
                "p_low": state_out_evap[1],
                "p_high": state_in_cond[1],
                "T_hh": _STORAGE_T_OUT_,
                "h_h_out_sec": state_sec_out[2],
                "h_h_out_w": state_out_cond[2],
                "h_l_out_cold": state_cold_out[2],
                "h_l_out_w": state_out_evap[2],
                "T_hl": _STORAGE_T_IN_,
                "T_lh": _STORAGE_T_IN_,
                "T_ll": _COLD_STORAGE_T_OUT_,  # 256.0,
                "Q_dot_h": _Q_DOT_MIN_,
                "d_temp_min": _D_T_MIN_}

print(
    f"p-ratio: {state_in_cond[1]/state_out_evap[1]: .2f}, p_low: {state_out_evap[1]/1e5: .2} bar")
hp0 = cb.hp_simple.HeatPump([myFluid, secFluid, coldFluid], FIXED_POINTS)
cop = hp0.calc_heat_pump(FIXED_POINTS["p_high"], verbose=False)
hp0.hp_plot()
out = hp0.evaluation
print(
    f"COP: {cop},p-ratio: {out['p_high']/out['p_low']:.2f}, p_low {out['p_low']/1e5:.2f} bar")
print(
    f"COP: {cop},p-ratio: {out['p_high']/out['p_low']}, p_low {out['p_low']/1e5}")
print(
    f'exergy loss rate: {out["exergy_loss_rate"]}, eff: {1-out["exergy_loss_rate"]/out["Power"]:.4f}')
