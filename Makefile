CC = gcc
CFLAGS = -Wall -Wextra
LDFLAGS = -lraylib -lm

HUMAN_TARGET = game_human
HUMAN_SRC = laser_puzzle_human.c

all: $(HUMAN_TARGET)

human: $(HUMAN_TARGET)

generate-levels:
	python3 level_generation/export_verified_puzzles_header.py

$(HUMAN_TARGET): $(HUMAN_SRC) level_generation/puzzle_types.h assets/laser_puzzle_levels.bin
	$(CC) $(CFLAGS) $(HUMAN_SRC) -o $(HUMAN_TARGET) $(LDFLAGS)

run: $(HUMAN_TARGET)
	./$(HUMAN_TARGET)

run-human: $(HUMAN_TARGET)
	./$(HUMAN_TARGET)

clean:
	rm -f $(HUMAN_TARGET)

# ensure we don't accidentally mix up commands for files while running make
.PHONY: all human run run-human clean generate-levels
