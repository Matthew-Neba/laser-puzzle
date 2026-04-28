#include "laser_puzzle.h"

int main() {
    srand((unsigned int)time(NULL));

    LaserPuzzle env = {0};

    // allocate memory, initialize the client
    c_reset(&env);
    env.client = make_client();

    while (!WindowShouldClose()) {
        if (IsKeyPressed(KEY_R)) {
            c_reset(&env);
        }

        if (IsMouseButtonPressed(MOUSE_LEFT_BUTTON)) {
            int gridWidth = env.COLS * CELL_SIZE;
            int gridHeight = env.ROWS * CELL_SIZE;
            int offsetX = (GetScreenWidth() - gridWidth) / 2;
            int offsetY = (GetScreenHeight() - gridHeight) / 2;

            Vector2 mouse = GetMousePosition();
            int c = (mouse.x - offsetX) / CELL_SIZE;
            int r = (mouse.y - offsetY) / CELL_SIZE;

            if (r >= 1 && r < env.ROWS - 1 && c >= 1 && c < env.COLS - 1) {
                Cell* cell = &env.board[BOARD_IDX(env.COLS, r, c)];
                int mirror_action = (cell->mirror + 1) % ACTIONS_PER_CELL;
                int cell_idx = (r - 1) * INNER_COLS + (c - 1);
                env.actions[0] = (float)(cell_idx * ACTIONS_PER_CELL + mirror_action);
                c_step(&env);
            }
        }

        c_render(&env);
    }

    // deallocate memory, close client
    close_client(env.client);
    env.client = NULL;
    c_close(&env);

}
