#!/usr/bin/env python3

import pandas as pd 

from ete3 import Tree

from pan import *

# define functions

# set up test objects 
pan = pd.DataFrame({"reprf": ["1", "2", "3", "3", "4", "5", "6", "6"], 
    "genome": ["A", "B", "C", "D", "A", "B", "C", "D"]})
tree = Tree("(((1,2),3),((4, 5),6));")
# tree = Tree("(((A,B)G,C)H,((D,E)I,F)J);")

# try lowest copy-numberrooting
roots = lowest_cn_roots(tree, pan)

# inspect result
print(len(roots))
root = roots[0]
print(root)

# test removing and re-adding node
print(tree)
parent = root.up
root.detach()
print(tree)
parent.add_child(root)
print(tree)
