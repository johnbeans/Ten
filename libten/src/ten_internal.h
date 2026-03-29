/*
 * ten_internal.h — Internal declarations shared between libten .c files
 * NOT part of the public API.
 */

#ifndef TEN_INTERNAL_H
#define TEN_INTERNAL_H

#include "ten.h"

/* Arena: allocate n bytes, 8-byte aligned, zero-initialized.
 * Returns NULL if arena is full. */
void *ten__arena_alloc(ten_arena_t *a, size_t n);

/* Arena: allocate a new expression node. Increments node_count.
 * Returns NULL if arena full or node limit exceeded. */
ten_expr_t *ten__arena_new_expr(ten_arena_t *a, ten_type_t type);

#endif /* TEN_INTERNAL_H */
