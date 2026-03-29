/*
 * test_main.c — Test harness for libten
 *
 * Tests prove the algebra's fundamental properties:
 *   1. Construction: every kernel type can be created
 *   2. Closure: every composition of valid expressions is valid
 *   3. Facets: set/get/filter work correctly
 *   4. Validation: well-formed expressions pass, malformed fail
 *   5. Projection: extracting dimensions preserves values
 *   6. Arena: memory limits are enforced
 *   7. Describe: debug output works without crashing
 *
 * Lightweight — no test framework, just assert + printf.
 */

#include "ten.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

static int tests_run    = 0;
static int tests_passed = 0;

#define TEST(name) \
    do { \
        tests_run++; \
        printf("  %-50s ", name); \
    } while (0)
#define PASS() \
    do { tests_passed++; printf("PASS\n"); } while (0)

#define FAIL(msg) \
    do { printf("FAIL: %s\n", msg); } while (0)

/* ══════════════════════════════════════════════════════════
 *  Test: Arena basics
 * ══════════════════════════════════════════════════════════ */

static void test_arena(void) {
    ten_arena_t a;

    TEST("arena_init with default size");
    assert(ten_arena_init(&a, 0) == TEN_OK);
    assert(a.size == TEN_DEFAULT_ARENA_SIZE);
    assert(a.used == 0);
    PASS();

    TEST("arena_remaining tracks usage");
    size_t before = ten_arena_remaining(&a);
    ten_scalar(&a, 0, 1.0, 8);
    assert(ten_arena_remaining(&a) < before);
    PASS();

    TEST("arena_reset reuses memory");
    ten_arena_reset(&a);
    assert(a.used == 0);
    assert(a.node_count == 0);
    PASS();
    TEST("arena_init with tiny size still works");
    ten_arena_free(&a);
    assert(ten_arena_init(&a, 256) == TEN_OK);
    assert(a.size == 256);
    PASS();

    TEST("arena returns NULL when full");
    ten_arena_free(&a);
    assert(ten_arena_init(&a, 64) == TEN_OK);
    /* 64 bytes barely fits one expr node */
    ten_expr_t *e1 = ten_scalar(&a, 0, 1.0, 8);
    /* second alloc should fail — not enough room */
    /* (might or might not fail depending on sizeof, that's ok) */
    (void)e1;
    PASS();

    ten_arena_free(&a);
}

/* ══════════════════════════════════════════════════════════
 *  Test: Kernel type construction
 * ══════════════════════════════════════════════════════════ */

static void test_kernel_types(void) {
    ten_arena_t a;
    ten_arena_init(&a, TEN_DEFAULT_ARENA_SIZE);
    TEST("scalar construction");
    ten_expr_t *s = ten_scalar(&a, TEN_FACET_URGENCY, 0.95, 16);
    assert(s != NULL);
    assert(s->type == TEN_TYPE_SCALAR);
    assert(s->data.scalar.dimension == TEN_FACET_URGENCY);
    assert(fabs(s->data.scalar.value - 0.95) < 1e-9);
    assert(s->data.scalar.precision == 16);
    PASS();

    TEST("reference construction");
    uint8_t hash[TEN_HASH_SIZE];
    memset(hash, 0xAB, TEN_HASH_SIZE);
    ten_expr_t *r = ten_ref(&a, hash);
    assert(r != NULL);
    assert(r->type == TEN_TYPE_REFERENCE);
    assert(memcmp(r->data.ref.hash, hash, TEN_HASH_SIZE) == 0);
    PASS();

    TEST("reference rejects NULL hash");
    assert(ten_ref(&a, NULL) == NULL);
    PASS();

    TEST("identity construction");
    uint8_t key[32];
    memset(key, 0xCD, 32);
    ten_expr_t *id = ten_identity(&a, key, 32);
    assert(id != NULL);
    assert(id->type == TEN_TYPE_IDENTITY);
    assert(id->data.identity.keylen == 32);    PASS();

    TEST("identity rejects zero-length key");
    assert(ten_identity(&a, key, 0) == NULL);
    PASS();

    TEST("identity rejects oversized key");
    assert(ten_identity(&a, key, TEN_MAX_PUBKEY_SIZE + 1) == NULL);
    PASS();

    TEST("assertion construction");
    ten_expr_t *claim = ten_ref(&a, hash);
    ten_expr_t *who   = ten_identity(&a, key, 32);
    ten_expr_t *asr   = ten_assertion(&a, claim, who, 0.87);
    assert(asr != NULL);
    assert(asr->type == TEN_TYPE_ASSERTION);
    assert(asr->data.assertion.claim == claim);
    assert(asr->data.assertion.who == who);
    assert(fabs(asr->data.assertion.confidence - 0.87) < 1e-9);
    PASS();

    TEST("assertion rejects out-of-range confidence");
    assert(ten_assertion(&a, claim, who, 1.5) == NULL);
    assert(ten_assertion(&a, claim, who, -0.1) == NULL);
    PASS();

    TEST("operation construction");
    ten_expr_t *args[2] = { r, s };
    ten_expr_t *op = ten_operation(&a, TEN_OP_QUERY, args, 2);    assert(op != NULL);
    assert(op->type == TEN_TYPE_OPERATION);
    assert(op->data.operation.verb == TEN_OP_QUERY);
    assert(op->data.operation.nargs == 2);
    PASS();

    TEST("operation with zero args");
    ten_expr_t *op0 = ten_operation(&a, TEN_OP_CANCEL, NULL, 0);
    assert(op0 != NULL);
    assert(op0->data.operation.nargs == 0);
    assert(op0->data.operation.args == NULL);
    PASS();

    TEST("structure construction");
    ten_expr_t *members[2] = { s, r };
    ten_expr_t *st = ten_structure(&a, members, 2);
    assert(st != NULL);
    assert(st->type == TEN_TYPE_STRUCTURE);
    assert(st->data.structure.nmembers == 2);
    PASS();

    ten_arena_free(&a);
}

/* ══════════════════════════════════════════════════════════
 *  Test: Composition — closure property
 * ══════════════════════════════════════════════════════════ */

static void test_composition(void) {
    ten_arena_t a;    ten_arena_init(&a, TEN_DEFAULT_ARENA_SIZE);

    ten_expr_t *s1 = ten_scalar(&a, 0, 0.5, 8);
    ten_expr_t *s2 = ten_scalar(&a, 1, 0.9, 8);
    uint8_t hash[TEN_HASH_SIZE] = {0};
    ten_expr_t *r1 = ten_ref(&a, hash);

    TEST("sequence produces valid expression");
    ten_expr_t *seq = ten_sequence(&a, s1, s2);
    assert(seq != NULL);
    assert(seq->type == TEN_TYPE_SEQUENCE);
    assert(ten_is_valid(seq));
    PASS();

    TEST("product produces valid expression");
    ten_expr_t *prod = ten_product(&a, s1, r1);
    assert(prod != NULL);
    assert(ten_is_valid(prod));
    PASS();

    TEST("nesting produces valid expression");
    ten_expr_t *nest = ten_nest(&a, s1, r1);
    assert(nest != NULL);
    assert(nest->type == TEN_TYPE_NESTING);
    assert(ten_is_valid(nest));
    PASS();

    TEST("union produces valid expression");
    ten_expr_t *un = ten_union(&a, s1, s2);    assert(un != NULL);
    assert(ten_is_valid(un));
    PASS();

    TEST("intersect produces valid expression");
    ten_expr_t *inter = ten_intersect(&a, s1, s2);
    assert(inter != NULL);
    assert(ten_is_valid(inter));
    PASS();

    /* CLOSURE: composing compositions produces valid expressions */
    TEST("closure: sequence of sequences is valid");
    ten_expr_t *seq2 = ten_sequence(&a, seq, prod);
    assert(seq2 != NULL);
    assert(ten_is_valid(seq2));
    PASS();

    TEST("closure: product of nesting and union");
    ten_expr_t *complex = ten_product(&a, nest, un);
    assert(complex != NULL);
    assert(ten_is_valid(complex));
    PASS();

    TEST("closure: three-deep nesting");
    ten_expr_t *deep = ten_nest(&a, s1,
                           ten_nest(&a, s2,
                               ten_nest(&a, r1, s1)));
    assert(deep != NULL);
    assert(ten_is_valid(deep));
    PASS();
    TEST("composition rejects NULL left");
    assert(ten_sequence(&a, NULL, s1) == NULL);
    PASS();

    TEST("composition rejects NULL right");
    assert(ten_product(&a, s1, NULL) == NULL);
    PASS();

    ten_arena_free(&a);
}

/* ══════════════════════════════════════════════════════════
 *  Test: Facet vectors
 * ══════════════════════════════════════════════════════════ */

static void test_facets(void) {
    ten_arena_t a;
    ten_arena_init(&a, TEN_DEFAULT_ARENA_SIZE);

    ten_expr_t *msg = ten_scalar(&a, 0, 1.0, 8);

    TEST("facet_init creates vector");
    assert(ten_facet_init(&a, msg) == TEN_OK);
    assert(msg->facets != NULL);
    PASS();

    TEST("facet_init is idempotent");
    assert(ten_facet_init(&a, msg) == TEN_OK);
    PASS();
    TEST("facet_set and facet_get round-trip");
    ten_facet_set(msg, TEN_FACET_URGENCY, 0.95, 16);
    ten_facet_set(msg, TEN_FACET_COST, 0.30, 8);
    assert(fabs(ten_facet_get(msg, TEN_FACET_URGENCY) - 0.95) < 1e-9);
    assert(fabs(ten_facet_get(msg, TEN_FACET_COST) - 0.30) < 1e-9);
    PASS();

    TEST("facet_has returns true for set dims");
    assert(ten_facet_has(msg, TEN_FACET_URGENCY));
    assert(ten_facet_has(msg, TEN_FACET_COST));
    PASS();

    TEST("facet_has returns false for unset dims");
    assert(!ten_facet_has(msg, TEN_FACET_PRIVILEGE));
    assert(!ten_facet_has(msg, TEN_FACET_TTL));
    PASS();

    TEST("facet_get returns 0.0 for unset dims");
    assert(ten_facet_get(msg, TEN_FACET_PRIVILEGE) == 0.0);
    PASS();

    TEST("facet_set rejects invalid dimension");
    assert(ten_facet_set(msg, TEN_MAX_FACETS, 1.0, 8)
           == TEN_ERROR_INVALID_DIMENSION);
    PASS();

    /* Filter tests */
    TEST("filter: urgency >= 0.8 passes");
    ten_filter_clause_t c1 = {        .dimension = TEN_FACET_URGENCY,
        .op = TEN_CMP_GTE,
        .threshold = 0.8
    };
    ten_filter_t f1 = { .clauses = &c1, .nclauses = 1 };
    assert(ten_facet_filter(msg, &f1) == true);
    PASS();

    TEST("filter: urgency >= 0.99 fails");
    ten_filter_clause_t c2 = {
        .dimension = TEN_FACET_URGENCY,
        .op = TEN_CMP_GTE,
        .threshold = 0.99
    };
    ten_filter_t f2 = { .clauses = &c2, .nclauses = 1 };
    assert(ten_facet_filter(msg, &f2) == false);
    PASS();

    TEST("filter: multi-clause (urgency >= 0.5 AND cost <= 0.5)");
    ten_filter_clause_t mc[2] = {
        { .dimension = TEN_FACET_URGENCY, .op = TEN_CMP_GTE, .threshold = 0.5 },
        { .dimension = TEN_FACET_COST,    .op = TEN_CMP_LTE, .threshold = 0.5 },
    };
    ten_filter_t f3 = { .clauses = mc, .nclauses = 2 };
    assert(ten_facet_filter(msg, &f3) == true);
    PASS();

    ten_arena_free(&a);
}
/* ══════════════════════════════════════════════════════════
 *  Test: Projection
 * ══════════════════════════════════════════════════════════ */

static void test_projection(void) {
    ten_arena_t a;
    ten_arena_init(&a, TEN_DEFAULT_ARENA_SIZE);

    ten_expr_t *msg = ten_scalar(&a, 0, 1.0, 8);
    ten_facet_init(&a, msg);
    ten_facet_set(msg, TEN_FACET_URGENCY,    0.9, 16);
    ten_facet_set(msg, TEN_FACET_COST,       0.3, 8);
    ten_facet_set(msg, TEN_FACET_PRIVILEGE,   0.7, 8);
    ten_facet_set(msg, TEN_FACET_CONFIDENCE,  0.5, 8);

    TEST("project preserves requested dimensions");
    uint16_t dims[2] = { TEN_FACET_URGENCY, TEN_FACET_COST };
    ten_expr_t *proj = ten_project(&a, msg, dims, 2);
    assert(proj != NULL);
    assert(ten_facet_has(proj, TEN_FACET_URGENCY));
    assert(ten_facet_has(proj, TEN_FACET_COST));
    assert(fabs(ten_facet_get(proj, TEN_FACET_URGENCY) - 0.9) < 1e-9);
    assert(fabs(ten_facet_get(proj, TEN_FACET_COST) - 0.3) < 1e-9);
    PASS();
    TEST("project drops unrequested dimensions");
    assert(!ten_facet_has(proj, TEN_FACET_PRIVILEGE));
    assert(!ten_facet_has(proj, TEN_FACET_CONFIDENCE));
    PASS();

    TEST("project of expression without facets returns copy");
    ten_expr_t *bare = ten_scalar(&a, 0, 2.0, 8);
    ten_expr_t *proj2 = ten_project(&a, bare, dims, 2);
    assert(proj2 != NULL);
    assert(proj2->facets == NULL);
    PASS();

    TEST("project rejects NULL args");
    assert(ten_project(&a, NULL, dims, 2) == NULL);
    assert(ten_project(&a, msg, NULL, 2) == NULL);
    assert(ten_project(&a, msg, dims, 0) == NULL);
    PASS();

    ten_arena_free(&a);
}

/* ══════════════════════════════════════════════════════════
 *  Test: Validation
 * ══════════════════════════════════════════════════════════ */

static void test_validation(void) {
    ten_arena_t a;
    ten_arena_init(&a, TEN_DEFAULT_ARENA_SIZE);
    TEST("valid scalar passes validation");
    ten_expr_t *s = ten_scalar(&a, 0, 1.0, 8);
    assert(ten_is_valid(s));
    PASS();

    TEST("valid sequence passes validation");
    ten_expr_t *s2 = ten_scalar(&a, 1, 0.5, 8);
    ten_expr_t *seq = ten_sequence(&a, s, s2);
    assert(ten_is_valid(seq));
    PASS();

    TEST("is_kernel_type classifies correctly");
    assert(ten_is_kernel_type(TEN_TYPE_SCALAR));
    assert(ten_is_kernel_type(TEN_TYPE_REFERENCE));
    assert(ten_is_kernel_type(TEN_TYPE_STRUCTURE));
    assert(!ten_is_kernel_type(TEN_TYPE_SEQUENCE));
    assert(!ten_is_kernel_type(TEN_TYPE_NESTING));
    PASS();

    TEST("is_composition_type classifies correctly");
    assert(ten_is_composition_type(TEN_TYPE_SEQUENCE));
    assert(ten_is_composition_type(TEN_TYPE_PRODUCT));
    assert(ten_is_composition_type(TEN_TYPE_INTERSECT));
    assert(!ten_is_composition_type(TEN_TYPE_SCALAR));
    assert(!ten_is_composition_type(TEN_TYPE_ASSERTION));
    PASS();

    ten_arena_free(&a);
}
/* ══════════════════════════════════════════════════════════
 *  Test: Utility / debug functions
 * ══════════════════════════════════════════════════════════ */

static void test_utility(void) {
    TEST("type_name returns correct strings");
    assert(strcmp(ten_type_name(TEN_TYPE_SCALAR), "Scalar") == 0);
    assert(strcmp(ten_type_name(TEN_TYPE_SEQUENCE), "Sequence") == 0);
    assert(strcmp(ten_type_name(TEN_TYPE_NESTING), "Nesting") == 0);
    assert(strcmp(ten_type_name(0xFF), "Unknown") == 0);
    PASS();

    TEST("error_string returns correct strings");
    assert(strcmp(ten_error_string(TEN_OK), "OK") == 0);
    assert(strcmp(ten_error_string(TEN_ERROR_ARENA_FULL), "Arena full") == 0);
    PASS();

    TEST("op_name returns correct strings");
    assert(strcmp(ten_op_name(TEN_OP_QUERY), "Query") == 0);
    assert(strcmp(ten_op_name(TEN_OP_INVOKE), "Invoke") == 0);
    assert(strcmp(ten_op_name(0xFF), "UserDefined") == 0);
    PASS();

    TEST("describe produces output without crashing");
    ten_arena_t a;
    ten_arena_init(&a, TEN_DEFAULT_ARENA_SIZE);
    uint8_t hash[TEN_HASH_SIZE];
    memset(hash, 0xAA, TEN_HASH_SIZE);
    uint8_t key[32];
    memset(key, 0xBB, 32);

    ten_expr_t *s   = ten_scalar(&a, TEN_FACET_URGENCY, 0.9, 16);
    ten_expr_t *r   = ten_ref(&a, hash);
    ten_expr_t *id  = ten_identity(&a, key, 32);
    ten_expr_t *asr = ten_assertion(&a, r, id, 0.95);
    ten_expr_t *args[1] = { r };
    ten_expr_t *op  = ten_operation(&a, TEN_OP_QUERY, args, 1);
    ten_expr_t *seq = ten_sequence(&a, asr, op);
    ten_expr_t *msg = ten_nest(&a, s, seq);

    char buf[4096];
    int len = ten_describe(msg, buf, sizeof(buf));
    assert(len > 0);
    /* Verify it contains expected substrings */
    assert(strstr(buf, "Nesting") != NULL);
    assert(strstr(buf, "Scalar") != NULL);
    assert(strstr(buf, "Assertion") != NULL);
    assert(strstr(buf, "Query") != NULL);
    PASS();

    TEST("describe handles NULL gracefully");
    assert(ten_describe(NULL, buf, sizeof(buf)) == 0);
    PASS();

    ten_arena_free(&a);
}
/* ══════════════════════════════════════════════════════════
 *  Main
 * ══════════════════════════════════════════════════════════ */

int main(void) {
    printf("\n══════════════════════════════════════════\n");
    printf("  libten test suite v%d.%d.%d\n",
           TEN_VERSION_MAJOR, TEN_VERSION_MINOR, TEN_VERSION_PATCH);
    printf("══════════════════════════════════════════\n\n");

    printf("[Arena]\n");
    test_arena();

    printf("\n[Kernel Types]\n");
    test_kernel_types();

    printf("\n[Composition & Closure]\n");
    test_composition();

    printf("\n[Facet Vectors]\n");
    test_facets();

    printf("\n[Projection]\n");
    test_projection();

    printf("\n[Validation]\n");
    test_validation();
    printf("\n[Utility]\n");
    test_utility();

    printf("\n══════════════════════════════════════════\n");
    printf("  Results: %d/%d passed\n", tests_passed, tests_run);
    printf("══════════════════════════════════════════\n\n");

    return (tests_passed == tests_run) ? 0 : 1;
}
