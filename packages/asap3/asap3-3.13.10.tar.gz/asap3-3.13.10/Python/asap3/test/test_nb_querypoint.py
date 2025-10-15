from ase.lattice.cubic import FaceCenteredCubic
from asap3 import FullNeighborList, print_version
from asap3.test.pytest_markers import ReportTest, serial
import ase
import numpy as np

import pytest

class AseNeigborListWrapper:
    """
    Wrapper around ASE neighborlist to have the same interface as asap3 neighborlist
    """

    def __init__(self, cutoff, atoms):
        self.neighborlist = ase.neighborlist.NewPrimitiveNeighborList(
            cutoff, skin=0.0, self_interaction=False, bothways=True
        )
        self.neighborlist.build(
            atoms.get_pbc(), atoms.get_cell(), atoms.get_positions()
        )
        self.cutoff = cutoff
        self.atoms_positions = atoms.get_positions()
        self.atoms_cell = atoms.get_cell()

    def get_neighbors(self, i, cutoff):
        assert (
            cutoff == self.cutoff
        ), "Cutoff must be the same as used to initialise the neighborlist"

        indices, offsets = self.neighborlist.get_neighbors(i)

        rel_positions = (
            self.atoms_positions[indices]
            + offsets @ self.atoms_cell
            - self.atoms_positions[i][None]
        )

        dist2 = np.sum(np.square(rel_positions), axis=1)

        return indices, rel_positions, dist2


def compare_with_ase_neighborlist(atoms, query_points, cutoff):
    """Test FullNeighborList.get_neighbors_querypoint
    by comparing the output with an equivalent implementation in ASE
    that inserts query atoms into an atoms object."""
    # Insert query atoms into ASE atoms object
    query_atoms = ase.Atoms(numbers=[0] * query_points.shape[0], positions=query_points)
    atoms_with_query = atoms.copy()
    atoms_with_query.extend(query_atoms)

    # Compute neighborlists
    asefullneighbors = AseNeigborListWrapper(cutoff, atoms_with_query)
    asapfullneighbors = FullNeighborList(cutoff, atoms)

    ase_neighbor_info = []
    for i in range(len(atoms), len(atoms_with_query)):
        indices, rel_positions, dist2 = asefullneighbors.get_neighbors(i, cutoff)
        # Filter out query atom neighbors
        rel_positions = rel_positions[indices < len(atoms)]
        dist2 = dist2[indices < len(atoms)]
        indices = indices[indices < len(atoms)]
        ase_neighbor_info.append((indices, rel_positions, dist2))

    asap_neighbor_info = asapfullneighbors.get_neighbors_querypoint(query_points)

    for asap_info, ase_info in zip(asap_neighbor_info, asap_neighbor_info):
        # Sort all lists based on neighbor distance (dist2)
        asap_sort = np.argsort(asap_info[2])
        ase_sort = np.argsort(ase_info[2])

        assert np.allclose(asap_info[2][asap_sort], ase_info[2][ase_sort]), "Distances equal"
        assert np.all(asap_info[0][asap_sort] == ase_info[0][ase_sort]), "Indices equal"
        assert np.all(asap_info[1][asap_sort] == ase_info[1][ase_sort]), "Differences equal"


@serial
def test_nbcelllocator_querypoint():
    # Setup test system
    element = "Cu"
    cutoff = 5
    atoms = FaceCenteredCubic(
        directions=[[1, 0, 0], [0, 1, 1], [0, 0, 1]],
        size=(9, 7, 5),
        symbol=element,
        debug=0,
    )

    # Test single query point
    query_points = np.array([[1.0, 2.0, 3.0]])
    compare_with_ase_neighborlist(atoms, query_points, cutoff)

    # Test multiple query points
    query_points = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    compare_with_ase_neighborlist(atoms, query_points, cutoff)

    # Test non-periodic boundaries
    query_points = np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    atoms.set_pbc(False)
    compare_with_ase_neighborlist(atoms, query_points, cutoff)

    # Test non-periodic boundaries with query points outside boundaries
    query_points = np.array([[-1.0, 0.0, 0.0], [33.0, 21.0, 13.0]])
    atoms.set_pbc(False)
    compare_with_ase_neighborlist(atoms, query_points, cutoff)
