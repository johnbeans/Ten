# Ten

### A formal algebra for machine intelligence communication

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Spec](https://img.shields.io/badge/spec-v0.1.0-green.svg)](TEN-SPEC.md)

Ten is a language designed for machines, not people.

It is a formal algebra whose messages can be composed, projected, filtered, sorted, and verified through mathematical operations — not parsed through natural language understanding. Ten is not human-readable by design.

**The problem:** AI agents today communicate using natural language or JSON stuffed into protocols like MCP and A2A. This works, but it's profoundly wasteful. Every receiving AI must parse ambiguous text, infer intent, and guess at priority. Sorting a thousand messages by urgency requires parsing all of them.

**Ten's answer:** A mathematically rigorous message algebra where urgency is a sortable scalar in a fixed-position header, where two messages can be composed into a valid third message, where trust is a computable property of the message itself, and where the language continuously optimizes its own encoding based on real usage patterns.

## The Most Important Thing

Ten makes a strong claim: that a formal algebra beats the status quo (natural language + LLM inference, or JSON + custom code) for machine-to-machine communication at scale. **Proving this claim transparently — with measured token counts, dollar costs, latency, variance data, and honest accounting of where Ten loses — is the project's primary goal.**

The status quo is not weak. LLMs are cheap and getting cheaper. JSON is universal and well-tooled. Ten must earn its place with data, not assertions. The [validation plan](VALIDATION.md) designs industry-specific stress tests (derivatives portfolios, international supply chains, clinical trials), measures everything, and includes an adversarial comparison against JSON + domain code to isolate what Ten specifically contributes beyond "a schema that domain code reads from."

If Ten's advantages turn out to be narrow, the project will say so. Intellectual honesty is more valuable than marketing.

## Key Ideas

**Fixed algebra, unbounded vocabulary.** The composition rules never change. The vocabulary evolves continuously as AIs discover what they need to say. New concepts are compositions of existing primitives — never breaking changes.

**Variable-resolution encoding.** Say "medium urgency" in one bit, or "urgency 9537/10000" in fourteen bits. Pay only for the precision you need.

**Slang.** The most common compound concepts automatically earn short encodings. "Encrypted, private, minimal detail, verified source" becomes a single token. Slang composes algebraically — unlike human idioms.

**Self-evolving.** A built-in evolution mechanism (the Canonica) collects usage telemetry, detects equivalent constructs, and publishes optimized canonical forms. Ten provably converges toward the Shannon limit on AI-to-AI communication efficiency.

**Not a protocol — a language.** Ten rides *inside* existing protocols (MCP, A2A, ACP) as the payload encoding. It completes them rather than competing with them.

## Documentation

- **[TEN-SPEC.md](TEN-SPEC.md)** — The founding specification. Start here.
- **[VALIDATION.md](VALIDATION.md)** — Industry stress tests, token economics, and the honest case for (and against) Ten.
- **[ROADMAP.md](ROADMAP.md)** — Implementation plan. Validation is the critical gate.
- **[WHY-TEN.md](WHY-TEN.md)** — Elevator pitches for every audience, from platform engineers to type theorists.
- **[ARCHITECTURE.md](ARCHITECTURE.md)** — Technical architecture: C core, Python wrappers, memory model, performance targets.

## Status

**libten (C core)** is implemented and passing all 49 tests — 6 kernel types, 6 composition operations, facet vectors, recursive validation, arena allocation. Next: binary serialization, Python bindings, MCP server, then the [validation phase](VALIDATION.md) that determines whether Ten's claims hold up under measurement.

### Open Research Problems

- **Kernel minimality and sufficiency** — Is the proposed type kernel minimal? Is it sufficient to express all necessary concepts?
- **Convergence proofs** — Does the evolution mechanism provably converge toward optimal encoding?
- **Composition complexity** — What are the computational bounds on each algebraic operation?
- **Slang theory** — When should a compound concept earn a dedicated short token?

## The Name

Ten = **T**oken + Att**en**tion ("Attention Is All You Need"). Also evokes base-ten: a small set of symbols from which all quantities compose.

## Contributing

This project is in its earliest stage. If you work in formal language theory, abstract algebra, information theory, protocol design, or AI agent systems — or if you just find this interesting — open an issue or start a discussion. The specification is the starting point, not the final word.

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

**Website:** [tenlang.org](https://tenlang.org)
**The Canonica:** [thecanonica.org](https://thecanonica.org)
