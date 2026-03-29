/*
 * facets.c — Facet vector operations
 *
 * A facet vector is the "sortable header" of a Ten expression.
 * Urgency, cost, privilege, confidence — all are fixed-position
 * scalars that can be compared without parsing the expression body.
 *
 * This is what makes Ten messages sortable, filterable, and
 * prioritizable without LLM inference.
 */

#include "ten.h"
#include "ten_internal.h"
#include <string.h>
#include <math.h>

/* ── Initialize facet vector on an expression ─────────────── */

ten_error_t ten_facet_init(ten_arena_t *a, ten_expr_t *expr) {
    if (!a || !expr) return TEN_ERROR_NULL_ARG;
    if (expr->facets) return TEN_OK;  /* already initialized */

    ten_facet_vec_t *fv = (ten_facet_vec_t *)ten__arena_alloc(
        a, sizeof(ten_facet_vec_t));
    if (!fv) return TEN_ERROR_ARENA_FULL;
    memset(fv, 0, sizeof(ten_facet_vec_t));
    expr->facets = fv;
    return TEN_OK;
}

/* ── Set a facet dimension ────────────────────────────────── */

ten_error_t ten_facet_set(ten_expr_t *expr, uint16_t dimension,
                          double value, uint8_t precision) {
    if (!expr) return TEN_ERROR_NULL_ARG;
    if (!expr->facets) return TEN_ERROR_NULL_ARG;
    if (dimension >= TEN_MAX_FACETS) return TEN_ERROR_INVALID_DIMENSION;

    ten_facet_vec_t *fv = expr->facets;

    if (!fv->set[dimension])
        fv->count++;

    fv->values[dimension]    = value;
    fv->set[dimension]       = 1;
    fv->precision[dimension] = precision;
    return TEN_OK;
}

/* ── Get a facet value ────────────────────────────────────── */

double ten_facet_get(const ten_expr_t *expr, uint16_t dimension) {
    if (!expr || !expr->facets) return 0.0;
    if (dimension >= TEN_MAX_FACETS) return 0.0;
    if (!expr->facets->set[dimension]) return 0.0;
    return expr->facets->values[dimension];
}

/* ── Check if a facet dimension is set ────────────────────── */

bool ten_facet_has(const ten_expr_t *expr, uint16_t dimension) {
    if (!expr || !expr->facets) return false;
    if (dimension >= TEN_MAX_FACETS) return false;
    return expr->facets->set[dimension] != 0;
}

/* ── Filter: does this expression pass all criteria? ──────── 
 *
 * This is the hot path for inbox processing. An agent with 1000
 * pending messages filters by urgency >= 0.8 in a single pass —
 * no parsing, no LLM, just array comparisons.
 */

bool ten_facet_filter(const ten_expr_t *expr,
                      const ten_filter_t *criteria) {
    if (!expr || !criteria) return false;
    if (!expr->facets) return false;

    for (uint16_t i = 0; i < criteria->nclauses; i++) {
        const ten_filter_clause_t *c = &criteria->clauses[i];
        if (c->dimension >= TEN_MAX_FACETS) return false;
        if (!expr->facets->set[c->dimension]) return false;

        double val = expr->facets->values[c->dimension];

        switch (c->op) {
            case TEN_CMP_GTE: if (val < c->threshold) return false; break;
            case TEN_CMP_LTE: if (val > c->threshold) return false; break;
            case TEN_CMP_EQ:
                if (fabs(val - c->threshold) > 1e-9) return false;
                break;
            case TEN_CMP_NEQ:
                if (fabs(val - c->threshold) <= 1e-9) return false;
                break;
        }
    }

    return true;  /* passed all clauses */
}
