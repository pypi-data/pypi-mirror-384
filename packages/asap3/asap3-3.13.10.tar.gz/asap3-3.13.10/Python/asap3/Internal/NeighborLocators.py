"""Python access to NeighborLocators."""

from asap3 import _asap
import numpy as np

def _decide_minimumimage(rCut, atoms, driftfactor=0.0):
    # Auto-detect minimum-image conditions
    if atoms is None:
        # No information, assuming minimum image conditions.
        minimum_image = True
    else:
        cell = atoms.cell
        heights = cell.volume / cell.areas()
        toosmall = np.less_equal(heights, rCut * (1 + driftfactor))
        toosmall = np.logical_and(toosmall, atoms.get_pbc())
        minimum_image = not toosmall.any()
    return minimum_image

def FullNeighborList(rCut, atoms=None, driftfactor=0.0, minimum_image=None):
    if minimum_image is None:
        minimum_image = _decide_minimumimage(rCut, atoms)
    return _asap.FullNeighborList(rCut, atoms, driftfactor, minimum_image)

