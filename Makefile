CC = gcc
CFLAGS = -Wall -Wextra
LDFLAGS = -lraylib

TARGET = game
SRC = laser_puzzle.c

all: $(TARGET)

generate-levels:
	python3 level_generation/export_verified_puzzles_header.py

$(TARGET): $(SRC) laser_puzzle.h level_generation/puzzle_types.h level_generation/verified_puzzles.h
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

# ensure we don't accidentally mix up commands for files while running make
.PHONY: all run clean generate-levels
