"""
ten-rest-api — HTTP endpoints mirroring the Ten MCP server tools.

Every endpoint accepts and returns JSON. The API is stateless —
each request creates its own arena, encodes/decodes, and returns.
All operations are pure code: no AI inference, no LLM calls.

Usage:
    uvicorn ten_rest_api.app:app --host 0.0.0.0 --port 8420
    # or
    python -m ten_rest_api
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

# Reuse all the core logic from the MCP server
from ten_mcp_server.server import (
    _build_expr, _expr_to_dict, _resolve_input, _resolve_facet,
    _decode_bytes, COMPOSE_MAP, CMP_MAP, FACET_MAP,
    TEN_TYPE_ASSERTION, TEN_TYPE_IDENTITY,
)
from tenlang import Arena, encode, decode, TenError

app = FastAPI(
    title="Ten REST API",
    version="0.1.0",
    description=(
        "HTTP endpoints for the Ten formal algebra — "
        "encode, decode, compose, project, filter, describe, and verify "
        "structured machine-to-machine messages. Pure code, no AI inference."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────

class EncodeRequest(BaseModel):
    expression: dict = Field(..., description="Expression tree as a nested dict")
    facets: Optional[dict] = Field(None, description="Facet values to attach")

class DecodeRequest(BaseModel):
    wire_b64: Optional[str] = Field(None, description="Base64-encoded wire bytes")
    wire_hex: Optional[str] = Field(None, description="Hex-encoded wire bytes")

class ComposeRequest(BaseModel):
    operation: str = Field(..., description="sequence | product | nest | union | intersect")
    left: Optional[dict] = None
    right: Optional[dict] = None
    envelope: Optional[dict] = None
    payload: Optional[dict] = None
    left_wire_b64: Optional[str] = None
    right_wire_b64: Optional[str] = None
    envelope_wire_b64: Optional[str] = None
    payload_wire_b64: Optional[str] = None

class ProjectRequest(BaseModel):
    expression: Optional[dict] = None
    wire_b64: Optional[str] = None
    dimensions: list = Field(..., description="Facet names or IDs to keep")

class FilterCriterion(BaseModel):
    dimension: str = Field(..., description="Facet name or ID")
    op: str = Field(">=", description=">=, <=, ==, !=")
    threshold: float = Field(..., description="Threshold value")

class FilterRequest(BaseModel):
    expressions: list = Field(..., description="List of expression dicts or wire_b64 objects")
    criteria: list[FilterCriterion]

class ExprInput(BaseModel):
    expression: Optional[dict] = None
    wire_b64: Optional[str] = None


# ── Helpers ────────────────────────────────────────────────

import base64

def _encode_result(arena, expr):
    """Encode an expression and return the standard response dict."""
    wire = encode(expr)
    return {
        "wire_b64": base64.b64encode(wire).decode("ascii"),
        "wire_hex": wire.hex(),
        "size_bytes": len(wire),
        "expression": _expr_to_dict(expr),
    }


# ── Health check ───────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "ten-rest-api", "version": "0.1.0"}


# ── Encode ─────────────────────────────────────────────────

@app.post("/v1/encode")
def encode_expr(req: EncodeRequest):
    """
    Encode a structured expression into Ten binary wire format.

    Accepts a nested dict describing the expression tree and optional
    facet values. Returns base64 and hex wire representations.
    """
    try:
        with Arena() as a:
            expr = _build_expr(a, req.expression)
            if req.facets:
                for dim_name, val in req.facets.items():
                    dim = _resolve_facet(dim_name)
                    expr.set_facet(dim, float(val))
            return _encode_result(a, expr)
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Decode ─────────────────────────────────────────────────

@app.post("/v1/decode")
def decode_expr(req: DecodeRequest):
    """
    Decode Ten binary wire format back into a structured expression.

    Provide either wire_b64 or wire_hex. Returns the expression tree,
    validation status, and a human-readable description.
    """
    try:
        if req.wire_b64:
            wire = base64.b64decode(req.wire_b64)
        elif req.wire_hex:
            wire = bytes.fromhex(req.wire_hex)
        else:
            raise HTTPException(status_code=400,
                                detail="Provide either wire_b64 or wire_hex")
        with Arena() as a:
            expr = decode(a, wire)
            return {
                "expression": _expr_to_dict(expr),
                "valid": expr.is_valid(),
                "description": expr.describe(),
            }
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Compose ────────────────────────────────────────────────

@app.post("/v1/compose")
def compose_expr(req: ComposeRequest):
    """
    Compose two Ten expressions using an algebraic operation.

    Supports sequence, product, nest (nesting), union, and intersect.
    Inputs can be expression dicts or previously encoded wire bytes.
    """
    op = req.operation.lower()
    if op not in COMPOSE_MAP:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown operation: {req.operation}. "
                   f"Valid: {', '.join(COMPOSE_MAP.keys())}")
    op = COMPOSE_MAP[op]

    try:
        with Arena() as a:
            if op == "nest":
                env = _resolve_input(a, req.envelope, req.envelope_wire_b64, "envelope")
                pay = _resolve_input(a, req.payload, req.payload_wire_b64, "payload")
                result = a.nest(env, pay)
            else:
                l = _resolve_input(a, req.left, req.left_wire_b64, "left")
                r = _resolve_input(a, req.right, req.right_wire_b64, "right")
                fn = getattr(a, op)
                result = fn(l, r)
            return _encode_result(a, result)
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Project ────────────────────────────────────────────────

@app.post("/v1/project")
def project_expr(req: ProjectRequest):
    """
    Extract a subset of facet dimensions from an expression.

    Like SQL SELECT — keeps only the specified dimensions, discards the rest.
    """
    if not req.dimensions:
        raise HTTPException(status_code=400,
                            detail="dimensions is required")
    try:
        dims = [_resolve_facet(d) for d in req.dimensions]
        with Arena() as a:
            expr = _resolve_input(a, req.expression, req.wire_b64, "expression")
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
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Filter ─────────────────────────────────────────────────

@app.post("/v1/filter")
def filter_exprs(req: FilterRequest):
    """
    Filter expressions by facet criteria.

    The inbox processing hot path: filter 1000 messages by
    urgency >= 0.8 without parsing message bodies.
    """
    try:
        clauses = []
        for c in req.criteria:
            dim = _resolve_facet(c.dimension)
            op = CMP_MAP.get(c.op, None)
            if op is None:
                raise ValueError(f"Unknown comparison op: {c.op}. "
                                 f"Valid: >=, <=, ==, !=")
            clauses.append((dim, op, c.threshold))

        matched = []
        with Arena() as a:
            for i, item in enumerate(req.expressions):
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
            "total": len(req.expressions),
        }
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Describe ───────────────────────────────────────────────

@app.post("/v1/describe")
def describe_expr(req: ExprInput):
    """
    Return a human-readable description and structural analysis.

    Useful for debugging and understanding message contents.
    """
    try:
        with Arena() as a:
            expr = _resolve_input(a, req.expression, req.wire_b64, "expression")
            return {
                "description": expr.describe(),
                "type": expr.type_name,
                "is_kernel": expr.is_kernel,
                "is_composition": expr.is_composition,
                "valid": expr.is_valid(),
                "structure": _expr_to_dict(expr),
            }
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Verify ─────────────────────────────────────────────────

@app.post("/v1/verify")
def verify_expr(req: ExprInput):
    """
    Verify the structural integrity of a Ten expression.

    Checks well-formedness: compositions have valid children,
    assertions have claims and identities, etc. For assertions,
    also reports confidence and identity info.
    """
    try:
        with Arena() as a:
            expr = _resolve_input(a, req.expression, req.wire_b64, "expression")
            valid = expr.is_valid()

            details = {
                "type": expr.type_name,
                "is_kernel": expr.is_kernel,
                "is_composition": expr.is_composition,
            }

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
    except (ValueError, TenError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Entry point ────────────────────────────────────────────

def main():
    import uvicorn
    uvicorn.run("ten_rest_api.app:app", host="0.0.0.0", port=8420, reload=True)

if __name__ == "__main__":
    main()
