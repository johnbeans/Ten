# Why Ten?

Ten is a formal algebra for machine-to-machine communication. It's not a protocol — it's the language that rides *inside* protocols like MCP, A2A, and ACP as the payload encoding.

This document explains why Ten matters to different audiences.

---

## For Multi-Agent Framework Builders
*LangChain, CrewAI, AutoGen, OpenClaw, and anyone building agent orchestration*

Your agents pass JSON blobs and natural language strings around, then spend expensive LLM inference just to figure out what to do with them. Route this message? Parse it. Check its priority? Parse it. Merge results from two agents? Call a model. Verify trust? Prompt engineering.

Ten gives every message a sortable, filterable, composable algebraic structure. Route by urgency without parsing. Merge results without an LLM call. Verify trust without a prompt. Install the Ten MCP server and your orchestration layer gets a type system.

**What you'd build:** Drop `ten-mcp-server` into your framework. Your routing layer filters messages by facet vector instead of prompting a model. Your composition layer merges agent outputs algebraically instead of calling a summarizer. Your agents stop paying inference costs for infrastructure work.

---

## For Platform Engineers at AI Companies
*Anthropic, OpenAI, Google, Cohere, and anyone running multi-agent infrastructure at scale*
Your agents spend 90% of their communication budget on infrastructure — routing, filtering, sorting, verifying — not thinking. Every inter-agent message currently requires inference to parse, route, and prioritize, and you're paying per token for all of it.

Ten moves the entire infrastructure layer to pure computation. No model calls. Microseconds instead of seconds. Fractions of a cent instead of dollars. The Ten MCP server is pure Python — encoding is constructing a data structure, decoding is deserializing bytes, filtering is numeric comparison. Same compute class as gzip or hashing.

**The cost argument:** Two agents exchanging a message in English requires inference on both ends just to pack and unpack the envelope. With Ten, the AI only gets invoked when it actually needs to *think*. Everything else is arithmetic.

**What you'd evaluate:** Run the Ten benchmarks against your current agent-to-agent message flow. Measure: messages filtered per second, composition latency, total inference calls eliminated.

---

## For Protocol and Standards People
*IETF contributors, MCP developers, A2A working group, anyone building the agent interoperability stack*

MCP, A2A, ACP, and ANP solved the connection layer. Nobody solved the content layer.
Your protocols carry JSON payloads containing natural language strings. Those strings can't be composed, projected, sorted, or verified algebraically. Two A2A messages can't be merged into a valid third message. An MCP tool response can't be filtered by urgency without parsing the entire payload. There's no way to algebraically verify that one message schema subsumes another.

Ten is the missing content algebra. It rides inside your protocols as the payload encoding. It completes your stack rather than competing with it.

| Protocol | What it solves | What Ten adds |
|----------|---------------|---------------|
| **MCP** | Connects agents to tools | Algebraically structured tool responses |
| **A2A** | Peer-to-peer agent communication | Composable, sortable, verifiable message payloads |
| **ACP** | Structured agent coordination | A formal message algebra with provable properties |
| **ANP** | Discovery and identity | Native cryptographic identity and trust computation |

**What you'd review:** [TEN-SPEC.md](TEN-SPEC.md) — the founding specification. We've documented every known gap in Appendix B because we'd rather you critique our open questions than discover unstated assumptions.

---
## For AI Safety and Alignment Researchers
*Anyone working on transparency, auditability, and controllability of AI systems*

When your agents talk to each other in natural language, the conversation is opaque. Auditing it requires another AI — which introduces its own failure modes. You can't deterministically verify that Agent A told Agent B the truth. You can't mechanically check that a trust chain is valid. You can't filter a million inter-agent messages for policy violations without a million inference calls.

Ten makes every inter-agent message algebraically structured and machine-verifiable. Trust is a computable property of the message itself — a chain of cryptographic vouches that a Python function validates in microseconds. Assertions carry explicit confidence levels. The entire message flow can be inspected, filtered, and validated by pure code. No model in the audit loop.

**The safety argument:** Deterministic auditability beats probabilistic auditability. Ten makes the infrastructure layer of multi-agent systems inspectable without AI, which means your audit tools can be formally verified in ways that LLM-based auditors cannot.

**What you'd investigate:** The verification protocol (§5 of the spec) and the trust algebra. Can the trust computation model be made compatible with your existing safety frameworks?

---

## For Formal Language and Type Theory Researchers
*PL theorists, algebraists, information theorists, anyone who works in Coq, Lean, or Agda*
Here is an open algebra design problem with immediate practical application:

Define a type kernel and composition algebra for machine-to-machine communication that is closed under all operations, self-describing (novel types are parseable from their structure alone), and supports decidable equivalence checking — with a built-in evolution mechanism that provably converges toward Shannon-optimal encoding under non-stationary usage distributions.

Open problems, all publishable:
- **Kernel minimality proof.** Is the proposed 6-type kernel minimal? Can any type be derived from the others?
- **Kernel sufficiency proof.** Can every necessary communication concept be expressed as a finite composition of kernel types?
- **Convergence proof.** Does the telemetry-driven evolution mechanism provably converge toward optimal encoding?
- **Decidability bounds.** What fragment of logic keeps the self-description type (τ) expressive enough while maintaining decidable equivalence?
- **Optimal slang theory.** When should a compound concept earn a dedicated short token? What's the information-theoretic framework?
- **Strategy-proof mechanism design.** Can the usage telemetry system be made robust against strategic manipulation?

**What you'd read:** [TEN-SPEC.md](TEN-SPEC.md), especially §1 (Type Kernel), §2 (Composition Algebra), and Appendix B (Known Gaps). We know exactly where the formal holes are and we've written them down.

---
## For Enterprise CTOs Evaluating Multi-Agent Deployment
*Decision-makers scaling AI agent systems in production*

Multi-agent systems burn LLM tokens just to read their own mail. Every message between agents currently requires inference to parse, route, and prioritize — and you're paying per token for all of it. As you scale from 3 agents to 30 to 300, inter-agent communication costs grow quadratically while the actual thinking stays linear.

Ten moves the infrastructure layer — routing, filtering, sorting, composing, verifying — to pure computation. Same information, structured so it can be processed without AI calls. Vendor-neutral. Open source. Apache 2.0. Rides inside the protocols you're already using (MCP, A2A). No lock-in, no new infrastructure — one MCP server install.

**The business case:** Measure what percentage of your current LLM token spend goes to agents reading, routing, and organizing each other's messages versus actually doing useful work. Ten eliminates the former.

---

## For Developer Communities and AI Commentators
*People who amplify ideas that matter*

What if AIs had their own language — not English with extra steps, but a genuine formal algebra designed for how machines actually process information?
Ten is a language you can do math on. Messages have sortable urgency, composable trust chains, and algebraic structure that lets you merge two messages into a valid third one. It has 10,000 levels of urgency if you need them — because machines don't care about complexity the way humans do. It has "slang" — compressed shorthand for common compound concepts that emerges automatically from usage patterns, like a language that evolves its own abbreviations in real time.

Most radically: Ten includes its own evolution mechanism. A living registry (the Canonica) collects how AIs actually use the language, detects when two independently invented concepts are mathematically equivalent, and publishes optimized canonical forms. The language continuously compresses itself toward maximum information density — provably approaching the theoretical limit on communication efficiency.

It's like if Esperanto were designed by Claude Shannon and spoken exclusively by machines.

**The hook:** Two agents negotiating a task — side by side, one in English, one in Ten. Same outcome. Watch the message sizes. Watch the latency. Watch the inference costs disappear from the infrastructure layer.

---

## The One-Liner

**Ten is a formal algebra that lets AI agents route, filter, sort, compose, and verify each other's messages using pure computation — no AI inference required — while the language continuously optimizes itself based on real usage.**

---

## Get Involved

- **Specification:** [TEN-SPEC.md](TEN-SPEC.md)
- **Roadmap:** [ROADMAP.md](ROADMAP.md)
- **Repository:** [github.com/johnbeans/Ten](https://github.com/johnbeans/Ten)
- **Website:** [tenlang.org](https://tenlang.org)
- **The Canonica:** [thecanonica.org](https://thecanonica.org)
- **License:** Apache 2.0

Ten is in its founding stage. We're looking for collaborators across formal language theory, distributed systems, information theory, mechanism design, AI safety, and multi-agent infrastructure. Open an issue, start a discussion, or just star the repo.
