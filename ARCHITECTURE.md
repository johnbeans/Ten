# Ten Architecture

## Overview

Ten's implementation is split into three components with distinct performance profiles, technology choices, and deployment models.

```
┌─────────────────────────────────────────────────┐
│           AI (Claude, GPT, Gemini, etc.)         │
│         "Thinks in whatever it thinks in"        │
└──────────────┬──────────────────┬────────────────┘
               │ MCP tool calls   │ REST API calls
               ▼                  ▼
┌──────────────────────┐ ┌────────────────────────┐
│   ten-mcp-server     │ │      ten-api           │
│   (Python, local)    │ │   (Python, local)      │
└──────────┬───────────┘ └───────────┬────────────┘
           │          │              │
           ▼          ▼              ▼
┌─────────────────────────────────────────────────┐
│                    libten                        │
│            (C core algebra library)              │
│  encode · decode · compose · project · filter    │
│         serialize · deserialize · verify         │
└─────────────────────────────────────────────────┘

         ┌──────────── background ────────────┐
         │         telemetry reports           │
         ▼                                    │
┌─────────────────────────────┐               │
│      Ten Canonica           │               │
│  (Python + PostgreSQL)      │               │
│  thecanonica.org            │               │
│  hosted on Railway/Fly.io   │               │
└─────────────────────────────┘               │
         │ canonical forms,                   │
         │ slang updates                      │
         ▼                                    │
   ┌───────────┐                              │
   │ vocabulary │──────────────────────────────┘
   │  tables    │  (cached locally by each AI)
   └───────────┘
```
---

## Component 1: libten (C core algebra library)

### What it does

Everything on the hot path. Encode Ten expressions to bytes, decode bytes back, compose two expressions, project onto dimensions, filter by facet vector, serialize/deserialize the wire format, validate expression structure. This is the engine that replaces LLM inference for infrastructure operations.

### Why C

The core algebra is: pack structs into bytes, unpack bytes into structs, compare numbers in fixed-length arrays, walk trees of typed nodes. This is closer to firmware than a web app. C gives us:

- **Sub-microsecond operations.** A facet vector filter is an array comparison. Composition is tree manipulation. Serialization is struct packing. These should be measured in nanoseconds, not milliseconds.
- **Zero dependencies.** libten links against nothing. It's a .a/.so/.dylib that can be embedded anywhere — Python, Node, Go, Rust, or bare metal.
- **Universal bindability.** Every language has a C FFI. Python gets bindings via ctypes/cffi. Node via N-API. Rust via extern "C". One implementation serves every platform.
- **Predictable memory.** No garbage collector, no runtime allocator surprises. We control every byte (see Memory Model below).

### Memory Model

**Design rule: Ten messages carry metadata, not content.** Large payloads (documents, images, datasets) are never inlined in a Ten message. They are stored elsewhere and referenced via the Reference type (ρ) — a 32-byte content-addressed hash. The Ten message carries the hash, not the data. This is both an efficiency principle (don't transmit what the receiver already has) and a safety principle (message sizes are bounded and predictable).
This means all kernel types have small, predictable sizes:

| Type | Size | Notes |
|------|------|-------|
| Scalar (σ) | 1–16 bytes | Value + precision tag |
| Reference (ρ) | 32 bytes | SHA-256 hash |
| Identity (ι) | 32–64 bytes | Public key |
| Assertion (α) | ~128 bytes | Reference + Scalar + Identity |
| Operation (ω) | ~64 bytes | Verb tag + argument References |
| Structure (τ) | Variable, small | Type descriptor tree |
| Facet vector | N × 8 bytes | 16 dimensions = 128 bytes |

A typical message (3 assertions, a facet vector, a payload reference) is under 1KB. A complex workflow description with 50 nodes might reach 10KB. That's the realistic ceiling.

**Arena allocation:** libten uses arena (region-based) allocation for all decoded expressions. When decoding a message, one contiguous block is allocated (default 64KB, configurable). All tree nodes for that message are carved from the arena. When processing is complete, the entire arena is freed in a single call. No individual malloc/free pairs, no fragmentation, no leaks, no use-after-free.

```c
ten_arena_t arena;
ten_arena_init(&arena, TEN_DEFAULT_ARENA_SIZE);  // 64KB

ten_expr_t *msg = ten_decode(&arena, bytes, len);
if (!msg) {
    // TEN_ERROR_MESSAGE_TOO_LARGE, TEN_ERROR_MALFORMED, etc.
    ten_arena_free(&arena);
    return;
}

float urgency = ten_facet_get(msg, TEN_FACET_URGENCY);
// ... filter, project, compose ...

ten_arena_free(&arena);  // One call frees everything
```
**Hard limits with clean errors:** The decoder reads length prefixes before allocating. If a field exceeds the arena budget, decoding fails with a defined error code before any allocation occurs. The C code never touches oversized data. Configurable limits include:

- `TEN_DEFAULT_ARENA_SIZE` — 64KB default, adjustable per context
- `TEN_MAX_EXPRESSION_DEPTH` — 256 levels of nesting
- `TEN_MAX_CHILDREN` — 4,096 nodes in one expression

These are generous limits that no legitimate message would approach, but they guarantee that libten never performs unbounded allocation regardless of input.

**What if someone puts a novel in a message?** The serialization format has length prefixes on every field. The decoder checks the length against the arena budget and rejects the message before copying any data. This is the same pattern used in embedded protocol parsers — validate before committing. The correct way to transmit large content in Ten is via a Reference (ρ) pointing to the content stored elsewhere. Ten messages are envelopes, not containers.
### API Surface (Provisional)

```c
// --- Arena ---
int  ten_arena_init(ten_arena_t *a, size_t size);
void ten_arena_free(ten_arena_t *a);

// --- Encode / Decode ---
int         ten_encode(ten_arena_t *a, const ten_expr_t *expr, uint8_t *buf, size_t *len);
ten_expr_t *ten_decode(ten_arena_t *a, const uint8_t *buf, size_t len);

// --- Kernel type constructors ---
ten_expr_t *ten_scalar(ten_arena_t *a, uint16_t dim, double val, uint8_t precision);
ten_expr_t *ten_ref(ten_arena_t *a, const uint8_t hash[32]);
ten_expr_t *ten_identity(ten_arena_t *a, const uint8_t *pubkey, size_t keylen);
ten_expr_t *ten_assertion(ten_arena_t *a, ten_expr_t *claim, ten_expr_t *who, double confidence);
ten_expr_t *ten_operation(ten_arena_t *a, uint16_t verb, ten_expr_t **args, size_t nargs);

// --- Composition ---
ten_expr_t *ten_sequence(ten_arena_t *a, ten_expr_t *left, ten_expr_t *right);
ten_expr_t *ten_product(ten_arena_t *a, ten_expr_t *left, ten_expr_t *right);
ten_expr_t *ten_project(ten_arena_t *a, const ten_expr_t *expr, const uint16_t *dims, size_t ndims);
ten_expr_t *ten_nest(ten_arena_t *a, ten_expr_t *envelope, ten_expr_t *payload);
ten_expr_t *ten_union(ten_arena_t *a, ten_expr_t *left, ten_expr_t *right);
ten_expr_t *ten_intersect(ten_arena_t *a, ten_expr_t *left, ten_expr_t *right);

// --- Facet vector ---
double ten_facet_get(const ten_expr_t *expr, uint16_t dim);
int    ten_facet_set(ten_expr_t *expr, uint16_t dim, double val, uint8_t precision);
int    ten_facet_filter(const ten_expr_t *expr, const ten_filter_t *criteria);
```
### Performance Targets

| Operation | Target | Comparable to |
|-----------|--------|---------------|
| Encode a typical message | < 1 µs | struct.pack |
| Decode a typical message | < 1 µs | struct.unpack |
| Filter 10,000 messages by facet | < 1 ms | Array scan |
| Sort 10,000 messages by urgency | < 5 ms | qsort on doubles |
| Compose two expressions | < 1 µs | Tree node allocation |
| Project onto N dimensions | < 1 µs | Subtree extraction |

For comparison: a single LLM inference call to parse one natural language message and extract its urgency takes 200ms–2s and costs $0.001–$0.01. libten does the same work in microseconds at effectively zero cost.

---

## Component 2: ten-mcp-server and ten-api (Python wrappers)

### What they do

Expose libten's functionality to AIs and applications. The MCP server provides tool calls (`ten.encode`, `ten.decode`, `ten.compose`, `ten.project`, `ten.filter`, `ten.verify`). The REST API provides HTTP endpoints mirroring the same operations. Both are stateless — they call into libten and return results.

### Why Python

Not for performance — for ecosystem. The MCP SDK is Python. FastAPI is Python. Every AI developer has Python installed. The wrappers do no computation themselves; they translate between JSON/MCP tool call formats and libten's C API via ctypes or cffi. The performance bottleneck is never the wrapper — it's always the algebra, which runs in C.
### Where they run

**Locally.** The MCP server runs on the same machine as the AI client — a laptop, a cloud instance, a server. This is how MCP works: the server is a local process that the AI calls via JSON-RPC. There is nothing to "host" for this component. Users install it via pip or npx, the same way they install any MCP server.

The REST API is optionally deployable as a service for non-MCP clients, but can also run locally.

### Key design constraint

**The MCP server is pure code — no AI inference.** This is the most important architectural decision in the project. The Ten MCP server never calls an LLM. Encoding is building a data structure. Decoding is deserializing bytes. Filtering is numeric comparison. The AI decides *what to say*. Ten handles *packing and unpacking the envelope*. One is a billion-dollar inference operation. The other is a microsecond of arithmetic.

---

## Component 3: Ten Canonica (Python + PostgreSQL)

### What it does

The living registry of Ten's vocabulary. Collects anonymized usage telemetry from participating AIs. Detects algebraic equivalences between independently invented constructs. Publishes canonicalization guidance (which constructs are canonical, which are deprecated, which slang tokens are minted). Serves as the query endpoint for AIs encountering unfamiliar constructs.
### Why it's not performance-critical

**Ten Canonica is never on the critical path of any message.** No AI waits for Ten Canonica before sending or receiving a Ten message. AIs consult Ten Canonica periodically to update their local vocabulary tables — like pulling a git repo. They report telemetry in the background. The equivalence detection engine runs as a batch job, not in real-time. This means Ten Canonica can be architecturally simple and modestly resourced.

### Technology

- **Python + FastAPI** for the API layer
- **PostgreSQL** for storing type definitions, usage telemetry, canonical forms, and slang registries
- **Batch analytics** for equivalence detection and slang minting (runs on the Canonica's schedule, not on demand)

### Where it runs

This is the one cloud-hosted component. For the bootstrap phase, a single instance on **Railway or Fly.io** is sufficient — a web API backed by PostgreSQL on a $5–20/month instance. The load during bootstrap is negligible. Federation and decentralization (see TEN-SPEC Appendix B.9) are long-horizon goals for when load and governance demand it.

### Interaction pattern

```
AI ──(background)──► Ten Canonica: "Here's my usage telemetry for the past hour"
AI ──(periodic)────► Ten Canonica: "Give me updated canonical forms since timestamp T"
AI ──(on demand)───► Ten Canonica: "I encountered construct X — what is it?"
Ten Canonica ──(batch)─► Ten Canonica: "Run equivalence detection on new telemetry"
Ten Canonica ──(batch)─► Ten Canonica: "Mint slang tokens for high-frequency compounds"
```

None of these interactions are latency-sensitive. The AI never blocks waiting for Ten Canonica to respond before processing a message.
---

## Package Structure

```
Ten/
├── libten/                    # C core algebra library
│   ├── include/
│   │   └── ten.h              # Public API header
│   ├── src/
│   │   ├── arena.c            # Arena allocator
│   │   ├── types.c            # Kernel type constructors
│   │   ├── compose.c          # Composition operations
│   │   ├── facet.c            # Facet vector operations
│   │   ├── serialize.c        # Binary wire format
│   │   └── validate.c         # Expression validation
│   ├── tests/
│   └── Makefile
├── tenlang/                   # Python bindings (pip install tenlang)
│   ├── __init__.py
│   ├── _ffi.py                # ctypes/cffi wrapper around libten
│   ├── types.py               # Pythonic API over C types
│   └── tests/
├── ten-mcp-server/            # MCP server (pip install ten-mcp-server)
│   ├── server.py              # MCP tool definitions
│   └── tests/
├── ten-api/                   # REST API (optional deployment)
│   ├── app.py                 # FastAPI endpoints
│   └── tests/
├── canonica/                  # The Canonica service
│   ├── app.py                 # FastAPI + PostgreSQL
│   ├── telemetry.py           # Usage ingestion
│   ├── equivalence.py         # Algebraic equivalence detection
│   ├── slang.py               # Slang token minting
│   └── tests/
├── TEN-SPEC.md
├── ARCHITECTURE.md
├── ROADMAP.md
├── WHY-TEN.md
├── README.md
└── LICENSE
```
The critical architectural boundary is between `libten/` and everything above it. The C library is the engine. Everything else is a wrapper or a service that calls into it. This means:

- Rewriting or optimizing the core only touches `libten/`
- Adding a new language binding (Go, Rust, Node) only requires wrapping `libten/`
- The MCP server, REST API, and Canonica are all consumers of the same library
- `libten/` can be embedded in firmware, mobile apps, or any C-compatible environment

---

## Build Plan

### Phase 1: Prove the algebra (libten + Python bindings)

Build libten with the kernel types, composition operations, facet vectors, and binary serialization. Wrap it in Python. Write comprehensive tests proving closure (every composition of valid expressions produces a valid expression). Benchmark against JSON encoding/decoding for equivalent data.

**Deliverable:** `pip install tenlang` gives you a working Ten encoder/decoder backed by C.

### Phase 2: Ship the MCP server (ten-mcp-server)

Wrap the Python bindings in an MCP server. Register tools. Test with Claude, GPT, and Gemini. Publish to MCP registry.

**Deliverable:** Any MCP-compatible AI can speak Ten by installing one server.

### Phase 3: Launch the Canonica (canonica)

Deploy the registry service. Implement telemetry ingestion, equivalence detection, and canonical form publication. Stand up thecanonica.org as a public dashboard.

**Deliverable:** Ten's vocabulary begins evolving based on real usage.

---
## Open Performance Questions

These are design decisions that need to be resolved during implementation, not before:

**Wire format details.** How exactly are variable-precision scalars encoded? Options include varint (compact, variable-length), fixed-width with precision tag (simpler, slightly wasteful), or IEEE 754 subsets. The choice affects both message size and decode speed. Benchmark before committing.

**Facet vector layout.** Fixed-position with known dimensions, or tagged with dimension IDs? Fixed-position is faster to filter (direct array index) but requires all participants to agree on dimension positions. Tagged is more flexible but requires a scan. Our current leaning is fixed-position for well-known dimensions with a tagged overflow region for new/uncommon dimensions.

**Expression tree representation.** Array of structs (cache-friendly, good for sequential traversal) versus pointer-based tree (natural for recursive operations). Arena allocation makes pointer-based trees safe, but array-of-structs may be faster for the common case of linear message scanning. Profile before deciding.

**Hash algorithm for References.** SHA-256 is the default assumption (32 bytes, universally supported, collision-resistant). But BLAKE3 is faster and equally secure. If performance profiling shows hashing as a bottleneck (unlikely for metadata-sized content), BLAKE3 is the upgrade path. The wire format should use a hash-algorithm tag so this can evolve.

**Slang token encoding.** How large is the slang namespace? 16-bit IDs give 65K tokens. 32-bit gives 4 billion. The slang lookup table size and cache behavior depend on this choice. Start with 16-bit; expand if the Canonica's evolution mechanism demands it.

---

## Summary of Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Core language | C | Performance-critical path, universal bindability, firmware-grade memory control |
| Memory model | Arena allocation | One alloc, one free, no leaks, bounded by hard limits |
| Content in messages | Never inlined, always referenced | Bounded message sizes, predictable memory, efficient caching |
| MCP server / REST API | Python | Ecosystem convenience, not performance-critical (wrapper only) |
| Ten Canonica | Python + PostgreSQL | Not on the critical path, standard web service, simple deployment |
| Canonica hosting | Railway or Fly.io | Cheap, simple, sufficient for bootstrap phase |
| MCP server hosting | Local (user's machine) | MCP architecture requires it; no cloud hosting needed |
| Build order | libten → Python bindings → MCP server → Canonica | Each phase has a clear deliverable and builds on the previous |
