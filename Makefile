CC = gcc
CFLAGS = -Wall -Wextra -std=c11
LDFLAGS = -lraylib

TARGET = game
SRC = laser-puzzle.c

all: $(TARGET)

generate-levels:
	python3 level_generation/export_verified_puzzles_header.py

$(TARGET): $(SRC) level_generation/verified_puzzles.h
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all run clean generate-levels
