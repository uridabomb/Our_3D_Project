from Bio.PDB import *
from scipy.sparse.csgraph import minimum_spanning_tree

import numpy as np


def parse_chains(pdbfilename):
    parser = PDBParser()
    structure = parser.get_structure('PROTEIN', pdbfilename)

    chains = []

    for model in structure:
        for chain in model:
            chains.append([])
            for residue in chain:
                if 'CA' in residue:  # residue is amino-acid (aa)
                    vector = residue['CA'].get_vector()
                    chains[-1].append(vector)

    return chains


def build_mst(chains):
    """
    finds the minimum spanning tree of a structure, represented by a list of chains.
    the nodes are the chains, and the minimal distance between two atoms in pair of chains is an edge.
    :param chains:
    :return: mst as array
    """
    N = len(chains)
    graph = np.zeros((N, N))
    nodes = -np.ones((N, N))  # nodes[i][j] is the index of the atom in the jth chain which the edge from ith chain is connected to.
    for i, ch1 in enumerate(chains):
        for j, ch2 in enumerate(chains):
            if i < j:
                s = t = 0
                min_distance = float('inf')
                for k, u in enumerate(ch1):
                    for l, v in enumerate(ch2):
                        distance = (u - v).norm()
                        if distance < min_distance:
                            min_distance = distance
                            s, t = k, l

                graph[i][j] = graph[j][i] = min_distance
                nodes[i][j] = t
                nodes[j][i] = s

    _mst = minimum_spanning_tree(graph)
    return _mst.toarray().astype(float), nodes.astype(int)


def find_virtualbonds(chains):
    N = len(chains)
    mst, nodes = build_mst(chains)

    qs = []
    for i in range(N):
        for j in range(N):
            if mst[i][j] > 0:
                qs.append((i, nodes[j][i], j, nodes[i][j]))

    return qs


def run(morph):
    A_chains = parse_chains('data/{}/A.pdb'.format(morph))
    B_chains = parse_chains('data/{}/B.pdb'.format(morph))
    for a, b in zip(A_chains, B_chains):
        assert len(a) == len(b)
        print(len(a), len(b))


chains = parse_chains('data/example.pdb')
print(find_virtualbonds(chains))