import random
from pathlib import Path

from generate_level import generate_puzzle
from optimal_solver import iddfs


OUTPUT_PATH = Path(__file__).with_name("verified_puzzles.h")

TARGETS = {
    7: {"count": 5, "sensor_counts": {4}, "generator_mirrors": 7},
    5: {"count": 5, "sensor_counts": {3, 4}, "generator_mirrors": 5},
    4: {"count": 5, "sensor_counts": {2, 3}, "generator_mirrors": 4},
    2: {"count": 5, "sensor_counts": {1, 2}, "generator_mirrors": 2},
}

CELL_EXPR = {
    "*": "{EMPTY, MIRROR_NONE, -1}",
    "ML": "{EMPTY, MIRROR_LEFT, -1}",
    "MR": "{EMPTY, MIRROR_RIGHT, -1}",
}


def strip_mirrors(grid):
    return [
        ["*" if cell in {"ML", "MR"} else cell for cell in row]
        for row in grid
    ]


def sensor_count(grid):
    return sum(cell.startswith("S") for row in grid for cell in row)


def cell_expr(token):
    if token in CELL_EXPR:
        return CELL_EXPR[token]

    cell_type = "LASER" if token[0] == "L" else "SENSOR"
    return f"{{{cell_type}, MIRROR_NONE, {token[1:]}}}"


def board_expr(board):
    rows = []
    for row in board:
        cells = ", ".join(cell_expr(cell) for cell in row)
        rows.append(f"            {{{cells}}}")
    return ",\n".join(rows)


def make_header(levels):
    lines = [
        "#ifndef VERIFIED_PUZZLES_H",
        "#define VERIFIED_PUZZLES_H",
        "",
        '#include "puzzle_types.h"',
        "",
        f"#define VERIFIED_PUZZLE_COUNT {len(levels)}",
        "",
        "typedef struct {",
        "    int optimal_mirrors;",
        "    int sensor_count;",
        "    Cell puzzle[INIT_ROWS][INIT_COLS];",
        "    Cell solution[INIT_ROWS][INIT_COLS];",
        "} VerifiedPuzzle;",
        "",
        "static const VerifiedPuzzle VERIFIED_PUZZLES[VERIFIED_PUZZLE_COUNT] = {",
    ]

    for level in levels:
        lines.extend([
            "    {",
            f"        .optimal_mirrors = {level['optimal_mirrors']},",
            f"        .sensor_count = {level['sensor_count']},",
            "        .puzzle = {",
            board_expr(level["puzzle"]),
            "        },",
            "        .solution = {",
            board_expr(level["solution"]),
            "        },",
            "    },",
        ])

    lines.extend([
        "};",
        "",
        "#endif",
    ])
    return "\n".join(lines) + "\n"


def generate_verified_puzzles(max_attempts=20000):
    found = {mirror_count: [] for mirror_count in TARGETS}
    seen_puzzles = set()
    attempts = 0

    while any(len(found[key]) < TARGETS[key]["count"] for key in TARGETS):
        attempts += 1
        if attempts > max_attempts:
            counts = {key: len(value) for key, value in found.items()}
            raise RuntimeError(f"Only generated {counts} after {max_attempts} attempts")

        unfilled = [
            key for key in TARGETS
            if len(found[key]) < TARGETS[key]["count"]
        ]
        desired_optimal = random.choice(unfilled)
        target = TARGETS[desired_optimal]
        min_sensors = min(target["sensor_counts"])
        max_sensors = max(target["sensor_counts"])
        generator_mirrors = target["generator_mirrors"]

        solved_grid, _tries = generate_puzzle(
            4,
            4,
            4,
            4,
            min_sensors,
            max_sensors,
            generator_mirrors,
            generator_mirrors,
            500,
        )
        if solved_grid is None:
            continue

        puzzle = strip_mirrors(solved_grid)
        sensors = sensor_count(puzzle)
        if sensors not in target["sensor_counts"]:
            continue

        puzzle_key = tuple(tuple(row) for row in puzzle)
        if puzzle_key in seen_puzzles:
            continue

        solution, optimal_mirrors = iddfs(puzzle, 7)
        if optimal_mirrors not in TARGETS:
            continue

        optimal_target = TARGETS[optimal_mirrors]
        if sensors not in optimal_target["sensor_counts"]:
            continue

        if len(found[optimal_mirrors]) >= optimal_target["count"]:
            continue

        seen_puzzles.add(puzzle_key)
        found[optimal_mirrors].append({
            "optimal_mirrors": optimal_mirrors,
            "sensor_count": sensors,
            "puzzle": puzzle,
            "solution": solution,
        })
        print(
            "found",
            optimal_mirrors,
            f"{len(found[optimal_mirrors])}/{optimal_target['count']}",
            "sensors",
            sensors,
            "attempts",
            attempts,
            flush=True,
        )

    levels = []
    for mirror_count in (7, 5, 4, 2):
        levels.extend(found[mirror_count])
    return levels


def main():
    levels = generate_verified_puzzles()
    OUTPUT_PATH.write_text(make_header(levels))
    print(f"wrote {len(levels)} levels to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
