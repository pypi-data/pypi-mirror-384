import enum

import numpy as np

npa = np.array


class Neighbour(enum.Enum):
    FOUR = "4"
    EIGHT = "8"
    M = "M"


class Neighbourhood4:
    UP = npa((0, 1))
    DOWN = npa((0, -1))
    LEFT = npa((-1, 0))
    RIGHT = npa((1, 0))


class Neighbourhood8:
    NW = npa((-1, 1))
    N = npa((0, 1))
    NE = npa((1, 1))
    W = npa((-1, 0))
    E = npa((1, 0))
    SW = npa((-1, -1))
    S = npa((0, -1))
    SE = npa((1, -1))


DIRECTION_EIGHT_ARRAY = npa([Neighbourhood8.NW, Neighbourhood8.N, Neighbourhood8.NE, Neighbourhood8.E,
                             Neighbourhood8.SE, Neighbourhood8.S, Neighbourhood8.SW, Neighbourhood8.W])

DIRECTION_FOUR_ARRAY = npa([Neighbourhood8.S, Neighbourhood8.E, Neighbourhood8.N, Neighbourhood8.W])
