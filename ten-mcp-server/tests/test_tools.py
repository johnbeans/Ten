"""
test_tools.py — Tests for ten-mcp-server tool functions.

These test the tool functions directly (not via MCP transport),
verifying the full encode → wire → decode round-trip through the
JSON-friendly dict interface.

Run with:  python -m pytest ten-mcp-server/tests/ -v
"""

import base64
import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from server import (
    ten_encode, ten_decode, ten_compose, ten_project,
    ten_filter, ten_describe, ten_verify,
)


# ══════════════════════════════════════════════════════════
#  ten_encode
# ══════════════════════════════════════════════════════════

class TestEncode:
    def test_scalar(self):
        result = ten_encode(
            {"scalar": {"dimension": "urgency", "value": 0.95, "precision": 16}})
        assert "wire_b64" in result
        assert result["size_bytes"] > 9
        assert result["expression"]["scalar"]["value"] == 0.95

    def test_reference(self):
        h = "ab" * 16  # 32 hex chars = 16 bytes... need 32 bytes
        h = "ab" * 32  # 64 hex chars = 32 bytes
        result = ten_encode({"reference": {"hash": h}})
        assert result["expression"]["reference"]["hash"] == h

    def test_operation_with_args(self):
        result = ten_encode({"operation": {
            "verb": "query",
            "args": [
                {"scalar": {"dimension": "urgency", "value": 0.9}},
                {"scalar": {"dimension": "cost", "value": 0.3}},
            ]
        }})
        assert result["expression"]["operation"]["verb"] == "Query"
        assert len(result["expression"]["operation"]["args"]) == 2

    def test_operation_zero_args(self):
        result = ten_encode({"operation": {"verb": "cancel", "args": []}})
        assert result["expression"]["operation"]["verb"] == "Cancel"

    def test_sequence(self):
        result = ten_encode({"sequence": {
            "left": {"scalar": {"dimension": 0, "value": 1.0}},
            "right": {"scalar": {"dimension": 1, "value": 2.0}},
        }})
        assert "sequence" in result["expression"]

    def test_nesting(self):
        result = ten_encode({"nest": {
            "envelope": {"scalar": {"dimension": 0, "value": 1.0}},
            "payload": {"reference": {"hash": "ff" * 32}},
        }})
        assert "nest" in result["expression"]

    def test_assertion(self):
        result = ten_encode({"assertion": {
            "claim": {"reference": {"hash": "aa" * 32}},
            "who": {"identity": {"pubkey": "bb" * 32}},
            "confidence": 0.95,
        }})
        assert math.isclose(
            result["expression"]["assertion"]["confidence"], 0.95)

    def test_identity(self):
        key_hex = "cd" * 32
        result = ten_encode({"identity": {"pubkey": key_hex}})
        assert result["expression"]["identity"]["pubkey"] == key_hex

    def test_structure(self):
        result = ten_encode({"structure": {
            "members": [
                {"scalar": {"dimension": 0, "value": 1.0}},
                {"scalar": {"dimension": 1, "value": 2.0}},
            ]
        }})
        assert len(result["expression"]["structure"]["members"]) == 2

    def test_with_facets(self):
        result = ten_encode(
            {"scalar": {"dimension": 0, "value": 1.0}},
            facets={"urgency": 0.95, "cost": 0.30})
        assert "_facets" in result["expression"]
        assert math.isclose(result["expression"]["_facets"]["urgency"], 0.95)

    def test_product_union_intersect(self):
        for op in ["product", "union", "intersect"]:
            result = ten_encode({op: {
                "left": {"scalar": {"dimension": 0, "value": 1.0}},
                "right": {"scalar": {"dimension": 1, "value": 2.0}},
            }})
            assert op in result["expression"]


# ══════════════════════════════════════════════════════════
#  ten_decode
# ══════════════════════════════════════════════════════════

class TestDecode:
    def test_roundtrip_b64(self):
        enc = ten_encode({"scalar": {"dimension": "urgency", "value": 0.95}})
        dec = ten_decode(wire_b64=enc["wire_b64"])
        assert dec["valid"]
        assert math.isclose(dec["expression"]["scalar"]["value"], 0.95)

    def test_roundtrip_hex(self):
        enc = ten_encode({"scalar": {"dimension": 0, "value": 42.0, "precision": 8}})
        dec = ten_decode(wire_hex=enc["wire_hex"])
        assert dec["valid"]

    def test_complex_roundtrip(self):
        original = {"nest": {
            "envelope": {"scalar": {"dimension": "urgency", "value": 0.8}},
            "payload": {"sequence": {
                "left": {"operation": {"verb": "query", "args": [
                    {"reference": {"hash": "ab" * 32}},
                ]}},
                "right": {"scalar": {"dimension": "cost", "value": 0.1}},
            }},
        }}
        enc = ten_encode(original)
        dec = ten_decode(wire_b64=enc["wire_b64"])
        assert dec["valid"]
        assert "nest" in dec["expression"]
        assert dec["description"] != ""

    def test_decode_with_facets(self):
        enc = ten_encode(
            {"scalar": {"dimension": 0, "value": 1.0}},
            facets={"urgency": 0.9, "cost": 0.4})
        dec = ten_decode(wire_b64=enc["wire_b64"])
        assert "_facets" in dec["expression"]
        assert math.isclose(dec["expression"]["_facets"]["urgency"], 0.9)


# ══════════════════════════════════════════════════════════
#  ten_compose
# ══════════════════════════════════════════════════════════

class TestCompose:
    def test_sequence_from_dicts(self):
        result = ten_compose(
            operation="sequence",
            left={"scalar": {"dimension": 0, "value": 1.0}},
            right={"scalar": {"dimension": 1, "value": 2.0}})
        assert "sequence" in result["expression"]
        assert result["size_bytes"] > 0

    def test_nest_from_dicts(self):
        result = ten_compose(
            operation="nest",
            envelope={"scalar": {"dimension": 0, "value": 1.0}},
            payload={"reference": {"hash": "ff" * 32}})
        assert "nest" in result["expression"]

    def test_compose_from_wire(self):
        """Compose two previously-encoded expressions."""
        e1 = ten_encode({"scalar": {"dimension": 0, "value": 1.0}})
        e2 = ten_encode({"scalar": {"dimension": 1, "value": 2.0}})
        result = ten_compose(
            operation="product",
            left_wire_b64=e1["wire_b64"],
            right_wire_b64=e2["wire_b64"])
        assert "product" in result["expression"]

    def test_all_composition_ops(self):
        left = {"scalar": {"dimension": 0, "value": 1.0}}
        right = {"scalar": {"dimension": 1, "value": 2.0}}
        for op in ["sequence", "product", "union", "intersect"]:
            result = ten_compose(operation=op, left=left, right=right)
            assert result["size_bytes"] > 0


# ══════════════════════════════════════════════════════════
#  ten_project
# ══════════════════════════════════════════════════════════

class TestProject:
    def test_project_by_name(self):
        enc = ten_encode(
            {"scalar": {"dimension": 0, "value": 1.0}},
            facets={"urgency": 0.9, "cost": 0.3, "privilege": 0.7})
        result = ten_project(
            wire_b64=enc["wire_b64"],
            dimensions=["urgency", "cost"])
        assert "urgency" in result["projected_facets"]
        assert "cost" in result["projected_facets"]
        assert "privilege" not in result["projected_facets"]

    def test_project_by_id(self):
        enc = ten_encode(
            {"scalar": {"dimension": 0, "value": 1.0}},
            facets={"urgency": 0.9, "cost": 0.3})
        result = ten_project(wire_b64=enc["wire_b64"], dimensions=[0])
        assert "urgency" in result["projected_facets"]
        assert "cost" not in result["projected_facets"]


# ══════════════════════════════════════════════════════════
#  ten_filter
# ══════════════════════════════════════════════════════════

class TestFilter:
    def _make_messages(self):
        """Create a batch of test messages with different urgency levels."""
        messages = []
        for urgency in [0.3, 0.6, 0.8, 0.95]:
            enc = ten_encode(
                {"scalar": {"dimension": 0, "value": 1.0}},
                facets={"urgency": urgency})
            messages.append({"wire_b64": enc["wire_b64"]})
        return messages

    def test_filter_gte(self):
        msgs = self._make_messages()
        result = ten_filter(
            expressions=msgs,
            criteria=[{"dimension": "urgency", "op": ">=", "threshold": 0.8}])
        assert result["matched"] == [2, 3]  # urgency 0.8 and 0.95
        assert result["matched_count"] == 2

    def test_filter_lte(self):
        msgs = self._make_messages()
        result = ten_filter(
            expressions=msgs,
            criteria=[{"dimension": "urgency", "op": "<=", "threshold": 0.6}])
        assert result["matched"] == [0, 1]

    def test_filter_multi_criteria(self):
        messages = []
        for u, c in [(0.9, 0.2), (0.9, 0.8), (0.3, 0.1)]:
            enc = ten_encode(
                {"scalar": {"dimension": 0, "value": 1.0}},
                facets={"urgency": u, "cost": c})
            messages.append({"wire_b64": enc["wire_b64"]})
        result = ten_filter(
            expressions=messages,
            criteria=[
                {"dimension": "urgency", "op": ">=", "threshold": 0.8},
                {"dimension": "cost", "op": "<=", "threshold": 0.5},
            ])
        assert result["matched"] == [0]  # high urgency, low cost

    def test_filter_from_dicts(self):
        """Filter can also accept expression dicts directly."""
        exprs = [
            {"scalar": {"dimension": 0, "value": 1.0}},
        ]
        # No facets → won't match any filter
        result = ten_filter(
            expressions=exprs,
            criteria=[{"dimension": "urgency", "op": ">=", "threshold": 0.0}])
        assert result["matched_count"] == 0  # no facets = no match


# ══════════════════════════════════════════════════════════
#  ten_describe
# ══════════════════════════════════════════════════════════

class TestDescribe:
    def test_describe_scalar(self):
        result = ten_describe(
            expression={"scalar": {"dimension": "urgency", "value": 0.95}})
        assert "Scalar" in result["description"]
        assert result["type"] == "Scalar"
        assert result["is_kernel"]
        assert not result["is_composition"]
        assert result["valid"]

    def test_describe_complex(self):
        enc = ten_encode({"nest": {
            "envelope": {"scalar": {"dimension": 0, "value": 1.0}},
            "payload": {"operation": {"verb": "query", "args": []}},
        }})
        result = ten_describe(wire_b64=enc["wire_b64"])
        assert "Nesting" in result["description"]
        assert result["type"] == "Nesting"
        assert result["is_composition"]


# ══════════════════════════════════════════════════════════
#  ten_verify
# ══════════════════════════════════════════════════════════

class TestVerify:
    def test_verify_valid_scalar(self):
        result = ten_verify(
            expression={"scalar": {"dimension": 0, "value": 1.0}})
        assert result["valid"]
        assert result["type"] == "Scalar"

    def test_verify_assertion(self):
        result = ten_verify(expression={"assertion": {
            "claim": {"reference": {"hash": "aa" * 32}},
            "who": {"identity": {"pubkey": "bb" * 32}},
            "confidence": 0.95,
        }})
        assert result["valid"]
        assert "assertion" in result["details"]
        assert math.isclose(result["details"]["assertion"]["confidence"], 0.95)
        assert result["details"]["assertion"]["identity_pubkey_hex"] == "bb" * 32

    def test_verify_with_facets(self):
        enc = ten_encode(
            {"scalar": {"dimension": 0, "value": 1.0}},
            facets={"urgency": 0.9})
        result = ten_verify(wire_b64=enc["wire_b64"])
        assert result["valid"]
        assert "facets" in result["details"]
        assert math.isclose(result["details"]["facets"]["urgency"], 0.9)

    def test_verify_complex_wire(self):
        enc = ten_encode({"sequence": {
            "left": {"scalar": {"dimension": 0, "value": 1.0}},
            "right": {"reference": {"hash": "cc" * 32}},
        }})
        result = ten_verify(wire_b64=enc["wire_b64"])
        assert result["valid"]
        assert result["type"] == "Sequence"
