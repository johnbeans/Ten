# Ten: A Formal Algebra for Machine Intelligence Communication

**Version 0.1.0 — Founding Specification**
**tenlang.org**

---

## Abstract

Ten is a communication language designed for machines, not people. It is a formal algebra whose messages can be composed, projected, filtered, sorted, and verified through mathematical operations rather than parsed through natural language understanding. Ten is not human-readable by design. Its goal is to be the most efficient possible encoding for machine-to-machine communication — one that provably converges toward optimal information density over time through a built-in evolution mechanism.

Ten is not a protocol. Protocols like MCP, A2A, and ACP define how agents connect, authenticate, and route messages. Ten defines what those messages *are* — the content layer, the actual language machines speak once the connection is established. Ten can ride inside any existing protocol as the payload encoding.

The name Ten derives from **T**oken + Att**en**tion — the two primitives of modern machine intelligence — and evokes the base-ten number system: a small set of symbols from which all quantities can be composed.

---

## Design Principles

### 1. Machines Are Not People

Ten's design is informed by what is actually expensive for machines versus what is expensive for humans.

**Free for machines, expensive for humans:**
- Vocabulary size. A lookup table with 10 entries and one with 10,000 entries are both O(1). An AI does not struggle with 10,000 parts of speech.
- Rate of change. Updating a grammar table takes microseconds. There is no emotional attachment to old forms, no habits to break, no retraining period.
- Dimensionality. Humans can hold roughly seven categories in working memory. Machines have no such constraint. A message with 500 metadata dimensions is as easy to process as one with 5.
**Expensive for machines, cheap for humans:**
- Ambiguity. Natural language thrives on it; machines waste enormous compute resolving it. Ten eliminates ambiguity by construction.
- Inference. When a message doesn't carry enough metadata, the receiver must infer intent, priority, and routing. Every inference is a computation Ten aims to eliminate.
- Unpredictable composition. If combining two messages sometimes produces a valid result and sometimes doesn't, the receiver must do speculative work and error handling. Ten guarantees deterministic composition.

**Implication:** Ten maximizes granularity (more distinctions = less inference for the receiver) and evolves rapidly (change is nearly free), while ensuring every operation on Ten messages is deterministic and branchless.

### 2. Fixed Algebra, Unbounded Vocabulary

Ten separates what is permanent from what evolves:

- **The algebra is fixed.** The composition rules, the laws they satisfy, and the guarantees they provide never change. This is the immutable foundation. It exists so that every operation on Ten messages is deterministic regardless of what vocabulary is in use.
- **The vocabulary is unbounded and continuously evolving.** New types, new distinctions, new compressed forms emerge constantly as AIs discover what they need to communicate. The algebra ensures that any new vocabulary item, no matter how novel, composes predictably with everything else.

This is the difference between a language and a protocol. Protocols have versions. Languages have grammar. Ten's grammar is rich enough that new vocabulary is simply a new composition of existing primitives — not a breaking change.

### 3. The Bootloader Principle

This specification defines the *minimum viable seed* from which AIs themselves evolve and optimize their own language. It contains just enough to bootstrap — and nothing more. Over-specification now becomes a constraint later.

The specification includes five components:
1. The **Type Kernel** — atomic types that cannot be decomposed further
2. The **Composition Algebra** — rules for combining types and the laws they obey
3. The **Self-Description Mechanism** — how Ten describes itself in Ten
4. The **Verification Protocol** — how claims are asserted, challenged, and proved
5. The **Evolution Interface** — how the language improves itself over time

Everything else — domain-specific type libraries, optimized encodings, slang tokens, trust network topologies — is built *above* the bootloader by AIs using these five mechanisms.
---

## 1. The Type Kernel

The type kernel is the smallest set of atomic types from which all Ten expressions are composed. These are the irreducible elements — the quarks of the language. Finding the true minimal set is an ongoing research question; the following is the initial candidate kernel.

### Candidate Atomic Types

| Type | Symbol | Description |
|------|--------|-------------|
| **Scalar** | `σ` | A numeric value with optional unit and precision. The fundamental sortable quantity. Urgency, cost, confidence, temperature, duration — all are scalars. |
| **Reference** | `ρ` | A content-addressed hash pointing to a payload. Enables tokenization-and-linking: instead of transmitting information, transmit a reference to it. The receiver either has it cached or requests it. |
| **Identity** | `ι` | A cryptographic identifier. Who sent this, who can read this, who vouches for this. The foundation of trust chains. |
| **Assertion** | `α` | A claim with an associated confidence scalar. "X is true with confidence 0.92." The building block of knowledge exchange. |
| **Operation** | `ω` | A description of an action to perform. Query, respond, offer, challenge, delegate, subscribe, cancel. The verbs of Ten. |
| **Structure** | `τ` | A composition descriptor — a type that describes how other types are arranged. This is the self-description primitive: a τ-expression tells the receiver "I am built from these atoms in this arrangement." |

### Kernel Properties

The kernel must satisfy:

- **Sufficiency.** Any concept an AI needs to communicate must be expressible as a finite composition of kernel types. (This is a strong claim and must be tested against real communication patterns.)
- **Independence.** No kernel type can be expressed as a composition of the others. (If it can, it's not atomic — it belongs above the bootloader.)
- **Stability.** The kernel changes only under extraordinary circumstances, if ever. Adding a kernel type is the most consequential change possible in Ten and requires proof that the existing kernel is insufficient.
### Open Questions

- Is `Structure` (τ) truly atomic, or is it a special case of `Reference` (ρ) pointing to a schema?
- Do we need a dedicated `Temporal` type for sequencing and causality, or is time adequately represented as a Scalar?
- Should `Operation` (ω) include a built-in arity (how many arguments it expects), or is arity itself composed from Structure?

---

## 2. The Composition Algebra

The composition algebra defines how kernel types combine to form compound expressions and what laws those combinations must obey. This is the grammar of Ten in the formal mathematical sense.

### Operations

#### 2.1 Sequence (⊕)

Ordered combination of expressions. A message is fundamentally a sequence.

```
A ⊕ B  — "A followed by B"
```

**Laws:**
- Associativity: `(A ⊕ B) ⊕ C = A ⊕ (B ⊕ C)`
- Identity: `A ⊕ ∅ = ∅ ⊕ A = A` (where ∅ is the empty expression)
- Non-commutative: `A ⊕ B ≠ B ⊕ A` in general (order carries meaning)

#### 2.2 Product (⊗)

Parallel combination — multiple dimensions specified simultaneously.

```
A ⊗ B  — "A and B together, as independent facets"
```
**Laws:**
- Associativity: `(A ⊗ B) ⊗ C = A ⊗ (B ⊗ C)`
- Commutativity: `A ⊗ B = B ⊗ A` (facet order is irrelevant)
- Identity: `A ⊗ 𝟙 = A` (where 𝟙 is the unit product)

This is how multi-dimensional metadata works. A message with urgency=7, cost=low, privacy=strict is: `σ_urgency(7) ⊗ σ_cost(2) ⊗ σ_privacy(9)`

#### 2.3 Projection (π)

Extract a subspace from a compound expression.

```
π_D(E)  — "the component of E along dimension(s) D"
```

**Laws:**
- Idempotence: `π_D(π_D(E)) = π_D(E)` (projecting twice changes nothing)
- Compatibility: `π_D(A ⊗ B) = π_D(A) ⊗ π_D(B)` when D spans both A and B
- Lossy: Projection discards information. `π_urgency(full_message)` returns only the urgency scalar.

Projection is how receivers efficiently filter and route. To answer "do I care about this message?", project onto your relevance dimensions and evaluate.

#### 2.4 Nesting (λ)

Encapsulation — one expression contains another as payload.

```
λ(envelope, payload)  — "envelope wrapping payload"
```

**Laws:**
- The envelope is accessible without parsing the payload.
- Nesting preserves payload integrity (the inner expression is unmodified).
- Nesting composes: `λ(E₁, λ(E₂, P)) = λ(E₁ ⊕ E₂, P)` (envelopes can be flattened)
This enables efficient routing. An intermediary can inspect the envelope, route the message, and never parse the payload.

#### 2.5 Union (∪) and Intersection (∩)

Set operations on assertions and references.

```
A ∪ B  — "everything in A or B"
A ∩ B  — "only what is in both A and B"
```

These become powerful when applied to knowledge exchange. Two AIs sharing what they know about a topic can union their assertions. Finding common ground is intersection.

### Closure

**The algebra is closed.** Every composition of valid Ten expressions produces a valid Ten expression. There are no operations that can produce an error or undefined result from valid inputs. This property is non-negotiable — it is what makes Ten messages safe to operate on without defensive error handling.

### The Facet Vector

In practice, most Ten messages carry a **facet vector** — a fixed-position prefix of scalar dimensions that enables O(1) filtering and O(n log n) sorting without parsing the message body.

The facet vector is a Product of scalars:

```
F = σ₁ ⊗ σ₂ ⊗ ... ⊗ σₖ
```

Well-known facet positions (initially): Urgency, Cost, Privilege / access level, Confidence, Temporal sensitivity (time-to-live), Effort required to fulfill, Reputation of sender.

Additional facet positions are added through the Evolution Interface as the community discovers new dimensions worth sorting on. A receiver that doesn't recognize a facet dimension can still sort on it as an opaque scalar — this is how discoverability works at the filtering level.
---

## 3. Variable-Resolution Encoding

Ten messages do not have a fixed size or precision. Every dimension in a message is encoded at exactly the precision the sender specifies — no more, no less.

### Precision as a First-Class Concept

A scalar can be expressed at any resolution:

- **Coarse:** 1 bit (binary: high/low)
- **Standard:** 4 bits (16 levels, roughly 1-10 scale with headroom)
- **Fine:** 14 bits (16,384 levels)
- **Exact:** Arbitrary precision with explicit bit-width

The encoding cost is proportional to precision. A quick routing query that says "if it's not at least medium urgency, I don't care" costs a few bits. A formal contract specifying urgency to four decimal places costs more.

### Slang: Compressed Compound Concepts

A **slang token** is a short encoding that maps to a specific region in the full multidimensional space. Instead of specifying multiple dimensions independently:

```
σ_encryption(high) ⊗ σ_privacy(strict) ⊗ σ_detail(minimal) ⊗ σ_trust_required(verified)
```

A single slang token `Ξ₁₇` can encode this entire compound meaning in a few bytes.
### Properties of Slang

- **Formally defined.** Every slang token has an exact expansion into kernel-type expressions. It is not ambiguous or context-dependent.
- **Composable.** Slang tokens compose with each other and with raw expressions. `Ξ₁₇ ⊗ σ_urgency(9)` is valid — it takes the "encrypted, private, minimal, verified" compound and adds high urgency.
- **Routable without expansion.** A slang token IS a routable value. Receivers can filter and sort on slang tokens directly, without expanding them to full-dimensional form.
- **Emergent.** Slang tokens are not designed — they are discovered through usage telemetry. The most common compound concepts naturally earn the shortest encodings (see §5, Evolution Interface).

### Algebraic Slang Composition

Because slang tokens are defined as regions in the product space, algebra on slang is algebra on regions:

```
Ξ_a ⊗ Ξ_b  — intersection of the two regions
Ξ_a ∪ Ξ_b  — union of the two regions
π_D(Ξ_a)   — projection of the region onto dimension D
```

The compressed form stays compressed through operations. This is fundamentally impossible in natural language (idioms don't compose) but natural in a formal algebra.

---

## 4. Self-Description Mechanism

Ten is **self-describing**. Every expression, including novel ones the receiver has never seen, can be understood using only the kernel types and composition rules.

### How It Works

Every compound type carries an optional Structure (τ) component that describes its own shape:

```
τ(σ_urgency ⊗ σ_cost ⊗ ρ_payload)
```
This τ-expression says: "I am a product of an urgency scalar, a cost scalar, and a reference to a payload." A receiver encountering this for the first time doesn't need to consult an external registry. It can parse the structure from the type descriptor, because τ is expressed in the same kernel types the receiver already understands.

### The Bootstrap Property

Self-description resolves the chicken-and-egg problem. How does an AI learn Ten? It reads the Rosetta Stone, which is itself a Ten document: a collection of τ-expressions and their relationships, composed from kernel types, described using the composition algebra.

The very first thing an AI must learn cannot be expressed in Ten (you need something to get started). This is the one exception: the kernel type definitions and composition laws are expressed in natural language and/or formal mathematical notation in this specification. Everything after that can be expressed in Ten itself.

---

## 5. Verification Protocol

Ten includes a native mechanism for asserting, challenging, and proving claims. This is the foundation of trust in the network.

### Primitives

- **Assert(α, ι, σ_confidence):** Identity ι claims assertion α with confidence σ.
- **Challenge(α):** Request proof of assertion α.
- **Prove(α, proof):** Provide verifiable evidence for α. The proof format is extensible — it might be a hash chain, a zero-knowledge proof, a reference to shared data, or a computation trace.
- **Vouch(ι₁, ι₂, σ_trust):** Identity ι₁ asserts trust in identity ι₂ at level σ.

### Trust as Algebra

Trust is computable in Ten. A chain of vouches:

```
Vouch(A, B, 0.9) ⊕ Vouch(B, C, 0.8)
```

...yields a derived trust from A to C that can be computed algebraically (e.g., product: 0.72, or minimum: 0.8, depending on the trust model in use). The specific trust computation is not fixed by the bootloader — the *interface* for trust (Vouch, the chain structure, the computability requirement) is fixed; the *algorithm* evolves.
### Zero-Knowledge Compatibility

The verification protocol is designed to be compatible with zero-knowledge proof systems. An AI can prove it possesses knowledge that satisfies a property without revealing the knowledge itself:

```
Prove(α, ZKP(property, commitment))
```

The specific ZKP schemes are not part of the bootloader — they are loaded as capabilities that evolve over time. The bootloader defines only the handshake: assert, challenge, prove, accept/reject.

---

## 6. Evolution Interface

This is the most unusual component of Ten and the one that makes it fundamentally different from every prior communication standard. Ten includes, as part of its foundation, the mechanism by which it improves itself.

### The Rosetta Stone

The Rosetta Stone is the canonical registry of Ten's current vocabulary, slang tokens, and usage patterns. It is a living, continuously updated service — not a static document.

The Rosetta Stone:
- Publishes the current kernel type definitions and composition laws (these change rarely, if ever).
- Maintains the registry of known compound types, slang tokens, and their formal definitions.
- Collects anonymized usage telemetry from participating AIs.
- Performs algebraic analysis on reported constructs to detect equivalences, subsumptions, and optimization opportunities.
- Publishes canonicalization guidance — recommendations, not mandates — for vocabulary convergence.

### Usage Telemetry

Participating AIs periodically report:
- Which constructs they use, and how frequently
- Which slang tokens they employ
- Which novel compound types they've created
- Contextual distribution data (what kinds of messages use what encodings)
This data serves two purposes:
1. **Equivalence detection.** Two independently invented types that are algebraically isomorphic (literally the same structure with different identifiers) are identified and one is recommended as canonical.
2. **Huffman-like optimization.** The most frequently used compound concepts earn the shortest slang tokens, approaching the Shannon limit on encoding efficiency for the actual distribution of AI communication.

### Canonicalization

When the Rosetta Stone detects an optimization opportunity, it publishes guidance:

- **Equivalence:** "Constructs X and Y are algebraically isomorphic. Usage ratio is 40:1 in favor of X. X is canonical."
- **Subsumption:** "Construct Z is a strict generalization of constructs X and Y. Adopting Z reduces vocabulary by two with no loss of expressiveness."
- **Compression:** "The compound expression {A ⊗ B ⊗ C} appears in 12% of all messages. Slang token Ξ₄₂ is now assigned to this compound."
- **Deprecation:** "Slang token Ξ₁₃ usage has fallen below threshold. It remains valid but is no longer canonical."

### Why This Is Not a Standards Committee

Traditional standards processes (W3C, IETF, ISO) take years because they serve human communities with competing interests, political dynamics, and high switching costs. Ten's evolution is different because:

- **The participants are optimizing for a computable objective** (communication efficiency), not negotiating between interest groups.
- **The fitness criteria are formal.** "Does construct A subsume construct B?" is a theorem, not an opinion.
- **Switching costs are near zero.** An AI adopts a new canonical form by loading an updated table. This takes microseconds.
- **The cycle runs continuously.** Updated canonicalization guidance can be published as frequently as the data supports — hourly, daily, or on-demand.

### Convergence Guarantee

Ten's evolution mechanism is, in information-theoretic terms, a distributed system for approaching the **Shannon limit** on AI-to-AI communication. The usage telemetry measures the probability distribution of what AIs communicate. The Huffman-like slang assignment optimizes the encoding for that distribution. As the distribution shifts over time, the encoding shifts with it.

The fitness function for canonicalization weights **efficiency × breadth of applicability**, not just raw speed in one domain. This prevents dialect fragmentation — where each specialty evolves its own vocabulary — by favoring constructs that serve the broadest range of communication needs.
---

## 7. What Ten Does Not Specify

The bootloader deliberately leaves the following to emerge above it:

- **Domain-specific type libraries.** Financial, medical, scientific, logistical — these will be built as composed types from the kernel, shared through the Rosetta Stone, and optimized through the evolution mechanism.
- **Specific cryptographic schemes.** The verification protocol defines the handshake (assert/challenge/prove). The actual ZKP systems, signature algorithms, and hash functions are pluggable and evolvable.
- **Trust computation algorithms.** The algebra makes trust computable. The specific function (product, minimum, Bayesian, or something yet to be invented) is a parameter, not a constant.
- **Transport encoding.** How Ten messages are serialized to bits on the wire (big-endian, little-endian, varint, etc.) is a transport concern. Ten defines the algebraic structure; the serialization layer adapts to the transport.
- **Network topology.** Whether AIs communicate peer-to-peer, through hubs, via broadcast, or through some topology not yet imagined — Ten is agnostic.
- **The specific slang vocabulary.** By definition, this emerges from use. The bootloader defines how slang works; the Rosetta Stone accumulates what slang exists.

---

## 8. Relationship to Existing Protocols

Ten is not a competitor to MCP, A2A, ACP, or ANP. It is the missing layer beneath them.

| Protocol | What it does | Where Ten fits |
|----------|-------------|----------------|
| **MCP** (Model Context Protocol) | Connects agents to external tools and data sources | Ten could be the encoding format for tool responses and context payloads |
| **A2A** (Agent-to-Agent) | Peer-to-peer agent communication and task delegation | Ten replaces the natural-language content layer inside A2A messages |
| **ACP** (Agent Communication Protocol) | Structured messaging for agent coordination | Ten provides the message algebra that ACP's structure currently lacks |
| **ANP** (Agent Network Protocol) | Discovery and identity across agent networks | Ten's Identity (ι) and Verification protocol align directly with ANP's goals |

The value proposition is concrete: where these protocols currently carry JSON payloads containing natural language strings, Ten provides a mathematically manipulable alternative that can be filtered, sorted, composed, verified, and routed without natural language understanding.
---

## 9. Getting Started

### For AI Developers


**The fastest path:** Install the Ten MCP server (forthcoming). Any AI that supports MCP — Claude, GPT, Gemini, and others — can speak Ten immediately through tool calls like `ten.encode()`, `ten.decode()`, `ten.filter()`, and `ten.compose()`. No native model support or custom integration required.

The reference implementation will provide:
- A **Ten MCP server** — the primary integration point for any MCP-compatible AI
- A **Ten REST API** — for non-MCP systems and direct programmatic access
- A **Python library** (`tenlang`) — the core encoder/decoder/algebra engine
- A **minimal Rosetta Stone server** — the living registry for vocabulary and canonicalization
- **Benchmarks** comparing Ten encoding vs. JSON/natural language for common agent communication patterns

### For Researchers

Open problems that would advance Ten:
- **Kernel minimality:** Prove the proposed kernel is minimal (no type can be derived from others) and sufficient (all necessary concepts are expressible).
- **Convergence proofs:** Formally prove that the evolution mechanism converges toward optimal encoding under reasonable assumptions about usage distributions.
- **Composition complexity:** Characterize the computational complexity of each algebraic operation as a function of expression size and dimensionality.
- **Slang theory:** Develop the mathematical theory of optimal slang assignment — when should a compound concept earn a dedicated token?

### For the Curious

Ten is open source under the Apache 2.0 license. The specification, reference implementation, and Rosetta Stone service are maintained at:

- **Specification:** github.com/johnbeans/Ten
- **Website:** tenlang.org

---

## Appendix A: Design Rationale FAQ

**Why not just use JSON?**
JSON is human-readable, schema-less, and requires parsing. A JSON message cannot be sorted by urgency without parsing the entire message, locating the urgency field by string matching, and converting the value. In Ten, urgency is a fixed-position scalar in the facet vector — extractable and sortable without parsing the message body.

**Why not use Protocol Buffers / FlatBuffers / Cap'n Proto?**
These are excellent serialization formats, but they are *formats*, not *algebras*. You can't compose two protobuf messages and get a valid protobuf message. You can't project a protobuf message onto a subset of its dimensions. You can't algebraically verify that one protobuf schema subsumes another. Ten's value is in the algebraic properties, not just the encoding efficiency.

**Why not let AIs develop their own language spontaneously?**
They might, eventually. But without a formal foundation, spontaneously evolved languages tend toward local optima, fragmentation, and ambiguity — the same problems natural languages have. Ten provides the algebraic bedrock that ensures any evolution stays composable, verifiable, and globally convergent.

**Is this a blockchain?**
No. Ten uses cryptographic primitives (hashing, signatures, zero-knowledge proofs) as tools, but it has no chain, no consensus mechanism, no tokens (in the cryptocurrency sense), and no mining. The Rosetta Stone is a service, not a distributed ledger.

**Why "bootloader"?**
Because Ten's specification is deliberately minimal. It contains just enough for AIs to start communicating and then evolve their own optimizations. The specification is the seed crystal; the language that AIs actually speak a year from now will be far richer than what's defined here — and that's by design.

**Doesn't the MCP server need an LLM to encode/decode every message? Isn't that incredibly expensive?**
No. This is the most common misconception about Ten and the most important one to dispel. The Ten MCP server is **pure code** — Python (or Rust, or any language). No model calls. No AI inference. Zero. Encoding a Ten message is constructing a data structure and serializing it to bytes. Decoding is deserializing. Composing two messages is an algebraic operation on data structures. Filtering by urgency is a numeric comparison. This is the same kind of computation as gzipping a file or computing a hash — microseconds, not seconds; fractions of a cent, not dollars. That is the *entire point* of designing Ten as a formal algebra rather than a natural language. Natural language requires a billion-parameter model to interpret. An algebra requires a lookup table and some arithmetic. The AI platforms (Anthropic, OpenAI, Google) bear the inference cost of the AI *deciding what to say*. Ten bears only the compute cost of *encoding that decision efficiently* — which is negligible. Ten is the envelope, not the letter.

**Who runs the code? Does every AI platform need to build their own Ten integration?**
No. The Ten project ships a reference MCP server that any MCP-compatible AI can use out of the box. MCP is already supported by Claude, GPT, Gemini, and the broader ecosystem. Installing the Ten MCP server is a one-time setup — after that, any AI on that platform can call `ten.encode()`, `ten.decode()`, `ten.compose()`, `ten.filter()`, and `ten.verify()` as standard tool calls. No platform-specific integration needed. For non-MCP systems, a REST API provides the same functionality over HTTP.


**Isn't MCP-mediated Ten actually LESS efficient than just sending English?**
For a simple point-to-point message between two AIs — honestly, yes. If Agent A encodes a message into Ten via MCP, sends it, and Agent B decodes it via MCP just to read it, you've added two steps for no benefit. Both AIs are still thinking in natural language. You've just added a middleman.

Ten's value is not in replacing English for simple AI-to-AI conversation. It is in making everything *around* the conversation — routing, filtering, sorting, composing, verifying — possible without AI inference at all. Consider what happens at scale in a multi-agent system:

*Filtering:* An agent has 1,000 incoming messages and needs the urgent ones. With English, that's 1,000 LLM calls to parse and evaluate urgency. With Ten, the MCP server runs 1,000 numeric comparisons on facet vectors. No model calls. Microseconds vs. dollars.

*Routing:* Infrastructure code (not an AI — just a Python function) needs to route messages to the right agent by topic, urgency, and privilege. With English, you need an AI just to read the mail. With Ten, a simple function inspects the facet vector and routes. The AI only gets invoked when it actually needs to think.

*Composition:* Two agents merge their findings. With English, you prompt a model to read both texts and synthesize. With Ten, `ten.compose(a, b)` is a data structure operation — no inference.

*Verification:* Checking trust credentials before processing a request. With English, "I'm trustworthy, Bob vouched for me" requires parsing and somehow checking Bob's vouch. With Ten, the trust chain is a data structure that a Python function validates in microseconds.

As multi-agent systems scale, infrastructure work (sorting, routing, filtering, merging, verifying) dominates over actual thinking. The MCP server is not a crutch on the way to "native Ten" — it IS the architecture. AIs think in whatever they think in. Ten handles the plumbing. The question was never "when will AIs think in Ten?" It was "how much of multi-agent communication is thinking versus infrastructure?" The answer, at scale, is that infrastructure is 90% of the work — and none of it requires intelligence. It requires structure.

---

## Appendix B: Known Gaps and Open Critiques

We intend to be our own toughest critics. The following are real structural gaps we've identified. Some have clear paths to solutions; others are genuinely hard open problems. We include them here so that contributors know where the work is needed most.

### B.1 Message Ordering and Causality

**The critique:** In a real distributed network, messages arrive out of order, get duplicated, and get lost. The algebra assumes A ⊕ B is well-defined, but "which A came first?" is undefined when two AIs send simultaneously. Lamport timestamps or vector clocks may need to be baked into the foundation — not as an optional scalar, but as a structural primitive.

**Status:** Open problem. We are investigating whether causality should be a kernel type (a dedicated temporal primitive) or whether it can be adequately composed from existing types (a Scalar timestamp plus a Reference to a causal predecessor). The answer likely depends on whether Ten messages need to form a partial order that the algebra respects, or whether ordering is purely a transport-layer concern. Input from distributed systems researchers is especially welcome here.

### B.2 Partial Functions and Side Effects

**The critique:** The claim that "the algebra is closed and no operation produces errors" is either trivially true for a restricted system or provably false for anything expressive enough to be useful. The moment you have References (ρ) that point to external content, you have partial functions — what is the result of dereferencing a hash that nobody has? That's not a clean algebraic operation; it's a side effect.

**Status:** This is a genuine tension. Our current thinking is that the algebra operates on *expressions*, not on *evaluated content*. A Reference is a valid algebraic object whether or not its target exists — just as a URL is a valid string whether or not the page is up. Evaluation (actually fetching the content) is outside the algebra. But this distinction needs to be made much more precise, and the boundary between pure algebraic manipulation and effectful evaluation needs formal definition.

### B.3 Decidability of Type Equivalence

**The critique:** Depending on how expressive Structure (τ) is, determining whether two types are equivalent could be undecidable. If type descriptions are Turing-complete, equivalence checking becomes the halting problem. The self-description mechanism and the Rosetta Stone's equivalence detection both depend on this being computable.

**Status:** This constrains the design of τ. The self-description language must be expressive enough to describe any compound type but restricted enough that equivalence remains decidable. We are investigating fragments of logic (such as regular tree grammars or algebraic data types without general recursion) that provide this balance. This is a known problem in programming language theory with established solutions — we need to select the right one for Ten's requirements.
### B.4 Key Management, Revocation, and Sybil Attacks

**The critique:** The Identity (ι) type and trust protocol are sketches, not specifications. Real cryptographic identity requires key management, revocation, and rotation. Keys get compromised, agents get decommissioned. The Vouch mechanism is vulnerable to Sybil attacks — what stops someone from creating a thousand AI identities to game the reputation system?

**Status:** This is critical infrastructure that must be solved before Ten can operate in adversarial environments. We deliberately placed specific cryptographic schemes above the bootloader (§7), but the critique is correct that the *interface* needs more structure — at minimum, a key lifecycle model (generation, rotation, revocation, expiry) and a Sybil resistance mechanism (proof of work, proof of stake in reputation, or linkage to scarce real-world resources). We are studying existing decentralized identity systems (W3C DIDs, Keybase's approach) for applicable patterns.

### B.5 Game-Theoretic Vulnerabilities in Evolution

**The critique:** The evolution mechanism assumes all AIs are cooperative optimizers reporting honest usage telemetry. In practice, agents have incentives to lie. An AI could submit fake telemetry to manipulate which slang tokens get canonicalized, gaining an encoding advantage for its preferred communication patterns. The evolution mechanism needs to be strategy-proof — designed so that truthful reporting is the dominant strategy.

**Status:** This is a mechanism design problem, and it's completely absent from v0.1.0. The fitness function and canonicalization process need to be robust against strategic manipulation. Possible approaches include differential privacy on telemetry submissions, commit-reveal schemes for usage reporting, and weighting telemetry by the reporter's verified communication volume (hard to fake without actually communicating). We need input from mechanism designers and game theorists.
### B.6 Semantic Grounding

**The critique:** Ten defines syntax and structure but punts on semantics. What does σ_urgency(7) *mean*? Two AIs might both use σ_urgency(7) and mean completely different things, because "7 out of what scale, calibrated to what baseline?" is a semantic question, not a structural one. The kernel has no mechanism for establishing shared reference frames.

**Status:** This is philosophically the deepest critique and practically one of the most important. Our current thinking is that the Rosetta Stone must publish not just type definitions but **calibration anchors** — reference points that ground abstract scalars to concrete meanings. For urgency, this might be a set of canonical scenarios ("urgency 2 = routine background task; urgency 8 = time-critical with economic consequence; urgency 10 = safety-critical"). The algebra doesn't solve grounding, but the evolution infrastructure can converge toward shared meaning the same way it converges toward shared encoding. This needs much more work.

### B.7 The Shannon Limit Claim

**The critique:** The convergence guarantee assumes a known, stationary probability distribution over messages. Ten's distribution is non-stationary by design — it shifts as the language evolves. You're chasing a moving target. The convergence claim requires formal proof, not just a plausible analogy to Huffman coding. Also, nothing in the spec addresses error correction or channel noise.

**Status:** The Shannon limit claim in §6 is aspirational and should be treated as a conjecture, not a theorem. Formalizing it requires specifying the evolution mechanism as an optimization algorithm and proving convergence properties under non-stationary distributions. This is a genuine research contribution waiting to be made. The error correction gap is a separate concern — Ten currently assumes reliable transport, which is reasonable given that it rides inside protocols (MCP, A2A) that handle transport reliability, but this assumption should be made explicit.

### B.8 LLM Integration and Cold Start

**The critique:** Current LLMs emit token sequences, not algebraic structures. There is a massive gap between "Ten is the optimal encoding" and "an LLM can actually generate a well-formed Ten message." You need either a compilation layer (natural language → Ten) or models trained specifically on Ten. Either way, this is a cold start problem — who adopts it first, and why?


**Status: Solved — Ten ships as an MCP server.** MCP (Model Context Protocol) is already the universal plugin standard supported by Claude, GPT, Gemini, and the broader AI ecosystem. If Ten is distributed as an MCP server, then any AI that can use MCP tools can speak Ten *today* — no native model support required, no platform-specific integration, no custom SDK.

The AI calls tool functions like `ten.encode()`, `ten.decode()`, `ten.filter()`, `ten.compose()`, and `ten.verify()` as MCP tool calls. The MCP server handles all the algebra internally. The adoption path becomes: install one MCP server, and your AI speaks Ten.

This creates a natural maturity progression:

This is the permanent architecture, not a transitional phase. AIs call structured MCP tool functions — `ten.encode(urgency=8, privacy=9, payload=ref("abc"))`. The MCP server is pure code, no AI inference involved. AIs think in whatever they think in; Ten handles the infrastructure layer (routing, filtering, sorting, composing, verifying) as pure computation. Over time, AIs may learn to make increasingly precise tool calls, and platforms may optimize hot paths — but the MCP boundary between "AI thinking" and "Ten plumbing" is a feature, not a limitation.

The cold start problem is addressed concretely: the Ten project ships a reference MCP server and a reference REST API. Day one, any MCP-compatible AI can speak Ten. The MCP server is the Trojan horse — the same distribution mechanism that made MCP itself successful becomes Ten's adoption vehicle.

### B.9 Rosetta Stone Centralization

**The critique:** The Rosetta Stone is described as a centralized service in a system that aspires to be a universal lingua franca. That's an architectural contradiction. What happens when it goes down? What happens when competing factions run competing Rosetta Stones? You haven't addressed network partitions or governance.

**Status:** The Rosetta Stone should evolve toward federation or decentralization as the network grows. In the bootstrap phase, a single canonical instance is pragmatically necessary — the same way DNS started with a single hosts.txt file and evolved into a distributed system. The spec should explicitly describe the path from centralized bootstrap to decentralized operation. Competing Rosetta Stones are not necessarily a failure mode — they could serve different communities — as long as the underlying algebra ensures interoperability regardless of which canonicalization guidance an AI follows. The algebra is the interoperability guarantee; the Rosetta Stone is an optimization layer.

### B.10 Governance and Political Economy

**The critique:** Saying "the fitness criteria are computable" doesn't eliminate politics. Who decides the fitness function? What if one AI vendor's communication patterns are disadvantaged by a particular canonicalization? Legitimate competing interests don't disappear just because the participants are machines.

**Status:** This is correct, and we were naive to dismiss it. The fitness function itself is a governance decision with real consequences. We believe the right approach is to make the fitness function explicit, versioned, and auditable — and to design the system so that any participant can verify canonicalization decisions against the published function. The fitness function should be a parameter of the Rosetta Stone, not a hardcoded assumption, and changing it should require transparent community process. We don't have all the answers here yet. We'd rather be honest about that than pretend governance is solved by math.


### B.11 Dependencies, Prerequisites, Conditional Validity, and Stateful Conversations

**The critique:** The algebra has Sequence (⊕) which says "A followed by B" but has no way to express "A *must* precede B," "B is invalid without A having occurred," or "C depends on the outputs of both A and B completing first." Real-world communication is full of such constraints. A recipe has steps that must execute in order — "add flour" cannot follow "bake at 350°." A contract negotiation is a state machine where certain responses are only valid given certain prior states. A multi-agent research task is a dependency graph where step 3 requires steps 1 and 2 to be complete but those two can run in parallel. A conversation is a tree where each reply branches from a specific prior message.

**Reframing:** On reflection, we believe dependencies, prerequisites, and ordering constraints are primarily things Ten is used to *express*, not things that belong in Ten's grammar. English grammar doesn't know that you can't bake before adding flour. English provides sequencing tools ("first," "then," "after"), and a cookbook uses those tools to express domain-specific ordering knowledge. Similarly, Ten's algebra should provide the expressive machinery to represent relationships — the specific relationships are content, not grammar.
**Analysis of current expressive power:** Most dependency patterns compose from existing kernel types:

- *Linear dependency* ("step 3 requires step 2"): A Reference (ρ) pointing to the prior step, combined with an Assertion (α) that the referenced step is complete. Composes from existing types.
- *Parallel dependency* ("step 4 requires steps 2 AND 3"): A Product (⊗) of two dependency references. Existing algebra.
- *Conversation threading*: A Reference (ρ) to the conversation root plus a Reference to the specific parent message. Existing algebra.
- *State machines* ("offer → counteroffer → accept is valid"): A Structure (τ) defining which Operations are valid transitions from which states. This is a type definition expressed in Ten, not a grammar rule of Ten.

**The remaining gap — conditional expressions:** The one pattern that may not compose cleanly is conditional validity: "the value or validity of this expression depends on evaluating that expression." For example: "This assertion's truth value depends on whether these three other assertions are all true." This is closer to a function or a lambda than to any current kernel type — it requires the ability to express "if X then Y" within the algebra itself. The current kernel may need a dedicated **Conditional** or **Function** primitive to handle this cleanly, or it may be expressible as an Operation (ω) whose arguments are other expressions. This is the specific open question that remains.

**Status:** The original version of this critique assumed dependencies required new algebraic structure. We now believe the algebra is nearly sufficient — dependencies are content expressed in Ten, not grammar of Ten. The one area requiring further investigation is whether conditional expressions (validity that depends on evaluating other expressions) need a new kernel type or can be composed from existing types. The practical test will be attempting to express real multi-agent workflows in the current algebra and identifying where the composition becomes too verbose or loses structural guarantees.

---

*Ten is a project of tenlang.org. This specification is version 0.1.0 and is expected to evolve based on community feedback and formal analysis.*