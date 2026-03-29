# Makefile for libten — Ten formal algebra library
#
# Targets:
#   make          — build libten.a (static library)
#   make test     — build and run all tests
#   make clean    — remove build artifacts
#   make debug    — build with debug symbols and sanitizers

CC       = cc
AR       = ar
CFLAGS   = -std=c11 -Wall -Wextra -Wpedantic -O2
CFLAGS  += -Iinclude
DEBUG_CFLAGS = -std=c11 -Wall -Wextra -Wpedantic -g -O0 \
               -fsanitize=address,undefined -Iinclude

SRC_DIR  = src
INC_DIR  = include
TEST_DIR = tests
BUILD    = build

SRCS = $(SRC_DIR)/arena.c \
       $(SRC_DIR)/types.c \
       $(SRC_DIR)/compose.c \
       $(SRC_DIR)/facets.c \
       $(SRC_DIR)/validate.c \
       $(SRC_DIR)/util.c \
       $(SRC_DIR)/serialize.c

OBJS = $(patsubst $(SRC_DIR)/%.c,$(BUILD)/%.o,$(SRCS))
LIB      = $(BUILD)/libten.a

.PHONY: all test clean debug

all: $(LIB)

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: $(SRC_DIR)/%.c $(INC_DIR)/ten.h $(SRC_DIR)/ten_internal.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(LIB): $(OBJS)
	$(AR) rcs $@ $^
	@echo "Built $(LIB)"

# ── Tests ─────────────────────────────────────────────────

TEST_SRCS = $(TEST_DIR)/test_main.c
TEST_BIN  = $(BUILD)/test_ten

test: $(LIB) $(TEST_SRCS)
	$(CC) $(CFLAGS) $(TEST_SRCS) -L$(BUILD) -lten -lm -o $(TEST_BIN)
	@echo "Running tests..."
	@./$(TEST_BIN)

debug: CFLAGS = $(DEBUG_CFLAGS)
debug: clean all	$(CC) $(DEBUG_CFLAGS) $(TEST_SRCS) -L$(BUILD) -lten -lm -o $(TEST_BIN)
	@echo "Running tests with sanitizers..."
	@./$(TEST_BIN)

clean:
	rm -rf $(BUILD)