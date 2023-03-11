from typing import Dict

import flopy
import numpy as np
from flopy.modflow import Modflow, ModflowDis


def create_packages_for_step(model: Modflow, step: int):
    for pkg in model.packagelist:
        if isinstance(pkg, flopy.modflow.ModflowDis):
            handle_dis_pkg(pkg, step)
            pkg.write_file()
        elif 'stress_period_data' in pkg.__dict__:
            stress_period_data = pkg.stress_period_data
            if any(map(lambda p: isinstance(pkg, p), __SPECIAL_TREATMENT_PACKAGES.keys())):
                pkg.stress_period_data = __SPECIAL_TREATMENT_PACKAGES[pkg.__class__](stress_period_data, step)
            else:
                stress_period_data.__data = {0: pkg.stress_period_data.data[step]}
                stress_period_data.__vtype = {0: pkg.stress_period_data.vtype[step]}
            pkg.write_file()


# TODO: Verify
def handle_stress_periods_oc(stress_period_data: Dict, step: int):
    new_data = {}
    if (-1, -1) in stress_period_data:
        new_data[(-1, -1)] = stress_period_data[(-1, -1)]
    for key, value in filter(lambda kv: kv[0][0] == step, stress_period_data.items()):
        new_data[(0, key[1])] = value
    return new_data


def handle_dis_pkg(pkg: ModflowDis, step: int):
    pkg.nstp = pkg.nstp[step]
    pkg.perlen = pkg.perlen[step]
    pkg.steady = [pkg.steady[step]] * pkg.nper
    pkg.tsmult = pkg.tsmult[step]
    pkg.nper = 1


__SPECIAL_TREATMENT_PACKAGES = {
    flopy.modflow.ModflowOc: handle_stress_periods_oc
}
