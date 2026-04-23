import random
from typing import List

DIRS = [(1,0), (-1,0), (0, 1), (0, -1)]
DIRS_MAP = {
    "down": DIRS[0],
    "up": DIRS[1],
    "right": DIRS[2],
    "left": DIRS[3] 
}

# returns a grid with one higher in each dimension (to store the border for the lasers sources and sinks)
def generate_grid(
    MIN_ROWS: int,
    MAX_ROWS: int,
    MIN_COLS: int,
    MAX_COLS: int,
    MIN_LASERS: int,
    MAX_LASERS: int,
) -> List[List[str]]:
    puzzle_rows = random.randint(MIN_ROWS, MAX_ROWS)
    puzzle_cols = random.randint(MIN_COLS, MAX_COLS)
    possible_lasers = random.randint(MIN_LASERS, MAX_LASERS)
    
    # we will augment the grid by one to store the laser sources and sinks on the border
    grid = [['*'] * (puzzle_cols + 2) for _ in range(puzzle_rows + 2)]

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
    laser_positions = random.sample(laser_choices, min(len(laser_choices),possible_lasers))

    # place lasers
    for idx,pos in enumerate(laser_positions):
        grid[pos[0]][pos[1]] = f"L{idx}"
    
    return grid


# take a step with laser, give new pos of laser, give new direction of laser also (None if at border)
def laser_step(
    pos: tuple[int, int],
    direction: tuple[int, int],
    grid: List[List[str]],
) -> tuple:
    
    ROWS, COLS = len(grid), len(grid[0])

    # take a step and check if we are at end / hit a mirror
    nr = pos[0] + direction[0]
    nc = pos[1] + direction[1]

    # we have hit the border
    if not (0 < nr < ROWS - 1 and 0 < nc < COLS - 1):
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
            elif grid[r][c][0] == "L":
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
        next_pos, next_dir = laser_step(cur_pos, cur_dir, grid)
        while (next_pos[0] not in [0, ROWS - 1]) and (next_pos[1] not in [0, COLS - 1]):
            """
            criteria: 
            - no laser loops forever - ensure while building, DONE 

            - no two lasers ever join to be in same spot and same direction, since we cant break mirror paths, guaranteed to give duplicate sinks - ensure while building  , DONE

            - every placed mirror is actually used by at least one beam - ensure while building, don't place mirror if breaks other ones paths, DONE
            """

            # make sure we havent:
            # 1) seen another laser be in the same spot with same dir -> same ending, invalid
            # 2) seen this same laser in the same spot with same dir -> cycle, invalid
            if (next_pos, next_dir) in visited_lasers:
                return False
            
            # remove from mirrors set to indicate we have visited this mirror
            if next_pos in mirrors:
                mirrors.remove(next_pos)

            # add to visited lasers set, store direction as well
            visited_lasers.add((next_pos, next_dir))

            next_pos, next_dir = laser_step(next_pos, next_dir, grid)

    # make sure that all placed mirrors are being used
    if len(mirrors) != 0:
        return False

    return True


#  expects a valid grid that follows the rules in ensure_rules
def place_a_mirror(grid):
    ROWS, COLS = len(grid), len(grid[0])

    lasers = set()
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c][0] == "L":
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
        
        next_pos, next_dir = laser_step(cur_pos, cur_dir, grid)
        while (next_pos[0] not in [0, ROWS - 1]) and (next_pos[1] not in [0, COLS - 1]):
            if grid[next_pos[0]][next_pos[1]] == '*':
                valid.append(next_pos)
            
            next_pos, next_dir = laser_step(next_pos, next_dir, grid)
    
    # Try valid slots in random order.
    # Duplicates bias toward cells hit by multiple lasers since using a list instead of a set
    random.shuffle(valid)

    for chosen in valid:
        orientations = ["ML", "MR"]
        random.shuffle(orientations)

        for orientation in orientations:
            grid[chosen[0]][chosen[1]] = orientation
            if ensure_rules(grid):
                return True
            
            # backtrack
            grid[chosen[0]][chosen[1]] = '*'

    return False


def generate_puzzle(
    MIN_ROWS,
    MAX_ROWS,
    MIN_COLS,
    MAX_COLS,
    MIN_LASERS,
    MAX_LASERS,
    MIN_MIRRORS,
    MAX_MIRRORS,
    MAX_TRIES,
) -> tuple:
    
    need_mirrors = random.randint(MIN_MIRRORS, MAX_MIRRORS)

    for tries in range(MAX_TRIES):
        # create a fresh grid for this full attempt
        grid = generate_grid(MIN_ROWS, MAX_ROWS, MIN_COLS, MAX_COLS, MIN_LASERS, MAX_LASERS)

        for _ in range(need_mirrors):
            if not place_a_mirror(grid):
                break
        else:
            break
    else:
        return None, None
    
    # we have followed all intermediary rules, do one more check for good measure and to ensure all conditions
    # are actually met
    #
    # 1) no two sinks in same spot
    # 2) no sink at a start
    # 3) all mirrors used at least once
    #

    # ensure 3)
    if not ensure_rules(grid):
        return None, None

    ROWS, COLS = len(grid), len(grid[0])

    lasers = set()
    for r in range(ROWS):
        for c in range(COLS):
            if grid[r][c][0] == "L":
                lasers.add((r, c))

    # ensure 1) and 2)
    sinks = set()
    insert_sinks = []
    for start in lasers:
        cur_pos = start
        if start[0] == 0:
            cur_dir = DIRS_MAP["down"]
        elif start[0] == len(grid) - 1:
            cur_dir = DIRS_MAP["up"]
        elif start[1] == 0:
            cur_dir = DIRS_MAP["right"]
        else:
            cur_dir = DIRS_MAP["left"]

        next_pos, next_dir = laser_step(cur_pos, cur_dir, grid)
        while (next_pos[0] not in [0, ROWS - 1]) and (next_pos[1] not in [0, COLS - 1]):
            next_pos, next_dir = laser_step(next_pos, next_dir, grid)
        
        if next_pos in sinks or next_pos in lasers:
            return None, None
        
        laser_number = grid[start[0]][start[1]][1:]
        sinks.add(next_pos)
        insert_sinks.append((next_pos, laser_number))
    
    # now make sure the source, sink pairs are paired and labelled correctly in the graph
    for sink, laser_number in insert_sinks:
        grid[sink[0]][sink[1]] = f"S{laser_number}"

    return grid, tries + 1

if __name__ == "__main__":

    MIN_MIRRORS = 7
    MAX_MIRRORS = 7
    MIN_ROWS = 4
    MAX_ROWS = 4
    MIN_COLS = 4
    MAX_COLS = 4
    MIN_LASERS = 3
    MAX_LASERS = 4

    grid, attempts = generate_puzzle(
        MIN_ROWS,
        MAX_ROWS,
        MIN_COLS,
        MAX_COLS,
        MIN_LASERS,
        MAX_LASERS,
        MIN_MIRRORS,
        MAX_MIRRORS,
        100000,
    )


    print(grid)
