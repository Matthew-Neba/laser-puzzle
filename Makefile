CC = gcc
CFLAGS = -Wall -Wextra -std=c11
LDFLAGS = -lraylib

TARGET = game
SRC = laser-puzzle.c

all: $(TARGET)

$(TARGET): $(SRC)
	$(CC) $(CFLAGS) $(SRC) -o $(TARGET) $(LDFLAGS)

run: $(TARGET)
	./$(TARGET)

clean:
	rm -f $(TARGET)

.PHONY: all run clean
