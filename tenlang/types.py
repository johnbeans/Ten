"""
types.py — Pythonic API over libten C types.

This is the module users interact with. It wraps the raw ctypes calls
in Arena, Expr, and helper classes that feel like natural Python.

Usage:
    from tenlang import Arena, Scalar, Reference, Sequence, encode, decode

    with Arena() as a:
        msg = a.sequence(
            a.scalar(urgency, 0.95, precision=16),
            a.scalar(cost, 0.30, precision=8),
        )
        msg.set_facet(urgency, 0.95)
        wire = encode(msg)

    with Arena() as a2:
        decoded = decode(a2, wire)
        assert decoded.is_valid()
"""

import ctypes
from contextlib import contextmanager
from typing import List, Optional, Sequence as SequenceType, Tuple

from . import _ffi

# Re-export constants for convenience
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
    # Precision
    TEN_PREC_1BIT, TEN_PREC_4BIT, TEN_PREC_8BIT,
    TEN_PREC_16BIT, TEN_PREC_32BIT, TEN_PREC_64BIT,
    # Type tags
    TEN_TYPE_SCALAR, TEN_TYPE_REFERENCE, TEN_TYPE_IDENTITY,
    TEN_TYPE_ASSERTION, TEN_TYPE_OPERATION, TEN_TYPE_STRUCTURE,
    TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT, TEN_TYPE_NESTING,
    TEN_TYPE_UNION, TEN_TYPE_INTERSECT,
    # Limits
    TEN_HASH_SIZE, TEN_MAX_FACETS, TEN_MAX_PUBKEY_SIZE,
    # Filter comparison ops
    TEN_CMP_GTE, TEN_CMP_LTE, TEN_CMP_EQ, TEN_CMP_NEQ,
)


class TenError(Exception):
    """Exception raised for libten errors."""
    def __init__(self, code: int, message: str = ""):
        self.code = code
        lib = _ffi.get_lib()
        self.error_name = lib.ten_error_string(code).decode("utf-8")
        super().__init__(message or f"Ten error {code}: {self.error_name}")


def _check(code: int):
    """Raise TenError if code is not TEN_OK."""
    if code != _ffi.TEN_OK:
        raise TenError(code)


class Expr:
    """
    Wrapper around a ten_expr_t pointer.

    Expr objects are owned by their Arena — do not use them after
    the arena is freed or reset.
    """

    def __init__(self, ptr: ctypes.POINTER(_ffi.TenExpr), arena: "Arena"):
        if not ptr:
            raise TenError(_ffi.TEN_ERROR_NULL_ARG, "Expression construction returned NULL")
        self._ptr = ptr
        self._arena = arena
        self._lib = _ffi.get_lib()

    @property
    def type_tag(self) -> int:
        """Raw type tag (TEN_TYPE_* constant)."""
        return self._ptr.contents.type

    @property
    def type_name(self) -> str:
        """Human-readable type name."""
        return self._lib.ten_type_name(self.type_tag).decode("utf-8")

    @property
    def is_kernel(self) -> bool:
        return self._lib.ten_is_kernel_type(self.type_tag)

    @property
    def is_composition(self) -> bool:
        return self._lib.ten_is_composition_type(self.type_tag)

    def is_valid(self) -> bool:
        """Check structural validity of this expression tree."""
        return self._lib.ten_is_valid(self._ptr)

    # ── Facet access ────────────────────────────────────

    def init_facets(self):
        """Initialize the facet vector on this expression."""
        _check(self._lib.ten_facet_init(
            ctypes.byref(self._arena._arena), self._ptr))

    def set_facet(self, dimension: int, value: float,
                  precision: int = TEN_PREC_64BIT):
        """Set a facet dimension value."""
        if not self._ptr.contents.facets:
            self.init_facets()
        _check(self._lib.ten_facet_set(self._ptr, dimension, value, precision))

    def get_facet(self, dimension: int) -> float:
        """Get a facet dimension value (0.0 if unset)."""
        return self._lib.ten_facet_get(self._ptr, dimension)

    def has_facet(self, dimension: int) -> bool:
        """Check if a facet dimension is set."""
        return self._lib.ten_facet_has(self._ptr, dimension)

    def matches_filter(self, clauses: list) -> bool:
        """
        Check if this expression passes filter criteria.

        clauses: list of (dimension, op, threshold) tuples.
            op is one of TEN_CMP_GTE, TEN_CMP_LTE, TEN_CMP_EQ, TEN_CMP_NEQ.
        """
        n = len(clauses)
        arr = (_ffi.TenFilterClause * n)()
        for i, (dim, op, thresh) in enumerate(clauses):
            arr[i].dimension = dim
            arr[i].op = op
            arr[i].threshold = thresh
        filt = _ffi.TenFilter(clauses=arr, nclauses=n)
        return self._lib.ten_facet_filter(self._ptr, ctypes.byref(filt))

    # ── Scalar access ───────────────────────────────────

    @property
    def scalar_value(self) -> float:
        """For Scalar expressions, return the value."""
        assert self.type_tag == TEN_TYPE_SCALAR
        return self._ptr.contents.data.scalar.value

    @property
    def scalar_dimension(self) -> int:
        assert self.type_tag == TEN_TYPE_SCALAR
        return self._ptr.contents.data.scalar.dimension

    @property
    def scalar_precision(self) -> int:
        assert self.type_tag == TEN_TYPE_SCALAR
        return self._ptr.contents.data.scalar.precision

    # ── Reference access ────────────────────────────────

    @property
    def ref_hash(self) -> bytes:
        """For Reference expressions, return the 32-byte hash."""
        assert self.type_tag == TEN_TYPE_REFERENCE
        return bytes(self._ptr.contents.data.ref.hash)

    # ── Identity access ─────────────────────────────────

    @property
    def identity_pubkey(self) -> bytes:
        """For Identity expressions, return the public key bytes."""
        assert self.type_tag == TEN_TYPE_IDENTITY
        kl = self._ptr.contents.data.identity.keylen
        return bytes(self._ptr.contents.data.identity.pubkey[:kl])

    # ── Assertion access ────────────────────────────────

    @property
    def assertion_confidence(self) -> float:
        assert self.type_tag == TEN_TYPE_ASSERTION
        return self._ptr.contents.data.assertion.confidence

    @property
    def assertion_claim(self) -> "Expr":
        assert self.type_tag == TEN_TYPE_ASSERTION
        return Expr(self._ptr.contents.data.assertion.claim, self._arena)

    @property
    def assertion_who(self) -> "Expr":
        assert self.type_tag == TEN_TYPE_ASSERTION
        return Expr(self._ptr.contents.data.assertion.who, self._arena)

    # ── Operation access ────────────────────────────────

    @property
    def operation_verb(self) -> int:
        assert self.type_tag == TEN_TYPE_OPERATION
        return self._ptr.contents.data.operation.verb

    @property
    def operation_verb_name(self) -> str:
        assert self.type_tag == TEN_TYPE_OPERATION
        return self._lib.ten_op_name(
            self._ptr.contents.data.operation.verb).decode("utf-8")

    @property
    def operation_args(self) -> List["Expr"]:
        assert self.type_tag == TEN_TYPE_OPERATION
        n = self._ptr.contents.data.operation.nargs
        args_ptr = self._ptr.contents.data.operation.args
        return [Expr(args_ptr[i], self._arena) for i in range(n)]

    # ── Structure access ────────────────────────────────

    @property
    def structure_members(self) -> List["Expr"]:
        assert self.type_tag == TEN_TYPE_STRUCTURE
        n = self._ptr.contents.data.structure.nmembers
        m_ptr = self._ptr.contents.data.structure.members
        return [Expr(m_ptr[i], self._arena) for i in range(n)]

    # ── Pair access (Sequence, Product, Union, Intersect) ─

    @property
    def left(self) -> "Expr":
        assert self.type_tag in (
            TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT,
            TEN_TYPE_UNION, TEN_TYPE_INTERSECT)
        return Expr(self._ptr.contents.data.pair.left, self._arena)

    @property
    def right(self) -> "Expr":
        assert self.type_tag in (
            TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT,
            TEN_TYPE_UNION, TEN_TYPE_INTERSECT)
        return Expr(self._ptr.contents.data.pair.right, self._arena)

    # ── Nesting access ──────────────────────────────────

    @property
    def envelope(self) -> "Expr":
        assert self.type_tag == TEN_TYPE_NESTING
        return Expr(self._ptr.contents.data.nesting.envelope, self._arena)

    @property
    def payload(self) -> "Expr":
        assert self.type_tag == TEN_TYPE_NESTING
        return Expr(self._ptr.contents.data.nesting.payload, self._arena)

    # ── Debug ───────────────────────────────────────────

    def describe(self) -> str:
        """Human-readable debug representation."""
        buf = ctypes.create_string_buffer(4096)
        length = self._lib.ten_describe(self._ptr, buf, 4096)
        return buf.value.decode("utf-8") if length > 0 else ""

    def __repr__(self):
        return f"<Expr {self.type_name}>"


class Arena:
    """
    Arena allocator for Ten expressions.

    Usage as context manager:
        with Arena() as a:
            s = a.scalar(0, 0.95, precision=16)
            ...
        # arena freed automatically

    Or manual lifecycle:
        a = Arena()
        ...
        a.free()
    """

    def __init__(self, size: int = 0):
        self._lib = _ffi.get_lib()
        self._arena = _ffi.TenArena()
        _check(self._lib.ten_arena_init(ctypes.byref(self._arena), size))
        self._freed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.free()
        return False

    def free(self):
        if not self._freed:
            self._lib.ten_arena_free(ctypes.byref(self._arena))
            self._freed = True

    def reset(self):
        """Reuse the arena's memory without reallocating."""
        self._lib.ten_arena_reset(ctypes.byref(self._arena))

    @property
    def remaining(self) -> int:
        return self._lib.ten_arena_remaining(ctypes.byref(self._arena))

    def __del__(self):
        self.free()

    # ── Kernel type constructors ────────────────────────

    def scalar(self, dimension: int, value: float,
               precision: int = TEN_PREC_64BIT) -> Expr:
        ptr = self._lib.ten_scalar(
            ctypes.byref(self._arena), dimension, value, precision)
        return Expr(ptr, self)

    def ref(self, hash_bytes: bytes) -> Expr:
        """Create a Reference from a 32-byte hash."""
        if len(hash_bytes) != TEN_HASH_SIZE:
            raise ValueError(f"Hash must be exactly {TEN_HASH_SIZE} bytes")
        h = (ctypes.c_uint8 * TEN_HASH_SIZE)(*hash_bytes)
        ptr = self._lib.ten_ref(ctypes.byref(self._arena), h)
        return Expr(ptr, self)

    def identity(self, pubkey: bytes) -> Expr:
        """Create an Identity from a public key."""
        if len(pubkey) == 0 or len(pubkey) > TEN_MAX_PUBKEY_SIZE:
            raise ValueError(
                f"Key must be 1-{TEN_MAX_PUBKEY_SIZE} bytes, got {len(pubkey)}")
        key_arr = (ctypes.c_uint8 * len(pubkey))(*pubkey)
        ptr = self._lib.ten_identity(
            ctypes.byref(self._arena), key_arr, len(pubkey))
        return Expr(ptr, self)

    def assertion(self, claim: Expr, who: Expr,
                  confidence: float) -> Expr:
        ptr = self._lib.ten_assertion(
            ctypes.byref(self._arena), claim._ptr, who._ptr, confidence)
        return Expr(ptr, self)

    def operation(self, verb: int, args: Optional[List[Expr]] = None) -> Expr:
        if args:
            n = len(args)
            arr = (ctypes.POINTER(_ffi.TenExpr) * n)(
                *[a._ptr for a in args])
            ptr = self._lib.ten_operation(
                ctypes.byref(self._arena), verb, arr, n)
        else:
            ptr = self._lib.ten_operation(
                ctypes.byref(self._arena), verb, None, 0)
        return Expr(ptr, self)

    def structure(self, members: List[Expr]) -> Expr:
        n = len(members)
        arr = (ctypes.POINTER(_ffi.TenExpr) * n)(
            *[m._ptr for m in members])
        ptr = self._lib.ten_structure(
            ctypes.byref(self._arena), arr, n)
        return Expr(ptr, self)

    # ── Composition operations ──────────────────────────

    def sequence(self, left: Expr, right: Expr) -> Expr:
        ptr = self._lib.ten_sequence(
            ctypes.byref(self._arena), left._ptr, right._ptr)
        return Expr(ptr, self)

    def product(self, left: Expr, right: Expr) -> Expr:
        ptr = self._lib.ten_product(
            ctypes.byref(self._arena), left._ptr, right._ptr)
        return Expr(ptr, self)

    def nest(self, envelope: Expr, payload: Expr) -> Expr:
        ptr = self._lib.ten_nest(
            ctypes.byref(self._arena), envelope._ptr, payload._ptr)
        return Expr(ptr, self)

    def union(self, left: Expr, right: Expr) -> Expr:
        ptr = self._lib.ten_union(
            ctypes.byref(self._arena), left._ptr, right._ptr)
        return Expr(ptr, self)

    def intersect(self, left: Expr, right: Expr) -> Expr:
        ptr = self._lib.ten_intersect(
            ctypes.byref(self._arena), left._ptr, right._ptr)
        return Expr(ptr, self)

    def project(self, expr: Expr, dimensions: List[int]) -> Expr:
        n = len(dimensions)
        dims = (ctypes.c_uint16 * n)(*dimensions)
        ptr = self._lib.ten_project(
            ctypes.byref(self._arena), expr._ptr, dims, n)
        return Expr(ptr, self)


# ── Module-level encode/decode ──────────────────────────────

def encode(expr: Expr, bufsize: int = 8192) -> bytes:
    """
    Encode a Ten expression to its binary wire format.
    Returns the wire bytes.
    """
    lib = _ffi.get_lib()
    buf = (ctypes.c_uint8 * bufsize)()
    outlen = ctypes.c_size_t(0)
    rc = lib.ten_encode(expr._ptr, buf, bufsize, ctypes.byref(outlen))
    _check(rc)
    return bytes(buf[:outlen.value])


def decode(arena: Arena, wire: bytes) -> Expr:
    """
    Decode binary wire bytes into a Ten expression.
    The expression is allocated from the provided arena.
    """
    lib = _ffi.get_lib()
    buf = (ctypes.c_uint8 * len(wire))(*wire)
    ptr = lib.ten_decode(ctypes.byref(arena._arena), buf, len(wire))
    return Expr(ptr, arena)
