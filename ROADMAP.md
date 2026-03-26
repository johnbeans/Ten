# Ten Roadmap

## Phase 0: Foundation (Current)
- [x] Founding specification (TEN-SPEC.md v0.1.0)
- [x] Type kernel candidates identified
- [x] Composition algebra defined
- [x] Known gaps and open critiques documented (Appendix B)
- [ ] Secure tenlang.org domain
- [ ] Formal review of kernel minimality and sufficiency

## Phase 1: Reference Implementation
The core deliverable is a **Ten MCP server** — the primary adoption vehicle.

### Python Core Library (`tenlang`)
- [ ] Kernel type implementations (Scalar, Reference, Identity, Assertion, Operation, Structure)
- [ ] Composition operations (Sequence, Product, Projection, Nesting, Union, Intersection)
- [ ] Facet vector encoding and extraction
- [ ] Variable-resolution scalar encoding
- [ ] Binary serialization / deserialization
- [ ] Expression validation (closure property enforcement)
- [ ] Self-description: τ-expression generation and parsing

### Ten MCP Server
- [ ] MCP tool: `ten.encode` — natural language → Ten expression
- [ ] MCP tool: `ten.decode` — Ten expression → human-readable description
- [ ] MCP tool: `ten.compose` — combine two Ten expressions
- [ ] MCP tool: `ten.project` — extract dimensions from an expression
- [ ] MCP tool: `ten.filter` — evaluate a Ten expression against filter criteria
- [ ] MCP tool: `ten.describe` — return the τ-structure of an expression
- [ ] MCP tool: `ten.verify` — check assertions and trust chains
- [ ] Publish to MCP registry for one-click installation
### Ten REST API
- [ ] HTTP endpoints mirroring MCP tools for non-MCP systems
- [ ] WebSocket support for streaming Ten message exchanges
- [ ] API documentation and interactive playground

### Benchmarks
- [ ] Message size: Ten vs. JSON vs. natural language for equivalent content
- [ ] Parse/filter time: Ten facet vector extraction vs. JSON field lookup
- [ ] Compose time: Ten algebraic composition vs. string concatenation/merge
- [ ] Round-trip: encode → transmit → decode → act latency comparison

## Phase 2: Rosetta Stone (Living Registry)
- [ ] Minimal Rosetta Stone server (type registry, slang registry)
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
- [ ] Rosetta Stone federation (decentralized operation)

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
- Native LLM training on Ten syntax (Phase 3+ optimization, not a prerequisite)
- Blockchain or token economics
- Human-readable Ten notation (Ten is for machines; debugging tools are for humans)
- Replacing existing protocols (Ten complements MCP/A2A/ACP, doesn't compete)
