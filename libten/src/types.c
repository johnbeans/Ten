/*
 * types.c — Kernel type constructors and helpers
 */

#include "ten.h"
#include "ten_internal.h"
#include <string.h>

/* ── Internal: allocate a new expression node ─────────────── */

ten_expr_t *ten__arena_new_expr(ten_arena_t *a, ten_type_t type) {
    if (!a) return NULL;
    if (a->node_count >= TEN_MAX_CHILDREN) return NULL;

    ten_expr_t *e = (ten_expr_t *)ten__arena_alloc(a, sizeof(ten_expr_t));
    if (!e) return NULL;

    e->type   = type;
    e->facets = NULL;
    a->node_count++;
    return e;
}

/* ── Scalar ───────────────────────────────────────────────── */

ten_expr_t *ten_scalar(ten_arena_t *a, uint16_t dimension,
                       double value, uint8_t precision) {    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_SCALAR);
    if (!e) return NULL;

    e->data.scalar.dimension = dimension;
    e->data.scalar.value     = value;
    e->data.scalar.precision = precision;
    return e;
}

/* ── Reference ────────────────────────────────────────────── */

ten_expr_t *ten_ref(ten_arena_t *a, const uint8_t hash[TEN_HASH_SIZE]) {
    if (!hash) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_REFERENCE);
    if (!e) return NULL;

    memcpy(e->data.ref.hash, hash, TEN_HASH_SIZE);
    return e;
}

/* ── Identity ─────────────────────────────────────────────── */

ten_expr_t *ten_identity(ten_arena_t *a, const uint8_t *pubkey,
                         uint16_t keylen) {
    if (!pubkey || keylen == 0 || keylen > TEN_MAX_PUBKEY_SIZE)
        return NULL;
    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_IDENTITY);
    if (!e) return NULL;

    memcpy(e->data.identity.pubkey, pubkey, keylen);
    e->data.identity.keylen = keylen;
    return e;
}

/* ── Assertion ────────────────────────────────────────────── */

ten_expr_t *ten_assertion(ten_arena_t *a, ten_expr_t *claim,
                          ten_expr_t *who, double confidence) {
    if (!claim || !who) return NULL;
    if (confidence < 0.0 || confidence > 1.0) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_ASSERTION);
    if (!e) return NULL;

    e->data.assertion.claim      = claim;
    e->data.assertion.who        = who;
    e->data.assertion.confidence = confidence;
    return e;
}

/* ── Operation ────────────────────────────────────────────── */

ten_expr_t *ten_operation(ten_arena_t *a, uint16_t verb,
                          ten_expr_t **args, uint16_t nargs) {    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_OPERATION);
    if (!e) return NULL;

    e->data.operation.verb  = verb;
    e->data.operation.nargs = nargs;

    if (nargs > 0 && args) {
        ten_expr_t **argcopy = (ten_expr_t **)ten__arena_alloc(
            a, nargs * sizeof(ten_expr_t *));
        if (!argcopy) return NULL;
        memcpy(argcopy, args, nargs * sizeof(ten_expr_t *));
        e->data.operation.args = argcopy;
    } else {
        e->data.operation.args = NULL;
    }

    return e;
}

/* ── Structure ────────────────────────────────────────────── */

ten_expr_t *ten_structure(ten_arena_t *a, ten_expr_t **members,
                          uint16_t nmembers) {
    ten_expr_t *e = ten__arena_new_expr(a, TEN_TYPE_STRUCTURE);
    if (!e) return NULL;

    e->data.structure.nmembers = nmembers;
    if (nmembers > 0 && members) {
        ten_expr_t **mcopy = (ten_expr_t **)ten__arena_alloc(
            a, nmembers * sizeof(ten_expr_t *));
        if (!mcopy) return NULL;
        memcpy(mcopy, members, nmembers * sizeof(ten_expr_t *));
        e->data.structure.members = mcopy;
    } else {
        e->data.structure.members = NULL;
    }

    return e;
}
