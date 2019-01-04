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
    nodes = -np.ones((n,
                      n))  # nodes[a][b] is the index of the atom in the b'th chain which the edge from a'th chain is connected to.
    for a, (x0a, x1a) in enumerate(zip(chains0, chains1)):
        for b, (x0b, x1b) in enumerate(zip(chains0, chains1)):
            s = t = 0
            min_distance = float('inf')
            for i, (x0ia, x1ia) in enumerate(zip(x0a, x1a)):
                for j, (x0jb, x1jb), in enumerate(zip(x0b, x1b)):
                    distance = abs((x0ia - x0jb).norm() - (x1ia - x1jb).norm()) + (x0ia - x0jb).norm()
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


def get_joint_angles(chains0, chains1, bonds):
    res = []
    for i in range(len(bonds)):
        Conf_a_Chain_a, Conf_a_Chain_b = get_coordinates(chains0, bonds)[i]
        Conf_b_Chain_a, Conf_b_Chain_b = get_coordinates(chains1, bonds)[i]
        mid_point = Vector((Conf_a_Chain_a + Conf_a_Chain_b)._ar / (np.array(2)))

        first_conf_angles = calc_rotation(mid_point[0], mid_point[1], mid_point[2],
                                          Conf_a_Chain_b[0], Conf_a_Chain_b[1], Conf_a_Chain_b[2])
        second_conf_angles = calc_rotation(mid_point[0], mid_point[1], mid_point[2],
                                           Conf_b_Chain_b[0], Conf_b_Chain_b[1], Conf_b_Chain_b[2])
        res.append([angle_a - angle_b for angle_a, angle_b in zip(first_conf_angles, second_conf_angles)])

    return res


def get_constraint_lengths(chains0, chains1, bonds, pin_length=0.05, pin_radius=0.02):
    def calc(x):
        return abs(2 * pin_length * math.sin(x)) + pin_radius

    return [(calc(a1), calc(a2)) for a1, a2 in get_joint_angles(chains0, chains1, bonds)]


if __name__ == '__main__':
    protein = '2JUV'
    print('{}:'.format(protein))
    _chains0, _chains1 = parse_chains('data/{}.pdb'.format(protein))
    _bonds = find_virtualbonds(_chains0, _chains1)
    print('  bonds: {}'.format(_bonds))
    print('  A coordinates: {}'.format(get_coordinates(_chains0, _bonds)))
    print('  B coordinates: {}'.format(get_coordinates(_chains1, _bonds)))
    print('  Constraint dimensions: {}'.format(get_constraint_lengths(_chains0, _chains1, _bonds)))
