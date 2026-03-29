/*
 * ten.h — Public API for libten
 * 
 * Ten: A formal algebra for machine intelligence communication
 * https://tenlang.org
 *
 * Copyright 2026 Jolly Logic, LLC
 * Licensed under Apache 2.0
 */

#ifndef TEN_H
#define TEN_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ── Version ─────────────────────────────────────────────── */

#define TEN_VERSION_MAJOR  0
#define TEN_VERSION_MINOR  1
#define TEN_VERSION_PATCH  0
/* ── Limits ───────────────────────────────────────────────── */

#define TEN_DEFAULT_ARENA_SIZE    (64 * 1024)   /* 64 KB */
#define TEN_MAX_EXPRESSION_DEPTH  256
#define TEN_MAX_CHILDREN          4096
#define TEN_HASH_SIZE             32            /* SHA-256 */
#define TEN_MAX_PUBKEY_SIZE       64            /* Ed25519 = 32, room for others */
#define TEN_MAX_FACETS            64            /* Max facet vector dimensions */

/* ── Error Codes ──────────────────────────────────────────── */

typedef enum {
    TEN_OK = 0,
    TEN_ERROR_ARENA_FULL,
    TEN_ERROR_MESSAGE_TOO_LARGE,
    TEN_ERROR_MALFORMED,
    TEN_ERROR_DEPTH_EXCEEDED,
    TEN_ERROR_CHILDREN_EXCEEDED,
    TEN_ERROR_INVALID_TYPE,
    TEN_ERROR_INVALID_DIMENSION,
    TEN_ERROR_NULL_ARG,
    TEN_ERROR_BUFFER_TOO_SMALL,
    TEN_ERROR_DECODE_FAILED,
} ten_error_t;
/* ── Kernel Type Tags ─────────────────────────────────────── */

typedef enum {
    /* Kernel types (atoms) */
    TEN_TYPE_SCALAR     = 0x01,  /* σ — numeric value with dimension and precision */
    TEN_TYPE_REFERENCE  = 0x02,  /* ρ — content-addressed hash */
    TEN_TYPE_IDENTITY   = 0x03,  /* ι — cryptographic public key */
    TEN_TYPE_ASSERTION  = 0x04,  /* α — claim + who + confidence */
    TEN_TYPE_OPERATION  = 0x05,  /* ω — verb + arguments */
    TEN_TYPE_STRUCTURE  = 0x06,  /* τ — type descriptor */

    /* Composition types (molecules) */
    TEN_TYPE_SEQUENCE   = 0x10,  /* ⊕ — ordered combination */
    TEN_TYPE_PRODUCT    = 0x11,  /* ⊗ — parallel facets */
    TEN_TYPE_NESTING    = 0x12,  /* λ — envelope wrapping payload */
    TEN_TYPE_UNION      = 0x13,  /* ∪ — set union */
    TEN_TYPE_INTERSECT  = 0x14,  /* ∩ — set intersection */
} ten_type_t;

/* ── Well-Known Facet Dimensions ──────────────────────────── */

typedef enum {
    TEN_FACET_URGENCY    = 0,
    TEN_FACET_COST       = 1,
    TEN_FACET_PRIVILEGE  = 2,
    TEN_FACET_CONFIDENCE = 3,
    TEN_FACET_TTL        = 4,   /* time-to-live */
    TEN_FACET_EFFORT     = 5,
    TEN_FACET_REPUTATION = 6,
    TEN_FACET_VALUE      = 7,   /* summary value scalar */
} ten_facet_id_t;
/* ── Well-Known Operation Verbs ───────────────────────────── */

typedef enum {
    TEN_OP_QUERY      = 0x01,
    TEN_OP_RESPOND    = 0x02,
    TEN_OP_OFFER      = 0x03,
    TEN_OP_ACCEPT     = 0x04,
    TEN_OP_DECLINE    = 0x05,
    TEN_OP_CHALLENGE  = 0x06,
    TEN_OP_PROVE      = 0x07,
    TEN_OP_DELEGATE   = 0x08,
    TEN_OP_SUBSCRIBE  = 0x09,
    TEN_OP_CANCEL     = 0x0A,
    TEN_OP_VOUCH      = 0x0B,
    TEN_OP_ASSESS     = 0x0C,   /* value assessment */
    TEN_OP_BID        = 0x0D,
    TEN_OP_COUNTER    = 0x0E,
    TEN_OP_INVOKE     = 0x0F,   /* tool/function invocation */
} ten_op_verb_t;

/* ── Precision Levels ─────────────────────────────────────── */

typedef enum {
    TEN_PREC_1BIT   = 1,    /* binary: high/low */
    TEN_PREC_4BIT   = 4,    /* 16 levels (~1-10 scale) */
    TEN_PREC_8BIT   = 8,    /* 256 levels */
    TEN_PREC_16BIT  = 16,   /* 65,536 levels */
    TEN_PREC_32BIT  = 32,   /* full float */
    TEN_PREC_64BIT  = 64,   /* full double */
} ten_precision_t;
/* ── Arena Allocator ──────────────────────────────────────── */

typedef struct {
    uint8_t *base;       /* start of allocated block */
    size_t   size;       /* total arena size */
    size_t   used;       /* bytes consumed */
    int      depth;      /* current nesting depth (for limit checking) */
    int      node_count; /* total nodes allocated (for limit checking) */
} ten_arena_t;

/* ── Forward Declaration ──────────────────────────────────── */

typedef struct ten_expr ten_expr_t;

/* ── Facet Vector ─────────────────────────────────────────── */

typedef struct {
    double   values[TEN_MAX_FACETS];
    uint8_t  set[TEN_MAX_FACETS];    /* 1 if this dimension has been set */
    uint8_t  precision[TEN_MAX_FACETS];
    uint16_t count;                   /* number of dimensions actually set */
} ten_facet_vec_t;
/* ── Expression Node (tagged union) ───────────────────────── */

struct ten_expr {
    ten_type_t type;

    union {
        /* TEN_TYPE_SCALAR */
        struct {
            double    value;
            uint16_t  dimension;   /* facet ID or user-defined dimension */
            uint8_t   precision;   /* bits of precision */
        } scalar;

        /* TEN_TYPE_REFERENCE */
        struct {
            uint8_t hash[TEN_HASH_SIZE];
        } ref;

        /* TEN_TYPE_IDENTITY */
        struct {
            uint8_t  pubkey[TEN_MAX_PUBKEY_SIZE];
            uint16_t keylen;
        } identity;
        /* TEN_TYPE_ASSERTION */
        struct {
            ten_expr_t *claim;       /* what is being asserted (Reference) */
            ten_expr_t *who;         /* who asserts it (Identity) */
            double      confidence;  /* 0.0 to 1.0 */
        } assertion;

        /* TEN_TYPE_OPERATION */
        struct {
            uint16_t    verb;        /* ten_op_verb_t or user-defined */
            ten_expr_t **args;       /* argument expressions */
            uint16_t    nargs;
        } operation;

        /* TEN_TYPE_STRUCTURE */
        struct {
            ten_expr_t **members;    /* member type descriptors */
            uint16_t    nmembers;
        } structure;
        /* TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT, TEN_TYPE_UNION, TEN_TYPE_INTERSECT */
        struct {
            ten_expr_t *left;
            ten_expr_t *right;
        } pair;

        /* TEN_TYPE_NESTING */
        struct {
            ten_expr_t *envelope;
            ten_expr_t *payload;
        } nesting;
    } data;

    /* Optional facet vector — present on any message-level expression */
    ten_facet_vec_t *facets;
};
/* ── Filter Criteria ──────────────────────────────────────── */

typedef struct {
    uint16_t dimension;
    enum { TEN_CMP_GTE, TEN_CMP_LTE, TEN_CMP_EQ, TEN_CMP_NEQ } op;
    double   threshold;
} ten_filter_clause_t;

typedef struct {
    ten_filter_clause_t *clauses;
    uint16_t             nclauses;
} ten_filter_t;

/* ══════════════════════════════════════════════════════════════
 *                       PUBLIC API
 * ══════════════════════════════════════════════════════════════ */

/* ── Arena ────────────────────────────────────────────────── */

ten_error_t ten_arena_init(ten_arena_t *a, size_t size);
void        ten_arena_free(ten_arena_t *a);
void        ten_arena_reset(ten_arena_t *a);   /* reuse without realloc */
size_t      ten_arena_remaining(const ten_arena_t *a);
/* ── Kernel Type Constructors ─────────────────────────────── */

ten_expr_t *ten_scalar(ten_arena_t *a, uint16_t dimension,
                       double value, uint8_t precision);

ten_expr_t *ten_ref(ten_arena_t *a, const uint8_t hash[TEN_HASH_SIZE]);

ten_expr_t *ten_identity(ten_arena_t *a, const uint8_t *pubkey,
                         uint16_t keylen);

ten_expr_t *ten_assertion(ten_arena_t *a, ten_expr_t *claim,
                          ten_expr_t *who, double confidence);

ten_expr_t *ten_operation(ten_arena_t *a, uint16_t verb,
                          ten_expr_t **args, uint16_t nargs);

ten_expr_t *ten_structure(ten_arena_t *a, ten_expr_t **members,
                          uint16_t nmembers);

/* ── Composition Operations ───────────────────────────────── */

ten_expr_t *ten_sequence(ten_arena_t *a, ten_expr_t *left,
                         ten_expr_t *right);

ten_expr_t *ten_product(ten_arena_t *a, ten_expr_t *left,
                        ten_expr_t *right);

ten_expr_t *ten_nest(ten_arena_t *a, ten_expr_t *envelope,
                     ten_expr_t *payload);
ten_expr_t *ten_union(ten_arena_t *a, ten_expr_t *left,
                      ten_expr_t *right);

ten_expr_t *ten_intersect(ten_arena_t *a, ten_expr_t *left,
                          ten_expr_t *right);

ten_expr_t *ten_project(ten_arena_t *a, const ten_expr_t *expr,
                        const uint16_t *dims, uint16_t ndims);

/* ── Facet Vector Operations ──────────────────────────────── */

ten_error_t ten_facet_init(ten_arena_t *a, ten_expr_t *expr);

ten_error_t ten_facet_set(ten_expr_t *expr, uint16_t dimension,
                          double value, uint8_t precision);

double      ten_facet_get(const ten_expr_t *expr, uint16_t dimension);

bool        ten_facet_has(const ten_expr_t *expr, uint16_t dimension);

bool        ten_facet_filter(const ten_expr_t *expr,
                             const ten_filter_t *criteria);

/* ── Serialization ────────────────────────────────────────── */

ten_error_t ten_encode(const ten_expr_t *expr,
                       uint8_t *buf, size_t bufsize, size_t *outlen);

ten_expr_t *ten_decode(ten_arena_t *a,
                       const uint8_t *buf, size_t len);
/* ── Validation ───────────────────────────────────────────── */

bool        ten_is_valid(const ten_expr_t *expr);
bool        ten_is_kernel_type(ten_type_t type);
bool        ten_is_composition_type(ten_type_t type);

/* ── Utility ──────────────────────────────────────────────── */

const char *ten_type_name(ten_type_t type);
const char *ten_error_string(ten_error_t err);
const char *ten_op_name(uint16_t verb);

/* ── Debug (human-readable output, not part of the algebra) ─ */

int         ten_describe(const ten_expr_t *expr, char *buf, size_t bufsize);

#ifdef __cplusplus
}
#endif

#endif /* TEN_H */
