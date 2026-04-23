#include "raylib.h"

#define ROWS 6
#define COLS 6

typedef enum {
    EMPTY,
    MIRROR_LEFT,
    MIRROR_RIGHT,
    LASER,
    SENSOR
} CellType;

typedef struct {
    CellType type;
    int id;
} Cell;

// will hardcode a board for now
Cell board[ROWS][COLS] = {
    {{EMPTY,-1}, {EMPTY,-1}, {SENSOR,1}, {LASER,0}, {EMPTY,-1}, {EMPTY,-1}},
    {{EMPTY,-1}, {EMPTY,-1}, {MIRROR_LEFT,-1}, {MIRROR_LEFT,-1}, {MIRROR_LEFT,-1}, {EMPTY,-1}},
    {{LASER,1}, {EMPTY,-1}, {EMPTY,-1}, {MIRROR_RIGHT,-1}, {MIRROR_RIGHT,-1}, {EMPTY,-1}},
    {{EMPTY,-1}, {MIRROR_RIGHT,-1}, {EMPTY,-1}, {EMPTY,-1}, {MIRROR_LEFT,-1}, {EMPTY,-1}},
    {{EMPTY,-1}, {EMPTY,-1}, {EMPTY,-1}, {EMPTY,-1}, {EMPTY,-1}, {EMPTY,-1}},
    {{EMPTY,-1}, {SENSOR,2}, {EMPTY,-1}, {SENSOR,0}, {LASER,2}, {EMPTY,-1}},
};


int main() {
    // init window
    InitWindow(800, 800, "laser puzzle");

    while (!WindowShouldClose()) {

        // 1) take in user input
        // 2) update input/state
        BeginDrawing();
        ClearBackground(RAYWHITE);

        // 3) Draw
        int cellSize = 80;
        int offsetX = 100;
        int offsetY = 100;

        for (int r = 0; r < ROWS; r++) {
            for (int c = 0; c < COLS; c++) {
                int x = offsetX + c * cellSize;
                int y = offsetY + r * cellSize;

                DrawRectangleLines(x, y, cellSize, cellSize, BLACK);

                Cell cell = board[r][c];

                if (cell.type == MIRROR_LEFT) {
                    DrawLine(x + 10, y + 10, x + cellSize - 10, y + cellSize - 10, BLACK);
                } else if (cell.type == MIRROR_RIGHT) {
                    DrawLine(x + cellSize - 10, y + 10, x + 10, y + cellSize - 10, BLACK);
                } else if (cell.type == LASER) {
                    DrawText(TextFormat("L%d", cell.id), x + 20, y + 25, 24, RED);
                } else if (cell.type == SENSOR) {
                    DrawText(TextFormat("S%d", cell.id), x + 20, y + 25, 24, BLUE);
                }
            }
        }

        EndDrawing();
    }

    CloseWindow();
}
