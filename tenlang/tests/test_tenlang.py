"""
test_tenlang.py — Python test suite mirroring the C test_main.c

Run with:  python -m pytest tenlang/tests/ -v
    or:    python -m pytest tenlang/tests/test_tenlang.py -v

Requires libten shared library to be built:
    cd libten && make
"""

import math
import os
import pytest
import sys

# Ensure the repo root is on the path so tenlang can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from tenlang import (
    Arena, Expr, TenError, encode, decode,
    TEN_FACET_URGENCY, TEN_FACET_COST, TEN_FACET_PRIVILEGE,
    TEN_FACET_CONFIDENCE, TEN_FACET_TTL,
    TEN_OP_QUERY, TEN_OP_CANCEL, TEN_OP_INVOKE,
    TEN_PREC_1BIT, TEN_PREC_4BIT, TEN_PREC_8BIT,
    TEN_PREC_16BIT, TEN_PREC_32BIT, TEN_PREC_64BIT,
    TEN_TYPE_SCALAR, TEN_TYPE_REFERENCE, TEN_TYPE_IDENTITY,
    TEN_TYPE_ASSERTION, TEN_TYPE_OPERATION, TEN_TYPE_STRUCTURE,
    TEN_TYPE_SEQUENCE, TEN_TYPE_PRODUCT, TEN_TYPE_NESTING,
    TEN_TYPE_UNION, TEN_TYPE_INTERSECT,
    TEN_HASH_SIZE, TEN_MAX_FACETS,
    TEN_CMP_GTE, TEN_CMP_LTE,
)


# ── Helpers ─────────────────────────────────────────────────

def make_hash(fill: int = 0xAB) -> bytes:
    return bytes([fill] * TEN_HASH_SIZE)

def make_key(fill: int = 0xCD, length: int = 32) -> bytes:
    return bytes([fill] * length)


# ══════════════════════════════════════════════════════════
#  Arena
# ══════════════════════════════════════════════════════════

class TestArena:
    def test_init_default_size(self):
        with Arena() as a:
            assert a.remaining > 0

    def test_remaining_tracks_usage(self):
        with Arena() as a:
            before = a.remaining
            a.scalar(0, 1.0)
            assert a.remaining < before

    def test_reset_reuses_memory(self):
        with Arena() as a:
            a.scalar(0, 1.0)
            a.reset()
            # After reset, remaining should be back to full
            # (we can't check exact size, but it should be large)
            assert a.remaining > 60000  # 64KB default minus alignment

    def test_context_manager(self):
        """Arena frees cleanly via with-statement."""
        with Arena(256) as a:
            a.scalar(0, 1.0)
        # No crash = success


# ══════════════════════════════════════════════════════════
#  Kernel types
# ══════════════════════════════════════════════════════════

class TestKernelTypes:
    def test_scalar(self):
        with Arena() as a:
            s = a.scalar(TEN_FACET_URGENCY, 0.95, TEN_PREC_16BIT)
            assert s.type_tag == TEN_TYPE_SCALAR
            assert s.type_name == "Scalar"
            assert s.scalar_dimension == TEN_FACET_URGENCY
            assert math.isclose(s.scalar_value, 0.95)
            assert s.scalar_precision == TEN_PREC_16BIT
            assert s.is_kernel
            assert not s.is_composition

    def test_reference(self):
        with Arena() as a:
            h = make_hash(0xAB)
            r = a.ref(h)
            assert r.type_tag == TEN_TYPE_REFERENCE
            assert r.ref_hash == h

    def test_reference_rejects_wrong_size(self):
        with Arena() as a:
            with pytest.raises(ValueError):
                a.ref(b"\x00" * 16)  # too short

    def test_identity(self):
        with Arena() as a:
            key = make_key(0xCD)
            i = a.identity(key)
            assert i.type_tag == TEN_TYPE_IDENTITY
            assert i.identity_pubkey == key

    def test_identity_rejects_empty(self):
        with Arena() as a:
            with pytest.raises(ValueError):
                a.identity(b"")

    def test_assertion(self):
        with Arena() as a:
            claim = a.ref(make_hash())
            who = a.identity(make_key())
            asr = a.assertion(claim, who, 0.87)
            assert asr.type_tag == TEN_TYPE_ASSERTION
            assert math.isclose(asr.assertion_confidence, 0.87)
            assert asr.assertion_claim.type_tag == TEN_TYPE_REFERENCE
            assert asr.assertion_who.type_tag == TEN_TYPE_IDENTITY

    def test_assertion_rejects_bad_confidence(self):
        with Arena() as a:
            claim = a.ref(make_hash())
            who = a.identity(make_key())
            with pytest.raises(TenError):
                a.assertion(claim, who, 1.5)

    def test_operation(self):
        with Arena() as a:
            s = a.scalar(0, 1.0)
            r = a.ref(make_hash())
            op = a.operation(TEN_OP_QUERY, [r, s])
            assert op.type_tag == TEN_TYPE_OPERATION
            assert op.operation_verb == TEN_OP_QUERY
            assert op.operation_verb_name == "Query"
            assert len(op.operation_args) == 2

    def test_operation_zero_args(self):
        with Arena() as a:
            op = a.operation(TEN_OP_CANCEL)
            assert op.type_tag == TEN_TYPE_OPERATION
            assert len(op.operation_args) == 0

    def test_structure(self):
        with Arena() as a:
            s = a.scalar(0, 1.0)
            r = a.ref(make_hash())
            st = a.structure([s, r])
            assert st.type_tag == TEN_TYPE_STRUCTURE
            assert len(st.structure_members) == 2


# ══════════════════════════════════════════════════════════
#  Composition & Closure
# ══════════════════════════════════════════════════════════

class TestComposition:
    def test_sequence(self):
        with Arena() as a:
            s1 = a.scalar(0, 0.5)
            s2 = a.scalar(1, 0.9)
            seq = a.sequence(s1, s2)
            assert seq.type_tag == TEN_TYPE_SEQUENCE
            assert seq.is_valid()
            assert seq.is_composition

    def test_product(self):
        with Arena() as a:
            s1 = a.scalar(0, 0.5)
            r = a.ref(make_hash())
            prod = a.product(s1, r)
            assert prod.type_tag == TEN_TYPE_PRODUCT
            assert prod.is_valid()

    def test_nesting(self):
        with Arena() as a:
            s = a.scalar(0, 0.5)
            r = a.ref(make_hash())
            nest = a.nest(s, r)
            assert nest.type_tag == TEN_TYPE_NESTING
            assert nest.is_valid()

    def test_union(self):
        with Arena() as a:
            s1 = a.scalar(0, 0.5)
            s2 = a.scalar(1, 0.9)
            u = a.union(s1, s2)
            assert u.type_tag == TEN_TYPE_UNION
            assert u.is_valid()

    def test_intersect(self):
        with Arena() as a:
            s1 = a.scalar(0, 0.5)
            s2 = a.scalar(1, 0.9)
            i = a.intersect(s1, s2)
            assert i.type_tag == TEN_TYPE_INTERSECT
            assert i.is_valid()

    def test_closure_sequence_of_sequences(self):
        with Arena() as a:
            s1 = a.scalar(0, 0.5)
            s2 = a.scalar(1, 0.9)
            r = a.ref(make_hash())
            seq1 = a.sequence(s1, s2)
            prod = a.product(s1, r)
            seq2 = a.sequence(seq1, prod)
            assert seq2.is_valid()

    def test_closure_three_deep_nesting(self):
        with Arena() as a:
            s1 = a.scalar(0, 0.5)
            s2 = a.scalar(1, 0.9)
            r = a.ref(make_hash())
            deep = a.nest(s1, a.nest(s2, a.nest(r, s1)))
            assert deep.is_valid()

    def test_left_right_access(self):
        with Arena() as a:
            s1 = a.scalar(0, 1.0)
            s2 = a.scalar(1, 2.0)
            seq = a.sequence(s1, s2)
            assert seq.left.type_tag == TEN_TYPE_SCALAR
            assert seq.right.type_tag == TEN_TYPE_SCALAR

    def test_envelope_payload_access(self):
        with Arena() as a:
            env = a.scalar(0, 1.0)
            pay = a.ref(make_hash())
            nest = a.nest(env, pay)
            assert nest.envelope.type_tag == TEN_TYPE_SCALAR
            assert nest.payload.type_tag == TEN_TYPE_REFERENCE


# ══════════════════════════════════════════════════════════
#  Facet Vectors
# ══════════════════════════════════════════════════════════

class TestFacets:
    def test_set_get_roundtrip(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.95)
            msg.set_facet(TEN_FACET_COST, 0.30)
            assert math.isclose(msg.get_facet(TEN_FACET_URGENCY), 0.95)
            assert math.isclose(msg.get_facet(TEN_FACET_COST), 0.30)

    def test_has_facet(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.95)
            assert msg.has_facet(TEN_FACET_URGENCY)
            assert not msg.has_facet(TEN_FACET_PRIVILEGE)

    def test_unset_returns_zero(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.init_facets()
            assert msg.get_facet(TEN_FACET_TTL) == 0.0

    def test_filter_passes(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.95)
            msg.set_facet(TEN_FACET_COST, 0.30)
            assert msg.matches_filter([
                (TEN_FACET_URGENCY, TEN_CMP_GTE, 0.8),
            ])

    def test_filter_fails(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.95)
            assert not msg.matches_filter([
                (TEN_FACET_URGENCY, TEN_CMP_GTE, 0.99),
            ])

    def test_filter_multi_clause(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.95)
            msg.set_facet(TEN_FACET_COST, 0.30)
            assert msg.matches_filter([
                (TEN_FACET_URGENCY, TEN_CMP_GTE, 0.5),
                (TEN_FACET_COST, TEN_CMP_LTE, 0.5),
            ])


# ══════════════════════════════════════════════════════════
#  Projection
# ══════════════════════════════════════════════════════════

class TestProjection:
    def test_preserves_requested(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.9)
            msg.set_facet(TEN_FACET_COST, 0.3)
            msg.set_facet(TEN_FACET_PRIVILEGE, 0.7)
            proj = a.project(msg, [TEN_FACET_URGENCY, TEN_FACET_COST])
            assert proj.has_facet(TEN_FACET_URGENCY)
            assert proj.has_facet(TEN_FACET_COST)
            assert math.isclose(proj.get_facet(TEN_FACET_URGENCY), 0.9)

    def test_drops_unrequested(self):
        with Arena() as a:
            msg = a.scalar(0, 1.0)
            msg.set_facet(TEN_FACET_URGENCY, 0.9)
            msg.set_facet(TEN_FACET_PRIVILEGE, 0.7)
            proj = a.project(msg, [TEN_FACET_URGENCY])
            assert not proj.has_facet(TEN_FACET_PRIVILEGE)


# ══════════════════════════════════════════════════════════
#  Validation
# ══════════════════════════════════════════════════════════

class TestValidation:
    def test_valid_scalar(self):
        with Arena() as a:
            assert a.scalar(0, 1.0).is_valid()

    def test_valid_sequence(self):
        with Arena() as a:
            seq = a.sequence(a.scalar(0, 1.0), a.scalar(1, 0.5))
            assert seq.is_valid()


# ══════════════════════════════════════════════════════════
#  Utility
# ══════════════════════════════════════════════════════════

class TestUtility:
    def test_type_names(self):
        with Arena() as a:
            assert a.scalar(0, 1.0).type_name == "Scalar"
            s1 = a.scalar(0, 1.0)
            s2 = a.scalar(1, 2.0)
            assert a.sequence(s1, s2).type_name == "Sequence"

    def test_describe(self):
        with Arena() as a:
            h = make_hash(0xAA)
            k = make_key(0xBB)
            ref = a.ref(h)
            ident = a.identity(k)
            asr = a.assertion(ref, ident, 0.95)
            msg = a.nest(a.scalar(0, 0.9, TEN_PREC_16BIT), asr)
            desc = msg.describe()
            assert "Nesting" in desc
            assert "Scalar" in desc
            assert "Assertion" in desc


# ══════════════════════════════════════════════════════════
#  Serialization (encode/decode round-trip)
# ══════════════════════════════════════════════════════════

class TestSerialization:
    def test_scalar_64bit(self):
        with Arena() as a:
            s = a.scalar(TEN_FACET_URGENCY, 0.95, TEN_PREC_64BIT)
            wire = encode(s)
            assert len(wire) > 9  # at least envelope
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_SCALAR
            assert d.scalar_dimension == TEN_FACET_URGENCY
            assert d.scalar_precision == TEN_PREC_64BIT
            assert math.isclose(d.scalar_value, 0.95)

    def test_scalar_8bit(self):
        with Arena() as a:
            wire = encode(a.scalar(TEN_FACET_COST, 42.0, TEN_PREC_8BIT))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.scalar_precision == TEN_PREC_8BIT
            assert math.isclose(d.scalar_value, 42.0)

    def test_scalar_1bit(self):
        with Arena() as a:
            wire = encode(a.scalar(0, 1.0, TEN_PREC_1BIT))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.scalar_value == 1.0

    def test_reference(self):
        h = make_hash(0xAB)
        with Arena() as a:
            wire = encode(a.ref(h))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_REFERENCE
            assert d.ref_hash == h

    def test_identity(self):
        key = make_key(0xCD)
        with Arena() as a:
            wire = encode(a.identity(key))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_IDENTITY
            assert d.identity_pubkey == key

    def test_assertion(self):
        with Arena() as a:
            claim = a.ref(make_hash(0x11))
            who = a.identity(make_key(0x22))
            wire = encode(a.assertion(claim, who, 0.87))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_ASSERTION
            assert math.isclose(d.assertion_confidence, 0.87)
            assert d.assertion_claim.type_tag == TEN_TYPE_REFERENCE
            assert d.assertion_who.type_tag == TEN_TYPE_IDENTITY

    def test_operation_with_args(self):
        with Arena() as a:
            s1 = a.scalar(0, 100.0, TEN_PREC_32BIT)
            s2 = a.scalar(1, 200.0, TEN_PREC_32BIT)
            wire = encode(a.operation(TEN_OP_QUERY, [s1, s2]))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_OPERATION
            assert d.operation_verb == TEN_OP_QUERY
            assert len(d.operation_args) == 2

    def test_operation_zero_args(self):
        with Arena() as a:
            wire = encode(a.operation(TEN_OP_CANCEL))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.operation_verb == TEN_OP_CANCEL
            assert len(d.operation_args) == 0

    def test_structure(self):
        with Arena() as a:
            m1 = a.scalar(0, 1.0, TEN_PREC_8BIT)
            m2 = a.scalar(1, 2.0, TEN_PREC_8BIT)
            wire = encode(a.structure([m1, m2]))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_STRUCTURE
            assert len(d.structure_members) == 2

    def test_sequence(self):
        with Arena() as a:
            wire = encode(a.sequence(
                a.scalar(0, 1.0, TEN_PREC_8BIT),
                a.scalar(1, 2.0, TEN_PREC_8BIT)))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_SEQUENCE
            assert d.left.type_tag == TEN_TYPE_SCALAR
            assert d.right.type_tag == TEN_TYPE_SCALAR

    def test_nesting(self):
        with Arena() as a:
            wire = encode(a.nest(
                a.scalar(0, 1.0, TEN_PREC_8BIT),
                a.ref(make_hash(0xFF))))
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_NESTING
            assert d.envelope.type_tag == TEN_TYPE_SCALAR
            assert d.payload.type_tag == TEN_TYPE_REFERENCE

    def test_product_union_intersect(self):
        with Arena() as a:
            s1 = a.scalar(0, 1.0, TEN_PREC_8BIT)
            s2 = a.scalar(1, 2.0, TEN_PREC_8BIT)

            for compose_fn, expected_type in [
                (a.product, TEN_TYPE_PRODUCT),
                (a.union, TEN_TYPE_UNION),
                (a.intersect, TEN_TYPE_INTERSECT),
            ]:
                wire = encode(compose_fn(s1, s2))
                with Arena() as a2:
                    d = decode(a2, wire)
                    assert d.type_tag == expected_type

    def test_facet_vector_roundtrip(self):
        with Arena() as a:
            s = a.scalar(0, 5.0, TEN_PREC_16BIT)
            s.set_facet(TEN_FACET_URGENCY, 0.95)
            s.set_facet(TEN_FACET_COST, 0.30)
            wire = encode(s)
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.has_facet(TEN_FACET_URGENCY)
            assert d.has_facet(TEN_FACET_COST)
            assert math.isclose(d.get_facet(TEN_FACET_URGENCY), 0.95)
            assert math.isclose(d.get_facet(TEN_FACET_COST), 0.30)
            assert not d.has_facet(TEN_FACET_PRIVILEGE)

    def test_complex_nested(self):
        with Arena() as a:
            ref = a.ref(make_hash(0xAA))
            ident = a.identity(make_key(0xBB))
            asr = a.assertion(ref, ident, 0.99)
            s1 = a.scalar(TEN_FACET_URGENCY, 0.8, TEN_PREC_16BIT)
            seq = a.sequence(asr, s1)
            env = a.scalar(TEN_FACET_COST, 0.1, TEN_PREC_8BIT)
            msg = a.nest(env, seq)
            wire = encode(msg)
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.type_tag == TEN_TYPE_NESTING
            assert d.envelope.type_tag == TEN_TYPE_SCALAR
            assert d.payload.type_tag == TEN_TYPE_SEQUENCE
            assert d.payload.left.type_tag == TEN_TYPE_ASSERTION
            assert d.payload.right.type_tag == TEN_TYPE_SCALAR

    def test_wire_magic_header(self):
        with Arena() as a:
            wire = encode(a.scalar(0, 1.0, TEN_PREC_8BIT))
            assert wire[:4] == b"Ten:"
            assert wire[4] == 1  # version

    def test_decode_rejects_bad_magic(self):
        bad = b"Bad!" + b"\x01" + b"\x00" * 60
        with Arena() as a:
            with pytest.raises(TenError):
                decode(a, bad)

    def test_encode_rejects_tiny_buffer(self):
        with Arena() as a:
            s = a.scalar(0, 1.0, TEN_PREC_8BIT)
            with pytest.raises(TenError):
                encode(s, bufsize=5)

    def test_decoded_passes_validation(self):
        with Arena() as a:
            seq = a.sequence(
                a.scalar(0, 1.0, TEN_PREC_8BIT),
                a.scalar(1, 2.0, TEN_PREC_16BIT))
            wire = encode(seq)
        with Arena() as a2:
            d = decode(a2, wire)
            assert d.is_valid()
