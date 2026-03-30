# Ten Roadmap

## The Strategic Priority

Ten makes a bold claim: that a formal algebra can handle machine-to-machine communication more efficiently than natural language + LLM inference, and more robustly than JSON + custom code. **Proving this claim — transparently, with measured data, including where it fails — is the most important goal of the project.**

Everything in this roadmap serves that goal. The reference implementation exists to make measurement possible. The validation scenarios exist to make the measurements honest. The Canonica exists to demonstrate the long-term ecosystem value. If the measurements don't support the claim, the project should say so and recalibrate — not rationalize.

The status quo is not weak. LLMs are cheap, fast, and getting cheaper. JSON is universal, well-tooled, and understood by everyone. Ten must demonstrate concrete, measurable advantages that justify its existence — not just in theory, but in token counts, dollar costs, latency, determinism, and composability. The alternative is an elegant algebra that nobody needs.

See **[VALIDATION.md](VALIDATION.md)** for the full validation design, token economics, and honest accounting of where Ten wins and loses.

---

## Phase 0: Foundation (Current)
- [x] Founding specification (TEN-SPEC.md v0.1.0)
- [x] Type kernel candidates identified
- [x] Composition algebra defined
- [x] Known gaps and open critiques documented (Appendix B)
- [x] libten C core — 6 kernel types, 6 composition ops, facets, validation, serialization (69/69 tests pass)
- [ ] Secure tenlang.org domain
- [ ] Formal review of kernel minimality and sufficiency

## Phase 1: Reference Implementation
The core deliverable is a **Ten MCP server** — the primary adoption vehicle. But the MCP server is a means, not the end. The end is having a working system that can be measured against the status quo.

### libten Completion
- [x] Binary serialization / deserialization (wire format v1)
      Precision-aware encoding: 1-bit → 1 byte, 4/8-bit → 1 byte,
      16-bit → 2 bytes, 32-bit → 4 bytes (float), 64-bit → 8 bytes (double).
      Facet vectors use tagged layout (dim_id + precision + 8B value).
      SHA-256 assumed for Reference hashes (32 bytes on wire).
- [ ] Benchmark: SHA-256 vs. BLAKE3 for hash performance

### Python Core Library (`tenlang`) — COMPLETE, 53/53 tests pass
- [x] ctypes wrapper (_ffi.py): struct definitions, library loading, all function signatures
- [x] Pythonic API (types.py): Arena context manager, Expr with property accessors, encode/decode
- [x] All 6 kernel type constructors (Scalar, Reference, Identity, Assertion, Operation, Structure)
- [x] All 6 composition operations (Sequence, Product, Projection, Nesting, Union, Intersection)
- [x] Facet vector operations (init, set, get, has, filter)
- [x] Variable-resolution scalar encoding (1-bit through 64-bit via libten)
- [x] Expression validation (closure property enforcement)
- [x] Full binary serialization round-trip (encode/decode via wire format v1)
- [x] 53 pytest tests covering all of the above
- [x] pyproject.toml for `pip install tenlang`
- [ ] Self-description: τ-expression generation and parsing (deferred to Phase 2)

### Ten MCP Server — COMPLETE, 31/31 tests pass
- [x] MCP tool: `ten.encode` — structured data → Ten expression
- [x] MCP tool: `ten.decode` — Ten expression → human-readable description
- [x] MCP tool: `ten.compose` — combine two Ten expressions
- [x] MCP tool: `ten.project` — extract dimensions from an expression
- [x] MCP tool: `ten.filter` — evaluate a Ten expression against filter criteria
- [x] MCP tool: `ten.describe` — return the τ-structure of an expression
- [x] MCP tool: `ten.verify` — check assertions and trust chains
- [ ] Publish to MCP registry for one-click installation

### Ten REST API
- [ ] HTTP endpoints mirroring MCP tools for non-MCP systems
- [ ] WebSocket support for streaming Ten message exchanges
- [ ] API documentation and interactive playground

## Phase 1.5: Industry Validation — THE CRITICAL GATE

**Nothing beyond this phase matters if the validation fails.** This is not a nice-to-have appendix. It is the moment where Ten either proves its value with data or remains an interesting theoretical exercise.

Full design: **[VALIDATION.md](VALIDATION.md)**

### Scenario Encoding
- [ ] Derivatives portfolio: encode all 13 legs of a 5-strategy options portfolio in libten
- [ ] Supply chain: encode a multi-jurisdiction Shenzhen→Hamburg shipment document tree
- [ ] Clinical trial: encode a Phase III protocol with regulatory assertions and interim analysis
- [ ] All tests pass with `make test`

### Domain Computation Libraries
- [ ] Derivatives: ~95 lines of C — 6 composable functions handling all options strategies
- [ ] Supply chain: ~90 lines — landed cost, document completeness, trust chain verification
- [ ] Clinical: ~70 lines — site readiness, adverse event routing, enrollment projection
- [ ] For each library: count lines that are Ten-specific vs. domain math vs. glue

### Honest Measurement
- [ ] English baseline: run each analysis via LLM, measure tokens, cost, latency, accuracy, variance (100 runs)
- [ ] Ten approach: measure per-transaction tokens (should be 0 for structured sources), latency, accuracy, variance (should be 0)
- [ ] Breakeven calculation: how many analyses before Ten's library investment pays for itself
- [ ] **JSON adversarial: rewrite each domain library to read from JSON instead of Ten, measure the difference — this isolates Ten's contribution from the domain library's contribution**
- [ ] Longitudinal test: 200 synthetic trades over 12 months, annual P&L via Ten algebra vs. LLM chunked summarization, **measure variance in the LLM's final number**

### Publication
- [ ] Publish all results in VALIDATION-RESULTS.md — token counts, costs, latency, variance, breakevens
- [ ] Explicitly document where Ten loses (one-off analysis, novel domains, qualitative questions)
- [ ] Explicitly document where JSON-with-domain-library is nearly equivalent to Ten-with-domain-library
- [ ] Explicitly document where Ten's algebraic properties (composition, closure, facets, self-description) provide value that JSON cannot

**Gate decision:** If the validation shows that Ten's advantages over JSON + domain code are marginal, the project should focus on the specific scenarios where algebraic composition, closure, and facet vectors provide measurable value — not pretend Ten is universally better.

## Phase 2: Canonica (Living Registry)
- [ ] Minimal Canonica server (type registry, slang registry)
- [ ] Seed with domain type libraries from Phase 1.5 validation
- [ ] Telemetry ingestion endpoint
- [ ] Equivalence detection engine (algebraic isomorphism checking)
- [ ] Subsumption analysis (does type A generalize type B?)
- [ ] Slang minting: automatic short-token assignment for high-frequency compounds
- [ ] Canonicalization publication API
- [ ] Public dashboard showing vocabulary evolution

## Phase 3: Real-World Integration
- [ ] Demo: two LLMs negotiating a task via Ten over MCP (with side-by-side natural language comparison)
- [ ] Integration example: Ten payloads inside A2A messages
- [ ] Integration example: Ten payloads inside MCP tool responses
- [ ] Integration example: Ten in a multi-agent orchestration framework (e.g., OpenClaw, LangGraph, CrewAI)
- [ ] First external adopter

## Phase 4: Advanced Capabilities
- [ ] Zero-knowledge proof integration (pluggable ZKP schemes)
- [ ] Trust network computation engine
- [ ] Conditional expression support (B.11 resolution)
- [ ] Semantic grounding framework (calibration anchors for scalars)
- [ ] Sybil-resistant telemetry (mechanism design for honest reporting)
- [ ] Canonica federation (decentralized operation)

## Research Track (Parallel)
These are ongoing formal research problems, not gated by implementation phases:
- [ ] Kernel minimality proof
- [ ] Kernel sufficiency proof (test against real communication patterns)
- [ ] Convergence proof for evolution mechanism
- [ ] Decidability bounds for τ-equivalence
- [ ] Optimal slang theory (information-theoretic framework)
- [ ] Strategy-proof mechanism design for telemetry
- [ ] Formal semantics for conditional expressions

## Non-Goals (For Now)
- Native LLM generation of Ten syntax (the MCP boundary between AI thinking and Ten plumbing is a feature, not a limitation to overcome)
- Blockchain or token economics
- Human-readable Ten notation (Ten is for machines; debugging tools are for humans)
- Replacing existing protocols (Ten complements MCP/A2A/ACP, doesn't compete)
