#!/usr/bin/env python3

from ete3 import Tree

# define functions

# create test tree
tree = Tree("((A:1, B:0):0, (C:0, D:0):0):0;")

# midpoint root 
midoutgr = tree.get_midpoint_outgroup()
if midoutgr != tree:
    try: 
        tree.set_outgroup(midoutgr) 
    except Exception as e:
        print("error")
    
# inspect results
print(tree)
print(tree.children[0])
print(tree.children[1])
print(len(tree.children[0]))
print(len(tree.children[1]))
