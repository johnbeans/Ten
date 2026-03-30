# ten-mcp-server

<!-- mcp-name: io.github.johnbeans/ten -->

MCP server exposing the **Ten** formal algebra for machine intelligence communication.

Ten treats messages as math, not natural language. This server gives LLMs structured access to Ten's algebraic operations via the [Model Context Protocol](https://modelcontextprotocol.io/).

## Tools

| Tool | Description |
|------|-------------|
| `ten_encode` | Build a Ten expression from a structured dict and return its binary wire format |
| `ten_decode` | Deserialize wire bytes back into a structured expression |
| `ten_compose` | Algebraically combine two expressions (sequence, product, nest, union, intersect) |
| `ten_project` | Extract a subset of facet dimensions from an expression |
| `ten_filter` | Evaluate expressions against facet-based filter criteria |
| `ten_describe` | Return a human-readable structural description of an expression |
| `ten_verify` | Validate expression tree integrity and check assertion metadata |

All operations are **pure code** — no AI inference, no LLM calls. Encoding is building a data structure. Decoding is deserializing bytes. Filtering is numeric comparison.

## Installation

### One-click (MCP clients)

```bash
mcp install ten-mcp-server
```

### From PyPI

```bash
pip install ten-mcp-server
```

### From source

```bash
git clone https://github.com/johnbeans/Ten.git
cd Ten
pip install ./tenlang           # install Python bindings first
pip install ./ten_mcp_server    # install MCP server
```

## Usage

### As an MCP server (stdio transport)

```bash
ten-mcp-server
# or
python -m ten_mcp_server
```

### Claude Desktop configuration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ten": {
      "command": "ten-mcp-server"
    }
  }
}
```

## Expression Format

Expressions are JSON-friendly dicts with a `type` field:

```python
# Scalar: a numeric value with dimension and precision
{"type": "scalar", "dimension": 0, "value": 42.0, "precision": "64bit"}

# Operation: a verb with optional arguments
{"type": "operation", "verb": "query", "args": [
    {"type": "scalar", "dimension": 1, "value": 100.0}
]}

# Assertion: a claim with confidence and identity
{"type": "assertion", "claim": {"type": "scalar", "dimension": 0, "value": 1.0},
 "who": {"type": "identity", "pubkey": "AAAA..."},
 "confidence": 0.95}

# Compositions: combine expressions algebraically
{"type": "sequence", "left": {...}, "right": {...}}
{"type": "nesting", "envelope": {...}, "payload": {...}}
```

## Facets

Expressions can carry facet vectors — fixed-position sortable metadata:

```
urgency, cost, privilege, confidence, ttl, effort, reputation, value
```

Use `ten_filter` to evaluate expressions against facet criteria (e.g., "urgency >= 0.8 AND cost <= 50.0").

## Dependencies

- [tenlang](https://github.com/johnbeans/Ten) — Python bindings for the Ten algebra (wraps libten C core)
- [mcp](https://pypi.org/project/mcp/) — Model Context Protocol SDK

## License

Apache-2.0 — John Beans
