from Bio.PDB import *
from scipy.sparse.csgraph import minimum_spanning_tree

import numpy as np
import math

def parse_chains(pdbfilename):
    parser = PDBParser()
    structure = parser.get_structure('PROTEIN', pdbfilename)

    chains0, chains1 = [], []

    models = list(structure)
    assert len(models) > 1

    for model, chains in zip((models[0], models[-1]), (chains0, chains1)):
        for chain in model:
            chains.append([])
            for residue in chain:
                if 'CA' in residue:  # residue is amino-acid (aa)
                    vector = residue['CA'].get_vector()
                    chains[-1].append(vector)

    assert len(chains0) == len(chains1)
    for (x0, x1) in zip(chains0, chains1):
        assert len(x0) == len(x1)

    return chains0, chains1


def build_mst(chains0, chains1):
    """
    finds the minimum spanning tree of a structure, represented by a list of chains.
    the nodes are the chains, and the minimal distance between two atoms in pair of chains is an edge.
    :param chains0:
    :param chains1:
    :return: mst as array
    """
    n = len(chains0)
    graph = np.zeros((n, n))
    nodes = -np.ones((n, n))  # nodes[a][b] is the index of the atom in the b'th chain which the edge from a'th chain is connected to.
    for a, (x0a, x1a) in enumerate(zip(chains0, chains1)):
        for b, (x0b, x1b) in enumerate(zip(chains0, chains1)):
            s = t = 0
            min_distance = float('inf')
            for i, (x0ia, x1ia) in enumerate(zip(x0a, x1a)):
                for j, (x0jb, x1jb), in enumerate(zip(x0b, x1b)):
                    distance = abs((x0ia - x0jb).norm() - (x1ia - x1jb).norm())
                    if distance < min_distance:
                        min_distance = distance
                        s, t = i, j

            graph[a][b] = graph[b][a] = min_distance
            nodes[a][b] = t
            nodes[b][a] = s

    mst = minimum_spanning_tree(graph)
    return mst.toarray().astype(float), nodes.astype(int)


def find_virtualbonds(chains0, chains1):
    n = len(chains0)
    mst, nodes = build_mst(chains0, chains1)

    bonds = []
    for a in range(n):
        for b in range(n):
            if mst[a][b] > 0:
                bonds.append((a, nodes[b][a], b, nodes[a][b]))

    return bonds


def get_coordinates(chains0, bonds):
    return [(chains0[ch0][idx0], chains0[ch1][idx1]) for ch0, idx0, ch1, idx1 in bonds]


def calc_angles():
    pass


def calc_rotation(x1, y1, z1, x2, y2, z2):
    vx, vy, vz = x2 - x1, y2 - y1, z2 - z1
    distance = math.sqrt(vx * vx + vy * vy + vz * vz)

    phi = math.atan2(vy, vx)
    theta = math.acos(vz / distance)

    return phi, theta


def joint_angles(_chains0, _chains1, _bonds):
    res = []
    for i in range(len(_bonds)):
        Conf_a_Chain_a, Conf_a_Chain_b = get_coordinates(_chains0, _bonds)[i]
        Conf_b_Chain_a, Conf_b_Chain_b = get_coordinates(_chains1, _bonds)[i]
        mid_point = Vector((Conf_a_Chain_a + Conf_a_Chain_b)._ar / (np.array(2)))

        first_conf_angles = calc_rotation(mid_point[0], mid_point[1], mid_point[2],
                                          Conf_a_Chain_b[0], Conf_a_Chain_b[1], Conf_a_Chain_b[2])
        second_conf_angles = calc_rotation(mid_point[0], mid_point[1], mid_point[2],
                                           Conf_b_Chain_b[0], Conf_b_Chain_b[1], Conf_b_Chain_b[2])
        res.append([angle_a - angle_b for angle_a, angle_b in zip(first_conf_angles, second_conf_angles)])
    return res


def cube_lengths(pin_length):
    return[[pin_length*math.sin(angle[0]), pin_length*math.sin(angle[1])]
                for angle in joint_angles(_chains0, _chains1, _bonds)]


_chains0, _chains1 = parse_chains('data/2JUV.pdb')
_bonds = find_virtualbonds(_chains0, _chains1)
print(get_coordinates(_chains0, _bonds))
print(get_coordinates(_chains1, _bonds))
print(cube_lengths(0.05))