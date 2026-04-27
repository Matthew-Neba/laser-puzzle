#include <stdlib.h>
#include <time.h>
#include "raylib.h"

#define BOARD_IDX(cols, r, c) ((r) * (cols) + (c))

#include "level_generation/puzzle_types.h"
#include "level_generation/verified_puzzles.h"

static const int CELL_SIZE = 80;
static const Color LASER_COLORS[] = {SKYBLUE, RED, GREEN, YELLOW, BLUE, ORANGE, PURPLE, MAGENTA};


typedef struct {
    // previous game fields, in render version
    int ROWS;
    int COLS;
    Cell *board;
    Texture2D sprites;
    Texture2D background;
    Font font;
    int assets_loaded;
    int should_close;
    int sinks_found;
    int mirrors_placed;
    int moves_made;
    int game_over;
    int total_sinks;
    int optimal_mirrors;
} LaserPuzzle;


// reset the game state, start a new game
void c_reset(LaserPuzzle* env) {
    env->should_close = 0;
    env->sinks_found = 0;
    env->mirrors_placed = 0;
    env->moves_made = 0;
    env->game_over = 0;

    if (env->board == NULL) {
        env->board = calloc(env->ROWS * env->COLS, sizeof(Cell));
    }

    int level_index = rand() % VERIFIED_PUZZLE_COUNT;
    const VerifiedPuzzle* level = &VERIFIED_PUZZLES[level_index];
    env->total_sinks = level->sensor_count;
    env->optimal_mirrors = level->optimal_mirrors;

    for (int r = 0; r < env->ROWS; r++) {
        for (int c = 0; c < env->COLS; c++) {
            env->board[BOARD_IDX(env->COLS, r, c)] = level->puzzle[r][c];
        }
    }
}


// advance state
void c_step(LaserPuzzle* env) {
    // force a new reset of the game
    if (IsKeyPressed(KEY_R)) {
        c_reset(env);
        return;
    }

    int gridWidth = env->COLS * CELL_SIZE;
    int gridHeight = env->ROWS * CELL_SIZE;
    int offsetX = (GetScreenWidth() - gridWidth) / 2;
    int offsetY = (GetScreenHeight() - gridHeight) / 2;

    if (!IsMouseButtonPressed(MOUSE_LEFT_BUTTON)) {
        return;
    }

    Vector2 mouse = GetMousePosition();
    int c = (mouse.x - offsetX) / CELL_SIZE;
    int r = (mouse.y - offsetY) / CELL_SIZE;

    // we selected something on / outside the grid border
    if (r < 1 || r >= env->ROWS - 1 || c < 1 || c >= env->COLS - 1) {
        return;
    }

    // we can select any interior cell to cycle the mirros
    Cell* cell = &env->board[BOARD_IDX(env->COLS, r, c)];
    cell->mirror = (cell->mirror + 1) % 3;
    env->moves_made++;

    // now we need to detect and update how many lasers are in thier sink and mirros are placed
    env->sinks_found = 0;
    env->mirrors_placed = 0;
    for (int r = 0; r < env->ROWS; r++) {
        for (int c = 0; c < env->COLS; c++) {
            Cell boardCell = env->board[BOARD_IDX(env->COLS, r, c)];
            if (boardCell.mirror != MIRROR_NONE) {
                env->mirrors_placed++;
            }

            if (boardCell.type == LASER) {
                int laserId = boardCell.id;
                int curR = r;
                int curC = c;
                int dr = 0;
                int dc = 0;

                if (curR == 0) {
                    dr = 1;
                } else if (curR == env->ROWS - 1) {
                    dr = -1;
                } else if (curC == 0) {
                    dc = 1;
                } else if (curC == env->COLS - 1) {
                    dc = -1;
                }

                while (curR + dr >= 0 && curR + dr < env->ROWS && curC + dc >= 0 && curC + dc < env->COLS) {
                    curR += dr;
                    curC += dc;

                    Cell hitCell = env->board[BOARD_IDX(env->COLS, curR, curC)];
                    if (hitCell.type == SENSOR) {
                        if (hitCell.id == laserId) {
                            env->sinks_found++;
                        }
                        break;
                    } else if (hitCell.type == LASER) {
                        break;
                    } else if (hitCell.mirror == MIRROR_LEFT) {
                        int oldDr = dr;
                        dr = dc;
                        dc = oldDr;
                    } else if (hitCell.mirror == MIRROR_RIGHT) {
                        int oldDr = dr;
                        dr = -dc;
                        dc = -oldDr;
                    }
                }
            }
        }
    }

    // we have completed the game
    env->game_over = env->sinks_found == env->total_sinks && env->mirrors_placed == env->optimal_mirrors;
}


void trace_laser(LaserPuzzle * env, int r, int c) {
    Cell laser = env->board[BOARD_IDX(env->COLS, r, c)];
    Color laserColor = LASER_COLORS[laser.id % 8];

    int dr = 0;
    int dc = 0;
    if (r == 0) {
        dr = 1;
    } else if (r == env->ROWS - 1) {
        dr = -1;
    } else if (c == 0) {
        dc = 1;
    } else if (c == env->COLS - 1) {
        dc = -1;
    }

    int gridWidth = env->COLS * CELL_SIZE;
    int gridHeight = env->ROWS * CELL_SIZE;
    int offsetX = (GetScreenWidth() - gridWidth) / 2;
    int offsetY = (GetScreenHeight() - gridHeight) / 2;

    int curR = r;
    int curC = c;

    while (curR + dr >= 0 && curR + dr < env->ROWS && curC + dc >= 0 && curC + dc < env->COLS) {
        int nextR = curR + dr;
        int nextC = curC + dc;

        Vector2 start = {
            offsetX + curC * CELL_SIZE + CELL_SIZE / 2.0f,
            offsetY + curR * CELL_SIZE + CELL_SIZE / 2.0f
        };
        Vector2 end = {
            offsetX + nextC * CELL_SIZE + CELL_SIZE / 2.0f,
            offsetY + nextR * CELL_SIZE + CELL_SIZE / 2.0f
        };

        // offset so that the puffer fish mouth not blocked by lasers
        if (env->board[BOARD_IDX(env->COLS, curR, curC)].type == LASER) {
            start.x += dc * 27.0f;
            start.y += dr * 27.0f;
        }

        DrawLineEx(start, end, 7, Fade(laserColor, 0.65f));
        DrawLineEx(start, end, 3, Fade(WHITE, 0.75f));

        // update current cell
        curR = nextR;
        curC = nextC;
        
        // update direction
        Cell cell = env->board[BOARD_IDX(env->COLS, curR, curC)];
        if (cell.mirror == MIRROR_LEFT) {
            int oldDr = dr;
            dr = dc;
            dc = oldDr;
        } else if (cell.mirror == MIRROR_RIGHT) {
            int oldDr = dr;
            dr = -dc;
            dc = -oldDr;
        }
    }
}

void draw_lasers(LaserPuzzle *env) {
    for (int r = 0; r < env->ROWS; r++) {
        for (int c = 0; c < env->COLS; c++) {
            if (env->board[BOARD_IDX(env->COLS, r, c)].type == LASER) {
                trace_laser(env, r, c);
            }
        }
    }
}

// render the state
void c_render(LaserPuzzle* env) {
    // init window
    if (!IsWindowReady()) {
        InitWindow(800, 700, "laser puzzle");
        SetTargetFPS(60);
    }
    
    // load puffers and font
    if (!env->assets_loaded) {
        env->sprites = LoadTexture("assets/puffers.png");
        env->font = LoadFontEx("assets/JetBrainsMono-SemiBold.ttf", 32, NULL, 0);
        env->assets_loaded = 1;
    }

    // signal env to close
    if (WindowShouldClose()) {
        env->should_close = 1;
        return;
    }

    BeginDrawing();

    ClearBackground((Color){10, 12, 24, 255});

    // draw the centered grid
    int gridWidth = env->COLS * CELL_SIZE;
    int gridHeight = env->ROWS * CELL_SIZE;
    int offsetX = (GetScreenWidth() - gridWidth) / 2;
    int offsetY = (GetScreenHeight() - gridHeight) / 2;

    for (int r = 0; r < env->ROWS; r++) {
        for (int c = 0; c < env->COLS; c++) {
            int x = offsetX + c * CELL_SIZE;
            int y = offsetY + r * CELL_SIZE;

            // draw the grey "X" for the mirrors (exclude border cells)
            if (r > 0 && r < env->ROWS - 1 && c > 0 && c < env->COLS - 1) {
                DrawLineEx((Vector2){x + 20, y + 20}, (Vector2){x + CELL_SIZE - 20, y + CELL_SIZE - 20}, 2, Fade(GRAY, 0.25f));
                DrawLineEx((Vector2){x + CELL_SIZE - 20, y + 20}, (Vector2){x + 20, y + CELL_SIZE - 20}, 2, Fade(GRAY, 0.25f));
            }

            Cell cell = env->board[BOARD_IDX(env->COLS, r, c)];

            if (cell.mirror == MIRROR_LEFT) {
                DrawLineEx((Vector2){x + 10, y + 10}, (Vector2){x + CELL_SIZE - 10, y + CELL_SIZE - 10}, 12, Fade(VIOLET, 0.55f));
                DrawLineEx((Vector2){x + 10, y + 10}, (Vector2){x + CELL_SIZE - 10, y + CELL_SIZE - 10}, 8, Fade(SKYBLUE, 0.9f));
                DrawLineEx((Vector2){x + 10, y + 10}, (Vector2){x + CELL_SIZE - 10, y + CELL_SIZE - 10}, 4, BLACK);
            } else if (cell.mirror == MIRROR_RIGHT) {
                DrawLineEx((Vector2){x + CELL_SIZE - 10, y + 10}, (Vector2){x + 10, y + CELL_SIZE - 10}, 12, Fade(VIOLET, 0.55f));
                DrawLineEx((Vector2){x + CELL_SIZE - 10, y + 10}, (Vector2){x + 10, y + CELL_SIZE - 10}, 8, Fade(SKYBLUE, 0.9f));
                DrawLineEx((Vector2){x + CELL_SIZE - 10, y + 10}, (Vector2){x + 10, y + CELL_SIZE - 10}, 4, BLACK);
            } else if (cell.type == LASER) {
                int spriteIndex = cell.id % 8;
                Rectangle source = {spriteIndex * 64.0f, 392.0f, 64.0f, 46.0f};
                Rectangle dest = {x + CELL_SIZE / 2.0f, y + CELL_SIZE / 2.0f, 64.0f, 46.0f};

                // need to make sure pufferfish are facing the right direction
                Vector2 origin = {32.0f, 23.0f};
                float rotation = 0.0f;

                if (r == 0) {
                    rotation = 90.0f;
                } else if (r == env->ROWS - 1) {
                    rotation = -90.0f;
                } else if (c == env->COLS - 1) {
                    rotation = 180.0f;
                    source.height = -source.height;
                }

                DrawTexturePro(env->sprites, source, dest, origin, rotation, WHITE);
            } else if (cell.type == SENSOR) {
                int spriteIndex = cell.id % 8;
                Rectangle source = {spriteIndex * 64.0f, 529.0f, 64.0f, 30.0f};
                Rectangle dest = {x + 12.0f, y + 24.0f, 56.0f, 26.0f};
                DrawTexturePro(env->sprites, source, dest, (Vector2){0}, 0.0f, WHITE);
            }
        }
    }

    // draw the lasers
    draw_lasers(env);

    // draw the sinks found and mirrors used
    const float fontSize = 32.0f;
    const float spacing = 1.0f;
    const char* sinksText = TextFormat("Sinks: %i/%i", env->sinks_found, env->total_sinks);
    const char* movesText = TextFormat("Moves: %i", env->moves_made);
    const char* mirrorsText = TextFormat("Mirrors: %i/%i", env->mirrors_placed, env->optimal_mirrors);
    Vector2 movesSize = MeasureTextEx(env->font, movesText, fontSize, spacing);
    Vector2 mirrorsSize = MeasureTextEx(env->font, mirrorsText, fontSize, spacing);

    DrawTextEx(env->font, sinksText, (Vector2){16, 14}, fontSize, spacing, RAYWHITE);
    DrawTextEx(env->font, movesText, (Vector2){GetScreenWidth() - movesSize.x - 16, GetScreenHeight() - fontSize - 16}, fontSize, spacing, RAYWHITE);
    DrawTextEx(env->font, mirrorsText, (Vector2){GetScreenWidth() - mirrorsSize.x - 16, 14}, fontSize, spacing, RAYWHITE);

    // we only get here if we have found all sinks but not in the optimal mirror count (c_step will generate new
    // level if we foudn the optimal mirror count)
    if (env->sinks_found == env->total_sinks) {
        const char* solvedText = "Puzzle solved! Can you do it with less mirrors?";
        if (env->game_over) {
            solvedText = "Optimal solve! Press R for the next puzzle.";
        }

        const float solvedFontSize = 24.0f;
        Vector2 solvedSize = MeasureTextEx(env->font, solvedText, solvedFontSize, spacing);
        DrawTextEx(env->font, solvedText, (Vector2){(GetScreenWidth() - solvedSize.x) / 2.0f, 56}, solvedFontSize, spacing, RAYWHITE);
    }

    EndDrawing();
}


void free_laser_puzzle(LaserPuzzle * env) {
    free(env->board);
    env->board = NULL;
}

// any closing preparations, also close the renderer, free any allocated memory
void c_close(LaserPuzzle* env) {
    if (env->assets_loaded) {
        UnloadTexture(env->sprites);
        UnloadFont(env->font);
        env->assets_loaded = 0;
    }

    if (IsWindowReady()) {
        CloseWindow();
    }

    // free LaserPuzzle
    free_laser_puzzle(env);
}


int main() {
    srand((unsigned int)time(NULL));

    LaserPuzzle env = {
        .ROWS = INIT_ROWS,
        .COLS = INIT_COLS,
    };

    c_reset(&env);

    while (!env.should_close) {
        c_step(&env);
        c_render(&env);
    }

    c_close(&env);
    return 0;
}
