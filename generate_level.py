import random
from typing import List

DIRS = [(1,0), (-1,0), (0, 1), (0, -1)]
DIRS_MAP = {
    "down": DIRS[0],
    "up": DIRS[1],
    "right": DIRS[2],
    "left": DIRS[3] 
}

def generate_grid(MIN_ROWS: int, MAX_ROWS: int, MIN_COLS: int, MAX_COLS: int, MAX_LASERS: int) -> List[List[str]]:
    puzzle_rows = random.randint(MIN_ROWS, MAX_ROWS)
    puzzle_cols = random.randint(MIN_COLS, MAX_COLS)
    possible_lasers = random.randint(1,MAX_LASERS)
    
    # we will augment the grid by one to store the laser beams and goals
    grid = [['*'] * (puzzle_cols + 1) for _ in range(puzzle_rows + 1)]

    # choose where to put the lasers
    ROWS, COLS = len(grid), len(grid[0])
    laser_choices = []
    for r in range(ROWS):
        if r == 0 or r == ROWS - 1:
            # skip corners
            for c in range(1, COLS - 1):
                laser_choices.append((r,c))
        else:
            laser_choices.append((r,0))
            laser_choices.append((r,COLS - 1))
    
    # now choose laser choices
    laser_positions = random.sample(laser_choices, min(len(laser_choices) , possible_lasers))

    # place lasers
    for pos in laser_positions:
        grid[pos[0]][pos[1]] = 'L'
    
    return grid


# take a step with laser, give new pos of laser, give new direction of laser also (None if at border)
def laser_step(
    pos: tuple[int, int],
    direction: tuple[int, int],
    grid: List[List[str]],
) -> tuple:

    # take a step and check if we are at end / hit a mirror
    nr = pos[0] + direction[0]
    nc = pos[1] + direction[1]

    ROWS, COLS = len(grid), len(grid[0])

    if not (-1 < nr < ROWS and -1 < nc < COLS):
        # we are out of bounds
        return (nr,nc), None


    # check if we hit a mirror and reflect
    if grid[nr][nc] == "ML":
        return (nr,nc), (direction[1], direction[0])

    if grid[nr][nc] == "MR":
        return (nr,nc), (-direction[1], -direction[0])
    
    # no mirror
    return (nr,nc), direction


# returns if the current grid folllows all the rules
def ensure_rules(grid: List[List[str]]) -> bool:
    ROWS, COLS = len(grid), len(grid[0])
    
    # get all mirror positions
    mirrors = set()
    lasers = set()

    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] in ["MR", "ML"]:
                mirrors.add((r,c))
            elif grid[r][c] == "L":
                lasers.add((r,c))
    
    # fully trace each laser
    visited_lasers = set()
    for pos in lasers:
        cur_pos = pos
        # get initial direction of laser
        if pos[0] == 0:
            cur_dir = DIRS_MAP["down"]
        elif pos[0] == ROWS - 1:
            cur_dir = DIRS_MAP["up"]
        elif pos[1] == 0:
            cur_dir = DIRS_MAP["right"]
        else:
            cur_dir = DIRS_MAP["left"]

        # init with one step, leads to a cleaner while loop
        visited_lasers.add((cur_pos, cur_dir))
        reached_border = False
        while not reached_border:
            """
            criteria: 
            - no laser loops forever - ensure while building, DONE 

            - no two lasers ever join to be in same spot and same direction, since we cant break mirror paths, guaranteed to give duplicate sinks - ensure while building  , DONE

            - every placed mirror is actually used by at least one beam - ensure while building, don't place mirror if breaks other ones paths, DONE
            """
            cur_pos, cur_dir = laser_step(cur_pos, cur_dir, grid)

            # make sure we havent:
            # 1) seen another laser be in the same spot with same dir -> same ending, invalid
            # 2) seen this same laser in the same spot with same dir -> cycle, invalid
            if (cur_pos, cur_dir) in visited_lasers:
                return False
            
            # remove from mirrors set
            if cur_pos in mirrors:
                mirrors.remove(cur_pos)

            # add to visited lasers set, store direction as well
            visited_lasers.add((cur_pos, cur_dir))

            if (cur_pos[0] in [0, ROWS - 1]) or (cur_pos[1] in [0, COLS - 1]):
                reached_border = True
            
        
    # make sure that all placed mirrors are being used
    if len(mirrors) != 0:
        return False

    return True


#  expects a valid grid that follows the rules in ensures rules
def place_a_mirror(grid):
    ROWS, COLS = len(grid), len(grid[0])

    lasers = set()
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c] == "L":
                lasers.add((r,c))
    
    valid = []
    for pos in lasers:
        cur_pos = pos
        # get initial direction of laser
        if pos[0] == 0:
            cur_dir = DIRS_MAP["down"]
        elif pos[0] == ROWS - 1:
            cur_dir = DIRS_MAP["up"]
        elif pos[1] == 0:
            cur_dir = DIRS_MAP["right"]
        else:
            cur_dir = DIRS_MAP["left"]

        # init with one step, leads to a cleaner while loop
        reached_border = False
        while not reached_border:
            cur_pos, cur_dir = laser_step(cur_pos, cur_dir, grid)
            
            # TODO: make sure we are not placing mirrors on borders, this is an eroor ith how loop is bui;t, might be also a bug of not all mirros bweign hit
            if grid[cur_pos[0]][cur_pos[1]] == '*':
                valid.append(cur_pos)

            if (cur_pos[0] in [0, ROWS - 1]) or (cur_pos[1] in [0, COLS - 1]):
                reached_border = True
    
    # try random valid slots and random orientations until one works
    random.shuffle(valid)

    for chosen in valid:
        orientations = ["ML", "MR"]
        random.shuffle(orientations)

        for orientation in orientations:
            grid[chosen[0]][chosen[1]] = orientation
            if ensure_rules(grid):
                return True
            grid[chosen[0]][chosen[1]] = '*'

    return False


def generate_puzzle(MIN_ROWS, MAX_ROWS, MIN_COLS, MAX_COLS, MAX_LASERS, MAX_MIRRORS, MAX_TRIES):
    tries = 0

    grid = [["*"]]
    placed_all = None
    need_mirrors = random.randint(1, MAX_MIRRORS)

    for tries in range(MAX_TRIES):
        # create a fresh grid for this full attempt
        grid = generate_grid(MIN_ROWS, MAX_ROWS, MIN_COLS, MAX_COLS, MAX_LASERS)
        placed_all = True

        for _ in range(need_mirrors):
            placed = place_a_mirror(grid)
            if not placed:
                placed_all = False
                break

        if placed_all:
            break

    if not placed_all:
        return None


    # we have followed all intermediary rules, do one more check for good measure and to ensure all conditions
    # are actually met
    #
    # 1) no two sinks in same spot
    # 2) no sink at a start
    # 3) all mirrors used at least once
    #

    # ensure 3)
    if not ensure_rules(grid):
        return None

    lasers = set()
    for r in range(len(grid)):
        for c in range(len(grid[0])):
            if grid[r][c] == "L":
                lasers.add((r, c))

    # ensure 1) and 2)
    sinks = set()
    for pos in lasers:
        cur_pos = pos
        if pos[0] == 0:
            cur_dir = DIRS_MAP["down"]
        elif pos[0] == len(grid) - 1:
            cur_dir = DIRS_MAP["up"]
        elif pos[1] == 0:
            cur_dir = DIRS_MAP["right"]
        else:
            cur_dir = DIRS_MAP["left"]

        reached_border = False
        while not reached_border:
            cur_pos, cur_dir = laser_step(cur_pos, cur_dir, grid)
            if (cur_pos[0] in [0, len(grid) - 1]) or (cur_pos[1] in [0, len(grid[0]) - 1]):
                reached_border = True

        if cur_pos in sinks or cur_pos in lasers:
            return None
        sinks.add(cur_pos)
    
    return grid, tries + 1

MAX_MIRRORS = 7
MIN_ROWS = 5
MAX_ROWS = 5
MIN_COLS = 5
MAX_COLS = 5
MAX_LASERS = 4

grid = generate_puzzle(MIN_ROWS, MAX_ROWS, MIN_COLS, MAX_COLS, MAX_LASERS, MAX_MIRRORS, 100000)
print(grid)
