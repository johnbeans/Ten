/*
 * util.c — String conversion utilities and debug output
 *
 * These are NOT part of the algebra — they exist for debugging,
 * logging, and test output. Production hot paths never call these.
 */

#include "ten.h"
#include <stdio.h>
#include <string.h>

/* ── Type name strings ────────────────────────────────────── */

const char *ten_type_name(ten_type_t type) {
    switch (type) {
    case TEN_TYPE_SCALAR:     return "Scalar";
    case TEN_TYPE_REFERENCE:  return "Reference";
    case TEN_TYPE_IDENTITY:   return "Identity";
    case TEN_TYPE_ASSERTION:  return "Assertion";
    case TEN_TYPE_OPERATION:  return "Operation";
    case TEN_TYPE_STRUCTURE:  return "Structure";
    case TEN_TYPE_SEQUENCE:   return "Sequence";
    case TEN_TYPE_PRODUCT:    return "Product";
    case TEN_TYPE_NESTING:    return "Nesting";
    case TEN_TYPE_UNION:      return "Union";
    case TEN_TYPE_INTERSECT:  return "Intersect";
    default:                  return "Unknown";
    }
}
/* ── Error strings ────────────────────────────────────────── */

const char *ten_error_string(ten_error_t err) {
    switch (err) {
    case TEN_OK:                     return "OK";
    case TEN_ERROR_ARENA_FULL:       return "Arena full";
    case TEN_ERROR_MESSAGE_TOO_LARGE:return "Message too large";
    case TEN_ERROR_MALFORMED:        return "Malformed expression";
    case TEN_ERROR_DEPTH_EXCEEDED:   return "Max depth exceeded";
    case TEN_ERROR_CHILDREN_EXCEEDED:return "Max children exceeded";
    case TEN_ERROR_INVALID_TYPE:     return "Invalid type tag";
    case TEN_ERROR_INVALID_DIMENSION:return "Invalid facet dimension";
    case TEN_ERROR_NULL_ARG:         return "NULL argument";
    case TEN_ERROR_BUFFER_TOO_SMALL: return "Buffer too small";
    case TEN_ERROR_DECODE_FAILED:    return "Decode failed";
    default:                         return "Unknown error";
    }
}

/* ── Operation verb names ─────────────────────────────────── */

const char *ten_op_name(uint16_t verb) {
    switch (verb) {
    case TEN_OP_QUERY:     return "Query";
    case TEN_OP_RESPOND:   return "Respond";
    case TEN_OP_OFFER:     return "Offer";    case TEN_OP_ACCEPT:    return "Accept";
    case TEN_OP_DECLINE:   return "Decline";
    case TEN_OP_CHALLENGE: return "Challenge";
    case TEN_OP_PROVE:     return "Prove";
    case TEN_OP_DELEGATE:  return "Delegate";
    case TEN_OP_SUBSCRIBE: return "Subscribe";
    case TEN_OP_CANCEL:    return "Cancel";
    case TEN_OP_VOUCH:     return "Vouch";
    case TEN_OP_ASSESS:    return "Assess";
    case TEN_OP_BID:       return "Bid";
    case TEN_OP_COUNTER:   return "Counter";
    case TEN_OP_INVOKE:    return "Invoke";
    default:               return "UserDefined";
    }
}

/* ── Describe: human-readable expression dump ─────────────── 
 *
 * Recursive. Writes into buf up to bufsize bytes.
 * Returns number of bytes written (excluding NUL).
 * This is printf-style debug output, not serialization.
 */

static int describe_recursive(const ten_expr_t *expr,
                              char *buf, size_t bufsize, int depth) {
    if (!expr || bufsize < 2) return 0;
    int written = 0;
    int n;

    /* Indent */
    for (int i = 0; i < depth && written < (int)bufsize - 1; i++) {
        buf[written++] = ' ';
        buf[written++] = ' ';
    }

    switch (expr->type) {
    case TEN_TYPE_SCALAR:
        n = snprintf(buf + written, bufsize - written,
            "Scalar(dim=%u, val=%.4f, prec=%u)\n",
            expr->data.scalar.dimension,
            expr->data.scalar.value,
            expr->data.scalar.precision);
        if (n > 0) written += n;
        break;

    case TEN_TYPE_REFERENCE:
        n = snprintf(buf + written, bufsize - written,
            "Reference(%02x%02x%02x%02x...)\n",
            expr->data.ref.hash[0], expr->data.ref.hash[1],
            expr->data.ref.hash[2], expr->data.ref.hash[3]);
        if (n > 0) written += n;
        break;
    case TEN_TYPE_IDENTITY:
        n = snprintf(buf + written, bufsize - written,
            "Identity(keylen=%u)\n", expr->data.identity.keylen);
        if (n > 0) written += n;
        break;

    case TEN_TYPE_ASSERTION:
        n = snprintf(buf + written, bufsize - written,
            "Assertion(conf=%.4f)\n", expr->data.assertion.confidence);
        if (n > 0) written += n;
        written += describe_recursive(expr->data.assertion.claim,
            buf + written, bufsize - written, depth + 1);
        written += describe_recursive(expr->data.assertion.who,
            buf + written, bufsize - written, depth + 1);
        break;

    case TEN_TYPE_OPERATION:
        n = snprintf(buf + written, bufsize - written,
            "Operation(%s, nargs=%u)\n",
            ten_op_name(expr->data.operation.verb),
            expr->data.operation.nargs);
        if (n > 0) written += n;
        for (uint16_t i = 0; i < expr->data.operation.nargs; i++) {
            written += describe_recursive(expr->data.operation.args[i],
                buf + written, bufsize - written, depth + 1);
        }
        break;
    case TEN_TYPE_STRUCTURE:
        n = snprintf(buf + written, bufsize - written,
            "Structure(nmembers=%u)\n", expr->data.structure.nmembers);
        if (n > 0) written += n;
        for (uint16_t i = 0; i < expr->data.structure.nmembers; i++) {
            written += describe_recursive(expr->data.structure.members[i],
                buf + written, bufsize - written, depth + 1);
        }
        break;

    case TEN_TYPE_SEQUENCE:
    case TEN_TYPE_PRODUCT:
    case TEN_TYPE_UNION:
    case TEN_TYPE_INTERSECT:
        n = snprintf(buf + written, bufsize - written,
            "%s\n", ten_type_name(expr->type));
        if (n > 0) written += n;
        written += describe_recursive(expr->data.pair.left,
            buf + written, bufsize - written, depth + 1);
        written += describe_recursive(expr->data.pair.right,
            buf + written, bufsize - written, depth + 1);
        break;

    case TEN_TYPE_NESTING:
        n = snprintf(buf + written, bufsize - written, "Nesting\n");
        if (n > 0) written += n;        written += describe_recursive(expr->data.nesting.envelope,
            buf + written, bufsize - written, depth + 1);
        written += describe_recursive(expr->data.nesting.payload,
            buf + written, bufsize - written, depth + 1);
        break;

    default:
        n = snprintf(buf + written, bufsize - written, "Unknown\n");
        if (n > 0) written += n;
        break;
    }

    return written;
}

int ten_describe(const ten_expr_t *expr, char *buf, size_t bufsize) {
    if (!expr || !buf || bufsize == 0) return 0;
    int written = describe_recursive(expr, buf, bufsize, 0);
    if (written < (int)bufsize)
        buf[written] = '\0';
    return written;
}
