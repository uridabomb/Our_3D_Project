from Bio.PDB import *
from scipy.sparse.csgraph import minimum_spanning_tree

import numpy as np


def parse_chains(pdbfilename):
    parser = PDBParser()
    structure = parser.get_structure('PROTEIN', pdbfilename)

    chains0, chains1 = [], []

    models = list(structure)
    assert len(models) > 1

    for chain in models[0]:
        chains0.append([])
        for residue in chain:
            if 'CA' in residue:  # residue is amino-acid (aa)
                vector = residue['CA'].get_vector()
                chains0[-1].append(vector)

    for chain in models[-1]:
        chains1.append([])
        for residue in chain:
            if 'CA' in residue:  # residue is amino-acid (aa)
                vector = residue['CA'].get_vector()
                chains1[-1].append(vector)

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
    for a, ch0 in enumerate(chains0):
        for b, ch1 in enumerate(chains1):
            s = t = 0
            min_distance = float('inf')
            for i, x0ia in enumerate(ch0):
                for j, x1jb in enumerate(ch1):
                    x0jb, x1ia = ch0[b][j], ch1[a][i]
                    distance = (x0ia - x0jb).norm() - (x1ia - x1jb).norm()
                    if distance < min_distance:
                        min_distance = distance
                        s, t = i, j

            graph[a][b] = graph[b][a] = min_distance
            nodes[a][b] = t
            nodes[b][a] = s

    _mst = minimum_spanning_tree(graph)
    return _mst.toarray().astype(float), nodes.astype(int)


def find_virtualbonds(chains0, chains1):
    n = len(chains0)
    mst, nodes = build_mst(chains0, chains1)

    bonds = []
    for a in range(n):
        for b in range(n):
            if mst[a][b] > 0:
                bonds.append((a, nodes[b][a], b, nodes[a][b]))

    return bonds


def run(morph):
    chains0 = parse_chains('data/{}/A.pdb'.format(morph))
    chains1 = parse_chains('data/{}/B.pdb'.format(morph))
    for a, b in zip(chains0, chains1):
        assert len(a) == len(b)
        print(len(a), len(b))


_chains0, _chains1 = parse_chains('data/example.pdb')
print(find_virtualbonds(_chains0, _chains1))