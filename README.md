# Hold it, Move it
A Minimal Automatic Joint Modeling for Moving Molecular Objects

A 3D-modeling project by Uri Avron, Amnon Catav & Ori Yoran, Tel-Aviv University, fall semester 2019.

Final presentation can be found at: https://docs.google.com/presentation/d/1mR_NRwFVNsvtQpUSAWchAgTbV4Zn1_YVFoStaQPovMI/edit?usp=sharing

## Prerequisites
- Python 3
- Blender: https://www.blender.org/
- Atomic Blender Add-on: https://en.blender.org/index.php/Extensions:2.6/Py/Scripts/Import-Export/PDB

For installing the required python packages, you may run from the project directory:
`pip install -r requirements.txt`


## Getting Started
### Joint's cut view
By running `joint_cut.py` script in Blender, our ball-and-socket joint is created with a cut view. This is helpful for a better look inside the joint.


### Loading a protein in Blender
After installing the Atomic Blender add-on, you should be able to import a protein's pdb file (`File -> Import -> Protein Data Bank (.pdb)`), which will create a protein object in the opened Blender scene.

You may find pdb files at: https://www.rcsb.org/


### Generating a Blender script for creating bonds
`python process.py <protein id>` will generate a Blender script into the `scripts` directory for creating our method's best bonds for the given protein.

This process will also download the relevant pdb file into the `data` directory.

Usage example: `python process.py 2JUV` or `python process.py 2juv`.

For your convenience, the `scripts` directory already contains generated Blender scripts examples, and the `data` directory already contains the corresponded pdb files.
Moreover, the `results` directory contains load-ready Blender models.


### Running scripts in Blender
For running scripts in Blender, you may find the following article useful:
https://docs.blender.org/api/blender_python_api_2_59_2/info_tips_and_tricks.html



## Description & Introduction
### Proteins & other molecules
- Proteins are large, complex molecules
- Proteins play critical roles in the body
- They do most of the work in cells required for function and structure of the cells
- They are made out of smaller units called amino acids each forming a chain, to form a multi-chain structure
- They are stabilized by biochemical bonds
- Understanding the movement and structure of molecules is one of the main research areas in bioinformatics


### Why proteins
- Chain structure - only a finite set of points to connect each chain
- A real world problem
- Data already exists


### Printing molecules
- Each molecule is made out of one ore more chains
- When printing, the structure will collapse as the chains are not physically connected
- Naive solution - just connect the chains!
- Problem - we will lose the movement between the chains

### Goal
Given a multi-chain molecular object with multiple conformations, print a viable 3D-model capable of moving from one conformation to another!


### Steps
- Find the best virtual bonds between each pair of chains
- Use MST (Minimum Spanning Tree) algorithm to find minimal virtual bonds to connect structure
- For each virtual bond, we add a cylinder
- For each connected pair, build 3 ball-and-socket joints with moving constraints relative to the movement
- Place the joints at the bottom, middle and top of the cylinder


### Virtual bonds
For each pair of chains, a, b the best virtual bond between the chains is defined as

<img src="https://latex.codecogs.com/svg.latex?\dpi{300}&space;\large&space;v_{a,b}=&space;\min_{i,j\in[M]\times[N]}\left&space;|&space;\left&space;\|&space;x_{i,a}^0&space;-&space;x_{j,b}^0\right&space;\|&space;-&space;\left&space;\|&space;x_{i,a}^1&space;-&space;x_{j,b}^1&space;\right&space;\|&space;\right&space;|&space;&plus;&space;\left&space;\|&space;x_{i,a}^0&space;-&space;x_{j,b}^0&space;\right&space;\|" title="\large v_{a,b}= \min_{i,j\in[M]\times[N]}\left | \left \| x_{i,a}^0 - x_{j,b}^0\right \| - \left \| x_{i,a}^1 - x_{j,b}^1 \right \| \right | + \left \| x_{i,a}^0 - x_{j,b}^0 \right \|" />

We find the minimum amount of virtual bonds which is needed to connect the structure by running MST on all pairs.


### Joint structure
- The dimensions of the constraints box are determined by the angles of the transformation, and the safety dimensions
- The ”snap” should hold the protein model in conformation A


### Problems and difficulties
- Computational geometry - representing each vector as two angles, rotation and translation matrices
- 3D-Manufacturing - finding the best joint, and adding constraints


### Results



### Future work
- Validations - collisions, size of joints
- Regard the movement inside every chain 
- Multiple confirmations, multiple snaps


### Bibliography
- JointFit - 3D-Printing of Non-Assembly Articulated Models: http://reality.cs.ucl.ac.uk/projects/jointfit/jointfit.html
- A New Approach for Modeling of Conformational Changes of Multi-Chained Proteins: https://www.sciencedirect.com/science/article/pii/S187705091632676X
