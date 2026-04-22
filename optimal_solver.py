"""
Optimal Solver time complexity:


Exploration per state : (36 (cells) * 4 (beams))

Branching factor: (36 (cells to explore mirros, can be heavily pruned by tracing laser path) * 2 (left or right mirror)

Exponent: 6 -- Only create solutions that use up to 6 mirros

use bitmasks/bit string in c for state representation

with a 5x5 board and max 7 mirrors, unique states:  74,786,211  , 25 * 4 to trace the beams (work per state). 


Will implement idffs + pruning based on lazer beams path

"""


