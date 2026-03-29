# Ten Implementation Status
# Last updated: 2026-03-29
# Read this FIRST in any new chat to avoid re-reading 93KB of docs.

## Strategic Priority
Proving Ten's value versus the status quo (JSON + LLM, or JSON + domain
code) is the most important goal of the project. Everything we build
exists to make honest measurement possible. If the measurements don't
support the claims, we say so and recalibrate.
See VALIDATION.md for the full plan: industry stress tests, token
economics, breakeven analysis, and a JSON adversarial comparison that
isolates what Ten specifically contributes vs. what domain libraries
contribute independently of Ten.

## What Ten Is (30-second version)
A formal algebra for AI-to-AI communication. Not a protocol — a language
that rides inside protocols (MCP, A2A). Messages are math (sortable,
filterable, composable) not natural language. No LLM inference needed to
encode/decode — it's struct packing, array comparisons, tree walks.

## Architecture (decided)
- **libten** (C) — Core algebra library. Arena-allocated, zero deps.
- **Python bindings** — Thin ctypes/cffi wrapper around libten.
- **ten-mcp-server** (Python) — MCP tool exposure. No AI inference.
- **The Canonica** (Python + PostgreSQL) — Living token registry.

## Repo: github.com/johnbeans/Ten
Location on disk: /Users/johnbeans/Ten
## Doc files (reference only — don't re-read unless needed)
- TEN-SPEC.md (44KB) — Full algebra spec, kernel types, encoding, FAQ
- ARCHITECTURE.md (19KB) — C core rationale, arena model, package layout
- ROADMAP.md — Phase plan. Validation (Phase 1.5) is the critical gate.
- VALIDATION.md — Industry stress tests, token economics, honest accounting
- WHY-TEN.md (10KB) — Audience-targeted pitches

## libten Implementation Status

### COMPLETE — compiles clean, 49/49 tests pass
```
libten/
├── include/ten.h          (295 lines) — Full public API
├── src/ten_internal.h     — Internal arena helpers
├── src/arena.c            — Arena allocator (init/free/reset/alloc)
├── src/types.c            — All 6 kernel type constructors
│   scalar, ref, identity, assertion, operation, structure
├── src/compose.c          — All 6 composition operations
│   sequence(⊕), product(⊗), nest(λ), union(∪), intersect(∩), project(π)
├── src/facets.c           — Facet vector ops (init/set/get/has/filter)
├── src/validate.c         — Recursive expression validation
├── src/util.c             — type_name, error_string, op_name, describe
├── tests/test_main.c      — 49 tests covering all of the above
├── Makefile               — `make`, `make test`, `make debug` (ASan+UBSan)
└── build/libten.a         — Static library output
```
### NOT YET IMPLEMENTED
1. **Serialization (encode/decode)** — Wire format for binary encoding.
   Needs decisions on:
   - Scalar encoding: varint vs fixed-width+precision-tag vs IEEE 754 subset
   - Facet vector layout: fixed-position vs tagged with dimension IDs
   - Expression tree: array-of-structs vs pointer-based (arena makes both safe)
   - Hash algorithm: SHA-256 (default assumption) vs BLAKE3 (faster)
   Strategy: benchmark before committing.

2. **Python bindings (tenlang)** — ctypes/cffi wrapper around libten.
   ~200 lines. Blocked on: encode/decode (need wire format for round-trip).

3. **ten-mcp-server** — Python MCP server wrapping tenlang.
   Blocked on: Python bindings.

4. **The Canonica** — Token registry service.
   Blocked on: MCP server (needs real usage telemetry).

5. **Validation (Phase 1.5)** — Industry stress tests. Blocked on: libten
   serialization (need encode/decode for round-trip benchmarks, but the
   in-memory algebra is ready for domain library development now).

## Key Design Decisions (already made)
- Messages carry metadata, not content. Payloads are SHA-256 References.
- Arena allocation: one malloc per message, one free. No individual allocs.
- Hard limits: 256 depth, 4096 children, 64 facet dimensions.
- Facet vector = fixed-position sortable header (urgency, cost, etc.)
- All composition ops are CLOSED — valid in, valid out, always.

## Build & Test
```
cd /Users/johnbeans/Ten/libten
make        # builds build/libten.a
make test   # builds and runs 49 tests
make debug  # ASan + UBSan build
```

## C API Quick Reference (for new chat context)
```c
// Arena lifecycle
ten_arena_init(&a, size) → ten_arena_free(&a)

// Kernel constructors (all return ten_expr_t*)
ten_scalar(&a, dimension, value, precision)
ten_ref(&a, hash[32])
ten_identity(&a, pubkey, keylen)
ten_assertion(&a, claim_expr, who_expr, confidence)
ten_operation(&a, verb, args[], nargs)
ten_structure(&a, members[], nmembers)

// Composition (all return ten_expr_t*, all CLOSED)
ten_sequence(&a, left, right)    // ⊕ ordered
ten_product(&a, left, right)     // ⊗ parallel
ten_nest(&a, envelope, payload)  // λ wrapping
ten_union(&a, left, right)       // ∪
ten_intersect(&a, left, right)   // ∩
ten_project(&a, expr, dims[], ndims)  // π extract

// Facets
ten_facet_init(&a, expr)
ten_facet_set(expr, dim, value, precision)
ten_facet_get(expr, dim) → double
ten_facet_has(expr, dim) → bool
ten_facet_filter(expr, &filter) → bool

// Not yet: ten_encode(), ten_decode()
```
