from Bio.PDB import *
from scipy.sparse.csgraph import minimum_spanning_tree

import numpy as np
import math
import argparse
import os


SCRIPT_SKELETON_FILENAME = 'script_skeleton.txt'
DATA_DIR = 'data'
SCRIPTS_DIR = 'scripts'


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

    # nodes[a][b] is the index of the atom in the b'th chain which the edge from a'th chain is connected to.
    nodes = -np.ones((n,n))

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


def format_coordinates(coordinates):
    return [(tuple(u), tuple(v)) for u, v in coordinates]


def calc_rotation(x1, y1, z1, x2, y2, z2):
    vx, vy, vz = x2 - x1, y2 - y1, z2 - z1
    distance = math.sqrt(vx * vx + vy * vy + vz * vz)

    phi = math.atan2(vy, vx)
    theta = math.acos(vz / distance)

    return phi, theta


def get_chain_angle_constraints(chain, bond, first_chain=True):
    index_in_bond = 1 if first_chain else 3
    res = []
    curr = chain[0][bond[index_in_bond]]
    curr2 = chain[1][bond[index_in_bond]]
    if bond[index_in_bond] == len(chain[0]) - 1:
        next = chain[0][bond[index_in_bond] - 1]
        next2 = chain[1][bond[index_in_bond] - 1]
    else:
        next = chain[0][bond[index_in_bond] + 1]
        next2 = chain[1][bond[index_in_bond] + 1]
    first_conf_angles = calc_rotation(curr[0], curr[1], curr[2],
                                      next[0], next[1], next[2])
    second_conf_angles = calc_rotation(curr2[0], curr2[1], curr2[2],
                                       next2[0], next2[1], next2[2])
    if first_chain:
        res.append([angle_a - angle_b for angle_a, angle_b in zip(first_conf_angles, second_conf_angles)])
    else:
        res.append([-(angle_a - angle_b) for angle_a, angle_b in zip(first_conf_angles, second_conf_angles)])
    return res


def get_joint_angles(chains0, chains1, bonds):
    res = []
    for i in range(len(bonds)):
        curr_bond_lst = [get_chain_angle_constraints((chains0[0], chains1[0]), bonds[i])]

        conf_a_chain_a, conf_a_chain_b = get_coordinates(chains0, bonds)[i]
        conf_b_chain_a, conf_b_chain_b = get_coordinates(chains1, bonds)[i]
        mid_point = Vector((conf_a_chain_a + conf_a_chain_b)._ar / (np.array(2)))

        first_conf_angles = calc_rotation(mid_point[0], mid_point[1], mid_point[2],
                                          conf_a_chain_b[0], conf_a_chain_b[1], conf_a_chain_b[2])
        second_conf_angles = calc_rotation(mid_point[0], mid_point[1], mid_point[2],
                                           conf_b_chain_b[0], conf_b_chain_b[1], conf_b_chain_b[2])
        curr_bond_lst.append([[angle_a - angle_b for angle_a, angle_b in zip(first_conf_angles, second_conf_angles)]])

        curr_bond_lst.append(get_chain_angle_constraints((chains0[1], chains1[1]), bonds[i], False))
        res.append(curr_bond_lst)
    return res


def get_constraint_lengths(chains0, chains1, bonds, pin_length=0.05, pin_radius=0.02):
    def calc(x):
        return abs(2 * pin_length * math.sin(x)) + pin_radius

    res = []
    joints_angles = get_joint_angles(chains0, chains1, bonds)
    for bond in joints_angles:
        bond_joints = []
        for joint in bond:
            bond_joints.append((calc(joint[0][0]), calc(joint[0][1])))
        res.append(bond_joints)

    return res


def main(protein):
    protein = protein.upper()
    filename = '{}/{}.pdb'.format(DATA_DIR, protein)

    if not os.path.isfile(filename):
        pdblist = PDBList()
        pdblist.download_pdb_files([protein], file_format='pdb', pdir=DATA_DIR)
        fetched_filename = 'pdb{}.ent'.format(protein.lower())
        os.rename('{}/{}'.format(DATA_DIR, fetched_filename), filename)

    print('{}:'.format(protein))
    _chains0, _chains1 = parse_chains(filename)
    _bonds = find_virtualbonds(_chains0, _chains1)
    print('  bonds indices: {}'.format(_bonds))
    print('  A coordinates: {}'.format(format_coordinates(get_coordinates(_chains0, _bonds))))
    print('  B coordinates: {}\n'.format(format_coordinates(get_coordinates(_chains1, _bonds))))

    bonds_str = 'bonds = {}'.format(format_coordinates(get_coordinates(_chains0, _bonds)))
    all_constraints_str = 'all_constraints = {}'.format(get_constraint_lengths(_chains0, _chains1, _bonds))

    print('  {}'.format(bonds_str))
    print('  {}'.format(all_constraints_str))

    with open(SCRIPT_SKELETON_FILENAME, 'r') as f:
        script_skeleton = f.read()
        script = script_skeleton.format(protein, bonds_str, all_constraints_str)

        script_name = '{}/{}.py'.format(SCRIPTS_DIR, protein)
        with open(script_name, 'w') as scriptfile:
            scriptfile.write(script)

    print('\nA blender script for protein {} saved as {}.py in {} directory.'.format(protein, protein, SCRIPTS_DIR))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('protein', help='what protein to process', type=str)

    args = parser.parse_args()

    main(args.protein)
