"""
tenlang — Python bindings for the Ten formal algebra.

Ten is a formal algebra for machine intelligence communication.
Messages are math — sortable, filterable, composable — not natural language.

Quick start:
    from tenlang import Arena, encode, decode

    with Arena() as a:
        msg = a.scalar(0, 0.95, precision=16)
        msg.set_facet(0, 0.95)  # urgency
        wire = encode(msg)

    with Arena() as a2:
        decoded = decode(a2, wire)
        print(decoded.describe())
"""

from .types import (
    Arena,
    Expr,
    TenError,
    encode,
    decode,
)

from ._ffi import (
    # Facet dimensions
    TEN_FACET_URGENCY, TEN_FACET_COST, TEN_FACET_PRIVILEGE,
    TEN_FACET_CONFIDENCE, TEN_FACET_TTL, TEN_FACET_EFFORT,
    TEN_FACET_REPUTATION, TEN_FACET_VALUE,
    # Operation verbs
    TEN_OP_QUERY, TEN_OP_RESPOND, TEN_OP_OFFER, TEN_OP_ACCEPT,
    TEN_OP_DECLINE, TEN_OP_CHALLENGE, TEN_OP_PROVE, TEN_OP_DELEGATE,
    TEN_OP_SUBSCRIBE, TEN_OP_CANCEL, TEN_OP_VOUCH, TEN_OP_ASSESS,
    TEN_OP_BID, TEN_OP_COUNTER, TEN_OP_INVOKE,
    # Precision levels
    TEN_PREC_1BIT, TEN_PREC_4BIT, TEN_PREC_8BIT,
    TEN_PREC_16BIT, TEN_PREC_32BIT, TEN_PREC_64BIT,
    # Type tags
    TEN_TYPE_SCALAR, TEN_TYPE_REFERENCE, TEN_TYPE_IDENTITY,
    TEN_TYPE_ASSERTION, TEN_TYPE_OPERATION, TEN_TYPE_STRUCTURE,
    TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT, TEN_TYPE_NESTING,
    TEN_TYPE_UNION, TEN_TYPE_INTERSECT,
    # Limits
    TEN_HASH_SIZE, TEN_MAX_FACETS, TEN_MAX_PUBKEY_SIZE,
    # Filter ops
    TEN_CMP_GTE, TEN_CMP_LTE, TEN_CMP_EQ, TEN_CMP_NEQ,
)

__version__ = "0.1.0"
__all__ = [
    "Arena", "Expr", "TenError", "encode", "decode",
    "TEN_FACET_URGENCY", "TEN_FACET_COST", "TEN_FACET_PRIVILEGE",
    "TEN_FACET_CONFIDENCE", "TEN_FACET_TTL", "TEN_FACET_EFFORT",
    "TEN_FACET_REPUTATION", "TEN_FACET_VALUE",
    "TEN_OP_QUERY", "TEN_OP_RESPOND", "TEN_OP_OFFER", "TEN_OP_ACCEPT",
    "TEN_OP_DECLINE", "TEN_OP_CHALLENGE", "TEN_OP_PROVE", "TEN_OP_DELEGATE",
    "TEN_OP_SUBSCRIBE", "TEN_OP_CANCEL", "TEN_OP_VOUCH", "TEN_OP_ASSESS",
    "TEN_OP_BID", "TEN_OP_COUNTER", "TEN_OP_INVOKE",
    "TEN_PREC_1BIT", "TEN_PREC_4BIT", "TEN_PREC_8BIT",
    "TEN_PREC_16BIT", "TEN_PREC_32BIT", "TEN_PREC_64BIT",
    "TEN_TYPE_SCALAR", "TEN_TYPE_REFERENCE", "TEN_TYPE_IDENTITY",
    "TEN_TYPE_ASSERTION", "TEN_TYPE_OPERATION", "TEN_TYPE_STRUCTURE",
    "TEN_TYPE_SEQUENCE", "TEN_TYPE_PRODUCT", "TEN_TYPE_NESTING",
    "TEN_TYPE_UNION", "TEN_TYPE_INTERSECT",
    "TEN_HASH_SIZE", "TEN_MAX_FACETS", "TEN_MAX_PUBKEY_SIZE",
    "TEN_CMP_GTE", "TEN_CMP_LTE", "TEN_CMP_EQ", "TEN_CMP_NEQ",
]
