/*
 * validate.c — Expression validation
 *
 * Validates structural integrity of Ten expressions.
 * This is defensive — used after decoding untrusted input
 * to confirm the expression tree is well-formed before
 * any algebra operations touch it.
 */

#include "ten.h"
#include "ten_internal.h"

/* ── Type classification ──────────────────────────────────── */

bool ten_is_kernel_type(ten_type_t type) {
    return type >= TEN_TYPE_SCALAR && type <= TEN_TYPE_STRUCTURE;
}

bool ten_is_composition_type(ten_type_t type) {
    return type >= TEN_TYPE_SEQUENCE && type <= TEN_TYPE_INTERSECT;
}

/* ── Recursive validation ─────────────────────────────────── */

static bool validate_recursive(const ten_expr_t *expr, int depth) {
    if (!expr) return false;
    if (depth > TEN_MAX_EXPRESSION_DEPTH) return false;
    switch (expr->type) {
    /* Kernel atoms — leaf nodes, always valid if they exist */
    case TEN_TYPE_SCALAR:
        return expr->data.scalar.precision > 0;

    case TEN_TYPE_REFERENCE:
        return true;  /* hash is just 32 bytes, always structurally ok */

    case TEN_TYPE_IDENTITY:
        return expr->data.identity.keylen > 0
            && expr->data.identity.keylen <= TEN_MAX_PUBKEY_SIZE;

    case TEN_TYPE_ASSERTION:
        return expr->data.assertion.claim != NULL
            && expr->data.assertion.who != NULL
            && expr->data.assertion.confidence >= 0.0
            && expr->data.assertion.confidence <= 1.0
            && validate_recursive(expr->data.assertion.claim, depth + 1)
            && validate_recursive(expr->data.assertion.who, depth + 1);

    case TEN_TYPE_OPERATION:
        if (expr->data.operation.nargs > 0 && !expr->data.operation.args)
            return false;
        for (uint16_t i = 0; i < expr->data.operation.nargs; i++) {
            if (!validate_recursive(expr->data.operation.args[i], depth + 1))
                return false;
        }
        return true;
    case TEN_TYPE_STRUCTURE:
        if (expr->data.structure.nmembers > 0 && !expr->data.structure.members)
            return false;
        for (uint16_t i = 0; i < expr->data.structure.nmembers; i++) {
            if (!validate_recursive(expr->data.structure.members[i], depth + 1))
                return false;
        }
        return true;

    /* Composition types — binary pair nodes */
    case TEN_TYPE_SEQUENCE:
    case TEN_TYPE_PRODUCT:
    case TEN_TYPE_UNION:
    case TEN_TYPE_INTERSECT:
        return expr->data.pair.left != NULL
            && expr->data.pair.right != NULL
            && validate_recursive(expr->data.pair.left, depth + 1)
            && validate_recursive(expr->data.pair.right, depth + 1);

    case TEN_TYPE_NESTING:
        return expr->data.nesting.envelope != NULL
            && expr->data.nesting.payload != NULL
            && validate_recursive(expr->data.nesting.envelope, depth + 1)
            && validate_recursive(expr->data.nesting.payload, depth + 1);

    default:
        return false;  /* unknown type */
    }
}
/* ── Public API ───────────────────────────────────────────── */

bool ten_is_valid(const ten_expr_t *expr) {
    return validate_recursive(expr, 0);
}
