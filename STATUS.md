# Ten Implementation Status
# Last updated: 2026-03-29 (REST API + MCP registry packaging added)
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

### COMPLETE — compiles clean, 69/69 tests pass
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
├── src/serialize.c        — Binary wire format v1 (encode/decode)
│   Precision-aware scalar encoding (1–64 bits), facet vectors,
│   recursive expression tree, "Ten:" magic header envelope
├── src/util.c             — type_name, error_string, op_name, describe
├── tests/test_main.c      — 69 tests covering all of the above
├── Makefile               — `make`, `make test`, `make debug` (ASan+UBSan)
└── build/                 — libten.a (static) + libten.so/.dylib (shared)
```

### tenlang (Python bindings) — COMPLETE, 53/53 tests pass
```
tenlang/
├── __init__.py            — Package exports: Arena, Expr, encode, decode, constants
├── _ffi.py                — ctypes wrapper: struct definitions, library loading,
│                            function signatures for all 30+ C functions
├── types.py               — Pythonic API: Arena (context manager), Expr (property
│                            accessors), encode()/decode(), TenError exceptions
└── tests/
    └── test_tenlang.py    — 53 pytest tests mirroring the C test suite
```
```
pyproject.toml             — Package metadata for `pip install tenlang`
```

### ten_mcp_server — COMPLETE, 31/31 tests pass
```
ten_mcp_server/
├── __init__.py            — Package marker
├── __main__.py            — Entry point: python -m ten_mcp_server
├── server.py              — FastMCP server with 7 tools:
│   ten_encode             — structured dict → Ten wire format (b64/hex)
│   ten_decode             — wire format → structured dict + description
│   ten_compose            — combine two expressions (seq/prod/nest/union/inter)
│   ten_project            — extract facet dimensions (SELECT columns)
│   ten_filter             — batch filter by facet criteria (inbox processing)
│   ten_describe           — human-readable tree dump + structural analysis
│   ten_verify             — structural integrity check + assertion details
├── pyproject.toml         — Package metadata for `pip install ten-mcp-server`
├── server.json            — MCP registry metadata (io.github.johnbeans/ten)
├── README.md              — MCP server documentation
└── tests/
    └── test_tools.py      — 31 tests covering all 7 tools
```

### ten_rest_api — COMPLETE, 35/35 tests pass
```
ten_rest_api/
├── __init__.py            — Package marker
├── __main__.py            — Entry point: python -m ten_rest_api
├── app.py                 — FastAPI server with 7 endpoints + health check:
│   POST /v1/encode        — structured dict → Ten wire format (b64/hex)
│   POST /v1/decode        — wire format → structured dict + description
│   POST /v1/compose       — combine two expressions (seq/prod/nest/union/inter)
│   POST /v1/project       — extract facet dimensions (SELECT columns)
│   POST /v1/filter        — batch filter by facet criteria (inbox processing)
│   POST /v1/describe      — human-readable tree dump + structural analysis
│   POST /v1/verify        — structural integrity check + assertion details
│   GET  /health           — service health check
│   GET  /docs             — auto-generated OpenAPI docs (Swagger UI)
│   GET  /redoc            — auto-generated ReDoc docs
└── tests/
    └── test_api.py        — 35 tests using FastAPI TestClient
```

### NOT YET IMPLEMENTED
1. **MCP registry publication** — ten-mcp-server is packaged with server.json
   and pyproject.toml ready for PyPI + mcp-publisher. Needs `pip install twine`
   and `brew install mcp-publisher` on your Mac to publish.

2. **WebSocket support** — Streaming Ten message exchanges over WS.

3. **The Canonica** — Token registry service.
   Blocked on: real usage telemetry from MCP server deployment.

4. **Validation (Phase 1.5)** — Industry stress tests. The full stack
   (libten → tenlang → ten-mcp-server → ten-rest-api) is ready. Next step
   is building domain libraries and measuring against JSON + LLM baselines.

## Key Design Decisions (already made)
- Messages carry metadata, not content. Payloads are SHA-256 References.
- Arena allocation: one malloc per message, one free. No individual allocs.
- Hard limits: 256 depth, 4096 children, 64 facet dimensions.
- Facet vector = fixed-position sortable header (urgency, cost, etc.)
- All composition ops are CLOSED — valid in, valid out, always.

## Build & Test
```
# C core
cd /Users/johnbeans/Ten/libten
make        # builds build/libten.a + libten.so (or .dylib on macOS)
make test   # builds and runs 69 C tests
make debug  # ASan + UBSan build

# Python bindings
cd /Users/johnbeans/Ten
python -m pytest tenlang/tests/ -v        # 53 Python binding tests

# MCP server
python -m pytest ten_mcp_server/tests/ -v # 31 MCP tool tests

# REST API
pip install fastapi httpx
python -m pytest ten_rest_api/tests/ -v   # 35 REST endpoint tests

# Run REST API server
uvicorn ten_rest_api.app:app --port 8420  # → http://localhost:8420/docs
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

// Serialization (wire format v1)
ten_encode(expr, buf, bufsize, &outlen)   // → TEN_OK or error
ten_decode(&a, buf, len)                  // → ten_expr_t* or NULL
```

## Python API Quick Reference (for new chat context)
```python
from tenlang import Arena, encode, decode
from tenlang import TEN_FACET_URGENCY, TEN_OP_QUERY, TEN_PREC_16BIT

with Arena() as a:
    # Kernel constructors (all return Expr)
    s = a.scalar(dimension, value, precision=TEN_PREC_64BIT)
    r = a.ref(hash_bytes_32)
    i = a.identity(pubkey_bytes)
    asr = a.assertion(claim_expr, who_expr, confidence)
    op = a.operation(verb, [arg1, arg2])
    st = a.structure([member1, member2])

    # Composition (all return Expr, all CLOSED)
    a.sequence(left, right)    # ⊕
    a.product(left, right)     # ⊗
    a.nest(envelope, payload)  # λ
    a.union(left, right)       # ∪
    a.intersect(left, right)   # ∩
    a.project(expr, [dim1, dim2])  # π

    # Facets
    expr.set_facet(dim, value, precision=TEN_PREC_64BIT)
    expr.get_facet(dim)        # → float
    expr.has_facet(dim)        # → bool
    expr.matches_filter([(dim, op, threshold), ...])

    # Serialization
    wire = encode(expr)        # → bytes

with Arena() as a2:
    decoded = decode(a2, wire) # → Expr
    decoded.is_valid()         # → bool
    decoded.describe()         # → str (debug output)
```
