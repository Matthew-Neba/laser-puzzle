CC = gcc
CFLAGS = -Wall -Wextra -std=c11
LDFLAGS = -lraylib

TARGET = game
SRC = laser-puzzle.c

all: $(TARGET)

verified_puzzles.h: verified_puzzles.py export_verified_puzzles_header.py
	python3 export_verified_puzzles_header.py

$(TARGET): $(SRC) verified_puzzles.h
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all run clean
