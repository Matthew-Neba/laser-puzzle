import random

MAX_MIRRORS = 7
MAX_ROWS = 5
MAX_COLS = 5
MAX_LASERS = 4

DIRS = [(1,0), (-1,0), (0, 1), (0, -1)]


def laser_step(pos, dir):
    pass


def generate_level():
    MIRRORS = random.randint(1, MAX_MIRRORS)
    PUZZLE_ROWS = random.randint(1, MAX_ROWS)
    PUZZLE_COLS = random.randint(1, MAX_COLS)
    LASERS = random.randint(1,MAX_LASERS)
    
    # we will augment the grid by one to store the laser beams and goals
    grid = [[0] * (PUZZLE_COLS + 1) for _ in range(PUZZLE_ROWS + 1)]
    
    #
    # now lets place the mirros and work backwards, we will backwards generate to ensure it is actually possible to
    # finish the level
    #
        

    """
    criteria: 
    - no two lasers share the same end slot - check at end

    - no laser loops forever - ensure while building

    - no two lasers ever join to be in same spot and same direction, since we cant break mirror paths, guaranteed to give duplicate sinks

    - every placed mirror is actually used by at least one beam - ensure while building, don't place mirror if breaks other ones paths
    """

    # choose where to put the lasers
    ROWS, COLS = len(grid), len(grid[0])
    laser_choices = []
    for r in range(ROWS):
        if r == 0 or r == ROWS - 1:
            for c in range(1, COLS - 1):
                laser_choices.append((r,c))
        else:
            laser_choices.append((r,0))
            laser_choices.append((r,COLS))
    
    


generate_level()













