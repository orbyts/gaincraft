"""Portable reference vectors for the M2 TIFF transfer-function foundation."""

import math

import pytest

from luvix.hdr.pq import pq_decode, pq_encode


@pytest.mark.parametrize("nits", [0.0, 0.001, 0.1, 1.0, 100.0, 203.0, 1000.0, 4000.0, 10000.0])
def test_pq_roundtrip(nits: float) -> None:
    assert pq_decode(pq_encode(nits)) == pytest.approx(nits, abs=1e-7, rel=1e-8)


def test_pq_known_reference() -> None:
    assert pq_encode(100.0) == pytest.approx(0.508078, abs=1e-6)
    assert pq_encode(1000.0) == pytest.approx(0.751827, abs=1e-6)
    assert pq_encode(10000.0) == pytest.approx(1.0, abs=1e-12)


def test_pq_monotonic() -> None:
    values = [pq_encode(n) for n in [0, 1, 10, 100, 1000, 10000]]
    assert values == sorted(values)


@pytest.mark.parametrize("bad", [-1, math.inf, -math.inf, math.nan, 10001])
def test_encode_rejects_invalid(bad: float) -> None:
    with pytest.raises(ValueError):
        pq_encode(bad)


@pytest.mark.parametrize("bad", [-0.01, math.inf, math.nan, 1.01])
def test_decode_rejects_invalid(bad: float) -> None:
    with pytest.raises(ValueError):
        pq_decode(bad)
