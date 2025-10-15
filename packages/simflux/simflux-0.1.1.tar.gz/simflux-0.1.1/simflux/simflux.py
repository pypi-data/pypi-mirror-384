#!/usr/bin/env python3

"""
MINFLUX-like simulator with two mutually exclusive modes:

  1) poly  — polygonal monomers arranged into linear oligomers, placed under a
             hard-core constraint, with optional single shared interfaces.

  2) grid  — DNA-origami–style point grids. Each grid is represented by an
             axis-aligned lattice of (rows × cols) points with a fixed separation,
             then rotated and translated to a centroid. The effective radius R is
             computed automatically as the largest centroid→node distance.

Both modes distribute labelled/unlabelled emitters, generate noisy measurements, optionally distribute spurious
clutter measurements, and can write an HDF5 file and render a simple 2D overview plot. Output filenames
are formed from a user prefix plus a succinct descriptor of key parameters.

CLI note (argparse):
  Global options (those declared on the main parser) must appear before the
  subcommand name on the command line unless duplicated on the subparser.
  For example, --plot is global-only, so it should be placed before 'poly'
  or 'grid'. Example:

      ... --plot poly --radius 5 --mix ...
      ... --plot grid --grid 3 3 --sep 10
"""

import argparse
import math
import sys
from typing import Callable, Dict, List, Sequence, Tuple, Optional, Any

import h5py
import numpy as np
import pandas as pd
import plotly.graph_objects as go


# =============================================================================
# Parsing (poly mode)
# =============================================================================

def parse_mix(mix_str: str) -> List[Tuple[int, float]]:
    """
    Parse a geometry mixture string into ``(sides, weight)`` pairs.

    :param mix_str: Comma-separated specifications such as
        ``"polygon:8@1.0,polygon:5@0.4"``. If every weight is omitted, equal
        weights are assumed.
    :type mix_str: str
    :returns: List of ``(sides, normalised_weight)`` with weights summing to 1.0.
    :rtype: List[Tuple[int, float]]
    :raises ValueError: On empty/invalid input or invalid weights.
    """
    if not mix_str:
        raise ValueError("Empty --mix string.")

    specs: List[Tuple[int, Optional[float]]] = []
    for item in mix_str.split(","):
        item = item.strip()
        if not item:
            continue

        # Allow explicit weight with '@'; otherwise mark as None to equalise later.
        if "@" in item:
            shape_part, w_part = item.split("@", 1)
            weight = float(w_part)
        else:
            shape_part, weight = item, None

        shape_part = shape_part.strip().lower()
        if shape_part.startswith("polygon"):
            if ":" not in shape_part:
                raise ValueError("Polygon requires sides, e.g. 'polygon:8'.")
            _, n_str = shape_part.split(":", 1)
            sides = int(n_str)
        else:
            raise ValueError(f"Unknown structure spec: {shape_part}")

        specs.append((sides, weight))

    # Weight handling and normalisation
    if all(w is None for (_, w) in specs):
        weights = [1.0] * len(specs)
    elif any(w is None for (_, w) in specs):
        raise ValueError("Either provide weights for all entries or none.")
    else:
        weights = [float(w) for (_, w) in specs]

    weights = np.asarray(weights, dtype=float)
    if np.any(weights < 0):
        raise ValueError("Weights must be non-negative.")
    if np.all(weights == 0):
        raise ValueError("At least one weight must be > 0.")

    weights = weights / weights.sum()
    return [(specs[i][0], float(weights[i])) for i in range(len(specs))]


def parse_oligomers(spec: Optional[str]) -> Dict[int, float]:
    """
    Parse an oligomer probability mass function.

    :param spec: Comma-separated ``"k:weight"`` (e.g., ``"1:1.0,2:0.1"``) or
        short names ``"mono:1,di:0.1,tri:0.05"``. ``None``/empty → ``{1: 1.0}``.
    :type spec: Optional[str]
    :returns: Mapping oligomer size ``k`` to normalised probability.
    :rtype: Dict[int, float]
    :raises ValueError: On malformed entries or invalid weights.
    """
    if spec is None or str(spec).strip() == "":
        return {1: 1.0}

    # Accept both long and short names; duplicates are merged later.
    name_to_k = {
        "mono": 1, "monomer": 1,
        "dimer": 2, "di": 2,
        "trimer": 3, "tri": 3,
        "tetramer": 4, "tetra": 4,
    }

    items = [it.strip() for it in spec.split(",") if it.strip()]
    kv: Dict[int, float] = {}
    for it in items:
        if ":" not in it:
            raise ValueError("Oligomer spec must be 'k:weight', e.g. '2:0.1'.")
        k_part, w_part = it.split(":", 1)
        k_part = k_part.strip().lower()

        # Resolve names to integers; fall back to parsing as int.
        k = name_to_k.get(k_part, None)
        if k is None:
            k = int(k_part)

        w = float(w_part)
        if k < 1:
            raise ValueError("Oligomer k must be ≥ 1.")
        kv[k] = kv.get(k, 0.0) + w  # merge duplicates if present

    # Normalise to a PMF
    weights = np.array(list(kv.values()), dtype=float)
    if np.any(weights < 0) or np.all(weights == 0):
        raise ValueError("Oligomer weights must be non-negative and not all zero.")
    weights = weights / weights.sum()
    for i, key in enumerate(list(kv.keys())):
        kv[key] = float(weights[i])
    return kv


# =============================================================================
# Geometry helpers (poly mode)
# =============================================================================

def gen_poly_edge_aligned(sides: int, radius: float = 1.0) -> np.ndarray:
    """
    Regular polygon centred at the origin, aligned so that edge (0,1)
    has outward normal along +x.

    :param sides: Number of vertices (≥ 3).
    :type sides: int
    :param radius: Circumradius.
    :type radius: float
    :returns: Array of polygon vertices ``(sides × 2)`` as ``(x, y)``.
    :rtype: np.ndarray
    :raises ValueError: If ``sides < 3``.
    """
    if sides < 3:
        raise ValueError("sides must be ≥ 3")
    # Start angle chosen so an edge, not a vertex, faces +x (helps edge sharing).
    angles = (-np.pi / sides) + np.arange(sides) * (2.0 * np.pi / sides)
    x = radius * np.cos(angles)
    y = radius * np.sin(angles)
    return np.column_stack((x, y))


def edge_share_distance(sides: int, radius: float) -> float:
    """
    Centre–centre spacing for two identical n-gons to share one full side.

    :param sides: Polygon sides.
    :type sides: int
    :param radius: Polygon circumradius.
    :type radius: float
    :returns: Required centroid spacing.
    :rtype: float
    """
    # Derived from circumradius geometry of a regular n-gon.
    return 2.0 * radius * np.cos(np.pi / sides)


# =============================================================================
# Common helpers
# =============================================================================

def _sample_from_dist(items: Sequence, probs: Sequence[float]) -> Any:
    """
    Sample a single element from a discrete distribution.

    :param items: Candidate items.
    :type items: Sequence
    :param probs: Probabilities aligned with items.
    :type probs: Sequence[float]
    :returns: One sampled item.
    :rtype: Any
    """
    # np.random.choice handles the multinomial draw with provided probabilities.
    idx = np.random.choice(len(items), p=np.asarray(probs, dtype=float))
    return items[idx]


def _min_dist2_to_set(pt: np.ndarray, S: np.ndarray) -> float:
    """
    Minimum squared distance from a point to a set of points.

    :param pt: A point of shape ``(2,)``.
    :type pt: np.ndarray
    :param S: Array of points of shape ``(N, 2)``; may be empty.
    :type S: np.ndarray
    :returns: Minimum squared distance; ``∞`` if ``S`` is empty.
    :rtype: float
    """
    if S.size == 0:
        return np.inf
    d = S - pt[None, :]
    return float(np.min(np.sum(d * d, axis=1)))


# =============================================================================
# Oligomer-aware centroid placement (poly mode)
# =============================================================================

def generate_oligomeric_centroids(
    xrange: Tuple[float, float],
    yrange: Tuple[float, float],
    poisson_mean_groups: float,
    radius: float,
    geom_dist: List[Tuple[int, float]],
    oligomer_pmf: Dict[int, float],
    hardcore_radius: Optional[float] = None,
    max_group_attempts: int = 1000,
    seed: Optional[int] = None,
):
    """
    Place group centroids (each group is a linear oligomer chain) under a hard-core constraint.

    :param xrange: ``(xmin, xmax)`` for centroid sampling window.
    :type xrange: Tuple[float, float]
    :param yrange: ``(ymin, ymax)`` for centroid sampling window.
    :type yrange: Tuple[float, float]
    :param poisson_mean_groups: Poisson mean number of groups to place.
    :type poisson_mean_groups: float
    :param radius: Monomer circumradius (affects spacing in chains).
    :type radius: float
    :param geom_dist: Geometry mixture as ``(sides, weight)``.
    :type geom_dist: List[Tuple[int, float]]
    :param oligomer_pmf: PMF dict of oligomer sizes ``k → probability``.
    :type oligomer_pmf: Dict[int, float]
    :param hardcore_radius: Exclusion radius; defaults to ``2*radius`` if ``None``.
    :type hardcore_radius: Optional[float]
    :param max_group_attempts: Maximum placement attempts per group.
    :type max_group_attempts: int
    :param seed: RNG seed.
    :type seed: Optional[int]
    :returns: Table with keys ``id``, ``position(N,2)``, ``group_id``,
        ``group_index``, ``group_size``, ``sides``, ``theta``.
    :rtype: Dict[str, np.ndarray]
    """
    if seed is not None:
        np.random.seed(seed)

    # Use provided hard-core radius if given; otherwise fall back to monomer scale.
    hc = radius if hardcore_radius is None else float(hardcore_radius)
    hc2 = hc * hc  # operate in squared distance for speed

    sides_arr, geom_probs = zip(*geom_dist)
    sides_arr = list(sides_arr)
    geom_probs = list(geom_probs)

    n_groups = np.random.poisson(lam=poisson_mean_groups)
    rows: List[Tuple[Any, ...]] = []

    # Keep a running set of accepted centroids to enforce the hard-core rule.
    existing = np.empty((0, 2), dtype=float)
    centroid_id = 0
    group_id = 0

    xmin, xmax = float(xrange[0]), float(xrange[1])
    ymin, ymax = float(yrange[0]), float(yrange[1])

    # Prepare arrays for oligomer size sampling (vectorised PMF).
    ks = sorted(oligomer_pmf.keys())
    kp = np.array([oligomer_pmf[k] for k in ks], dtype=float)

    for _ in range(n_groups):
        placed = False
        for _attempt in range(max_group_attempts):
            # Propose a random seed point within the sampling window.
            sx = np.random.uniform(xmin, xmax)
            sy = np.random.uniform(ymin, ymax)
            seed_pt = np.array([sx, sy], dtype=float)

            # Reject if too close to any previously accepted centroid.
            if _min_dist2_to_set(seed_pt, existing) < hc2:
                continue

            # Draw polygon sides and an oligomer length for this group.
            sides = int(_sample_from_dist(sides_arr, geom_probs))
            k = int(_sample_from_dist(ks, kp))

            if k == 1:
                # Simple case: single monomer as its own group.
                rows.append((centroid_id, sx, sy, group_id, 0, 1, sides,
                             np.random.uniform(0.0, 2.0 * np.pi)))
                existing = np.vstack((existing, seed_pt))
                centroid_id += 1
                group_id += 1
                placed = True
                break

            # Compute spacing so adjacent monomers share a full edge.
            d = edge_share_distance(sides, radius)
            base_theta = np.random.uniform(0.0, 2.0 * np.pi)
            edge_shifts = np.random.permutation(sides)  # try different edge orientations

            success = False
            for m in edge_shifts:
                theta_try = base_theta + (2.0 * np.pi / sides) * m
                # Try both forward and backward chain growth directions.
                for direction in (+1.0, -1.0):
                    u = direction * np.array([math.cos(theta_try), math.sin(theta_try)], dtype=float)
                    chain = [seed_pt]
                    ok = True
                    for j in range(1, k):
                        c = seed_pt + j * d * u
                        # Discard chain if any centroid would leave the window or violate hard-core.
                        if not (xmin <= c[0] <= xmax and ymin <= c[1] <= ymax):
                            ok = False
                            break
                        if _min_dist2_to_set(c, existing) < hc2:
                            ok = False
                            break
                        chain.append(c)
                    if not ok:
                        continue
                    # Commit the entire chain.
                    for j, cp in enumerate(chain):
                        rows.append((centroid_id, float(cp[0]), float(cp[1]),
                                     group_id, j, k, sides, theta_try))
                        centroid_id += 1
                    existing = np.vstack((existing, np.vstack(chain)))
                    group_id += 1
                    success = True
                    break
                if success:
                    break
            if success:
                placed = True
                break
        if not placed:
            # Give up on this group if placement budget is exhausted.
            continue

    if len(rows) == 0:
        # Return a consistent empty table if nothing could be placed.
        return {
            "id": np.empty((0,), dtype=np.int32),
            "position": np.empty((0, 2), dtype=float),
            "group_id": np.empty((0,), dtype=np.int32),
            "group_index": np.empty((0,), dtype=np.int32),
            "group_size": np.empty((0,), dtype=np.int32),
            "sides": np.empty((0,), dtype=np.int32),
            "theta": np.empty((0,), dtype=float),
        }

    # Convert list of tuples into structured numpy arrays.
    arr = np.array(rows, dtype=object)
    return {
        "id": arr[:, 0].astype(np.int32),
        "position": np.column_stack((arr[:, 1].astype(float), arr[:, 2].astype(float))),
        "group_id": arr[:, 3].astype(np.int32),
        "group_index": arr[:, 4].astype(np.int32),
        "group_size": arr[:, 5].astype(np.int32),
        "sides": arr[:, 6].astype(np.int32),
        "theta": arr[:, 7].astype(float),
    }


# =============================================================================
# Grid helpers and placement (grid mode)
# =============================================================================

def grid_node_offsets(rows: int, cols: int, sep: float) -> np.ndarray:
    """
    Build centred grid node offsets before rotation/translation.

    :param rows: Number of rows (≥ 1).
    :type rows: int
    :param cols: Number of columns (≥ 1).
    :type cols: int
    :param sep: Separation between adjacent nodes (absolute units).
    :type sep: float
    :returns: Array of offsets ``(rows*cols, 2)`` centred at ``(0,0)``.
    :rtype: np.ndarray
    :raises ValueError: If ``rows < 1`` or ``cols < 1``.
    """
    if rows < 1 or cols < 1:
        raise ValueError("rows and cols must be ≥ 1.")
    # Build a centred lattice so later rotations are about the centroid.
    rr = np.arange(rows) - (rows - 1) / 2.0
    cc = np.arange(cols) - (cols - 1) / 2.0
    yy, xx = np.meshgrid(rr, cc, indexing="xy")
    offsets = np.column_stack((xx.ravel() * sep, yy.ravel() * sep))
    return offsets


def grid_effective_R(offsets: np.ndarray) -> float:
    """
    Compute effective grid radius as the largest centroid→node distance.

    :param offsets: Grid node offsets centred at the origin, shape ``(N,2)``.
    :type offsets: np.ndarray
    :returns: Maximum Euclidean radius to any node.
    :rtype: float
    """
    if offsets.size == 0:
        return 0.0
    # Equivalent to the maximum norm of the set of offset vectors.
    return float(np.sqrt(np.max(np.sum(offsets * offsets, axis=1))))


def generate_grid_centroids(
    xrange: Tuple[float, float],
    yrange: Tuple[float, float],
    poisson_mean_groups: float,
    R: float,
    hardcore_radius: Optional[float] = None,
    max_group_attempts: int = 1000,
    seed: Optional[int] = None,
):
    """
    Place grid centroids under a hard-core constraint; each grid receives a random rotation.

    :param xrange: ``(xmin, xmax)`` sampling bounds.
    :type xrange: Tuple[float, float]
    :param yrange: ``(ymin, ymax)`` sampling bounds.
    :type yrange: Tuple[float, float]
    :param poisson_mean_groups: Poisson mean number of grids to place.
    :type poisson_mean_groups: float
    :param R: Effective grid radius (largest centroid→node distance).
    :type R: float
    :param hardcore_radius: Exclusion radius; defaults to ``2*R`` if ``None``.
    :type hardcore_radius: Optional[float]
    :param max_group_attempts: Maximum placement attempts per grid.
    :type max_group_attempts: int
    :param seed: RNG seed.
    :type seed: Optional[int]
    :returns: Table with keys ``id``, ``position(N,2)``, ``group_id``, ``theta``.
    :rtype: Dict[str, np.ndarray]
    """
    if seed is not None:
        np.random.seed(seed)

    hc = (2.0 * R) if hardcore_radius is None else float(hardcore_radius)
    hc2 = hc * hc

    n_groups = np.random.poisson(lam=poisson_mean_groups)
    rows: List[Tuple[Any, ...]] = []

    # Maintain accepted centroids to check spacing constraints.
    existing = np.empty((0, 2), dtype=float)
    centroid_id = 0
    group_id = 0

    xmin, xmax = float(xrange[0]), float(xrange[1])
    ymin, ymax = float(yrange[0]), float(yrange[1])

    for _ in range(n_groups):
        placed = False
        for _attempt in range(max_group_attempts):
            # Uniform candidate within the rectangular window.
            sx = np.random.uniform(xmin, xmax)
            sy = np.random.uniform(ymin, ymax)
            seed_pt = np.array([sx, sy], dtype=float)
            if _min_dist2_to_set(seed_pt, existing) < hc2:
                # Reject if any existing centroid is too close.
                continue

            theta = np.random.uniform(0.0, 2.0 * np.pi)
            rows.append((centroid_id, sx, sy, group_id, theta))
            existing = np.vstack((existing, seed_pt))
            centroid_id += 1
            group_id += 1
            placed = True
            break
        if not placed:
            # Skip if a valid location could not be found within budget.
            continue

    if len(rows) == 0:
        # Empty result with correct schema if nothing placed.
        return {
            "id": np.empty((0,), dtype=np.int32),
            "position": np.empty((0, 2), dtype=float),
            "group_id": np.empty((0,), dtype=np.int32),
            "theta": np.empty((0,), dtype=float),
        }

    arr = np.array(rows, dtype=object)
    return {
        "id": arr[:, 0].astype(np.int32),
        "position": np.column_stack((arr[:, 1].astype(float), arr[:, 2].astype(float))),
        "group_id": arr[:, 3].astype(np.int32),
        "theta": arr[:, 4].astype(float),
    }


# =============================================================================
# Measurement / clutter / membrane
# =============================================================================

def generate_measurements(emitter_position, poisson_mean, uncertainty_std):
    """
    Generate measurement points around emitters (Poisson count, Gaussian scatter).

    :param emitter_position: Single emitter ``(2,)`` or array of emitters ``(M,2)``.
    :type emitter_position: array_like
    :param poisson_mean: Expected number of measurements per emitter.
    :type poisson_mean: float
    :param uncertainty_std: Gaussian sigma for measurement noise.
    :type uncertainty_std: float
    :returns: Measurement coordinates across all emitters, shape ``(K,2)``.
    :rtype: np.ndarray
    """
    # Canonicalise input to a 2D array for unified handling.
    emitter_position = np.atleast_2d(emitter_position)
    out: List[np.ndarray] = []
    for pos in emitter_position:
        # Number of measurements drawn from a Poisson distribution.
        m = np.random.poisson(poisson_mean)
        # Offsets represent localisation noise around the true emitter.
        offsets = np.random.normal(0.0, uncertainty_std, size=(m, 2))
        out.extend(pos + offsets)
    return np.asarray(out)


def _sample_cluster_centres_with_exclusion(xrange, yrange, n_clusters, forbidden_centres, forbidden_radius,
                                           max_trials_per_cluster=2000, batch=256):
    """
    Sample cluster centres while avoiding discs around forbidden centres.

    :param xrange: ``(xmin, xmax)`` sampling bounds.
    :type xrange: Tuple[float, float]
    :param yrange: ``(ymin, ymax)`` sampling bounds.
    :type yrange: Tuple[float, float]
    :param n_clusters: Number of clusters to sample.
    :type n_clusters: int
    :param forbidden_centres: Centres to avoid; empty allowed. Shape ``(M,2)``.
    :type forbidden_centres: array_like
    :param forbidden_radius: Exclusion radius around forbidden centres.
    :type forbidden_radius: float
    :param max_trials_per_cluster: Trial budget per cluster.
    :type max_trials_per_cluster: int
    :param batch: Candidate batch size per iteration.
    :type batch: int
    :returns: Accepted centres, shape ``(n_clusters,2)`` (may be empty).
    :rtype: np.ndarray
    """
    if n_clusters <= 0:
        return np.empty((0, 2))

    forbidden_centres = np.asarray(forbidden_centres, dtype=float).reshape(-1, 2)
    have_forbidden = forbidden_centres.size > 0 and forbidden_radius > 0.0

    accepted: List[np.ndarray] = []
    trials = 0
    need = n_clusters
    while need > 0 and trials < max_trials_per_cluster * n_clusters:
        # Draw a batch of candidates to reduce Python overhead.
        k = min(batch, need * 4)
        xs = np.random.uniform(xrange[0], xrange[1], k)
        ys = np.random.uniform(yrange[0], yrange[1], k)
        pts = np.column_stack((xs, ys))
        if have_forbidden:
            # Compute distances to nearest forbidden centre and mask those too close.
            diffs = pts[:, None, :] - forbidden_centres[None, :, :]
            d2 = np.sum(diffs * diffs, axis=2)
            min_d = np.sqrt(np.min(d2, axis=1))
            mask = min_d >= forbidden_radius
            pts = pts[mask]
        for p in pts:
            accepted.append(p)
            need -= 1
            if need == 0:
                break
        trials += k

    if len(accepted) == 0:
        return np.empty((0, 2))
    return np.vstack(accepted)


def gen_clutter(xrange, yrange, n_clusters, measured, ms_uncertainty,
                forbidden_centres=None, forbidden_radius=0.0):
    """
    Generate clutter measurement clusters (not tied to emitters).

    :param xrange: Bounds for cluster centres ``(xmin, xmax)``.
    :type xrange: Tuple[float, float]
    :param yrange: Bounds for cluster centres ``(ymin, ymax)``.
    :type yrange: Tuple[float, float]
    :param n_clusters: Number of clutter clusters.
    :type n_clusters: int
    :param measured: Poisson mean measurements per clutter cluster.
    :type measured: float
    :param ms_uncertainty: Gaussian sigma for clutter localisation noise.
    :type ms_uncertainty: float
    :param forbidden_centres: Optional set of centres to avoid; shape ``(M,2)``.
    :type forbidden_centres: array_like or None
    :param forbidden_radius: Exclusion radius around ``forbidden_centres``.
    :type forbidden_radius: float
    :returns: Array ``(K,3)`` with columns ``[x, y, emitter_id=-1]``.
    :rtype: np.ndarray
    """
    if n_clusters <= 0:
        return np.empty((0, 3))

    # Canonicalise the forbidden set; use empty array if none supplied.
    if forbidden_centres is None:
        forbidden_centres_arr = np.empty((0, 2))
    else:
        forbidden_centres_arr = np.asarray(forbidden_centres, dtype=float).reshape(-1, 2)

    # Pick centres subject to exclusion, then realise Gaussian scatter about each centre.
    centres = _sample_cluster_centres_with_exclusion(
        xrange, yrange, n_clusters, forbidden_centres_arr, forbidden_radius
    )

    out: List[Tuple[float, float, int]] = []
    for c in centres:
        meas = generate_measurements(c, poisson_mean=measured, uncertainty_std=ms_uncertainty)
        for m in meas:
            out.append((float(m[0]), float(m[1]), -1))
    return np.asarray(out).reshape(-1, 3)


def apply_membrane(xy: np.ndarray, membrane_function: Optional[Callable]) -> np.ndarray:
    """
    Optionally lift 2D points into 3D via a membrane function.

    :param xy: Input 2D points, shape ``(N,2)``.
    :type xy: np.ndarray
    :param membrane_function: Callable ``f(x, y) -> z``; if ``None``, ``z = 0``.
    :type membrane_function: Optional[Callable]
    :returns: Array of shape ``(N,3)`` with columns ``[x, y, z]``.
    :rtype: np.ndarray
    :raises ValueError: If the membrane output length mismatches ``N``.
    """
    # Always return an array of shape (N,3); if no membrane, z is zeros.
    xy = np.atleast_2d(xy)
    if xy.size == 0:
        return xy
    if membrane_function is None:
        z = np.zeros(len(xy), dtype=float)
    else:
        x, y = xy[:, 0], xy[:, 1]
        z = np.asarray(membrane_function(x, y))
        if z.shape[0] != xy.shape[0]:
            raise ValueError("Membrane function output length mismatch.")
    return np.column_stack((xy, z))


# =============================================================================
# Simulation cores
# =============================================================================

def simulate_poly(
    filename: Optional[str],
    xrange: Tuple[float, float],
    yrange: Tuple[float, float],
    centroid_mean_groups: float,
    radius: float,
    geom_mix: List[Tuple[int, float]],
    oligomer_pmf: Dict[int, float],
    p: float,
    q: float,
    measured: float,
    gt_uncertainty: float = 0.0,
    ms_uncertainty: float = 1.0,
    clutter_fraction: Optional[float] = None,
    membrane_function: Optional[Callable] = None,
    enforce_shared_edge: bool = True,
    store_edges: bool = False,
    seed: Optional[int] = None,
):
    """
    Simulate polygonal monomer chains with hard-core placement and optional shared-edge snapping.

    :param filename: Output HDF5 path or ``None`` to keep in-memory only.
    :type filename: Optional[str]
    :param xrange: Sampling window ``(xmin, xmax)`` for chain centroids.
    :type xrange: Tuple[float, float]
    :param yrange: Sampling window ``(ymin, ymax)`` for chain centroids.
    :type yrange: Tuple[float, float]
    :param centroid_mean_groups: Poisson mean for number of chains.
    :type centroid_mean_groups: float
    :param radius: Monomer circumradius.
    :type radius: float
    :param geom_mix: Mixture of polygon geometries as ``(sides, weight)``.
    :type geom_mix: List[Tuple[int, float]]
    :param oligomer_pmf: PMF over oligomer sizes.
    :type oligomer_pmf: Dict[int, float]
    :param p: Probability an emitter is labelled.
    :type p: float
    :param q: Per-measurement signal probability.
    :type q: float
    :param measured: Poisson mean measurements per labelled emitter.
    :type measured: float
    :param gt_uncertainty: Ground-truth vertex jitter (sigma, absolute units).
    :type gt_uncertainty: float
    :param ms_uncertainty: Measurement noise (sigma, absolute units).
    :type ms_uncertainty: float
    :param clutter_fraction: Number of clutter clusters =
        ``floor(fraction × N_labelled_emitters)``; ``None`` disables clutter.
    :type clutter_fraction: Optional[float]
    :param membrane_function: Optional surface for lifting to 3D.
    :type membrane_function: Optional[Callable]
    :param enforce_shared_edge: Snap two coincident shared-edge vertices (default ``True``).
    :type enforce_shared_edge: bool
    :param store_edges: If ``True``, store fully connected edges per monomer.
    :type store_edges: bool
    :param seed: RNG seed.
    :type seed: Optional[int]
    :returns: Dictionary containing centroid, emitter, observed, clutter (and edges if requested).
    :rtype: Dict[str, Dict[str, np.ndarray]]
    """
    # Helper to find up to two closest vertex pairs across adjacent monomers.
    def _find_shared_vertex_pairs_local(pts_a: np.ndarray, pts_b: np.ndarray, tol: float) -> List[Tuple[int, int]]:
        da = pts_a[:, None, :] - pts_b[None, :, :]
        d2 = np.sum(da * da, axis=2)
        flat = np.argsort(d2, axis=None)
        pairs: List[Tuple[int, int]] = []
        used_a: set = set()
        used_b: set = set()
        for f in flat:
            ia, ib = np.unravel_index(int(f), d2.shape)
            if ia in used_a or ib in used_b:
                continue
            if d2[ia, ib] <= tol * tol:
                pairs.append((int(ia), int(ib)))
                used_a.add(int(ia)); used_b.add(int(ib))
                if len(pairs) == 2:
                    break
        return pairs

    if seed is not None:
        np.random.seed(seed)

    # Step 1: place chain centroids with the oligomer-aware routine.
    cen_tbl = generate_oligomeric_centroids(
        xrange, yrange, centroid_mean_groups, radius,
        geom_dist=geom_mix, oligomer_pmf=oligomer_pmf,
        hardcore_radius=2.0 * radius, seed=seed,
    )

    C = len(cen_tbl["id"])
    if C == 0:
        # Provide a fully shaped but empty payload and, if requested, an empty file.
        data = {
            "centroid": {"position": np.empty((0, 2)), "id": np.empty((0,), dtype=np.int32),
                         "group_id": np.empty((0,), dtype=np.int32), "group_index": np.empty((0,), dtype=np.int32),
                         "group_size": np.empty((0,), dtype=np.int32), "sides": np.empty((0,), dtype=np.int32),
                         "theta": np.empty((0,), dtype=float)},
            "emitter": {"position": np.empty((0, 2)), "id": np.empty((0,), dtype=np.int32),
                        "centroid_id": np.empty((0,), dtype=np.int32), "type": np.empty((0,), dtype=str)},
            "observed": {"position": np.empty((0, 2)), "emitter_id": np.empty((0,), dtype=np.int32),
                         "centroid_id": np.empty((0,), dtype=np.int32)},
            "clutter": {"position": np.empty((0, 2)), "emitter_id": np.empty((0,), dtype=np.int32),
                        "type": np.empty((0,), dtype=str)},
            "edges": np.empty((0, 2), dtype=np.int32),
        }
        if filename:
            with h5py.File(filename, "w") as hf:
                hf.create_group("centroid").create_dataset("position", data=np.empty((0, 3)))
        return data

    # Accumulators for emitter catalogue and observed points.
    observed_data: List[Tuple[float, float, int, int]] = []
    emitter_rows: List[Tuple[float, float, int, int, str]] = []
    edges: List[Tuple[int, int]] = []
    emitter_index = 0

    # Iterate through chains, preserving monomer order by group_index.
    group_ids = np.unique(cen_tbl["group_id"])
    for gid in group_ids:
        idxs = np.where(cen_tbl["group_id"] == gid)[0]
        idxs = sorted(idxs, key=lambda c: int(cen_tbl["group_index"][c]))

        sides = int(cen_tbl["sides"][idxs[0]])
        theta = float(cen_tbl["theta"][idxs[0]])

        # Precompute a prototype polygon at the origin and a rotation matrix.
        poly = gen_poly_edge_aligned(sides, radius=radius)
        cth, sth = math.cos(theta), math.sin(theta)
        Rm = np.array([[cth, -sth], [sth, cth]])

        # Transform polygon to each centroid in the chain.
        pts_list: List[np.ndarray] = []
        for ci in idxs:
            cx, cy = cen_tbl["position"][ci]
            pts = (poly @ Rm.T) + np.array([cx, cy])
            pts_list.append(pts)

        # Determine which vertices to drop on shared interfaces to avoid duplicates.
        drop_sets: List[set] = [set() for _ in idxs]
        keep_pairs_for_snap: List[Tuple[int, int, int, int]] = []
        tol_shared = 1e-7 * max(1.0, float(radius))

        if enforce_shared_edge and len(idxs) > 1:
            for j in range(1, len(idxs)):
                L, Rv = pts_list[j - 1], pts_list[j]
                pairs = _find_shared_vertex_pairs_local(L, Rv, tol_shared)
                if len(pairs) < 2:
                    # Fallback: pick two nearest distinct vertex pairs.
                    da = L[:, None, :] - Rv[None, :, :]
                    d2 = np.sum(da * da, axis=2)
                    flat = np.argsort(d2, axis=None)
                    used_a, used_b, pairs = set(), set(), []
                    for f in flat:
                        ia, ib = np.unravel_index(int(f), d2.shape)
                        if ia in used_a or ib in used_b:
                            continue
                        pairs.append((int(ia), int(ib)))
                        used_a.add(int(ia)); used_b.add(int(ib))
                        if len(pairs) == 2:
                            break
                # One pair is kept and snapped; the other pair is removed from one side.
                (ia_keep, ib_keep), (ia_drop, ib_drop) = pairs[0], pairs[1]
                drop_sets[j].update([ib_keep, ib_drop])
                if ia_keep not in drop_sets[j - 1] and ib_keep not in drop_sets[j]:
                    keep_pairs_for_snap.append((j - 1, ia_keep, j, ib_keep))

        # Convert drop sets into boolean masks per monomer.
        keep_masks: List[np.ndarray] = []
        for ds in drop_sets:
            keep = np.ones(len(poly), dtype=bool)
            if ds:
                keep[list(ds)] = False
            keep_masks.append(keep)

        # Optional ground-truth perturbation at vertex level.
        if gt_uncertainty > 0:
            for j in range(len(idxs)):
                pts_list[j] += np.random.normal(0.0, gt_uncertainty, size=pts_list[j].shape)

        # Snap the kept shared-vertex pair to their midpoint for exact coincidence.
        if enforce_shared_edge and keep_pairs_for_snap:
            for (jl, ia_k, jr, ib_k) in keep_pairs_for_snap:
                v = 0.5 * (pts_list[jl][ia_k] + pts_list[jr][ib_k])
                pts_list[jl][ia_k] = v
                pts_list[jr][ib_k] = v

        # Catalogue emitters, draw labelled/unlabelled, then simulate measurements.
        for j, ci in enumerate(idxs):
            pts = pts_list[j]
            mask = keep_masks[j]
            for point in pts[mask]:
                etype = "labelled" if np.random.binomial(1, p) else "unlabelled"
                emitter_rows.append((float(point[0]), float(point[1]), emitter_index, int(cen_tbl["id"][ci]), etype))
                if etype == "labelled":
                    measurements = generate_measurements(point, poisson_mean=measured, uncertainty_std=ms_uncertainty)
                    for m in measurements:
                        if np.random.binomial(1, q):
                            observed_data.append((float(m[0]), float(m[1]), emitter_index, int(cen_tbl["id"][ci])))
                emitter_index += 1

            if store_edges:
                # Optionally store a complete local edge list (quadratic in retained vertices).
                start = emitter_index - np.count_nonzero(mask)
                for a in range(start, emitter_index):
                    for b in range(a + 1, emitter_index):
                        edges.append((a, b))

    # Optional clutter: number of clusters scales with the count of labelled emitters.
    clutter_data: List[Tuple[float, float, int]] = []
    if clutter_fraction is not None and clutter_fraction >= 0:
        n_labelled = sum(1 for e in emitter_rows if e[4] == "labelled")
        n_clusters = int(np.floor(clutter_fraction * n_labelled))
        if n_clusters > 0:
            emitter_xy = np.array([[e[0], e[1]] for e in emitter_rows])
            xmin, ymin = emitter_xy.min(axis=0) if len(emitter_xy) else (0.0, 0.0)
            xmax, ymax = emitter_xy.max(axis=0) if len(emitter_xy) else (0.0, 0.0)
            clutter_data = gen_clutter(
                (xmin, xmax), (ymin, ymax), n_clusters,
                measured=measured, ms_uncertainty=ms_uncertainty,
                forbidden_centres=cen_tbl["position"],
                forbidden_radius=radius
            )

    # Assemble arrays for output payload.
    emitter_xy = np.array([[e[0], e[1]] for e in emitter_rows], dtype=float)
    observed_xy = (np.array([[o[0], o[1]] for o in observed_data], dtype=float)
                   if len(observed_data) else np.empty((0, 2)))
    clutter_xy = (np.array([[c[0], c[1]] for c in clutter_data], dtype=float)
                  if len(clutter_data) else np.empty((0, 2)))

    data = {
        "centroid": {k: cen_tbl[k] for k in ("position", "id", "group_id", "group_index", "group_size", "sides", "theta")},
        "emitter": {
            "position": emitter_xy,
            "id": np.array([e[2] for e in emitter_rows], dtype=np.int32),
            "centroid_id": np.array([e[3] for e in emitter_rows], dtype=np.int32),
            "type": np.array([e[4] for e in emitter_rows], dtype=str),
        },
        "observed": {
            "position": observed_xy,
            "emitter_id": (np.array([o[2] for o in observed_data], dtype=np.int32)
                           if len(observed_data) else np.empty((0,), dtype=np.int32)),
            "centroid_id": (np.array([o[3] for o in observed_data], dtype=np.int32)
                            if len(observed_data) else np.empty((0,), dtype=np.int32)),
        },
        "clutter": {
            "position": clutter_xy,
            "emitter_id": (np.array([c[2] for c in clutter_data], dtype=np.int32)
                           if len(clutter_data) else np.empty((0,), dtype=np.int32)),
            "type": (np.array(["clutter"] * len(clutter_xy), dtype=str)
                     if len(clutter_data) else np.empty((0,), dtype=str)),
        },
        "edges": np.array(edges, dtype=np.int32) if len(edges) else np.empty((0, 2), dtype=np.int32),
    }

    # Quick audit to flag any accidental inter-group hard-core violations.
    viol = audit_hardcore_filtered(data["centroid"]["position"], cen_tbl["group_id"], 2.0 * radius)
    if len(viol) > 0:
        print(f"[hardcore audit] {len(viol)} inter-group violating centroid pairs (distance < {2.0 * radius}):")
        for (i, j, d) in viol[:20]:
            ci = data["centroid"]["position"][i]; cj = data["centroid"]["position"][j]
            print(f"  pair ({i},{j}) d={d:.4f}  ci=({ci[0]:.2f},{ci[1]:.2f}) cj=({cj[0]:.2f},{cj[1]:.2f})")

    # Optional write-out with membrane lifting applied to positions prior to storage.
    if filename:
        centroid_pos = apply_membrane(cen_tbl["position"], membrane_function)
        emitter_pos = apply_membrane(emitter_xy, membrane_function)
        observed_pos = apply_membrane(observed_xy, membrane_function) if len(observed_xy) else observed_xy
        clutter_pos = apply_membrane(clutter_xy, membrane_function) if len(clutter_xy) else clutter_xy

        with h5py.File(filename, "w") as hf:
            g = hf.create_group("centroid")
            g.create_dataset("position", data=centroid_pos)
            for k in ("id", "group_id", "group_index", "group_size", "sides", "theta"):
                g.create_dataset(k, data=cen_tbl[k])

            if len(emitter_xy):
                egrp = hf.create_group("emitter")
                egrp.create_dataset("position", data=emitter_pos)
                egrp.create_dataset("id", data=data["emitter"]["id"])
                egrp.create_dataset("centroid_id", data=data["emitter"]["centroid_id"])
                egrp.create_dataset("type", data=np.array([t.encode() for t in data["emitter"]["type"]], dtype="S"))
            else:
                hf.create_group("emitter").create_dataset("position", data=np.empty((0, 3)))

            if len(observed_xy):
                ogrp = hf.create_group("observed")
                ogrp.create_dataset("position", data=observed_pos)
                ogrp.create_dataset("emitter_id", data=data["observed"]["emitter_id"])
                ogrp.create_dataset("centroid_id", data=data["observed"]["centroid_id"])

            if len(clutter_xy):
                cgrp = hf.create_group("clutter")
                cgrp.create_dataset("position", data=clutter_pos)
                cgrp.create_dataset("emitter_id", data=data["clutter"]["emitter_id"])
                cgrp.create_dataset("type", data=np.array(["clutter"] * len(clutter_xy), dtype="S"))

    return data


def simulate_grid(
    filename: Optional[str],
    xrange: Tuple[float, float],
    yrange: Tuple[float, float],
    centroid_mean_groups: float,
    rows: int,
    cols: int,
    sep: float,
    p: float,
    q: float,
    measured: float,
    gt_uncertainty: float = 0.0,
    ms_uncertainty: float = 1.0,
    clutter_fraction: Optional[float] = None,
    membrane_function: Optional[Callable] = None,
    seed: Optional[int] = None,
):
    """
    Simulate DNA-origami–style grids. Each grid is placed by sampling a centroid
    under a hard-core constraint (``2R``) and applying a random in-plane rotation.
    ``R`` is computed from ``(rows, cols, sep)``.

    :param filename: Output HDF5 path or ``None`` to keep in-memory only.
    :type filename: Optional[str]
    :param xrange: Sampling window ``(xmin, xmax)`` for grid centroids.
    :type xrange: Tuple[float, float]
    :param yrange: Sampling window ``(ymin, ymax)`` for grid centroids.
    :type yrange: Tuple[float, float]
    :param centroid_mean_groups: Poisson mean for number of grids.
    :type centroid_mean_groups: float
    :param rows: Grid rows.
    :type rows: int
    :param cols: Grid columns.
    :type cols: int
    :param sep: Node separation.
    :type sep: float
    :param p: Probability an emitter is labelled.
    :type p: float
    :param q: Per-measurement signal probability.
    :type q: float
    :param measured: Poisson mean measurements per labelled emitter.
    :type measured: float
    :param gt_uncertainty: Ground-truth node jitter (sigma, absolute units).
    :type gt_uncertainty: float
    :param ms_uncertainty: Measurement noise (sigma, absolute units).
    :type ms_uncertainty: float
    :param clutter_fraction: Number of clutter clusters =
        ``floor(fraction × N_labelled_emitters)``; ``None`` disables clutter.
    :type clutter_fraction: Optional[float]
    :param membrane_function: Optional surface for lifting to 3D.
    :type membrane_function: Optional[Callable]
    :param seed: RNG seed.
    :type seed: Optional[int]
    :returns: Dictionary containing centroid, emitter, observed, clutter.
    :rtype: Dict[str, Dict[str, np.ndarray]]
    """
    if seed is not None:
        np.random.seed(seed)

    # Build centred grid offsets and compute its effective radius once.
    offsets = grid_node_offsets(rows, cols, sep)
    R = grid_effective_R(offsets)

    # Place grid centroids with a default 2R exclusion to avoid overlap.
    cen_tbl = generate_grid_centroids(
        xrange, yrange, centroid_mean_groups, R, hardcore_radius=2.0 * R, seed=seed
    )

    C = len(cen_tbl["id"])
    if C == 0:
        # Mirror the poly-mode empty structure for consistency.
        data = {
            "centroid": {"position": np.empty((0, 2)), "id": np.empty((0,), dtype=np.int32),
                         "group_id": np.empty((0,), dtype=np.int32), "theta": np.empty((0,), dtype=float),
                         "rows": np.empty((0,), dtype=np.int32), "cols": np.empty((0,), dtype=np.int32),
                         "sep": np.empty((0,), dtype=float), "R": np.empty((0,), dtype=float)},
            "emitter": {"position": np.empty((0, 2)), "id": np.empty((0,), dtype=np.int32),
                        "centroid_id": np.empty((0,), dtype=np.int32), "type": np.empty((0,), dtype=str)},
            "observed": {"position": np.empty((0, 2)), "emitter_id": np.empty((0,), dtype=np.int32),
                         "centroid_id": np.empty((0,), dtype=np.int32)},
            "clutter": {"position": np.empty((0, 2)), "emitter_id": np.empty((0,), dtype=np.int32),
                        "type": np.empty((0,), dtype=str)},
        }
        if filename:
            with h5py.File(filename, "w") as hf:
                hf.create_group("centroid").create_dataset("position", data=np.empty((0, 3)))
        return data

    observed_data: List[Tuple[float, float, int, int]] = []
    emitter_rows: List[Tuple[float, float, int, int, str]] = []
    emitter_index = 0

    # For each grid, rotate the offsets and translate to its centroid.
    for ci in range(C):
        cx, cy = cen_tbl["position"][ci]
        th = float(cen_tbl["theta"][ci])
        cth, sth = math.cos(th), math.sin(th)
        Rm = np.array([[cth, -sth], [sth, cth]])

        pts = (offsets @ Rm.T) + np.array([cx, cy])

        # Optional ground-truth jitter at the node level.
        if gt_uncertainty > 0:
            pts = pts + np.random.normal(0.0, gt_uncertainty, size=pts.shape)

        # Emitters at each node; labelled emitters generate measurements.
        for point in pts:
            etype = "labelled" if np.random.binomial(1, p) else "unlabelled"
            emitter_rows.append((float(point[0]), float(point[1]), emitter_index, int(cen_tbl["id"][ci]), etype))
            if etype == "labelled":
                measurements = generate_measurements(point, poisson_mean=measured, uncertainty_std=ms_uncertainty)
                for m in measurements:
                    if np.random.binomial(1, q):
                        observed_data.append((float(m[0]), float(m[1]), emitter_index, int(cen_tbl["id"][ci])))
            emitter_index += 1

    # Optional clutter sampling within bounding box of all emitters.
    clutter_data: List[Tuple[float, float, int]] = []
    if clutter_fraction is not None and clutter_fraction >= 0:
        n_labelled = sum(1 for e in emitter_rows if e[4] == "labelled")
        n_clusters = int(np.floor(clutter_fraction * n_labelled))
        if n_clusters > 0:
            emitter_xy = np.array([[e[0], e[1]] for e in emitter_rows])
            xmin, ymin = emitter_xy.min(axis=0) if len(emitter_xy) else (0.0, 0.0)
            xmax, ymax = emitter_xy.max(axis=0) if len(emitter_xy) else (0.0, 0.0)
            clutter_data = gen_clutter(
                (xmin, xmax), (ymin, ymax), n_clusters,
                measured=measured, ms_uncertainty=ms_uncertainty,
                forbidden_centres=cen_tbl["position"],
                forbidden_radius=R
            )

    # Convert lists to arrays for output.
    emitter_xy = np.array([[e[0], e[1]] for e in emitter_rows], dtype=float)
    observed_xy = (np.array([[o[0], o[1]] for o in observed_data], dtype=float)
                   if len(observed_data) else np.empty((0, 2)))
    clutter_xy = (np.array([[c[0], c[1]] for c in clutter_data], dtype=float)
                  if len(clutter_data) else np.empty((0, 2)))

    # Attach per-grid metadata so reconstruction is straightforward.
    centroid_meta = {
        "position": cen_tbl["position"],
        "id": cen_tbl["id"],
        "group_id": cen_tbl["group_id"],
        "theta": cen_tbl["theta"],
        "rows": np.full(C, rows, dtype=np.int32),
        "cols": np.full(C, cols, dtype=np.int32),
        "sep": np.full(C, sep, dtype=float),
        "R": np.full(C, R, dtype=float),
    }

    data = {
        "centroid": centroid_meta,
        "emitter": {
            "position": emitter_xy,
            "id": np.array([e[2] for e in emitter_rows], dtype=np.int32),
            "centroid_id": np.array([e[3] for e in emitter_rows], dtype=np.int32),
            "type": np.array([e[4] for e in emitter_rows], dtype=str),
        },
        "observed": {
            "position": observed_xy,
            "emitter_id": (np.array([o[2] for o in observed_data], dtype=np.int32)
                           if len(observed_data) else np.empty((0,), dtype=np.int32)),
            "centroid_id": (np.array([o[3] for o in observed_data], dtype=np.int32)
                            if len(observed_data) else np.empty((0,), dtype=np.int32)),
        },
        "clutter": {
            "position": clutter_xy,
            "emitter_id": (np.array([c[2] for c in clutter_data], dtype=np.int32)
                           if len(clutter_data) else np.empty((0,), dtype=np.int32)),
            "type": (np.array(["clutter"] * len(clutter_xy), dtype=str)
                     if len(clutter_data) else np.empty((0,), dtype=str)),
        },
    }

    # Audit inter-grid spacing; prints a short report if any pairs violate the rule.
    viol = audit_hardcore_filtered(data["centroid"]["position"], data["centroid"]["group_id"], 2.0 * R)
    if len(viol) > 0:
        print(f"[hardcore audit] {len(viol)} inter-grid violating centroid pairs (distance < {2.0 * R}):")
        for (i, j, d) in viol[:20]:
            ci = data["centroid"]["position"][i]; cj = data["centroid"]["position"][j]
            print(f"  pair ({i},{j}) d={d:.4f}  ci=({ci[0]:.2f},{ci[1]:.2f}) cj=({cj[0]:.2f},{cj[1]:.2f})")

    # Optional persistence: apply membrane then write arrays into groups.
    if filename:
        centroid_pos = apply_membrane(centroid_meta["position"], membrane_function)
        emitter_pos = apply_membrane(emitter_xy, membrane_function)
        observed_pos = apply_membrane(observed_xy, membrane_function) if len(observed_xy) else observed_xy
        clutter_pos = apply_membrane(clutter_xy, membrane_function) if len(clutter_xy) else clutter_xy

        with h5py.File(filename, "w") as hf:
            g = hf.create_group("centroid")
            g.create_dataset("position", data=centroid_pos)
            for k in ("id", "group_id", "theta", "rows", "cols", "sep", "R"):
                g.create_dataset(k, data=centroid_meta[k])

            if len(emitter_xy):
                egrp = hf.create_group("emitter")
                egrp.create_dataset("position", data=emitter_pos)
                egrp.create_dataset("id", data=data["emitter"]["id"])
                egrp.create_dataset("centroid_id", data=data["emitter"]["centroid_id"])
                egrp.create_dataset("type", data=np.array([t.encode() for t in data["emitter"]["type"]], dtype="S"))
            else:
                hf.create_group("emitter").create_dataset("position", data=np.empty((0, 3)))

            if len(observed_xy):
                ogrp = hf.create_group("observed")
                ogrp.create_dataset("position", data=observed_pos)
                ogrp.create_dataset("emitter_id", data=data["observed"]["emitter_id"])
                ogrp.create_dataset("centroid_id", data=data["observed"]["centroid_id"])

            if len(clutter_xy):
                cgrp = hf.create_group("clutter")
                cgrp.create_dataset("position", data=clutter_pos)
                cgrp.create_dataset("emitter_id", data=data["clutter"]["emitter_id"])
                cgrp.create_dataset("type", data=np.array(["clutter"] * len(clutter_xy), dtype="S"))

    return data


# =============================================================================
# Plotting (common)
# =============================================================================

def plot2d(data: Optional[Dict[str, Dict[str, np.ndarray]]] = None, filename: Optional[str] = None):
    """
    Render a simple 2D overview using Plotly.

    :param data: In-memory dataset to plot (exclusive with ``filename``).
    :type data: Optional[Dict[str, Dict[str, np.ndarray]]]
    :param filename: HDF5 file path to read and plot (exclusive with ``data``).
    :type filename: Optional[str]
    :returns: ``None``. Shows an interactive figure.
    :rtype: None
    :raises ValueError: If neither source is provided or no data are found.
    """
    records: List[Tuple[float, float, str]] = []

    if data is not None:
        # Flatten major layers to a single table for convenient plotting.
        for x, y in data["centroid"]["position"]:
            records.append((float(x), float(y), "centroid"))
        etypes = data.get("emitter", {}).get("type", np.array([], dtype=str))
        for (x, y), t in zip(
            data["emitter"]["position"],
            etypes if len(etypes) else ["labelled"] * len(data["emitter"]["position"])
        ):
            records.append((float(x), float(y), t.lower()))
        for x, y in data["observed"]["position"]:
            records.append((float(x), float(y), "observed"))
        for x, y in data["clutter"]["position"]:
            records.append((float(x), float(y), "clutter"))

    elif filename:
        # Load the same layers from file if a path is supplied.
        with h5py.File(filename, 'r') as f:
            if 'centroid' in f and 'position' in f['centroid']:
                for pos in f['centroid']['position'][:]:
                    records.append((float(pos[0]), float(pos[1]), 'centroid'))
            if 'emitter' in f and 'position' in f['emitter']:
                pos = f['emitter']['position'][:]
                types = f['emitter'].get('type', None)
                if types is not None:
                    raw = types[:]
                    if isinstance(raw, np.ndarray) and raw.dtype.kind in {'S', 'O'}:
                        kinds = [t.decode() if isinstance(t, (bytes, bytearray)) else str(t) for t in raw]
                    else:
                        kinds = [str(t) for t in raw]
                else:
                    kinds = ['labelled'] * len(pos)
                for (p, t) in zip(pos, kinds):
                    records.append((float(p[0]), float(p[1]), t.lower()))
            if 'observed' in f and 'position' in f['observed']:
                for p in f['observed']['position'][:]:
                    records.append((float(p[0]), float(p[1]), 'observed'))
            if 'clutter' in f and 'position' in f['clutter']:
                for p in f['clutter']['position'][:]:
                    records.append((float(p[0]), float(p[1]), 'clutter'))
    else:
        raise ValueError("plot2d requires either `data` or `filename`.")

    if not records:
        raise ValueError("No data found to plot.")

    # Construct a small DataFrame to split traces by type.
    df = pd.DataFrame(records, columns=["x", "y", "type"])
    colors = {
        "labelled": "#d62728", "unlabelled": "#1f77b4", "observed": "#ff7f0e",
        "centroid": "#000000", "clutter": "#cccccc"
    }
    sizes = {"centroid": 8, "labelled": 5, "unlabelled": 5, "observed": 4, "clutter": 3}
    symbols = {"centroid": "x", "labelled": "circle", "unlabelled": "circle", "observed": "circle", "clutter": "circle"}
    order = ["centroid", "labelled", "unlabelled", "observed", "clutter"]

    # Each type gets its own scatter trace for legend clarity.
    traces = []
    for t in order:
        sub = df[df["type"] == t]
        if sub.empty:
            continue
        traces.append(go.Scatter(
            x=sub["x"], y=sub["y"], mode="markers", name=t,
            marker=dict(
                size=sizes[t], color=colors[t], symbol=symbols[t],
                opacity=0.9 if t in ("observed", "labelled", "unlabelled") else 1.0
            ),
            hovertemplate=f"{t}<br>x=%{{x}}<br>y=%{{y}}<extra></extra>",
        ))
    fig = go.Figure(traces)
    fig.update_layout(
        title="Simulated Dataset Visualisation (2D)",
        legend_title_text="Data Type",
        legend=dict(x=0.01, y=0.99),
        width=900, height=700,
        xaxis_title="x", yaxis_title="y",
        xaxis=dict(constrain="domain", scaleratio=1),
        yaxis=dict(scaleanchor="x", scaleratio=1)
    )
    fig.show()


# =============================================================================
# HC audit utility
# =============================================================================

def audit_hardcore_filtered(centroid_xy: np.ndarray,
                            group_ids: np.ndarray,
                            hardcore: float) -> List[Tuple[int, int, float]]:
    """
    Report inter-group hard-core violations.

    :param centroid_xy: Centroid coordinates, shape ``(N,2)``.
    :type centroid_xy: np.ndarray
    :param group_ids: Group id per centroid, shape ``(N,)``.
    :type group_ids: np.ndarray
    :param hardcore: Exclusion radius.
    :type hardcore: float
    :returns: List of violating pairs as ``(i, j, distance)``.
    :rtype: List[Tuple[int, int, float]]
    """
    if len(centroid_xy) < 2:
        return []
    r2 = hardcore * hardcore
    viol: List[Tuple[int, int, float]] = []
    # Pairwise squared distances via broadcast; only upper triangle is examined.
    D = centroid_xy[:, None, :] - centroid_xy[None, :, :]
    d2 = np.sum(D * D, axis=2)
    n = len(centroid_xy)
    for i in range(n):
        gi = int(group_ids[i])
        for j in range(i + 1, n):
            if gi == int(group_ids[j]):
                continue
            if d2[i, j] < r2:
                viol.append((i, j, float(np.sqrt(d2[i, j]))))
    return viol


# =============================================================================
# CLI helpers (naming)
# =============================================================================

def _fmtf(x: float, nd=3) -> str:
    """
    Compact float formatting up to a maximum decimal count.

    :param x: Value to format.
    :type x: float
    :param nd: Maximum number of decimals to keep.
    :type nd: int
    :returns: Compact string with trailing zeros trimmed.
    :rtype: str
    """
    # Format then strip trailing zeros and decimal point if redundant.
    s = f"{x:.{nd}f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _fmt_poly(mix: List[Tuple[int, float]]) -> str:
    """
    Format polygon mixture as '+'-joined unique side counts (no weights).

    :param mix: Mixture list ``(sides, weight)``.
    :type mix: List[Tuple[int, float]]
    :returns: String such as ``"8+5"``.
    :rtype: str
    """
    sides = sorted({int(s) for s, w in mix if w > 0}, reverse=True)
    return "+".join(str(s) for s in sides)


def _fmt_oligs_simple(pmf: Dict[int, float]) -> str:
    """
    Format an oligomer PMF with short labels and probabilities.

    :param pmf: Dict ``k → probability``.
    :type pmf: Dict[int, float]
    :returns: String like ``"mono0.9-di0.1-tri0.05"``.
    :rtype: str
    """
    names = {1: "mono", 2: "di", 3: "tri", 4: "tetra", 5: "penta", 6: "hexa", 7: "hepta", 8: "octa"}
    parts = []
    for k in sorted(pmf):
        label = names.get(k, f"k{k}")
        parts.append(f"{label}{_fmtf(pmf[k])}")
    return "-".join(parts)


def _ensure_prefix(prefix: Optional[str]) -> Optional[str]:
    """
    Clean an output prefix, stripping a trailing ``.h5`` if provided.

    :param prefix: User-provided output prefix or path.
    :type prefix: Optional[str]
    :returns: Cleaned prefix without the extension, or ``None``.
    :rtype: Optional[str]
    """
    if not prefix:
        return None
    return prefix[:-3] if prefix.lower().endswith(".h5") else prefix


# =============================================================================
# CLI
# =============================================================================

def main(argv=None):
    """
    Command-line entry point.

    Notes on global vs subcommand options
    -------------------------------------
    The main parser defines global options (e.g. ``--plot``). With argparse,
    any global option must appear *before* the subcommand token on the command
    line unless that option is also re-declared on the subparser. Here, ``--plot``
    is global-only, so it should be placed before ``poly`` or ``grid``.

    :param argv: Optional argument vector override (useful for testing).
    :type argv: Optional[Sequence[str]]
    :returns: ``None``.
    :rtype: None
    """
    ap = argparse.ArgumentParser(
        description="Simulate MINFLUX-like data: 'poly' (polygons/oligomers) or 'grid' (DNA-origami style).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    ap.add_argument("-o", "--o", "--output", dest="output", required=False, default=None,
                    help="Output prefix (no extension). A succinct descriptor and '.h5' are appended.")
    ap.add_argument("--xrange", type=float, nargs=2, required=True, metavar=("XMIN", "XMAX"))
    ap.add_argument("--yrange", type=float, nargs=2, required=True, metavar=("YMIN", "YMAX"))
    ap.add_argument("--centroid-mean", type=float, required=True,
                    help="Poisson mean for number of groups (poly chains or grids).")

    # Shared measurement / noise / clutter controls
    ap.add_argument("--p", type=float, default=0.7, help="Emitter labelled probability.")
    ap.add_argument("--q", type=float, default=0.8, help="Per-measurement signal probability.")
    ap.add_argument("--measured", type=float, default=7,
                    help="Poisson mean measurements per labelled emitter/cluster.")
    ap.add_argument("--gt-uncertainty", type=float, default=0.0, help="Ground-truth jitter sigma (absolute units).")
    ap.add_argument("--ms-uncertainty", type=float, default=1.0, help="Measurement noise sigma (absolute units).")
    ap.add_argument("--clutter-fraction", type=float, default=None,
                    help="Number of clutter clusters = floor(fraction × N_labelled_emitters).")
    ap.add_argument("--plot", action="store_true", help="Show 2D plot after simulation.")
    ap.add_argument("--seed", type=int, default=None, help="Random seed.")

    sub = ap.add_subparsers(dest="mode", required=True, metavar="{poly,grid}")

    # ---- poly subcommand
    ap_poly = sub.add_parser("poly", help="Polygonal monomers (oligomer chains).")
    ap_poly.add_argument("--radius", type=float, required=True, help="Monomer circumradius.")
    ap_poly.add_argument("--mix", type=str, required=True,
                         help="Geometry mixture, e.g. 'polygon:8@1.0,polygon:5@0.4'.")
    ap_poly.add_argument("--oligomers", type=str, default=None,
                         help="Oligomer PMF, e.g. '1:1.0,2:0.1,3:0.05' (default mono only).")
    enf_group = ap_poly.add_mutually_exclusive_group()
    enf_group.add_argument("--enforce-shared-edge", dest="enforce_shared_edge", action="store_true",
                           help="Keep shared-edge vertices coincident across neighbouring monomers (default).")
    enf_group.add_argument("--no-enforce-shared-edge", dest="enforce_shared_edge", action="store_false",
                           help="Do not enforce coincidence on shared edges.")
    ap_poly.set_defaults(enforce_shared_edge=True)
    ap_poly.add_argument("--store-edges", action="store_true",
                         help="Store fully connected edges per monomer (expensive).")

    # ---- grid subcommand
    ap_grid = sub.add_parser("grid", help="DNA-origami style grids.")
    ap_grid.add_argument("--grid", type=int, nargs=2, metavar=("ROWS", "COLS"), required=True,
                         help="Grid dimensions (rows, cols).")
    ap_grid.add_argument("--sep", type=float, required=True,
                         help="Separation between adjacent grid nodes (absolute units).")

    args = ap.parse_args(argv)
    if args.seed is not None:
        np.random.seed(args.seed)

    prefix = _ensure_prefix(args.output)

    if args.mode == "poly":
        # Prepare geometry and oligomer distributions from string specs.
        geom_mix = parse_mix(args.mix)
        oligomer_pmf = parse_oligomers(getattr(args, "oligomers", None))

        # Naming: poly, olig, p, q, cl, mu, R, gt, ms, SE[, seed]
        parts = [
            f"poly-{_fmt_poly(geom_mix)}",
            f"olig-{_fmt_oligs_simple(oligomer_pmf)}",
            f"p-{_fmtf(args.p)}",
            f"q-{_fmtf(args.q)}",
            f"cl-{_fmtf(0.0 if args.clutter_fraction is None else args.clutter_fraction)}",
            f"mu-{_fmtf(args.centroid_mean)}",
            f"R-{_fmtf(args.radius)}",
            f"gt-{_fmtf(args.gt_uncertainty)}",
            f"ms-{_fmtf(args.ms_uncertainty)}",
            ("SE" if args.enforce_shared_edge else "nSE"),
        ]
        if args.seed is not None:
            parts.append(f"seed-{args.seed}")
        desc = "_".join(parts)
        out_path = None if prefix is None else f"{prefix}_{desc}.h5"

        # Run the simulation and, if a prefix is supplied, write the HDF5 file.
        data = simulate_poly(
            filename=out_path,
            xrange=tuple(args.xrange),
            yrange=tuple(args.yrange),
            centroid_mean_groups=args.centroid_mean,
            radius=args.radius,
            geom_mix=geom_mix,
            oligomer_pmf=oligomer_pmf,
            p=args.p, q=args.q,
            measured=args.measured,
            gt_uncertainty=args.gt_uncertainty,
            ms_uncertainty=args.ms_uncertainty,
            clutter_fraction=args.clutter_fraction,
            membrane_function=None,
            enforce_shared_edge=args.enforce_shared_edge,
            store_edges=args.store_edges,
            seed=args.seed,
        )

    else:  # grid
        # Unpack grid dimensions and separation; compute R for metadata/naming.
        rows, cols = args.grid
        sep = args.sep
        offsets = grid_node_offsets(rows, cols, sep)
        R = grid_effective_R(offsets)

        # Naming: grid, sep, p, q, cl, mu, R, gt, ms[, seed]
        parts = [
            f"grid-{rows}x{cols}",
            f"sep-{_fmtf(sep)}",
            f"p-{_fmtf(args.p)}",
            f"q-{_fmtf(args.q)}",
            f"cl-{_fmtf(0.0 if args.clutter_fraction is None else args.clutter_fraction)}",
            f"mu-{_fmtf(args.centroid_mean)}",
            f"R-{_fmtf(R)}",
            f"gt-{_fmtf(args.gt_uncertainty)}",
            f"ms-{_fmtf(args.ms_uncertainty)}",
        ]
        if args.seed is not None:
            parts.append(f"seed-{args.seed}")
        desc = "_".join(parts)
        out_path = None if prefix is None else f"{prefix}_{desc}.h5"

        # Run the grid simulation, mirroring the poly branch structure.
        data = simulate_grid(
            filename=out_path,
            xrange=tuple(args.xrange),
            yrange=tuple(args.yrange),
            centroid_mean_groups=args.centroid_mean,
            rows=rows,
            cols=cols,
            sep=sep,
            p=args.p, q=args.q,
            measured=args.measured,
            gt_uncertainty=args.gt_uncertainty,
            ms_uncertainty=args.ms_uncertainty,
            clutter_fraction=args.clutter_fraction,
            membrane_function=None,
            seed=args.seed,
        )

    if args.plot:
        # Show a quick 2D overview in the browser or notebook.
        plot2d(data=data, filename=None)


if __name__ == "__main__":
    # Avoid .pyc for tidier output directories
    sys.dont_write_bytecode = True
    main()
