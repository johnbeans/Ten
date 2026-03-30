"""
test_api.py — Tests for the Ten REST API endpoints.

Uses FastAPI's TestClient to exercise every endpoint without
starting a real HTTP server.

Run with:  python -m pytest ten_rest_api/tests/ -v
"""

import base64
import math

import pytest
from fastapi.testclient import TestClient

from ten_rest_api.app import app

client = TestClient(app)


# ══════════════════════════════════════════════════════════
#  Health check
# ══════════════════════════════════════════════════════════

class TestHealth:
    def test_health(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert data["service"] == "ten-rest-api"


# ══════════════════════════════════════════════════════════
#  /v1/encode
# ══════════════════════════════════════════════════════════

class TestEncode:
    def test_scalar(self):
        r = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 42.0, "precision": 64}}
        })
        assert r.status_code == 200
        data = r.json()
        assert "wire_b64" in data
        assert data["size_bytes"] > 0
        assert data["expression"]["scalar"]["value"] == 42.0

    def test_reference(self):
        h = "ab" * 32  # SHA-256 = 32 bytes = 64 hex chars
        r = client.post("/v1/encode", json={
            "expression": {"reference": {"hash": h}}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["expression"]["reference"]["hash"] == h

    def test_operation_with_args(self):
        r = client.post("/v1/encode", json={
            "expression": {"operation": {"verb": "query", "args": [
                {"scalar": {"dimension": 0, "value": 1.0}}
            ]}}
        })
        assert r.status_code == 200
        assert r.json()["expression"]["operation"]["verb"].lower() == "query"

    def test_operation_no_args(self):
        r = client.post("/v1/encode", json={
            "expression": {"operation": {"verb": "cancel"}}
        })
        assert r.status_code == 200

    def test_nesting(self):
        r = client.post("/v1/encode", json={
            "expression": {"nest": {
                "envelope": {"operation": {"verb": "query"}},
                "payload": {"scalar": {"dimension": 0, "value": 99.0}},
            }}
        })
        assert r.status_code == 200
        data = r.json()
        assert "nest" in data["expression"]

    def test_assertion(self):
        r = client.post("/v1/encode", json={
            "expression": {"assertion": {
                "claim": {"scalar": {"dimension": 0, "value": 1.0}},
                "who": {"identity": {"pubkey": "cc" * 32}},
                "confidence": 0.87,
            }}
        })
        assert r.status_code == 200
        data = r.json()["expression"]["assertion"]
        assert abs(data["confidence"] - 0.87) < 0.01

    def test_identity(self):
        r = client.post("/v1/encode", json={
            "expression": {"identity": {"pubkey": "dd" * 32}}
        })
        assert r.status_code == 200

    def test_structure(self):
        r = client.post("/v1/encode", json={
            "expression": {"structure": {"members": [
                {"scalar": {"dimension": 0, "value": 1.0}},
                {"scalar": {"dimension": 1, "value": 2.0}},
            ]}}
        })
        assert r.status_code == 200
        assert len(r.json()["expression"]["structure"]["members"]) == 2

    def test_with_facets(self):
        r = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}},
            "facets": {"urgency": 0.9, "cost": 50.0}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["expression"]["_facets"]["urgency"] == pytest.approx(0.9)
        assert data["expression"]["_facets"]["cost"] == pytest.approx(50.0)

    def test_sequence(self):
        r = client.post("/v1/encode", json={
            "expression": {"sequence": {
                "left": {"scalar": {"dimension": 0, "value": 1.0}},
                "right": {"scalar": {"dimension": 1, "value": 2.0}},
            }}
        })
        assert r.status_code == 200
        assert "sequence" in r.json()["expression"]

    def test_product_union_intersect(self):
        for op in ("product", "union", "intersect"):
            r = client.post("/v1/encode", json={
                "expression": {op: {
                    "left": {"scalar": {"dimension": 0, "value": 1.0}},
                    "right": {"scalar": {"dimension": 1, "value": 2.0}},
                }}
            })
            assert r.status_code == 200, f"{op} failed"
            assert op in r.json()["expression"]

    def test_invalid_expression(self):
        r = client.post("/v1/encode", json={
            "expression": {"bogus": {"stuff": 1}}
        })
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════
#  /v1/decode
# ══════════════════════════════════════════════════════════

class TestDecode:
    def _encode_scalar(self):
        r = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 42.0, "precision": 64}}
        })
        return r.json()

    def test_roundtrip_b64(self):
        enc = self._encode_scalar()
        r = client.post("/v1/decode", json={"wire_b64": enc["wire_b64"]})
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is True
        assert data["expression"]["scalar"]["value"] == 42.0

    def test_roundtrip_hex(self):
        enc = self._encode_scalar()
        r = client.post("/v1/decode", json={"wire_hex": enc["wire_hex"]})
        assert r.status_code == 200
        assert r.json()["expression"]["scalar"]["value"] == 42.0

    def test_complex_roundtrip(self):
        enc = client.post("/v1/encode", json={
            "expression": {"sequence": {
                "left": {"operation": {"verb": "query", "args": [
                    {"scalar": {"dimension": 0, "value": 1.0}}
                ]}},
                "right": {"assertion": {
                    "claim": {"scalar": {"dimension": 1, "value": 2.0}},
                    "who": {"identity": {"pubkey": "aa" * 32}},
                    "confidence": 0.95,
                }},
            }}
        }).json()
        r = client.post("/v1/decode", json={"wire_b64": enc["wire_b64"]})
        assert r.status_code == 200
        assert r.json()["valid"] is True
        assert "sequence" in r.json()["expression"]

    def test_decode_with_facets(self):
        enc = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}},
            "facets": {"urgency": 0.9}
        }).json()
        r = client.post("/v1/decode", json={"wire_b64": enc["wire_b64"]})
        assert r.status_code == 200
        assert r.json()["expression"]["_facets"]["urgency"] == pytest.approx(0.9)

    def test_missing_input(self):
        r = client.post("/v1/decode", json={})
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════
#  /v1/compose
# ══════════════════════════════════════════════════════════

class TestCompose:
    def test_sequence_from_dicts(self):
        r = client.post("/v1/compose", json={
            "operation": "sequence",
            "left": {"scalar": {"dimension": 0, "value": 1.0}},
            "right": {"scalar": {"dimension": 1, "value": 2.0}},
        })
        assert r.status_code == 200
        assert "sequence" in r.json()["expression"]

    def test_nest_from_dicts(self):
        r = client.post("/v1/compose", json={
            "operation": "nest",
            "envelope": {"operation": {"verb": "query"}},
            "payload": {"scalar": {"dimension": 0, "value": 1.0}},
        })
        assert r.status_code == 200
        assert "nest" in r.json()["expression"]

    def test_compose_from_wire(self):
        e1 = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}}
        }).json()
        e2 = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 1, "value": 2.0}}
        }).json()
        r = client.post("/v1/compose", json={
            "operation": "product",
            "left_wire_b64": e1["wire_b64"],
            "right_wire_b64": e2["wire_b64"],
        })
        assert r.status_code == 200
        assert "product" in r.json()["expression"]

    def test_all_composition_ops(self):
        for op in ("sequence", "product", "union", "intersect"):
            r = client.post("/v1/compose", json={
                "operation": op,
                "left": {"scalar": {"dimension": 0, "value": 1.0}},
                "right": {"scalar": {"dimension": 1, "value": 2.0}},
            })
            assert r.status_code == 200, f"{op} failed"

    def test_invalid_operation(self):
        r = client.post("/v1/compose", json={
            "operation": "bogus",
            "left": {"scalar": {"dimension": 0, "value": 1.0}},
            "right": {"scalar": {"dimension": 1, "value": 2.0}},
        })
        assert r.status_code == 400


# ══════════════════════════════════════════════════════════
#  /v1/project
# ══════════════════════════════════════════════════════════

class TestProject:
    def test_project_by_name(self):
        enc = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}},
            "facets": {"urgency": 0.9, "cost": 50.0, "ttl": 300.0}
        }).json()
        r = client.post("/v1/project", json={
            "wire_b64": enc["wire_b64"],
            "dimensions": ["urgency", "cost"],
        })
        assert r.status_code == 200
        facets = r.json()["projected_facets"]
        assert "urgency" in facets
        assert "cost" in facets
        assert "ttl" not in facets

    def test_project_by_id(self):
        enc = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}},
            "facets": {"urgency": 0.9, "cost": 50.0}
        }).json()
        r = client.post("/v1/project", json={
            "wire_b64": enc["wire_b64"],
            "dimensions": [0],  # urgency = dimension 0
        })
        assert r.status_code == 200
        assert "urgency" in r.json()["projected_facets"]


# ══════════════════════════════════════════════════════════
#  /v1/filter
# ══════════════════════════════════════════════════════════

class TestFilter:
    def _make_expressions(self):
        """Create 3 expressions with different urgency levels."""
        exprs = []
        for urg in (0.3, 0.6, 0.9):
            enc = client.post("/v1/encode", json={
                "expression": {"scalar": {"dimension": 0, "value": 1.0}},
                "facets": {"urgency": urg}
            }).json()
            exprs.append({"wire_b64": enc["wire_b64"]})
        return exprs

    def test_filter_gte(self):
        exprs = self._make_expressions()
        r = client.post("/v1/filter", json={
            "expressions": exprs,
            "criteria": [{"dimension": "urgency", "op": ">=", "threshold": 0.5}]
        })
        assert r.status_code == 200
        data = r.json()
        assert data["matched"] == [1, 2]
        assert data["matched_count"] == 2
        assert data["total"] == 3

    def test_filter_lte(self):
        exprs = self._make_expressions()
        r = client.post("/v1/filter", json={
            "expressions": exprs,
            "criteria": [{"dimension": "urgency", "op": "<=", "threshold": 0.5}]
        })
        assert r.status_code == 200
        assert r.json()["matched"] == [0]

    def test_filter_from_dicts(self):
        r = client.post("/v1/filter", json={
            "expressions": [
                {"scalar": {"dimension": 0, "value": 1.0}},
            ],
            "criteria": [{"dimension": "urgency", "op": ">=", "threshold": 0.0}]
        })
        assert r.status_code == 200

    def test_filter_multi_criteria(self):
        enc = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}},
            "facets": {"urgency": 0.9, "cost": 50.0}
        }).json()
        r = client.post("/v1/filter", json={
            "expressions": [{"wire_b64": enc["wire_b64"]}],
            "criteria": [
                {"dimension": "urgency", "op": ">=", "threshold": 0.8},
                {"dimension": "cost", "op": "<=", "threshold": 100.0},
            ]
        })
        assert r.status_code == 200
        assert r.json()["matched"] == [0]


# ══════════════════════════════════════════════════════════
#  /v1/describe
# ══════════════════════════════════════════════════════════

class TestDescribe:
    def test_describe_scalar(self):
        r = client.post("/v1/describe", json={
            "expression": {"scalar": {"dimension": 0, "value": 42.0}}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["type"] == "Scalar"
        assert data["is_kernel"] is True
        assert data["valid"] is True

    def test_describe_complex(self):
        r = client.post("/v1/describe", json={
            "expression": {"sequence": {
                "left": {"operation": {"verb": "query"}},
                "right": {"scalar": {"dimension": 0, "value": 1.0}},
            }}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["is_composition"] is True
        assert len(data["description"]) > 0


# ══════════════════════════════════════════════════════════
#  /v1/verify
# ══════════════════════════════════════════════════════════

class TestVerify:
    def test_verify_valid_scalar(self):
        r = client.post("/v1/verify", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is True
        assert data["type"] == "Scalar"

    def test_verify_assertion(self):
        r = client.post("/v1/verify", json={
            "expression": {"assertion": {
                "claim": {"scalar": {"dimension": 0, "value": 1.0}},
                "who": {"identity": {"pubkey": "bb" * 32}},
                "confidence": 0.95,
            }}
        })
        assert r.status_code == 200
        data = r.json()
        assert data["valid"] is True
        assert "assertion" in data["details"]
        assert data["details"]["assertion"]["identity_pubkey_hex"] == "bb" * 32

    def test_verify_with_facets(self):
        enc = client.post("/v1/encode", json={
            "expression": {"scalar": {"dimension": 0, "value": 1.0}},
            "facets": {"urgency": 0.8}
        }).json()
        r = client.post("/v1/verify", json={"wire_b64": enc["wire_b64"]})
        assert r.status_code == 200
        assert r.json()["details"]["facets"]["urgency"] == pytest.approx(0.8)

    def test_verify_complex_wire(self):
        enc = client.post("/v1/encode", json={
            "expression": {"nest": {
                "envelope": {"operation": {"verb": "query"}},
                "payload": {"structure": {"members": [
                    {"scalar": {"dimension": 0, "value": 1.0}},
                    {"scalar": {"dimension": 1, "value": 2.0}},
                ]}},
            }}
        }).json()
        r = client.post("/v1/verify", json={"wire_b64": enc["wire_b64"]})
        assert r.status_code == 200
        assert r.json()["valid"] is True
