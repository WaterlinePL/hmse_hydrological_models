import numpy as np
from pandas import read_csv
from scipy.optimize import root_scalar
import phydrus as ph

from . import hydrus_utils
from .file_processing.selector_in_processor import SelectorInProcessor
from .. import unit_manager
from ..unit_manager import LengthUnit


def calculate_hydrostatic_pressure(hydrus_root_dir: str, water_depth_in_profile: float, hydrus_unit: LengthUnit):
    # Contains DF with x, h (pressure)
    profile = ph.profile.profile_from_file(hydrus_utils.find_hydrus_file_path(hydrus_root_dir, file_name="profile.dat"),
                                           ws="")
    x = profile["x"]
    pressure = -x - water_depth_in_profile
    above_table_value = unit_manager.convert_units(-1.0,
                                                   from_unit=LengthUnit.m,
                                                   to_unit=hydrus_unit)
    pressure[pressure < above_table_value] = above_table_value
    return pressure.tolist()


# Credit to Adam Szymkiewicz
def calculate_pressure_for_hydrus_model(hydrus_root_dir: str, water_depth_in_profile: float):
    time_inf2 = ph.read_tlevel(hydrus_utils.find_hydrus_file_path(hydrus_root_dir, file_name="t_level.out"))
    rval2 = time_inf2["vBot"].to_numpy()

    profile = ph.profile.profile_from_file(hydrus_utils.find_hydrus_file_path(hydrus_root_dir, file_name="profile.dat"),
                                           ws="")
    nod_inf2 = ph.read_nod_inf(hydrus_utils.find_hydrus_file_path(hydrus_root_dir, file_name="nod_inf.out"))
    perlen = max(nod_inf2.keys())
    if perlen == 0:
        raise RuntimeError(f"Model {hydrus_root_dir} contains only initial profile nodes data in NOD_INF.OUT file!")

    selector_in_path = hydrus_utils.find_hydrus_file_path(hydrus_root_dir, file_name="selector.in")
    with open(selector_in_path, 'r', encoding='utf-8') as fp:
        selector_processor = SelectorInProcessor(fp)
        waterflow_config = selector_processor.read_waterflow_config()
        material_properties = selector_processor.read_material_properties()

    qbot = rval2[-1]  # bottom flux from the last Hydrus time step
    kold = nod_inf2[perlen].K.to_numpy()
    qold = nod_inf2[perlen].Flux.to_numpy()
    matid = profile["Mat"]
    h2new = nod_inf2[perlen].Head.to_numpy()
    h2new[-1] = water_depth_in_profile  # new pressure head at the bottom
    h_low = h2new[-1]
    k_low = kold[-1]

    for idx in range(len(h2new) - 2, 0, -1):
        qold1 = 0.5 * (qold[idx] + qold[idx + 1])
        # check if the profile update should be terminated
        if qold1 * qbot < 0:
            # flux changes direction
            break
        qmax = max(abs(qold1), abs(qbot))
        if abs(qold1 - qbot) > (1e-12 + 0.1 * qmax):
            # flux value significantly different from the value in the saturated zone
            break

        dz = abs(profile["x"].iloc[idx + 1] - profile["x"].iloc[idx])
        midx = matid.iloc[idx]
        iModel = waterflow_config["iModel"]
        ThR = material_properties.iloc[midx - 1, 0]
        ThS = material_properties.iloc[midx - 1, 1]
        alpha = material_properties.iloc[midx - 1, 2]
        nvg = material_properties.iloc[midx - 1, 3]
        ks = material_properties.iloc[midx - 1, 4]
        tau = material_properties.iloc[midx - 1, 5]

        args = [qbot, h_low, k_low, dz, iModel, ThR, ThS, alpha, nvg, ks, tau]
        targs = tuple(args)

        hmin = -1000.
        kmin = __kh(hmin, iModel, ThR, ThS, alpha, nvg, ks, tau)
        fluxmax = -0.5 * (kmin + k_low) * ((hmin - h_low) / dz + 1)
        hmax = 100.
        kmax = ks
        fluxmin = -0.5 * (kmax + k_low) * ((hmax - h_low) / dz + 1)
        hz = h_low - dz
        if abs(qbot) < 1e-12:
            # almost hydrostatic
            h_up = hz
        elif qbot < 0:
            # downward flux
            if qbot < fluxmin:
                h_up = hmax
            else:
                my_bracket = [hz, hmax]
                sol = root_scalar(__flux_bal, args=targs, bracket=my_bracket)
                print(sol.root, sol.converged, sol.flag)
                h_up = sol.root
        else:
            # upward flux
            if qbot > fluxmax:
                h_up = hmin
            else:
                my_bracket = [hmin, hz]
                sol = root_scalar(__flux_bal, args=targs, bracket=my_bracket)
                print(sol.root, sol.converged, sol.flag)
                h_up = sol.root
        h2new[idx] = h_up
        h_low = h_up
        k_low = __kh(h_low, iModel, ThR, ThS, alpha, nvg, ks, tau)
    return h2new


# Credit to Adam Szymkiewicz
def __kh(h, *args):
    # calculates hydraulic conductivity as a function of pressure head
    # required to modify Hydrus pressure profiles after each Modflow period
    iModel = args[0]
    Qr = args[1]
    Qs = args[2]
    Alfa = args[3]
    n = args[4]
    Ks = max(args[5], 1.0e-37)
    BPar = args[6]

    if iModel not in (0, 1, 3):
        raise RuntimeError(f"Not implemented: iModel {iModel}!")

    PPar = 2
    if iModel == 0 or iModel == 3:
        Qm = Qs
        Qa = Qr
        Qk = Qs
        Kk = Ks
    elif iModel == 1:
        # DEAD CODE
        ###
        lAltern = False
        if not lAltern:
            Qm = args[7]
            Qa = args[8]
            Qk = args[9]
            Kk = args[10]
        ###
        else:
            Qm = Qs
            Qa = Qr
            Qk = Qs
            Kk = Ks
            Alfa = args[9]
            n = args[10]

    if iModel == 3:
        Qm = args[7]
    m = 1.0 - 1.0 / n

    # DEAD CODE
    ###
    lUnbound = False
    if lUnbound:
        m = args[6]
        BPar = 0.5
    ###

    HMin = -1.0e300 ** (1.0 / n) / max(Alfa, 1.0)
    HH = max(h, HMin)
    Qees = min((Qs - Qa) / (Qm - Qa), 0.999999999999999)
    Qeek = min((Qk - Qa) / (Qm - Qa), Qees)
    Hs = -1.0 / Alfa * (Qees ** (-1.0 / m) - 1.0) ** (1.0 / n)
    Hk = -1.0 / Alfa * (Qeek ** (-1.0 / m) - 1.0) ** (1.0 / n)
    if h < Hk:
        if not lUnbound:
            Qee = (1.0 + (-Alfa * HH) ** n) ** (-m)
            Qe = (Qm - Qa) / (Qs - Qa) * Qee
            Qek = (Qm - Qa) / (Qs - Qa) * Qeek
            FFQ = 1.0 - (1.0 - Qee ** (1.0 / m)) ** (-m)
            FFQk = 1.0 - (1.0 - Qeek ** (1.0 / m)) ** (-m)
            if FFQ <= 0.0:
                FFQ = m * Qee ** (1.0 / m)
            Kr = (Qe / Qek) ** BPar * (FFQ / FFQk) ** PPar * Kk / Ks
            if iModel == 0:
                Kr = Qe ** BPar * FFQ ** PPar
            return max(Ks * Kr, 1.0e-37)
        # DEAD CODE
        ###
        else:
            raise RuntimeError("Not implemented case!")
        ###
    if Hk <= h < Hs:
        Kr = (1.0 - Kk / Ks) / (Hs - Hk) * (h - Hs) + 1
        return Ks * Kr
    if h >= Hs:
        return Ks


# Credit to Adam Szymkiewicz
def __flux_bal(h, *args):
    # calculates residuum for steady flow equation
    # required to modify Hydrus pressure profiles after each Modflow period
    q = args[0]  # flux (negative downward)
    h0 = args[1]  # pressure at lower node
    k0 = args[2]  # hyd. cond. at lower node
    dz = args[3]  # node spacing
    my_kh = __kh(h, *args[4:])
    kaver = 0.5 * (k0 + my_kh)
    bal = q + kaver * ((h - h0) / dz + 1)
    return bal
