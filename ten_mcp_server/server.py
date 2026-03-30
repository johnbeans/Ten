"""
ten-mcp-server — MCP server exposing the Ten formal algebra.

This server provides tools for encoding, decoding, composing, projecting,
filtering, describing, and verifying Ten expressions. It is pure code —
no AI inference, no LLM calls. Encoding is building a data structure.
Decoding is deserializing bytes. Filtering is numeric comparison.

Usage:
    python -m ten_mcp_server           # stdio transport (for MCP clients)
    mcp install ten-mcp-server         # register with MCP registry
"""

import base64
import json

from mcp.server.fastmcp import FastMCP

from tenlang import (
    Arena, Expr, TenError, encode, decode,
    TEN_FACET_URGENCY, TEN_FACET_COST, TEN_FACET_PRIVILEGE,
    TEN_FACET_CONFIDENCE, TEN_FACET_TTL, TEN_FACET_EFFORT,
    TEN_FACET_REPUTATION, TEN_FACET_VALUE,
    TEN_OP_QUERY, TEN_OP_RESPOND, TEN_OP_OFFER, TEN_OP_ACCEPT,
    TEN_OP_DECLINE, TEN_OP_CHALLENGE, TEN_OP_PROVE, TEN_OP_DELEGATE,
    TEN_OP_SUBSCRIBE, TEN_OP_CANCEL, TEN_OP_VOUCH, TEN_OP_ASSESS,
    TEN_OP_BID, TEN_OP_COUNTER, TEN_OP_INVOKE,
    TEN_PREC_1BIT, TEN_PREC_4BIT, TEN_PREC_8BIT,
    TEN_PREC_16BIT, TEN_PREC_32BIT, TEN_PREC_64BIT,
    TEN_TYPE_SCALAR, TEN_TYPE_REFERENCE, TEN_TYPE_IDENTITY,
    TEN_TYPE_ASSERTION, TEN_TYPE_OPERATION, TEN_TYPE_STRUCTURE,
    TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT, TEN_TYPE_NESTING,
    TEN_TYPE_UNION, TEN_TYPE_INTERSECT,
    TEN_HASH_SIZE,
    TEN_CMP_GTE, TEN_CMP_LTE, TEN_CMP_EQ, TEN_CMP_NEQ,
)

mcp = FastMCP(
    "ten",
    instructions="Ten: a formal algebra for machine intelligence communication. "
                 "Encode, decode, compose, filter, and verify structured messages "
                 "without LLM inference. All operations are pure code — no AI "
                 "inference needed.",
)

# ── Lookup tables ───────────────────────────────────────────

VERB_MAP = {
    "query": TEN_OP_QUERY, "respond": TEN_OP_RESPOND,
    "offer": TEN_OP_OFFER, "accept": TEN_OP_ACCEPT,
    "decline": TEN_OP_DECLINE, "challenge": TEN_OP_CHALLENGE,
    "prove": TEN_OP_PROVE, "delegate": TEN_OP_DELEGATE,
    "subscribe": TEN_OP_SUBSCRIBE, "cancel": TEN_OP_CANCEL,
    "vouch": TEN_OP_VOUCH, "assess": TEN_OP_ASSESS,
    "bid": TEN_OP_BID, "counter": TEN_OP_COUNTER,
    "invoke": TEN_OP_INVOKE,
}

FACET_MAP = {
    "urgency": TEN_FACET_URGENCY, "cost": TEN_FACET_COST,
    "privilege": TEN_FACET_PRIVILEGE, "confidence": TEN_FACET_CONFIDENCE,
    "ttl": TEN_FACET_TTL, "effort": TEN_FACET_EFFORT,
    "reputation": TEN_FACET_REPUTATION, "value": TEN_FACET_VALUE,
}

PRECISION_MAP = {
    "1": TEN_PREC_1BIT, "4": TEN_PREC_4BIT, "8": TEN_PREC_8BIT,
    "16": TEN_PREC_16BIT, "32": TEN_PREC_32BIT, "64": TEN_PREC_64BIT,
}

CMP_MAP = {
    "gte": TEN_CMP_GTE, ">=": TEN_CMP_GTE,
    "lte": TEN_CMP_LTE, "<=": TEN_CMP_LTE,
    "eq": TEN_CMP_EQ, "==": TEN_CMP_EQ,
    "neq": TEN_CMP_NEQ, "!=": TEN_CMP_NEQ,
}

COMPOSE_MAP = {
    "sequence": "sequence", "product": "product",
    "nest": "nest", "nesting": "nest",
    "union": "union", "intersect": "intersect",
}


def _resolve_facet(name) -> int:
    """Resolve a facet name or numeric ID."""
    if isinstance(name, int):
        return name
    if isinstance(name, str):
        lower = name.lower()
        if lower in FACET_MAP:
            return FACET_MAP[lower]
        try:
            return int(name)
        except ValueError:
            pass
    raise ValueError(f"Unknown facet dimension: {name}. "
                     f"Valid names: {', '.join(FACET_MAP.keys())}")


def _resolve_verb(name) -> int:
    """Resolve a verb name or numeric ID."""
    if isinstance(name, int):
        return name
    if isinstance(name, str):
        lower = name.lower()
        if lower in VERB_MAP:
            return VERB_MAP[lower]
        try:
            return int(name)
        except ValueError:
            pass
    raise ValueError(f"Unknown verb: {name}. "
                     f"Valid verbs: {', '.join(VERB_MAP.keys())}")


def _resolve_precision(p) -> int:
    """Resolve a precision value."""
    if isinstance(p, int):
        return p
    s = str(p)
    if s in PRECISION_MAP:
        return PRECISION_MAP[s]
    raise ValueError(f"Unknown precision: {p}. Valid: 1, 4, 8, 16, 32, 64")


def _build_expr(arena: Arena, spec: dict) -> Expr:
    """
    Recursively build a Ten expression from a JSON-friendly dict spec.

    Supported formats:
      {"scalar": {"dimension": "urgency", "value": 0.95, "precision": 16}}
      {"reference": {"hash": "<hex or base64>"}}
      {"identity": {"pubkey": "<hex or base64>"}}
      {"assertion": {"claim": <expr>, "who": <expr>, "confidence": 0.87}}
      {"operation": {"verb": "query", "args": [<expr>, ...]}}
      {"structure": {"members": [<expr>, ...]}}
      {"sequence": {"left": <expr>, "right": <expr>}}
      {"product": {"left": <expr>, "right": <expr>}}
      {"nest": {"envelope": <expr>, "payload": <expr>}}
      {"union": {"left": <expr>, "right": <expr>}}
      {"intersect": {"left": <expr>, "right": <expr>}}
    """
    if not isinstance(spec, dict) or len(spec) != 1:
        raise ValueError(
            "Expression spec must be a dict with exactly one key "
            "(scalar, reference, identity, assertion, operation, "
            "structure, sequence, product, nest, union, intersect)")

    type_name = list(spec.keys())[0].lower()
    data = spec[type_name]

    if type_name == "scalar":
        dim = _resolve_facet(data.get("dimension", 0))
        val = float(data.get("value", 0.0))
        prec = _resolve_precision(data.get("precision", 64))
        return arena.scalar(dim, val, prec)

    elif type_name == "reference":
        h = _decode_bytes(data.get("hash", ""), TEN_HASH_SIZE)
        return arena.ref(h)

    elif type_name == "identity":
        key = _decode_bytes(data.get("pubkey", ""), None)
        return arena.identity(key)

    elif type_name == "assertion":
        claim = _build_expr(arena, data["claim"])
        who = _build_expr(arena, data["who"])
        conf = float(data.get("confidence", 1.0))
        return arena.assertion(claim, who, conf)

    elif type_name == "operation":
        verb = _resolve_verb(data["verb"])
        args = [_build_expr(arena, a) for a in data.get("args", [])]
        return arena.operation(verb, args if args else None)

    elif type_name == "structure":
        members = [_build_expr(arena, m) for m in data["members"]]
        return arena.structure(members)

    elif type_name in ("sequence", "product", "union", "intersect"):
        left = _build_expr(arena, data["left"])
        right = _build_expr(arena, data["right"])
        fn = getattr(arena, type_name)
        return fn(left, right)

    elif type_name in ("nest", "nesting"):
        envelope = _build_expr(arena, data["envelope"])
        payload = _build_expr(arena, data["payload"])
        return arena.nest(envelope, payload)

    else:
        raise ValueError(f"Unknown expression type: {type_name}")


def _decode_bytes(val, expected_len=None) -> bytes:
    """Decode a hex or base64 string to bytes."""
    if isinstance(val, bytes):
        b = val
    elif isinstance(val, str):
        # Try hex first
        try:
            b = bytes.fromhex(val)
        except ValueError:
            # Fall back to base64
            b = base64.b64decode(val)
    else:
        raise ValueError(f"Expected hex or base64 string, got {type(val)}")
    if expected_len is not None and len(b) != expected_len:
        raise ValueError(f"Expected {expected_len} bytes, got {len(b)}")
    return b


def _expr_to_dict(expr: Expr) -> dict:
    """Convert an Expr back to a JSON-friendly dict."""
    tag = expr.type_tag

    if tag == TEN_TYPE_SCALAR:
        result = {"scalar": {
            "dimension": expr.scalar_dimension,
            "value": expr.scalar_value,
            "precision": expr.scalar_precision,
        }}
    elif tag == TEN_TYPE_REFERENCE:
        result = {"reference": {"hash": expr.ref_hash.hex()}}
    elif tag == TEN_TYPE_IDENTITY:
        result = {"identity": {"pubkey": expr.identity_pubkey.hex()}}
    elif tag == TEN_TYPE_ASSERTION:
        result = {"assertion": {
            "claim": _expr_to_dict(expr.assertion_claim),
            "who": _expr_to_dict(expr.assertion_who),
            "confidence": expr.assertion_confidence,
        }}
    elif tag == TEN_TYPE_OPERATION:
        result = {"operation": {
            "verb": expr.operation_verb_name,
            "args": [_expr_to_dict(a) for a in expr.operation_args],
        }}
    elif tag == TEN_TYPE_STRUCTURE:
        result = {"structure": {
            "members": [_expr_to_dict(m) for m in expr.structure_members],
        }}
    elif tag in (TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT,
                 TEN_TYPE_UNION, TEN_TYPE_INTERSECT):
        name = expr.type_name.lower()
        result = {name: {
            "left": _expr_to_dict(expr.left),
            "right": _expr_to_dict(expr.right),
        }}
    elif tag == TEN_TYPE_NESTING:
        result = {"nest": {
            "envelope": _expr_to_dict(expr.envelope),
            "payload": _expr_to_dict(expr.payload),
        }}
    else:
        result = {"unknown": {"type_tag": tag}}

    # Include facets if present
    facets = {}
    for name, dim_id in FACET_MAP.items():
        if expr.has_facet(dim_id):
            facets[name] = expr.get_facet(dim_id)
    if facets:
        result["_facets"] = facets

    return result


# ══════════════════════════════════════════════════════════════
#                       MCP TOOLS
# ══════════════════════════════════════════════════════════════


@mcp.tool()
def ten_encode(expression: dict, facets: dict = None) -> dict:
    """
    Encode a structured expression into Ten binary wire format.

    Args:
        expression: A nested dict describing the expression tree. Examples:
            {"scalar": {"dimension": "urgency", "value": 0.95, "precision": 16}}
            {"operation": {"verb": "query", "args": [{"reference": {"hash": "ab" * 16}}]}}
            {"sequence": {"left": {"scalar": {...}}, "right": {"scalar": {...}}}}
        facets: Optional dict of facet values to attach. Keys are facet names
            (urgency, cost, privilege, confidence, ttl, effort, reputation, value)
            or numeric IDs. Values are floats.

    Returns:
        {"wire_b64": "<base64 encoded bytes>", "wire_hex": "<hex>", "size_bytes": N,
         "expression": <decoded structure for verification>}
    """
    with Arena() as a:
        expr = _build_expr(a, expression)

        if facets:
            for dim_name, val in facets.items():
                dim = _resolve_facet(dim_name)
                expr.set_facet(dim, float(val))

        wire = encode(expr)
        structure = _expr_to_dict(expr)

    return {
        "wire_b64": base64.b64encode(wire).decode("ascii"),
        "wire_hex": wire.hex(),
        "size_bytes": len(wire),
        "expression": structure,
    }


@mcp.tool()
def ten_decode(wire_b64: str = None, wire_hex: str = None) -> dict:
    """
    Decode Ten binary wire format back into a structured expression.

    Args:
        wire_b64: Base64-encoded wire bytes (from ten_encode output).
        wire_hex: Hex-encoded wire bytes (alternative to base64).
        Provide exactly one of wire_b64 or wire_hex.

    Returns:
        {"expression": <structured dict>, "valid": bool, "description": "<debug text>"}
    """
    if wire_b64:
        wire = base64.b64decode(wire_b64)
    elif wire_hex:
        wire = bytes.fromhex(wire_hex)
    else:
        return {"error": "Provide either wire_b64 or wire_hex"}

    with Arena() as a:
        expr = decode(a, wire)
        return {
            "expression": _expr_to_dict(expr),
            "valid": expr.is_valid(),
            "description": expr.describe(),
        }


@mcp.tool()
def ten_compose(
    operation: str,
    left: dict = None,
    right: dict = None,
    envelope: dict = None,
    payload: dict = None,
    left_wire_b64: str = None,
    right_wire_b64: str = None,
    envelope_wire_b64: str = None,
    payload_wire_b64: str = None,
) -> dict:
    """
    Compose two Ten expressions using an algebraic operation.

    Args:
        operation: One of "sequence", "product", "nest", "union", "intersect".
        left/right: Expression dicts for sequence/product/union/intersect.
        envelope/payload: Expression dicts for nesting.
        *_wire_b64: Alternative — provide previously encoded wire bytes instead of dicts.

    Returns:
        {"wire_b64": "...", "wire_hex": "...", "size_bytes": N, "expression": {...}}
    """
    op = operation.lower()
    if op not in COMPOSE_MAP:
        return {"error": f"Unknown operation: {operation}. "
                f"Valid: {', '.join(COMPOSE_MAP.keys())}"}
    op = COMPOSE_MAP[op]

    with Arena() as a:
        if op == "nest":
            env = _resolve_input(a, envelope, envelope_wire_b64, "envelope")
            pay = _resolve_input(a, payload, payload_wire_b64, "payload")
            result = a.nest(env, pay)
        else:
            l = _resolve_input(a, left, left_wire_b64, "left")
            r = _resolve_input(a, right, right_wire_b64, "right")
            fn = getattr(a, op)
            result = fn(l, r)

        wire = encode(result)
        return {
            "wire_b64": base64.b64encode(wire).decode("ascii"),
            "wire_hex": wire.hex(),
            "size_bytes": len(wire),
            "expression": _expr_to_dict(result),
        }


def _resolve_input(arena, spec, wire_b64, name):
    """Build an expr from a dict spec or decode from wire bytes."""
    if spec:
        return _build_expr(arena, spec)
    elif wire_b64:
        wire = base64.b64decode(wire_b64)
        return decode(arena, wire)
    else:
        raise ValueError(f"Provide either {name} (dict) or {name}_wire_b64 (string)")


@mcp.tool()
def ten_project(
    expression: dict = None,
    wire_b64: str = None,
    dimensions: list = None,
) -> dict:
    """
    Extract a subset of facet dimensions from an expression (like SELECT columns).

    Args:
        expression: Expression dict (or provide wire_b64 instead).
        wire_b64: Previously encoded wire bytes.
        dimensions: List of facet names or IDs to keep.
            e.g. ["urgency", "cost"] or [0, 1]

    Returns:
        {"wire_b64": "...", "expression": {...}, "projected_facets": {...}}
    """
    if not dimensions:
        return {"error": "dimensions is required (list of facet names or IDs)"}

    dims = [_resolve_facet(d) for d in dimensions]

    with Arena() as a:
        expr = _resolve_input(a, expression, wire_b64, "expression")
        projected = a.project(expr, dims)
        wire = encode(projected)

        facets = {}
        for name, dim_id in FACET_MAP.items():
            if projected.has_facet(dim_id):
                facets[name] = projected.get_facet(dim_id)

        return {
            "wire_b64": base64.b64encode(wire).decode("ascii"),
            "wire_hex": wire.hex(),
            "size_bytes": len(wire),
            "expression": _expr_to_dict(projected),
            "projected_facets": facets,
        }


@mcp.tool()
def ten_filter(
    expressions: list,
    criteria: list,
) -> dict:
    """
    Filter a list of expressions by facet criteria. This is the inbox
    processing hot path — filter 1000 messages by urgency >= 0.8 without
    parsing message bodies.

    Args:
        expressions: List of expression dicts or {"wire_b64": "..."} objects.
        criteria: List of filter clauses, each a dict:
            {"dimension": "urgency", "op": ">=", "threshold": 0.8}
            Valid ops: ">=", "<=", "==", "!=", "gte", "lte", "eq", "neq"

    Returns:
        {"matched": [<indices of matching expressions>],
         "matched_count": N, "total": N}
    """
    clauses = []
    for c in criteria:
        dim = _resolve_facet(c["dimension"])
        op = CMP_MAP.get(c.get("op", "gte"), TEN_CMP_GTE)
        threshold = float(c["threshold"])
        clauses.append((dim, op, threshold))

    matched = []
    with Arena() as a:
        for i, item in enumerate(expressions):
            a.reset()
            if isinstance(item, dict) and "wire_b64" in item:
                wire = base64.b64decode(item["wire_b64"])
                expr = decode(a, wire)
            else:
                expr = _build_expr(a, item)
            if expr.matches_filter(clauses):
                matched.append(i)

    return {
        "matched": matched,
        "matched_count": len(matched),
        "total": len(expressions),
    }


@mcp.tool()
def ten_describe(
    expression: dict = None,
    wire_b64: str = None,
) -> dict:
    """
    Return a human-readable description and structural analysis of a
    Ten expression. Useful for debugging and understanding message contents.

    Args:
        expression: Expression dict (or provide wire_b64 instead).
        wire_b64: Previously encoded wire bytes.

    Returns:
        {"description": "<human-readable tree>", "type": "...",
         "is_kernel": bool, "is_composition": bool, "valid": bool,
         "structure": <JSON dict representation>}
    """
    with Arena() as a:
        expr = _resolve_input(a, expression, wire_b64, "expression")
        return {
            "description": expr.describe(),
            "type": expr.type_name,
            "is_kernel": expr.is_kernel,
            "is_composition": expr.is_composition,
            "valid": expr.is_valid(),
            "structure": _expr_to_dict(expr),
        }


@mcp.tool()
def ten_verify(
    expression: dict = None,
    wire_b64: str = None,
) -> dict:
    """
    Verify the structural integrity of a Ten expression. Checks that the
    expression tree is well-formed: all compositions have valid children,
    assertions have claims and identities, operations have valid args, etc.

    For Assertion expressions, also reports the claim, identity, and
    confidence for inspection (cryptographic signature verification
    is not yet implemented).

    Args:
        expression: Expression dict (or provide wire_b64 instead).
        wire_b64: Previously encoded wire bytes.

    Returns:
        {"valid": bool, "type": "...", "details": {...}}
    """
    with Arena() as a:
        expr = _resolve_input(a, expression, wire_b64, "expression")
        valid = expr.is_valid()

        details = {
            "type": expr.type_name,
            "is_kernel": expr.is_kernel,
            "is_composition": expr.is_composition,
        }

        # For assertions, extract trust chain info
        if expr.type_tag == TEN_TYPE_ASSERTION:
            details["assertion"] = {
                "confidence": expr.assertion_confidence,
                "claim_type": expr.assertion_claim.type_name,
                "who_type": expr.assertion_who.type_name,
                "claim_valid": expr.assertion_claim.is_valid(),
                "who_valid": expr.assertion_who.is_valid(),
            }
            if expr.assertion_who.type_tag == TEN_TYPE_IDENTITY:
                details["assertion"]["identity_pubkey_hex"] = \
                    expr.assertion_who.identity_pubkey.hex()

        # Check facets
        facets = {}
        for name, dim_id in FACET_MAP.items():
            if expr.has_facet(dim_id):
                facets[name] = expr.get_facet(dim_id)
        if facets:
            details["facets"] = facets

        return {
            "valid": valid,
            "type": expr.type_name,
            "details": details,
        }


# ── Entry point ─────────────────────────────────────────────

def main():
    mcp.run()

if __name__ == "__main__":
    main()
