/*
 * serialize.c — Binary serialization for Ten expressions
 *
 * Wire format (v1):
 *
 * ENVELOPE (9 bytes):
 *   "Ten:" (4B)  — magic, human-recognizable in hex dumps
 *   version (1B) — 0x01 for this format
 *   total_len (4B LE) — byte count of everything after this field
 *
 * EXPRESSION (recursive, prefix walk):
 *   type_tag (1B)
 *   flags (1B): bit 0 = has facets attached
 *   <type-specific payload>
 *   [facet vector if flagged]
 *
 * SCALAR:    dim (2B LE) + precision (1B) + value (1–8B per precision)
 * REFERENCE: hash (32B)
 * IDENTITY:  keylen (2B LE) + pubkey[keylen]
 * ASSERTION: confidence (8B double LE) + claim (expr) + who (expr)
 * OPERATION: verb (2B LE) + nargs (2B LE) + args[nargs] (exprs)
 * STRUCTURE: nmembers (2B LE) + members[nmembers] (exprs)
 * PAIR (seq/prod/union/intersect): left (expr) + right (expr)
 * NESTING:   envelope (expr) + payload (expr)
 *
 * FACET VECTOR: count (1B) + [dim_id (1B) + prec (1B) + value (8B)] × count
 */

#include "ten.h"
#include "ten_internal.h"
#include <string.h>
#include <math.h>

/* ── Constants ─────────────────────────────────────────────── */

static const uint8_t TEN_MAGIC[4] = { 'T', 'e', 'n', ':' };
#define TEN_WIRE_VERSION  1
#define TEN_ENVELOPE_SIZE 9   /* 4 magic + 1 version + 4 length */

#define FLAG_HAS_FACETS 0x01

/* ── Write cursor ──────────────────────────────────────────── */

typedef struct {
    uint8_t *buf;
    size_t   cap;
    size_t   pos;
    bool     overflow;
} wbuf_t;

static void wb_init(wbuf_t *w, uint8_t *buf, size_t cap) {
    w->buf = buf;
    w->cap = cap;
    w->pos = 0;
    w->overflow = false;
}

static void wb_u8(wbuf_t *w, uint8_t v) {
    if (w->pos + 1 > w->cap) { w->overflow = true; return; }
    w->buf[w->pos++] = v;
}

static void wb_u16le(wbuf_t *w, uint16_t v) {
    if (w->pos + 2 > w->cap) { w->overflow = true; return; }
    w->buf[w->pos++] = (uint8_t)(v & 0xFF);
    w->buf[w->pos++] = (uint8_t)(v >> 8);
}

static void wb_u32le(wbuf_t *w, uint32_t v) {
    if (w->pos + 4 > w->cap) { w->overflow = true; return; }
    w->buf[w->pos++] = (uint8_t)(v & 0xFF);
    w->buf[w->pos++] = (uint8_t)((v >> 8) & 0xFF);
    w->buf[w->pos++] = (uint8_t)((v >> 16) & 0xFF);
    w->buf[w->pos++] = (uint8_t)((v >> 24) & 0xFF);
}

static void wb_bytes(wbuf_t *w, const uint8_t *data, size_t n) {
    if (w->pos + n > w->cap) { w->overflow = true; return; }
    memcpy(w->buf + w->pos, data, n);
    w->pos += n;
}

static void wb_f64le(wbuf_t *w, double v) {
    uint8_t tmp[8];
    memcpy(tmp, &v, 8);
    wb_bytes(w, tmp, 8);
}

static void wb_f32le(wbuf_t *w, double v) {
    float f = (float)v;
    uint8_t tmp[4];
    memcpy(tmp, &f, 4);
    wb_bytes(w, tmp, 4);
}

/* ── Read cursor ───────────────────────────────────────────── */

typedef struct {
    const uint8_t *buf;
    size_t         len;
    size_t         pos;
    bool           error;
} rbuf_t;

static void rb_init(rbuf_t *r, const uint8_t *buf, size_t len) {
    r->buf   = buf;
    r->len   = len;
    r->pos   = 0;
    r->error = false;
}

static uint8_t rb_u8(rbuf_t *r) {
    if (r->pos + 1 > r->len) { r->error = true; return 0; }
    return r->buf[r->pos++];
}

static uint16_t rb_u16le(rbuf_t *r) {
    if (r->pos + 2 > r->len) { r->error = true; return 0; }
    uint16_t v = (uint16_t)r->buf[r->pos]
               | ((uint16_t)r->buf[r->pos + 1] << 8);
    r->pos += 2;
    return v;
}

static uint32_t rb_u32le(rbuf_t *r) {
    if (r->pos + 4 > r->len) { r->error = true; return 0; }
    uint32_t v = (uint32_t)r->buf[r->pos]
               | ((uint32_t)r->buf[r->pos + 1] << 8)
               | ((uint32_t)r->buf[r->pos + 2] << 16)
               | ((uint32_t)r->buf[r->pos + 3] << 24);
    r->pos += 4;
    return v;
}

static void rb_bytes(rbuf_t *r, uint8_t *out, size_t n) {
    if (r->pos + n > r->len) { r->error = true; return; }
    memcpy(out, r->buf + r->pos, n);
    r->pos += n;
}

static double rb_f64le(rbuf_t *r) {
    double v;
    uint8_t tmp[8];
    rb_bytes(r, tmp, 8);
    if (r->error) return 0.0;
    memcpy(&v, tmp, 8);
    return v;
}

static double rb_f32le_as_double(rbuf_t *r) {
    float f;
    uint8_t tmp[4];
    rb_bytes(r, tmp, 4);
    if (r->error) return 0.0;
    memcpy(&f, tmp, 4);
    return (double)f;
}

/* ── Scalar value encode/decode by precision ───────────────── */

static void wb_scalar_value(wbuf_t *w, double val, uint8_t prec) {
    switch (prec) {
    case TEN_PREC_1BIT:
        wb_u8(w, val != 0.0 ? 1 : 0);
        break;
    case TEN_PREC_4BIT:
        wb_u8(w, (uint8_t)((unsigned)val & 0x0F));
        break;
    case TEN_PREC_8BIT:
        wb_u8(w, (uint8_t)val);
        break;
    case TEN_PREC_16BIT:
        wb_u16le(w, (uint16_t)val);
        break;
    case TEN_PREC_32BIT:
        wb_f32le(w, val);
        break;
    case TEN_PREC_64BIT:
    default:
        wb_f64le(w, val);
        break;
    }
}

static double rb_scalar_value(rbuf_t *r, uint8_t prec) {
    switch (prec) {
    case TEN_PREC_1BIT:
        return (double)rb_u8(r);
    case TEN_PREC_4BIT:
        return (double)(rb_u8(r) & 0x0F);
    case TEN_PREC_8BIT:
        return (double)rb_u8(r);
    case TEN_PREC_16BIT:
        return (double)rb_u16le(r);
    case TEN_PREC_32BIT:
        return rb_f32le_as_double(r);
    case TEN_PREC_64BIT:
    default:
        return rb_f64le(r);
    }
}

/* ── Facet vector encode/decode ────────────────────────────── */

static void wb_facets(wbuf_t *w, const ten_facet_vec_t *fv) {
    wb_u8(w, (uint8_t)fv->count);
    for (uint16_t i = 0; i < TEN_MAX_FACETS && !w->overflow; i++) {
        if (fv->set[i]) {
            wb_u8(w, (uint8_t)i);            /* dim id    */
            wb_u8(w, fv->precision[i]);       /* precision */
            wb_f64le(w, fv->values[i]);       /* value — always 8B on wire */
        }
    }
}

static bool rb_facets(rbuf_t *r, ten_arena_t *a, ten_expr_t *expr) {
    uint8_t count = rb_u8(r);
    if (r->error || count > TEN_MAX_FACETS) return false;
    if (count == 0) return true;  /* flag set but empty — legal */

    if (ten_facet_init(a, expr) != TEN_OK) return false;

    for (uint8_t i = 0; i < count && !r->error; i++) {
        uint8_t dim  = rb_u8(r);
        uint8_t prec = rb_u8(r);
        double  val  = rb_f64le(r);
        if (r->error) return false;
        if (dim >= TEN_MAX_FACETS) return false;
        ten_facet_set(expr, dim, val, prec);
    }
    return !r->error;
}

/* ── Expression encode (recursive) ─────────────────────────── */

static void wb_expr(wbuf_t *w, const ten_expr_t *e) {
    if (!e || w->overflow) return;

    wb_u8(w, (uint8_t)e->type);
    wb_u8(w, e->facets ? FLAG_HAS_FACETS : 0);

    switch (e->type) {

    case TEN_TYPE_SCALAR:
        wb_u16le(w, e->data.scalar.dimension);
        wb_u8(w, e->data.scalar.precision);
        wb_scalar_value(w, e->data.scalar.value, e->data.scalar.precision);
        break;

    case TEN_TYPE_REFERENCE:
        wb_bytes(w, e->data.ref.hash, TEN_HASH_SIZE);
        break;

    case TEN_TYPE_IDENTITY:
        wb_u16le(w, e->data.identity.keylen);
        wb_bytes(w, e->data.identity.pubkey, e->data.identity.keylen);
        break;

    case TEN_TYPE_ASSERTION:
        wb_f64le(w, e->data.assertion.confidence);
        wb_expr(w, e->data.assertion.claim);
        wb_expr(w, e->data.assertion.who);
        break;

    case TEN_TYPE_OPERATION:
        wb_u16le(w, e->data.operation.verb);
        wb_u16le(w, e->data.operation.nargs);
        for (uint16_t i = 0; i < e->data.operation.nargs && !w->overflow; i++)
            wb_expr(w, e->data.operation.args[i]);
        break;

    case TEN_TYPE_STRUCTURE:
        wb_u16le(w, e->data.structure.nmembers);
        for (uint16_t i = 0; i < e->data.structure.nmembers && !w->overflow; i++)
            wb_expr(w, e->data.structure.members[i]);
        break;

    case TEN_TYPE_SEQUENCE:
    case TEN_TYPE_PRODUCT:
    case TEN_TYPE_UNION:
    case TEN_TYPE_INTERSECT:
        wb_expr(w, e->data.pair.left);
        wb_expr(w, e->data.pair.right);
        break;

    case TEN_TYPE_NESTING:
        wb_expr(w, e->data.nesting.envelope);
        wb_expr(w, e->data.nesting.payload);
        break;

    default:
        w->overflow = true;  /* unknown type — bail */
        return;
    }

    /* Facet vector (if present) */
    if (e->facets && !w->overflow)
        wb_facets(w, e->facets);
}

/* ── Expression decode (recursive) ─────────────────────────── */

static ten_expr_t *rb_expr(rbuf_t *r, ten_arena_t *a, int depth) {
    if (r->error || depth > TEN_MAX_EXPRESSION_DEPTH) {
        r->error = true;
        return NULL;
    }

    uint8_t type_tag = rb_u8(r);
    uint8_t flags    = rb_u8(r);
    if (r->error) return NULL;

    ten_expr_t *e = ten__arena_new_expr(a, (ten_type_t)type_tag);
    if (!e) { r->error = true; return NULL; }

    switch ((ten_type_t)type_tag) {

    case TEN_TYPE_SCALAR:
        e->data.scalar.dimension = rb_u16le(r);
        e->data.scalar.precision = rb_u8(r);
        e->data.scalar.value = rb_scalar_value(r, e->data.scalar.precision);
        break;

    case TEN_TYPE_REFERENCE:
        rb_bytes(r, e->data.ref.hash, TEN_HASH_SIZE);
        break;

    case TEN_TYPE_IDENTITY: {
        uint16_t kl = rb_u16le(r);
        if (kl > TEN_MAX_PUBKEY_SIZE) { r->error = true; return NULL; }
        e->data.identity.keylen = kl;
        rb_bytes(r, e->data.identity.pubkey, kl);
        break;
    }

    case TEN_TYPE_ASSERTION:
        e->data.assertion.confidence = rb_f64le(r);
        e->data.assertion.claim = rb_expr(r, a, depth + 1);
        e->data.assertion.who   = rb_expr(r, a, depth + 1);
        if (!e->data.assertion.claim || !e->data.assertion.who)
            { r->error = true; return NULL; }
        break;

    case TEN_TYPE_OPERATION: {
        e->data.operation.verb  = rb_u16le(r);
        uint16_t nargs = rb_u16le(r);
        if (r->error) return NULL;
        e->data.operation.nargs = nargs;
        if (nargs > 0) {
            ten_expr_t **args = (ten_expr_t **)ten__arena_alloc(
                a, sizeof(ten_expr_t *) * nargs);
            if (!args) { r->error = true; return NULL; }
            e->data.operation.args = args;
            for (uint16_t i = 0; i < nargs && !r->error; i++)
                args[i] = rb_expr(r, a, depth + 1);
            if (r->error) return NULL;
        }
        break;
    }

    case TEN_TYPE_STRUCTURE: {
        uint16_t nm = rb_u16le(r);
        if (r->error) return NULL;
        e->data.structure.nmembers = nm;
        if (nm > 0) {
            ten_expr_t **members = (ten_expr_t **)ten__arena_alloc(
                a, sizeof(ten_expr_t *) * nm);
            if (!members) { r->error = true; return NULL; }
            e->data.structure.members = members;
            for (uint16_t i = 0; i < nm && !r->error; i++)
                members[i] = rb_expr(r, a, depth + 1);
            if (r->error) return NULL;
        }
        break;
    }

    case TEN_TYPE_SEQUENCE:
    case TEN_TYPE_PRODUCT:
    case TEN_TYPE_UNION:
    case TEN_TYPE_INTERSECT:
        e->data.pair.left  = rb_expr(r, a, depth + 1);
        e->data.pair.right = rb_expr(r, a, depth + 1);
        if (!e->data.pair.left || !e->data.pair.right)
            { r->error = true; return NULL; }
        break;

    case TEN_TYPE_NESTING:
        e->data.nesting.envelope = rb_expr(r, a, depth + 1);
        e->data.nesting.payload  = rb_expr(r, a, depth + 1);
        if (!e->data.nesting.envelope || !e->data.nesting.payload)
            { r->error = true; return NULL; }
        break;

    default:
        r->error = true;
        return NULL;
    }

    if (r->error) return NULL;

    /* Decode facet vector if flagged */
    if (flags & FLAG_HAS_FACETS) {
        if (!rb_facets(r, a, e)) { r->error = true; return NULL; }
    }

    return e;
}

/* ══════════════════════════════════════════════════════════════
 *                    PUBLIC API
 * ══════════════════════════════════════════════════════════════ */

ten_error_t ten_encode(const ten_expr_t *expr,
                       uint8_t *buf, size_t bufsize, size_t *outlen)
{
    if (!expr || !buf || !outlen) return TEN_ERROR_NULL_ARG;
    if (bufsize < TEN_ENVELOPE_SIZE) return TEN_ERROR_BUFFER_TOO_SMALL;

    /* Write expression body after the envelope — we'll backfill the header */
    wbuf_t w;
    wb_init(&w, buf, bufsize);

    /* Leave room for envelope */
    w.pos = TEN_ENVELOPE_SIZE;

    /* Encode expression tree */
    wb_expr(&w, expr);

    if (w.overflow) return TEN_ERROR_BUFFER_TOO_SMALL;

    /* Compute body length (everything after the 9-byte envelope) */
    uint32_t body_len = (uint32_t)(w.pos - TEN_ENVELOPE_SIZE);

    /* Backfill envelope */
    wbuf_t hdr;
    wb_init(&hdr, buf, TEN_ENVELOPE_SIZE);
    wb_bytes(&hdr, TEN_MAGIC, 4);
    wb_u8(&hdr, TEN_WIRE_VERSION);
    wb_u32le(&hdr, body_len);

    *outlen = w.pos;
    return TEN_OK;
}

ten_expr_t *ten_decode(ten_arena_t *a,
                       const uint8_t *buf, size_t len)
{
    if (!a || !buf) return NULL;
    if (len < TEN_ENVELOPE_SIZE) return NULL;

    /* Verify magic */
    if (memcmp(buf, TEN_MAGIC, 4) != 0) return NULL;

    /* Check version */
    if (buf[4] != TEN_WIRE_VERSION) return NULL;

    /* Read body length */
    uint32_t body_len = (uint32_t)buf[5]
                      | ((uint32_t)buf[6] << 8)
                      | ((uint32_t)buf[7] << 16)
                      | ((uint32_t)buf[8] << 24);

    /* Validate: body must fit within buffer */
    if (TEN_ENVELOPE_SIZE + body_len > len) return NULL;

    /* Decode expression tree from the body */
    rbuf_t r;
    rb_init(&r, buf + TEN_ENVELOPE_SIZE, body_len);

    ten_expr_t *expr = rb_expr(&r, a, 0);

    if (r.error) return NULL;
    return expr;
}
