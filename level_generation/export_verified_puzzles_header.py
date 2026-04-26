from pathlib import Path

from verified_puzzles import VERIFIED_PUZZLES


OUTPUT_PATH = Path(__file__).with_name("verified_puzzles.h")

CELL_EXPR = {
    "*": "{EMPTY, MIRROR_NONE, -1}",
    "ML": "{EMPTY, MIRROR_LEFT, -1}",
    "MR": "{EMPTY, MIRROR_RIGHT, -1}",
}


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


def main():
    lines = [
        "#ifndef VERIFIED_PUZZLES_H",
        "#define VERIFIED_PUZZLES_H",
        "",
        f"#define VERIFIED_PUZZLE_COUNT {len(VERIFIED_PUZZLES)}",
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

    for level in VERIFIED_PUZZLES:
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

    OUTPUT_PATH.write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
