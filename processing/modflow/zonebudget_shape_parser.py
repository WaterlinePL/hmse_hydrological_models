import os
from typing import List

import numpy as np


# Credits to FloPy
def read_zone_file(fname) -> List[np.ndarray]:
    """Method to read a zonebudget zone file into memory

    Parameters
    ----------
    fname : str
        zone file name

    Returns
    -------
    zones : np.array

    """
    with open(fname, "r") as f:
        lines = f.readlines()

    # Initialize layer
    lay = 0

    # Initialize data counter
    totlen = 0
    i = 0

    # First line contains array dimensions
    dimstring = __skip_comments(lines.pop(0).strip().split())
    nlay, nrow, ncol = [int(v) for v in dimstring]
    zones = np.zeros((nlay, nrow, ncol), dtype=np.int32)

    # The number of values to read before placing
    # them into the zone array
    datalen = nrow * ncol
    totaldatalen = nlay * nrow * ncol

    # List of valid values for LOCAT
    locats = ["CONSTANT", "INTERNAL", "EXTERNAL"]

    # ITERATE OVER THE ROWS
    for line in lines:
        if totlen == totaldatalen:
            break

        rowitems = __skip_comments(line.strip().split())

        # Skip blank lines
        if len(rowitems) == 0:
            continue

        # HEADER
        if rowitems[0].upper() in locats:
            vals = []
            locat = rowitems[0].upper()

            if locat == "CONSTANT":
                iconst = int(rowitems[1])
                vals = np.ones((nrow, ncol), dtype=int) * iconst
                lay += 1
                totlen += nrow * ncol
            else:
                fmt = rowitems[1].strip("()")
                if len(rowitems) < 3:
                    fmtin, iprn = [int(v) for v in fmt.split("I")]
                else:
                    fmtin = int(fmt.split("I")[0]) if len(fmt) > 0 else -1
                    iprn = int(rowitems[2])


        # ZONE DATA
        else:
            if locat == "INTERNAL":
                # READ ZONES
                rowvals = [int(v) for v in rowitems]
                s = "Too many values encountered on this line."
                if fmtin > 0:
                    assert len(rowvals) <= fmtin, s
                vals.extend(rowvals)

            elif locat == "EXTERNAL":
                # READ EXTERNAL FILE
                fname = rowitems[0]
                if not os.path.isfile(fname):
                    errmsg = f'Could not find external file "{fname}"'
                    raise Exception(errmsg)
                with open(fname, "r") as ext_f:
                    ext_flines = ext_f.readlines()
                for ext_frow in ext_flines:
                    ext_frowitems = ext_frow.strip().split()
                    rowvals = [int(v) for v in ext_frowitems]
                    vals.extend(rowvals)
                if len(vals) != datalen:
                    errmsg = (
                        "The number of values read from external "
                        'file "{}" does not match the expected '
                        "number.".format(len(vals))
                    )
                    raise Exception(errmsg)
            else:
                # Should not get here
                raise Exception(f"Locat not recognized: {locat}")

                # IGNORE COMPOSITE ZONES

            if len(vals) == datalen:
                # place values for the previous layer into the zone array
                vals = np.array(vals, dtype=int).reshape((nrow, ncol))
                zones[lay, :, :] = vals[:, :]
                lay += 1
            totlen += len(rowitems)
        i += 1
    s = (
        "The number of values read ({:,.0f})"
        " does not match the number expected"
        " ({:,.0f})".format(totlen, nlay * nrow * ncol)
    )
    assert totlen == nlay * nrow * ncol, s
    return __split_into_shapes(zones[0])


def __skip_comments(rowitems: List[str]):
    to_parse = []
    for item in rowitems:
        if '#' in item:
            break  # Skip comments
        else:
            to_parse.append(item)
    return to_parse


def __split_into_shapes(zones: np.ndarray) -> List[np.ndarray]:
    group_iter = 1
    shapes = []
    while zones[zones == group_iter].any():
        mask = np.zeros(zones.shape)
        mask[zones == group_iter] = 1
        shapes.append(mask)
        group_iter += 1
    return shapes
