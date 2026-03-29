/*
 * arena.c — Arena (region-based) allocator for libten
 *
 * All Ten expressions are allocated from an arena. One alloc per message,
 * one free when done. No individual malloc/free pairs, no fragmentation,
 * no leaks, no use-after-free.
 */

#include "ten.h"
#include <stdlib.h>
#include <string.h>

ten_error_t ten_arena_init(ten_arena_t *a, size_t size) {
    if (!a) return TEN_ERROR_NULL_ARG;
    if (size == 0) size = TEN_DEFAULT_ARENA_SIZE;

    a->base = (uint8_t *)malloc(size);
    if (!a->base) return TEN_ERROR_ARENA_FULL;

    a->size       = size;
    a->used       = 0;
    a->depth      = 0;
    a->node_count = 0;
    return TEN_OK;
}
void ten_arena_free(ten_arena_t *a) {
    if (!a) return;
    free(a->base);
    a->base       = NULL;
    a->size       = 0;
    a->used       = 0;
    a->depth      = 0;
    a->node_count = 0;
}

void ten_arena_reset(ten_arena_t *a) {
    if (!a) return;
    a->used       = 0;
    a->depth      = 0;
    a->node_count = 0;
    /* base and size unchanged — reuse the same block */
}

size_t ten_arena_remaining(const ten_arena_t *a) {
    if (!a) return 0;
    return a->size - a->used;
}

/*
 * Internal: allocate n bytes from the arena, aligned to 8 bytes.
 * Returns NULL if the arena is full.
 */
void *ten__arena_alloc(ten_arena_t *a, size_t n) {
    /* Align to 8-byte boundary */
    size_t aligned = (n + 7) & ~(size_t)7;

    if (a->used + aligned > a->size)
        return NULL;

    void *ptr = a->base + a->used;
    a->used += aligned;
    memset(ptr, 0, aligned);  /* zero-init for safety */
    return ptr;
}
