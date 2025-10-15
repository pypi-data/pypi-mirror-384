# test_simulator.py
# Pytest unit tests for the MINFLUX-like simulator.
import math
from pathlib import Path

import numpy as np
import h5py
import pytest

from simflux import simflux as sim

# ------------------------------
# Parsing helpers
# ------------------------------

def _assert_section_equal_numeric_or_str(section_a, section_b):
    """
    Compare two dicts of arrays, using allclose for numeric dtypes and exact
    equality for string/object arrays.
    """
    assert section_a.keys() == section_b.keys()
    for key in section_a.keys():
        a = section_a[key]
        b = section_b[key]
        # Fast shape check first
        assert a.shape == b.shape, f"shape mismatch for {key}: {a.shape} vs {b.shape}"

        # Decide comparator by dtype
        if getattr(a, "dtype", None) is not None:
            kind = a.dtype.kind
            if kind in ("f", "c"):  # float or complex
                np.testing.assert_allclose(a, b, rtol=1e-7, atol=0, equal_nan=True, err_msg=f"mismatch in {key}")
            elif kind in ("i", "u", "b"):  # int/uint/bool
                np.testing.assert_array_equal(a, b, err_msg=f"mismatch in {key}")
            elif kind in ("U", "S", "O"):  # unicode, bytes, object (e.g. strings)
                np.testing.assert_array_equal(a, b, err_msg=f"mismatch in {key}")
            else:
                # Fallback: exact compare
                np.testing.assert_array_equal(a, b, err_msg=f"mismatch in {key}")
        else:
            # Non-array payloads—compare directly
            assert a == b, f"non-array mismatch in {key}"


def test_parse_mix_equal_weights():
    out = sim.parse_mix("polygon:8,polygon:5,polygon:3")
    # Three entries, equal weights
    assert len(out) == 3
    sides, weights = zip(*out)
    assert set(sides) == {8, 5, 3}
    assert pytest.approx(sum(weights), rel=0, abs=1e-12) == 1.0
    # All equal → each 1/3
    assert all(pytest.approx(w, rel=0, abs=1e-12) == 1.0 / 3.0 for w in weights)


def test_parse_mix_with_weights_normalised():
    out = sim.parse_mix("polygon:4@2.0, polygon:6@1.0")
    sides, weights = zip(*out)
    assert sides == (4, 6)
    s = sum(weights)
    assert pytest.approx(s, rel=0, abs=1e-12) == 1.0
    # Ratio 2:1 → 2/3 and 1/3
    assert pytest.approx(weights[0], rel=0, abs=1e-12) == 2.0 / 3.0
    assert pytest.approx(weights[1], rel=0, abs=1e-12) == 1.0 / 3.0


@pytest.mark.parametrize("bad", ["", "polygon", "hexagon:6"])
def test_parse_mix_invalid(bad):
    with pytest.raises(ValueError):
        sim.parse_mix(bad)


def test_parse_oligomers_defaults_and_names_merge():
    # Default: None / empty → mono
    assert sim.parse_oligomers(None) == {1: 1.0}
    assert sim.parse_oligomers("") == {1: 1.0}
    # Names and duplicates should merge, then normalise
    pmf = sim.parse_oligomers("mono:1,di:1,2:1,tri:2")
    # di appeared twice (as name and number) → merged weight 2
    # tri weight 2; mono weight 1; sum 5 → probs 0.2, 0.4, 0.4
    assert set(pmf.keys()) == {1, 2, 3}
    assert pytest.approx(pmf[1]) == 1 / 5
    assert pytest.approx(pmf[2]) == 2 / 5
    assert pytest.approx(pmf[3]) == 2 / 5


# ------------------------------
# Geometry helpers
# ------------------------------

def test_gen_poly_edge_aligned_radius_and_count():
    sides = 6
    r = 3.0
    pts = sim.gen_poly_edge_aligned(sides, r)
    assert pts.shape == (sides, 2)
    # Every vertex should be at distance r (within numerical tolerance).
    d = np.sqrt(np.sum(pts**2, axis=1))
    assert np.allclose(d, r, atol=1e-12)


def test_edge_share_distance_square():
    # For a square of circumradius 1, spacing is 2 * cos(pi/4) = sqrt(2).
    dist = sim.edge_share_distance(4, 1.0)
    assert pytest.approx(dist) == math.sqrt(2.0)


def test_grid_node_offsets_centered_and_shape():
    rows, cols, sep = 3, 2, 10.0
    off = sim.grid_node_offsets(rows, cols, sep)
    assert off.shape == (rows * cols, 2)
    # Mean should be ~0 for a centred lattice.
    assert np.allclose(off.mean(axis=0), 0.0, atol=1e-12)


def test_grid_effective_R():
    rows, cols, sep = 2, 2, 10.0
    off = sim.grid_node_offsets(rows, cols, sep)
    R = sim.grid_effective_R(off)
    # Coordinates will be ±5, ±5 → radius = sqrt(5^2 + 5^2)
    assert pytest.approx(R) == math.sqrt(50.0)


# ------------------------------
# Placement under constraints
# ------------------------------

def test_generate_oligomeric_centroids_respects_hardcore_and_seed():
    np.random.seed(123)
    mix = [(6, 1.0)]
    olig = {1: 1.0}
    tbl = sim.generate_oligomeric_centroids(
        xrange=(0, 50), yrange=(0, 50),
        poisson_mean_groups=10,
        radius=2.0,
        geom_dist=mix,
        oligomer_pmf=olig,
        hardcore_radius=4.0,  # explicit to test auditing
        seed=42,
    )
    xy = tbl["position"]
    gids = tbl["group_id"]
    # Verify no inter-group violations below hardcore
    viol = sim.audit_hardcore_filtered(xy, gids, 4.0)
    assert len(viol) == 0
    # Deterministic with same seed call
    tbl2 = sim.generate_oligomeric_centroids(
        xrange=(0, 50), yrange=(0, 50),
        poisson_mean_groups=10,
        radius=2.0,
        geom_dist=mix,
        oligomer_pmf=olig,
        hardcore_radius=4.0,
        seed=42,
    )
    np.testing.assert_allclose(tbl["position"], tbl2["position"])
    assert np.array_equal(tbl["group_id"], tbl2["group_id"])
    assert np.array_equal(tbl["sides"], tbl2["sides"])


def test_generate_grid_centroids_respects_hardcore_and_seed():
    np.random.seed(123)
    R = 5.0
    tbl = sim.generate_grid_centroids(
        xrange=(0, 100), yrange=(0, 100),
        poisson_mean_groups=12, R=R, hardcore_radius=2 * R, seed=7
    )
    xy = tbl["position"]
    gids = tbl["group_id"]
    viol = sim.audit_hardcore_filtered(xy, gids, 2 * R)
    assert len(viol) == 0
    # Repeatability
    tbl2 = sim.generate_grid_centroids(
        xrange=(0, 100), yrange=(0, 100),
        poisson_mean_groups=12, R=R, hardcore_radius=2 * R, seed=7
    )
    np.testing.assert_allclose(tbl["position"], tbl2["position"])
    assert np.array_equal(tbl["theta"], tbl2["theta"])


# ------------------------------
# Measurements / membrane
# ------------------------------

def test_generate_measurements_reproducible_with_seed():
    np.random.seed(999)
    pos = np.array([[0.0, 0.0], [1.0, 1.0]])
    m1 = sim.generate_measurements(pos, poisson_mean=5.0, uncertainty_std=0.1)
    np.random.seed(999)
    m2 = sim.generate_measurements(pos, poisson_mean=5.0, uncertainty_std=0.1)
    assert m1.shape == m2.shape
    np.testing.assert_allclose(m1, m2)


def test_apply_membrane_none_and_callable():
    pts = np.array([[0.0, 0.0], [1.0, 2.0]])
    # None → z zeros, shape preserved to (N,3)
    out = sim.apply_membrane(pts, membrane_function=None)
    assert out.shape == (2, 3)
    assert np.allclose(out[:, 2], 0.0, atol=0)

    # Simple z = x + 2y
    def membrane(x, y):
        return x + 2.0 * y

    out2 = sim.apply_membrane(pts, membrane_function=membrane)
    assert np.allclose(out2[:, 2], np.array([0.0, 1.0 + 2 * 2.0]))


# ------------------------------
# Audit
# ------------------------------

def test_audit_hardcore_filtered_no_pairs_for_single_group():
    xy = np.array([[0.0, 0.0], [1.0, 0.0]])
    gids = np.array([1, 1], dtype=int)  # same group
    out = sim.audit_hardcore_filtered(xy, gids, hardcore=2.0)
    assert out == []


# ------------------------------
# Simulation cores
# ------------------------------

def test_simulate_poly_shapes_and_seed(tmp_path: Path):
    np.random.seed(1234)
    # Small config to keep runtime low
    out = sim.simulate_poly(
        filename=None,
        xrange=(0, 40),
        yrange=(0, 40),
        centroid_mean_groups=4,
        radius=2.5,
        geom_mix=[(5, 1.0)],
        oligomer_pmf={1: 1.0},
        p=0.9,
        q=0.9,
        measured=3,
        gt_uncertainty=0.0,
        ms_uncertainty=0.2,
        clutter_fraction=0.0,
        membrane_function=None,
        enforce_shared_edge=True,
        store_edges=False,
        seed=101,
    )
    # Basic schema checks
    for k in ("centroid", "emitter", "observed", "clutter", "edges"):
        assert k in out
    assert out["centroid"]["position"].shape[1] == 2
    assert out["emitter"]["position"].shape[1] == 2
    assert out["observed"]["position"].shape[1] == 2

    # Determinism under seed
    out2 = sim.simulate_poly(
        filename=None,
        xrange=(0, 40), yrange=(0, 40),
        centroid_mean_groups=4,
        radius=2.5,
        geom_mix=[(5, 1.0)],
        oligomer_pmf={1: 1.0},
        p=0.9, q=0.9, measured=3,
        gt_uncertainty=0.0, ms_uncertainty=0.2,
        clutter_fraction=0.0, membrane_function=None,
        enforce_shared_edge=True, store_edges=False,
        seed=101,
    )
    _assert_section_equal_numeric_or_str(out["centroid"], out2["centroid"])
    _assert_section_equal_numeric_or_str(out["emitter"], out2["emitter"])
    _assert_section_equal_numeric_or_str(out["observed"], out2["observed"])


def test_simulate_grid_shapes_and_seed(tmp_path: Path):
    out = sim.simulate_grid(
        filename=None,
        xrange=(0, 60),
        yrange=(0, 60),
        centroid_mean_groups=3,
        rows=2,
        cols=3,
        sep=8.0,
        p=0.8,
        q=0.8,
        measured=4,
        gt_uncertainty=0.0,
        ms_uncertainty=0.25,
        clutter_fraction=0.0,
        membrane_function=None,
        seed=202,
    )
    assert out["centroid"]["position"].shape[1] == 2
    # Emitters should be rows*cols per grid centroid
    C = len(out["centroid"]["id"])
    assert len(out["emitter"]["id"]) in (0, C * 2 * 3)  # p<1 may produce zero labelled but all emitters exist
    # Determinism under same seed
    out2 = sim.simulate_grid(
        filename=None,
        xrange=(0, 60), yrange=(0, 60),
        centroid_mean_groups=3,
        rows=2, cols=3, sep=8.0,
        p=0.8, q=0.8, measured=4,
        gt_uncertainty=0.0, ms_uncertainty=0.25,
        clutter_fraction=0.0, membrane_function=None,
        seed=202,
    )
    _assert_section_equal_numeric_or_str(out["centroid"], out2["centroid"])
    _assert_section_equal_numeric_or_str(out["emitter"], out2["emitter"])
    _assert_section_equal_numeric_or_str(out["observed"], out2["observed"])


def test_simulate_poly_hdf5_write(tmp_path: Path):
    # Write out a small file and confirm groups/datasets exist.
    out_file = tmp_path / "poly_test.h5"
    _ = sim.simulate_poly(
        filename=str(out_file),
        xrange=(0, 30), yrange=(0, 30),
        centroid_mean_groups=2,
        radius=2.0,
        geom_mix=[(4, 1.0)],
        oligomer_pmf={1: 1.0},
        p=1.0, q=1.0, measured=1,
        gt_uncertainty=0.0, ms_uncertainty=0.1,
        clutter_fraction=0.0, membrane_function=None,
        enforce_shared_edge=True, store_edges=False, seed=1,
    )
    assert out_file.exists()
    with h5py.File(out_file, "r") as f:
        assert "centroid" in f
        assert "position" in f["centroid"]
        assert "emitter" in f
        # emitter group may be empty position dataset, still present
        assert "position" in f["emitter"]


def test_simulate_grid_hdf5_write(tmp_path: Path):
    out_file = tmp_path / "grid_test.h5"
    _ = sim.simulate_grid(
        filename=str(out_file),
        xrange=(0, 30), yrange=(0, 30),
        centroid_mean_groups=2,
        rows=2, cols=2, sep=5.0,
        p=1.0, q=1.0, measured=1,
        gt_uncertainty=0.0, ms_uncertainty=0.1,
        clutter_fraction=0.0, membrane_function=None, seed=2,
    )
    assert out_file.exists()
    with h5py.File(out_file, "r") as f:
        assert "centroid" in f and "position" in f["centroid"]
        assert "emitter" in f and "position" in f["emitter"]


# ------------------------------
# CLI helper formatting
# ------------------------------

def test_fmtf_and_naming_helpers():
    assert sim._fmtf(1.23000) == "1.23"
    assert sim._fmtf(5.0) == "5"
    # mixture formatting only lists unique sides in descending order
    s = sim._fmt_poly([(8, 0.5), (5, 0.5), (8, 0.1)])
    assert s == "8+5"
    # olig pmf formatting
    name = sim._fmt_oligs_simple({1: 0.9, 2: 0.1, 5: 0.05})
    assert name.startswith("mono0.9") and "di0.1" in name and "penta0.05" in name
    # prefix cleaner
    assert sim._ensure_prefix(None) is None
    assert sim._ensure_prefix("out") == "out"
    assert sim._ensure_prefix("data.h5") == "data"
