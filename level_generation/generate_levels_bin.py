import argparse
import os
import random
import struct
import sys
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))

from generate_level import generate_puzzle
from optimal_solver import iddfs


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "assets" / "laser_puzzle_levels.bin"
MAGIC = b"LPZL"
VERSION = 1
WORKERS = max(1, (os.cpu_count() or 1) // 2)

GROUP_ORDER = (7, 6, 5, 4, 2, 1)
GROUPS = {
    7: {"count": 8, "sensor_counts": {4}, "generator_mirrors": 7},
    6: {"count": 12, "sensor_counts": {4}, "generator_mirrors": 6},
    5: {"count": 25, "sensor_counts": {3, 4}, "generator_mirrors": 5},
    4: {"count": 25, "sensor_counts": {2, 3}, "generator_mirrors": 4},
    2: {"count": 25, "sensor_counts": {1, 2}, "generator_mirrors": 2},
    1: {"count": 5, "sensor_counts": {1}, "generator_mirrors": 1},
}

CELL_TYPE_EMPTY = 0
CELL_TYPE_LASER = 1
CELL_TYPE_SENSOR = 2
MIRROR_NONE = 0
MIRROR_RIGHT = 1
MIRROR_LEFT = 2


def strip_mirrors(grid):
    return [["*" if cell in {"ML", "MR"} else cell for cell in row] for row in grid]


def sensor_count(grid):
    return sum(cell.startswith("S") for row in grid for cell in row)


def encode_cell(token):
    if token == "*":
        return CELL_TYPE_EMPTY, MIRROR_NONE, -1
    if token == "MR":
        return CELL_TYPE_EMPTY, MIRROR_RIGHT, -1
    if token == "ML":
        return CELL_TYPE_EMPTY, MIRROR_LEFT, -1
    if token.startswith("L"):
        return CELL_TYPE_LASER, MIRROR_NONE, int(token[1:])
    if token.startswith("S"):
        return CELL_TYPE_SENSOR, MIRROR_NONE, int(token[1:])
    raise ValueError(f"Unknown cell token: {token}")


def write_levels_bin(levels, output_path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as file:
        file.write(MAGIC)
        file.write(struct.pack("<II", VERSION, len(levels)))
        for level in levels:
            file.write(struct.pack("<ii", level["optimal_mirrors"], level["sensor_count"]))
            for row in level["puzzle"]:
                for token in row:
                    file.write(struct.pack("<BBbB", *encode_cell(token), 0))


def make_candidate(attempt, desired_optimal):
    group = GROUPS[desired_optimal]
    min_sensors = min(group["sensor_counts"])
    max_sensors = max(group["sensor_counts"])
    generator_mirrors = group["generator_mirrors"]

    solved_grid, _tries = generate_puzzle(
        4, 4, 4, 4,
        min_sensors, max_sensors,
        generator_mirrors, generator_mirrors,
        100,
    )
    if solved_grid is None:
        return {
            "attempt": attempt,
            "desired_optimal": desired_optimal,
            "puzzle": None,
        }

    puzzle = strip_mirrors(solved_grid)
    solution, optimal_mirrors = iddfs(puzzle, 7)
    return {
        "attempt": attempt,
        "desired_optimal": desired_optimal,
        "puzzle": puzzle,
        "sensors": sensor_count(puzzle),
        "optimal_mirrors": optimal_mirrors,
        "has_solution": solution is not None,
    }


def init_worker():
    random.seed()


def generate_verified_puzzles():
    found = {mirror_count: [] for mirror_count in GROUP_ORDER}
    seen_puzzles = set()

    def print_lower_optimal(attempt, desired_optimal, optimal_mirrors):
        found_counts = ",".join(f"{key}:{len(found[key])}" for key in GROUP_ORDER)
        print(
            f"optimal {optimal_mirrors} < goal {desired_optimal} "
            f"found=({found_counts}) attempt={attempt}",
            flush=True,
        )

    def unfilled_groups():
        return [
            mirror_count for mirror_count in GROUP_ORDER
            if len(found[mirror_count]) < GROUPS[mirror_count]["count"]
        ]

    attempt = 0
    pending = set()

    def submit_candidate(executor):
        nonlocal attempt
        unfilled = unfilled_groups()
        if not unfilled:
            return False
        attempt += 1
        desired_optimal = random.choice(unfilled)
        pending.add(executor.submit(make_candidate, attempt, desired_optimal))
        return True

    print(f"generating with {WORKERS} workers", flush=True)
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=init_worker) as executor:
        for _ in range(WORKERS):
            submit_candidate(executor)

        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                candidate = future.result()
                puzzle = candidate["puzzle"]
                if puzzle is None:
                    continue

                desired_optimal = candidate["desired_optimal"]
                optimal_mirrors = candidate["optimal_mirrors"]
                sensors = candidate["sensors"]

                puzzle_key = tuple(tuple(row) for row in puzzle)
                if puzzle_key in seen_puzzles:
                    continue

                if optimal_mirrors is not None and optimal_mirrors < desired_optimal:
                    print_lower_optimal(candidate["attempt"], desired_optimal, optimal_mirrors)

                if not candidate["has_solution"] or optimal_mirrors not in GROUPS:
                    continue
                if sensors not in GROUPS[optimal_mirrors]["sensor_counts"]:
                    continue
                if len(found[optimal_mirrors]) >= GROUPS[optimal_mirrors]["count"]:
                    continue

                seen_puzzles.add(puzzle_key)
                found[optimal_mirrors].append({
                    "optimal_mirrors": optimal_mirrors,
                    "sensor_count": sensors,
                    "puzzle": puzzle,
                })
                print(
                    "found",
                    optimal_mirrors,
                    f"{len(found[optimal_mirrors])}/{GROUPS[optimal_mirrors]['count']}",
                    "sensors",
                    sensors,
                    "attempts",
                    candidate["attempt"],
                    flush=True,
                )

            if not unfilled_groups():
                for future in pending:
                    future.cancel()
                break
            while len(pending) < WORKERS and unfilled_groups():
                submit_candidate(executor)

    return [level for mirror_count in GROUP_ORDER for level in found[mirror_count]]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    levels = generate_verified_puzzles()
    write_levels_bin(levels, args.output)
    print(f"wrote {len(levels)} levels to {args.output}")


if __name__ == "__main__":
    main()
