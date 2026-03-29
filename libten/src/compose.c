/*
 * compose.c — Algebraic composition operations
 *
 * These implement the core of Ten's algebra:
 *   Sequence (⊕)  — ordered combination ("A then B")
 *   Product  (⊗)  — parallel facets ("A and B simultaneously")
 *   Nesting  (λ)  — envelope wrapping payload
 *   Union    (∪)  — set union
 *   Intersect(∩)  — set intersection
 *   Project  (π)  — extract dimensions from an expression
 *
 * All operations are CLOSED: composing valid expressions always
 * produces a valid expression. This is the fundamental guarantee.
 */

#include "ten.h"
#include "ten_internal.h"
#include <string.h>

/* ── Sequence (⊕) ─────────────────────────────────────────── */

ten_expr_t *ten_sequence(ten_arena_t *a, ten_expr_t *left,
                         ten_expr_t *right) {
    if (!left || !right) return NULL;
    if (a->depth >= TEN_MAX_EXPRESSION_DEPTH) return NULL;
    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_SEQUENCE);
    if (!e) return NULL;

    e->data.pair.left  = left;
    e->data.pair.right = right;
    return e;
}

/* ── Product (⊗) ──────────────────────────────────────────── */

ten_expr_t *ten_product(ten_arena_t *a, ten_expr_t *left,
                        ten_expr_t *right) {
    if (!left || !right) return NULL;
    if (a->depth >= TEN_MAX_EXPRESSION_DEPTH) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_PRODUCT);
    if (!e) return NULL;

    e->data.pair.left  = left;
    e->data.pair.right = right;
    return e;
}

/* ── Nesting (λ) ──────────────────────────────────────────── */

ten_expr_t *ten_nest(ten_arena_t *a, ten_expr_t *envelope,
                     ten_expr_t *payload) {    if (!envelope || !payload) return NULL;
    if (a->depth >= TEN_MAX_EXPRESSION_DEPTH) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_NESTING);
    if (!e) return NULL;

    e->data.nesting.envelope = envelope;
    e->data.nesting.payload  = payload;
    return e;
}

/* ── Union (∪) ────────────────────────────────────────────── */

ten_expr_t *ten_union(ten_arena_t *a, ten_expr_t *left,
                      ten_expr_t *right) {
    if (!left || !right) return NULL;
    if (a->depth >= TEN_MAX_EXPRESSION_DEPTH) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_UNION);
    if (!e) return NULL;

    e->data.pair.left  = left;
    e->data.pair.right = right;
    return e;
}

/* ── Intersect (∩) ────────────────────────────────────────── */
ten_expr_t *ten_intersect(ten_arena_t *a, ten_expr_t *left,
                          ten_expr_t *right) {
    if (!left || !right) return NULL;
    if (a->depth >= TEN_MAX_EXPRESSION_DEPTH) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_INTERSECT);
    if (!e) return NULL;

    e->data.pair.left  = left;
    e->data.pair.right = right;
    return e;
}

/* ── Project (π) ──────────────────────────────────────────── 
 *
 * Projection extracts a subset of an expression's facet dimensions.
 * The result is a new expression with only the requested facets.
 * If the source has no facets, returns a shallow copy.
 *
 * This is the "SELECT columns FROM table" of Ten — you ask for
 * urgency and cost, you get back just urgency and cost.
 */

ten_expr_t *ten_project(ten_arena_t *a, const ten_expr_t *expr,
                        const uint16_t *dims, uint16_t ndims) {
    if (!expr || !dims || ndims == 0) return NULL;
    /* Create a shallow copy of the expression */
    ten_expr_t *e = (ten_expr_t *)ten__arena_alloc(a, sizeof(ten_expr_t));
    if (!e) return NULL;
    memcpy(e, expr, sizeof(ten_expr_t));
    a->node_count++;

    /* If no facets on source, nothing to project */
    if (!expr->facets) {
        e->facets = NULL;
        return e;
    }

    /* Allocate a new facet vector with only requested dimensions */
    ten_facet_vec_t *fv = (ten_facet_vec_t *)ten__arena_alloc(
        a, sizeof(ten_facet_vec_t));
    if (!fv) return NULL;
    memset(fv, 0, sizeof(ten_facet_vec_t));

    for (uint16_t i = 0; i < ndims; i++) {
        uint16_t d = dims[i];
        if (d < TEN_MAX_FACETS && expr->facets->set[d]) {
            fv->values[d]    = expr->facets->values[d];
            fv->set[d]       = 1;
            fv->precision[d] = expr->facets->precision[d];
            fv->count++;
        }
    }

    e->facets = fv;
    return e;
}
