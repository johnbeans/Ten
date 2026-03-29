"""
_ffi.py — ctypes wrapper around libten shared library.

This module provides the raw C-level interface. Users should generally
import from tenlang.types instead, which provides a Pythonic API.

Library loading order:
  1. Explicit path via LIBTEN_PATH environment variable
  2. Adjacent to this file (for development / pip install tenlang)
  3. ../libten/build/ (for monorepo development)
  4. System library paths
"""

import ctypes
import ctypes.util
import os
import platform
import struct
from pathlib import Path

# ── Constants (must match ten.h) ────────────────────────────

TEN_DEFAULT_ARENA_SIZE = 64 * 1024
TEN_MAX_EXPRESSION_DEPTH = 256
TEN_MAX_CHILDREN = 4096
TEN_HASH_SIZE = 32
TEN_MAX_PUBKEY_SIZE = 64
TEN_MAX_FACETS = 64

# Error codes
TEN_OK = 0
TEN_ERROR_ARENA_FULL = 1
TEN_ERROR_MESSAGE_TOO_LARGE = 2
TEN_ERROR_MALFORMED = 3
TEN_ERROR_DEPTH_EXCEEDED = 4
TEN_ERROR_CHILDREN_EXCEEDED = 5
TEN_ERROR_INVALID_TYPE = 6
TEN_ERROR_INVALID_DIMENSION = 7
TEN_ERROR_NULL_ARG = 8
TEN_ERROR_BUFFER_TOO_SMALL = 9
TEN_ERROR_DECODE_FAILED = 10

# Type tags
TEN_TYPE_SCALAR = 0x01
TEN_TYPE_REFERENCE = 0x02
TEN_TYPE_IDENTITY = 0x03
TEN_TYPE_ASSERTION = 0x04
TEN_TYPE_OPERATION = 0x05
TEN_TYPE_STRUCTURE = 0x06
TEN_TYPE_SEQUENCE = 0x10
TEN_TYPE_PRODUCT = 0x11
TEN_TYPE_NESTING = 0x12
TEN_TYPE_UNION = 0x13
TEN_TYPE_INTERSECT = 0x14

# Well-known facet dimensions
TEN_FACET_URGENCY = 0
TEN_FACET_COST = 1
TEN_FACET_PRIVILEGE = 2
TEN_FACET_CONFIDENCE = 3
TEN_FACET_TTL = 4
TEN_FACET_EFFORT = 5
TEN_FACET_REPUTATION = 6
TEN_FACET_VALUE = 7

# Operation verbs
TEN_OP_QUERY = 0x01
TEN_OP_RESPOND = 0x02
TEN_OP_OFFER = 0x03
TEN_OP_ACCEPT = 0x04
TEN_OP_DECLINE = 0x05
TEN_OP_CHALLENGE = 0x06
TEN_OP_PROVE = 0x07
TEN_OP_DELEGATE = 0x08
TEN_OP_SUBSCRIBE = 0x09
TEN_OP_CANCEL = 0x0A
TEN_OP_VOUCH = 0x0B
TEN_OP_ASSESS = 0x0C
TEN_OP_BID = 0x0D
TEN_OP_COUNTER = 0x0E
TEN_OP_INVOKE = 0x0F

# Precision levels
TEN_PREC_1BIT = 1
TEN_PREC_4BIT = 4
TEN_PREC_8BIT = 8
TEN_PREC_16BIT = 16
TEN_PREC_32BIT = 32
TEN_PREC_64BIT = 64

# ── ctypes structure definitions ────────────────────────────

class TenArena(ctypes.Structure):
    _fields_ = [
        ("base", ctypes.POINTER(ctypes.c_uint8)),
        ("size", ctypes.c_size_t),
        ("used", ctypes.c_size_t),
        ("depth", ctypes.c_int),
        ("node_count", ctypes.c_int),
    ]


class TenFacetVec(ctypes.Structure):
    _fields_ = [
        ("values", ctypes.c_double * TEN_MAX_FACETS),
        ("set", ctypes.c_uint8 * TEN_MAX_FACETS),
        ("precision", ctypes.c_uint8 * TEN_MAX_FACETS),
        ("count", ctypes.c_uint16),
    ]


# Forward declare TenExpr for self-referential pointers
class TenExpr(ctypes.Structure):
    pass


# ── Union members ───────────────────────────────────────────

class _ScalarData(ctypes.Structure):
    _fields_ = [
        ("value", ctypes.c_double),
        ("dimension", ctypes.c_uint16),
        ("precision", ctypes.c_uint8),
    ]


class _RefData(ctypes.Structure):
    _fields_ = [
        ("hash", ctypes.c_uint8 * TEN_HASH_SIZE),
    ]


class _IdentityData(ctypes.Structure):
    _fields_ = [
        ("pubkey", ctypes.c_uint8 * TEN_MAX_PUBKEY_SIZE),
        ("keylen", ctypes.c_uint16),
    ]


class _AssertionData(ctypes.Structure):
    _fields_ = [
        ("claim", ctypes.POINTER(TenExpr)),
        ("who", ctypes.POINTER(TenExpr)),
        ("confidence", ctypes.c_double),
    ]


class _OperationData(ctypes.Structure):
    _fields_ = [
        ("verb", ctypes.c_uint16),
        ("args", ctypes.POINTER(ctypes.POINTER(TenExpr))),
        ("nargs", ctypes.c_uint16),
    ]


class _StructureData(ctypes.Structure):
    _fields_ = [
        ("members", ctypes.POINTER(ctypes.POINTER(TenExpr))),
        ("nmembers", ctypes.c_uint16),
    ]


class _PairData(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.POINTER(TenExpr)),
        ("right", ctypes.POINTER(TenExpr)),
    ]


class _NestingData(ctypes.Structure):
    _fields_ = [
        ("envelope", ctypes.POINTER(TenExpr)),
        ("payload", ctypes.POINTER(TenExpr)),
    ]


class _ExprData(ctypes.Union):
    _fields_ = [
        ("scalar", _ScalarData),
        ("ref", _RefData),
        ("identity", _IdentityData),
        ("assertion", _AssertionData),
        ("operation", _OperationData),
        ("structure", _StructureData),
        ("pair", _PairData),
        ("nesting", _NestingData),
    ]


# Complete the TenExpr definition
TenExpr._fields_ = [
    ("type", ctypes.c_int),  # ten_type_t enum
    ("data", _ExprData),
    ("facets", ctypes.POINTER(TenFacetVec)),
]


# ── Filter structures ──────────────────────────────────────

class TenFilterClause(ctypes.Structure):
    _fields_ = [
        ("dimension", ctypes.c_uint16),
        ("op", ctypes.c_int),  # enum
        ("threshold", ctypes.c_double),
    ]

# Filter comparison operators
TEN_CMP_GTE = 0
TEN_CMP_LTE = 1
TEN_CMP_EQ = 2
TEN_CMP_NEQ = 3


class TenFilter(ctypes.Structure):
    _fields_ = [
        ("clauses", ctypes.POINTER(TenFilterClause)),
        ("nclauses", ctypes.c_uint16),
    ]


# ── Library loading ─────────────────────────────────────────

def _find_libten():
    """Locate the libten shared library."""
    ext = ".dylib" if platform.system() == "Darwin" else ".so"
    name = f"libten{ext}"

    # 1. Explicit path
    env_path = os.environ.get("LIBTEN_PATH")
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return str(p)
        if p.is_dir():
            candidate = p / name
            if candidate.is_file():
                return str(candidate)

    # 2. Adjacent to this file (pip install layout)
    here = Path(__file__).resolve().parent
    candidate = here / name
    if candidate.is_file():
        return str(candidate)

    # 3. Monorepo: ../libten/build/
    candidate = here.parent / "libten" / "build" / name
    if candidate.is_file():
        return str(candidate)

    # 4. System library paths
    found = ctypes.util.find_library("ten")
    if found:
        return found

    raise OSError(
        f"Cannot find {name}. Set LIBTEN_PATH or build libten:\n"
        f"  cd libten && make\n"
        f"Searched: LIBTEN_PATH, {here}, {here.parent / 'libten' / 'build'}, system paths"
    )


def load_libten(path=None):
    """Load libten and bind all function signatures. Returns the ctypes CDLL."""
    lib_path = path or _find_libten()
    lib = ctypes.CDLL(lib_path)

    # ── Arena ───────────────────────────────────────────
    lib.ten_arena_init.argtypes = [ctypes.POINTER(TenArena), ctypes.c_size_t]
    lib.ten_arena_init.restype = ctypes.c_int

    lib.ten_arena_free.argtypes = [ctypes.POINTER(TenArena)]
    lib.ten_arena_free.restype = None

    lib.ten_arena_reset.argtypes = [ctypes.POINTER(TenArena)]
    lib.ten_arena_reset.restype = None

    lib.ten_arena_remaining.argtypes = [ctypes.POINTER(TenArena)]
    lib.ten_arena_remaining.restype = ctypes.c_size_t

    # ── Kernel type constructors ────────────────────────
    lib.ten_scalar.argtypes = [
        ctypes.POINTER(TenArena), ctypes.c_uint16,
        ctypes.c_double, ctypes.c_uint8
    ]
    lib.ten_scalar.restype = ctypes.POINTER(TenExpr)

    lib.ten_ref.argtypes = [
        ctypes.POINTER(TenArena), ctypes.c_uint8 * TEN_HASH_SIZE
    ]
    lib.ten_ref.restype = ctypes.POINTER(TenExpr)

    lib.ten_identity.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_uint16
    ]
    lib.ten_identity.restype = ctypes.POINTER(TenExpr)

    lib.ten_assertion.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(TenExpr),
        ctypes.POINTER(TenExpr), ctypes.c_double
    ]
    lib.ten_assertion.restype = ctypes.POINTER(TenExpr)

    lib.ten_operation.argtypes = [
        ctypes.POINTER(TenArena), ctypes.c_uint16,
        ctypes.POINTER(ctypes.POINTER(TenExpr)), ctypes.c_uint16
    ]
    lib.ten_operation.restype = ctypes.POINTER(TenExpr)

    lib.ten_structure.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(ctypes.POINTER(TenExpr)),
        ctypes.c_uint16
    ]
    lib.ten_structure.restype = ctypes.POINTER(TenExpr)

    # ── Composition operations ──────────────────────────
    for fn_name in ("ten_sequence", "ten_product", "ten_union", "ten_intersect"):
        fn = getattr(lib, fn_name)
        fn.argtypes = [
            ctypes.POINTER(TenArena), ctypes.POINTER(TenExpr),
            ctypes.POINTER(TenExpr)
        ]
        fn.restype = ctypes.POINTER(TenExpr)

    lib.ten_nest.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(TenExpr),
        ctypes.POINTER(TenExpr)
    ]
    lib.ten_nest.restype = ctypes.POINTER(TenExpr)

    lib.ten_project.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(TenExpr),
        ctypes.POINTER(ctypes.c_uint16), ctypes.c_uint16
    ]
    lib.ten_project.restype = ctypes.POINTER(TenExpr)

    # ── Facet operations ────────────────────────────────
    lib.ten_facet_init.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(TenExpr)
    ]
    lib.ten_facet_init.restype = ctypes.c_int

    lib.ten_facet_set.argtypes = [
        ctypes.POINTER(TenExpr), ctypes.c_uint16,
        ctypes.c_double, ctypes.c_uint8
    ]
    lib.ten_facet_set.restype = ctypes.c_int

    lib.ten_facet_get.argtypes = [ctypes.POINTER(TenExpr), ctypes.c_uint16]
    lib.ten_facet_get.restype = ctypes.c_double

    lib.ten_facet_has.argtypes = [ctypes.POINTER(TenExpr), ctypes.c_uint16]
    lib.ten_facet_has.restype = ctypes.c_bool

    lib.ten_facet_filter.argtypes = [
        ctypes.POINTER(TenExpr), ctypes.POINTER(TenFilter)
    ]
    lib.ten_facet_filter.restype = ctypes.c_bool

    # ── Serialization ───────────────────────────────────
    lib.ten_encode.argtypes = [
        ctypes.POINTER(TenExpr), ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
    ]
    lib.ten_encode.restype = ctypes.c_int

    lib.ten_decode.argtypes = [
        ctypes.POINTER(TenArena), ctypes.POINTER(ctypes.c_uint8),
        ctypes.c_size_t
    ]
    lib.ten_decode.restype = ctypes.POINTER(TenExpr)

    # ── Validation ──────────────────────────────────────
    lib.ten_is_valid.argtypes = [ctypes.POINTER(TenExpr)]
    lib.ten_is_valid.restype = ctypes.c_bool

    lib.ten_is_kernel_type.argtypes = [ctypes.c_int]
    lib.ten_is_kernel_type.restype = ctypes.c_bool

    lib.ten_is_composition_type.argtypes = [ctypes.c_int]
    lib.ten_is_composition_type.restype = ctypes.c_bool

    # ── Utility ─────────────────────────────────────────
    lib.ten_type_name.argtypes = [ctypes.c_int]
    lib.ten_type_name.restype = ctypes.c_char_p

    lib.ten_error_string.argtypes = [ctypes.c_int]
    lib.ten_error_string.restype = ctypes.c_char_p

    lib.ten_op_name.argtypes = [ctypes.c_uint16]
    lib.ten_op_name.restype = ctypes.c_char_p

    lib.ten_describe.argtypes = [
        ctypes.POINTER(TenExpr), ctypes.c_char_p, ctypes.c_size_t
    ]
    lib.ten_describe.restype = ctypes.c_int

    return lib


# Module-level lazy singleton
_lib = None

def get_lib():
    """Return the loaded libten, loading it on first call."""
    global _lib
    if _lib is None:
        _lib = load_libten()
    return _lib
