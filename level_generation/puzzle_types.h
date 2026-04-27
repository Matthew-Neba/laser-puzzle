#ifndef PUZZLE_TYPES_H
#define PUZZLE_TYPES_H

const int INIT_ROWS = 6;
const int INIT_COLS = 6;

typedef enum {
    EMPTY,
    LASER,
    SENSOR
} CellType;

typedef enum {
    MIRROR_NONE,
    MIRROR_RIGHT,
    MIRROR_LEFT
} MirrorState;

typedef struct {
    CellType type;
    MirrorState mirror;
    int id;
} Cell;

#endif
