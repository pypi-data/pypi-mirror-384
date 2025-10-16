from __future__ import annotations

"""probabilistic_pareto_sampler.py

Stochastic Pareto‑aware selector with:
- Independent objective fusion temperature (`objective_temperature`)
- Separate sampling temperature (`sampling_temperature`)
- Optional objective normalization
- Diversity promotion and repetition penalization

Key formulas:
  • Shift: f'_ik = f_ik − min_k(f_ik) ≥ 0
  • Normalize (optional): \tilde f = (f' − mean_k)/std_k
  • Boltzmann fusion:
        Z_i = ∑_k w_k·exp(−fusion_k / T_obj)
        F_i = −T_obj·ln(Z_i + ε)
  • Cost before sampling:
        C_i = F_i − λ·R_i + κ·c_i
  • Sampling with T_samp:
        p_i ∝ exp(−C_i / T_samp)

Unit tests validate shape, distribution smearing, and diversity repulsion.
"""

from dataclasses import dataclass, field
from typing import Optional, Sequence
import unittest

import numpy as np
from sklearn.metrics import pairwise_distances
from scipy.special import logsumexp
from ..core.interfaces import ISelector

__all__ = ["Selector"]

_EPS = 1e-12

# Canonical IDs and accepted aliases (lowercased)
_CANONICAL = {
    # Multi-objective soft fusion + Boltzmann sampling (you already have this)
    "boltzmann": {"boltzmann", "stochastic", "softmin", "gumbel_topk"},

    "boltzmann_bigdata": {
        "boltzmann_bigdata", "big_boltzmann", "boltzmann_large",
        "bigdata", "big_data_boltzmann"
    },

    # Fitness-proportionate (roulette wheel)
    "roulette": {"roulette", "roulette_wheel", "fps"},

    # Non-dominated sorting (Pareto rank only)
    "pareto_rank": {"nondominated_sorted", "non_dominated_sort", "nds", "ns"},

    # NSGA-III environmental selection
    "nsga3": {"nsga3", "nsga-iii", "nsga3_environmental"},

    # NEW — Greedy (deterministic truncation) using your fused objective F
    "greedy": {"greedy", "truncation", "elitist", "greedy_boltzmann", "greedy_fusion"},

    # NEW — Tournament on fused objective F (deterministic best-of-k)
    "tournament": {"tournament", "k_tournament", "deterministic_tournament"},


    # Rank-based selection (roulette on ranks)
    #"rank_proportionate": {"rank_based", "rank_roulette", "linear_rank", "exponential_rank", "exp_rank"},
    # Stochastic Universal Sampling
    #"sus": {"stochastic_universal_sampling", "sus"},
    # Pareto-based tournament (dominance wins, tie-break by distance/crowding)
    #"pareto_tournament": {"mo_tournament", "dominance_tournament"},
}

# -------- safe log helpers (warning-free, preserve correct ±inf) --------
def log_clipped(x, eps: float = _EPS):
    """Return log(x) with x clipped away from 0."""
    return np.log(np.clip(x, eps, None))

def log1m(p, eps: float = _EPS):
    """Return log(1 - p) with exact -inf at p>=1-eps, no warnings."""
    p = np.asarray(p, dtype=np.float64)
    with np.errstate(divide="ignore"):
        y = np.log1p(-np.clip(p, 0.0, 1.0))
    y[p >= 1.0 - eps] = -np.inf
    return y

def neg_log1m(p, eps: float = _EPS):
    """Return -log(1 - p) with exact +inf at p>=1-eps, no warnings."""
    p = np.asarray(p, dtype=np.float64)
    with np.errstate(divide="ignore"):
        y = -np.log1p(-np.clip(p, 0.0, 1.0))
    y[p >= 1.0 - eps] = np.inf
    return y

def _canonicalize(name: str) -> str:
    name = (name or "").lower()
    for canon, aliases in _CANONICAL.items():
        if name == canon or name in aliases:
            return canon
    raise ValueError(f"Unknown selection_method: {name!r}")

def _repulsion_score(
    cand_feat: np.ndarray,
    sel_feat: np.ndarray,
    metric: str,
    mode: str,
    eps: float = _EPS,
    comp_weight: float = 0.0,       # NEW
    comp_decimals: int = 0,         # NEW
) -> np.ndarray:
    if sel_feat.size == 0:
        return np.zeros(cand_feat.shape[0])

    # --- distance-based part (unchanged) ---
    dmat = pairwise_distances(cand_feat, sel_feat, metric=metric)
    if mode == "avg":
        dvals = dmat.mean(axis=1)
    elif mode == "min":
        dvals = dmat.min(axis=1)
    elif mode == "max":
        dvals = dmat.max(axis=1)
    else:
        raise ValueError("repulsion_mode must be 'avg', 'min', or 'max'.")

    # Base repulsion: larger when close
    rep = np.log(1.0 / (dvals + eps))

    # --- composition multiplicity penalty (NEW) ---
    if comp_weight > 0.0:
        if np.issubdtype(cand_feat.dtype, np.integer) and np.issubdtype(sel_feat.dtype, np.integer):
            # exact integer equality
            eq = (cand_feat[:, None, :] == sel_feat[None, :, :]).all(axis=2)
        else:
            # float compositions: compare after rounding
            cf = np.round(cand_feat, comp_decimals)
            sf = np.round(sel_feat, comp_decimals)
            eq = (cf[:, None, :] == sf[None, :, :]).all(axis=2)
        m = eq.sum(axis=1)                   # how many selected share the same composition
        rep = rep + comp_weight * np.log1p(m)  # add β·log(1+m)

    return rep


@dataclass
class Selector(ISelector):
    """Probabilistic selector for multi‑objective optimisation.

    Parameters
    ----------
    weights : Optional[np.ndarray]
        Importance of each objective (sum to 1). Default equal.
    repulsion_weight : float
        λ ≥ 0, diversity strength.
    objective_temperature : float
        T_obj ≥ 0, acts on objectives (same units as f).
    sampling_temperature : float
        T_samp ≥ 0, scales sampling sharpness.
    normalize_objectives : bool
        If True, apply zero‑mean, unit‑variance normalization after shift.
    repetition_penalty : bool
        γ ∈ (0,1], multiplicative penalty per repeat.
    size : int
        Number of structures to select.
    repulsion_mode : str
        'avg', 'min', or 'max'.
    metric : str
        Distance metric for pairwise_distances.
    random_seed : Optional[int]
        For reproducibility.
    """
    # —————————————————————————————————————————————
    # Public API fields hyper‑parameters (all optional, with defaults)
    # —————————————————————————————————————————————

    # --- Core objective fusion & sampling ---
    weights: Optional[np.ndarray]   = None   # per-objective weights w_k (normalized internally); None → uniform
    objective_temperature: float    = 1.0    # T_obj ≥ 0: softness of multi-objective fusion (lower → sharper Pareto emphasis)
    sampling_temperature: float     = 1.0    # T_samp ≥ 0: sampling greediness (lower → greedier; higher → more exploratory)
    normalize_objectives: bool      = False  # if True: robust per-objective normalization after shifting baseline

    # --- Selection size ---
    size: int                       = 1      # number of survivors to pick per call

    # --- Diversity (intra-call) ---
    repulsion_weight: float         = 1.0    # λ ≥ 0: strength of diversity repulsion term
    repulsion_mode: str             = "min"  # {'min','avg','max'}: how candidate-to-selected distances are summarized
    metric: str                     = "manhattan"  # pairwise distance metric (sklearn-style); FAISS path uses Euclidean
    composition_repulsion_weight: float = 8.0  # β ≥ 0: stronger penalty for repeating the same composition
    composition_decimals: int       = 0      # rounding for float composition equality (if features encode composition)

    # --- Repetition memory (within-call) ---
    repetition_penalty: bool        = True   # down-weight/forbid overused items via counts-based penalty
    steepness: float                = 10.0   # shape of repetition penalty curve
    max_count: int                  = 100    # repetition horizon used by the penalty
    cooling_rate: float             = 0.1    # per-call decay of counts (higher → forget faster)
    counts: Optional[np.ndarray]    = None   # optional external counts; if None, managed internally

    # --- Method selection ---
    selection_method: str           = "boltzmann"  # {'boltzmann','roulette','greedy','tournament','pareto_rank','nsga3'}
    random_seed: Optional[int]      = None   # RNG seed for reproducibility

    # --- NSGA-III controls (only used when selection_method='nsga3') ---
    divisions: int                  = 12     # Das–Dennis reference directions granularity

    # --- Tournament auto-sizing (only used when selection_method='tournament') ---
    t_min: int                      = 2      # lower bound on tournament size
    t_max: int                      = 32     # upper bound on tournament size
    t_center_temperature: float     = 1.0    # T_samp at which tournament size is mid-point
    t_shape: float                  = 2.0    # steepness of t(T_samp) decay

    # --- Big-data screening (CPU-only) ---
    preselect_size: int            = 50_000     # L: shortlist size kept in RAM
    chunk_size: int                = 1_000_000  # rows per streaming chunk during screening
    use_float32: bool              = True       # downcast working arrays to float32
    repulsion_update_stride: int   = 1          # update distance cache every s picks (>=1)

    # --- Neighbour backend (NumPy-only grid hashing) ---
    neighbor_backend: str          = "grid"     # {"grid","none"}
    grid_bins: int                 = 32         # bins per projected dimension (8..64 typical)
    grid_radius: int               = 0          # 0=same cell; 1=include adjacent cells (limit d<=8)
    grid_max_neighbors: int        = 4096       # cap neighbours updated per pick
    grid_fallback_every: int       = 0          # 0=never; e.g. 10 = full update every 10 picks

    # --- Lightweight random projection for the grid (keeps memory small in high-D) ---
    grid_use_projection: bool      = True       # project features to d<<D for grid only
    grid_proj_dim: int             = 16         # projected dims for grid (8..16 typical)
    grid_proj_seed: int            = 12345



    # —————————————————————————————————————————————
    # Internal state (not passed by user)
    # —————————————————————————————————————————————
    _rng: np.random.Generator       = field(init=False, repr=False)  # RNG instance; set in __post_init__

    # ==========================================================================
    #                         Life‑cycle helpers
    # ==========================================================================
    def __post_init__(self):
        if self.objective_temperature < 0:
            raise ValueError("objective_temperature must be non‑negative")
        if self.sampling_temperature < 0:
            raise ValueError("sampling_temperature must be non‑negative")
        if not isinstance(self.repetition_penalty, bool):
            raise ValueError("repetition_penalty must be a bool")
        self._rng = np.random.default_rng(self.random_seed)

        self.selection_method = _canonicalize(self.selection_method)

    # ----------------------------------------------------------------------
    #                          Utility functions
    # ----------------------------------------------------------------------
    def set_temperature(self, temperature):
        """
        """
        self.sampling_temperature = temperature
        return True

    @staticmethod
    def _normalize_objectives(objectives, eps:float=_EPS, method:str='robust'):
        """
        Min-max normalize each objective column to [0, 1].

        Parameters
        ----------
        objectives : np.ndarray, shape (N, K)
            Raw objective scores (lower is better).
        eps : float
            Small value to avoid division by zero.

        Returns
        -------
        np.ndarray
            Normalized objectives in [0, 1].
        """
        if method == 'robust':
            med = np.median(objectives, axis=0)
            mad = np.median(np.abs(objectives - med), axis=0) + eps
            return (objectives - med) / mad

        else:
            normed = np.zeros_like(objectives)
            for j in range(objectives.shape[1]):
                col = objectives[:, j]
                cmin, cmax = col.min(), col.max()
                span = cmax - cmin
                if span < eps:
                    normed[:, j] = 0.0
                else:
                    normed[:, j] = (col - cmin) / span
            return normed

    #@staticmethod
    def _penalty( self, counts: np.ndarray ) -> np.ndarray:
        """
        Returns for each index i a penalty p_i ∈ [0,1], where
          p_i = 0 → no change,
          p_i = 1 → zero probability.
        """
        # your existing “steepness” shape
        raw = (np.tanh(self.steepness * (0.5 - counts/self.max_count)) + 1.0)  / (np.tanh(self.steepness * 0.5) + 1.0)  
        # raw ∈ (–1, +1); map it so that:
        #   raw = +1 → p = 0
        #   raw = –1 → p = 1
        p = (1.0 - raw) / 1.0
        # ensure strict bounds
        return np.clip(p, 0.0, 1.0)

    def _fused_objective(self, f_adj: np.ndarray, w: np.ndarray) -> np.ndarray:
        """
        Compute fused multi-objective scores F_i using stable log-sum-exp and objective_temperature.
        Lower is better.
        """
        T_obj = self.objective_temperature + _EPS
        log_w = np.log(np.clip(w, _EPS, None))

        # F_i = -T_obj * logsumexp( (-f_adj/T_obj) + log_w, axis=1 )
        a = (-f_adj / T_obj) + log_w[None, :]
        # clip extreme values to keep useful dynamic range
        a = np.clip(a, -50.0, 50.0, out=a)

        return -T_obj * logsumexp(a, axis=1)

    def _add_repulsion(self, base_cost: np.ndarray, features: np.ndarray, sel_feat: np.ndarray) -> np.ndarray:
        """
        Add diversity repulsion term (scaled by repulsion_weight). Repulsion score is negative for far points,
        so adding it with positive lambda reduces the cost of far-away candidates.
        """
        cost = base_cost.copy()
        if self.repulsion_weight > 0 and sel_feat.size:
            rep = _repulsion_score(
                features, sel_feat,
                metric=self.metric,
                mode=self.repulsion_mode,
                eps=_EPS,
                comp_weight=self.composition_repulsion_weight,   # NEW
                comp_decimals=self.composition_decimals,         # NEW
            )
            cost += self.repulsion_weight * rep
        return cost

    def _add_repetition_cost(self, cost: np.ndarray) -> np.ndarray:
        """
        Deterministic counterpart to the stochastic logit penalty: add -log(1 - p(count)).
        This is >= 0 and increases with overuse.
        """
        if self.repetition_penalty:
            p = self._penalty(self.counts)          # in [0,1]
            cost += neg_log1m(p)           # -log(1-p); is +inf when p=1
        return cost

    def _repetition_logit_penalty(self) -> np.ndarray:
        """
        Log-space repetition penalty term to be ADDED to sampling logits.
        Returns a length-N vector in [-inf, 0]. If repetition_penalty is off,
        returns zeros. When p(count)=1 -> log(1-1) = -inf (exact zero prob).
        """
        if not self.repetition_penalty:
            # ensure dtype aligns with downstream ops
            return np.zeros_like(self.counts, dtype=np.float64)
        p = self._penalty(self.counts).astype(np.float64)  # p in [0,1]
        return log1m(p)  # in [-inf, 0], warning-free

        #return np.log1p(-p)  # in [-inf, 0]

    def _effective_weights(self, f_adj: np.ndarray, w: np.ndarray,
                           tol: float = 1e-12, beta: float = 1.0) -> np.ndarray:
        # dispersion per objective (use robust MAD if you prefer)
        s = np.std(f_adj, axis=0)
        # zero-out degenerate objectives; optionally reweight by dispersion^beta
        w_eff = w * np.where(s > tol, (s + tol)**beta, 0.0)
        S = w_eff.sum()
        if S <= 0:          # fallback: if all degenerate, keep original
            return w / w.sum()
        return w_eff / S


    # ----------  BIG DATA HELPERS ----------
    # ---------- Streaming stats / screening ----------
    def _estimate_shift(self, objectives: np.ndarray) -> np.ndarray:
        """Chunked per-column minima (works for huge N)."""
        K = objectives.shape[1]
        fmin = np.full(K, np.inf, dtype=np.float64)
        for start in range(0, objectives.shape[0], self.chunk_size):
            sl = slice(start, min(start + self.chunk_size, objectives.shape[0]))
            fmin = np.minimum(fmin, objectives[sl].min(axis=0))
        return fmin

    def _preselect_topL(self, objectives: np.ndarray, f_min: np.ndarray, w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Streaming fused objective → keep top-L indices and their fused costs (lower=better)."""
        N = objectives.shape[0]
        L = min(self.preselect_size, N)
        F_vals = np.empty(0, dtype=np.float32)
        Idx    = np.empty(0, dtype=np.int64)

        for start in range(0, N, self.chunk_size):
            sl = slice(start, min(start + self.chunk_size, N))
            f_adj = objectives[sl].astype(np.float32 if self.use_float32 else np.float64, copy=False) - f_min
            if self.normalize_objectives:
                f_adj = self._normalize_objectives(f_adj)
            F_chunk = self._fused_objective(f_adj, w).astype(np.float32, copy=False)

            if Idx.size == 0:
                if F_chunk.size > L:
                    keep = np.argpartition(F_chunk, L - 1)[:L]
                    F_vals = F_chunk[keep]
                    Idx    = (start + keep).astype(np.int64, copy=False)
                else:
                    F_vals = F_chunk
                    Idx    = (start + np.arange(F_chunk.size)).astype(np.int64, copy=False)
            else:
                F_vals = np.concatenate([F_vals, F_chunk])
                Idx    = np.concatenate([Idx, (start + np.arange(F_chunk.size)).astype(np.int64, copy=False)])
                if F_vals.size > L:
                    keep = np.argpartition(F_vals, L - 1)[:L]
                    F_vals, Idx = F_vals[keep], Idx[keep]
        return Idx, F_vals

    # ---------- Repulsion cache (min L1 to selected) ----------
    def _estimate_l1_scale(self, feat: np.ndarray, sample: int = 2048) -> float:
        """Median L1 distance from a small sample (for finite initialisation)."""
        rng = np.random.default_rng(0)
        n = min(sample, feat.shape[0])
        idx = rng.choice(feat.shape[0], size=n, replace=False)
        A = feat[idx]
        idx2 = rng.choice(feat.shape[0], size=n, replace=True)
        B = feat[idx2]
        d = np.abs(A - B).sum(axis=1, dtype=np.float32)
        return float(np.median(d) + 1e-6)

    def _init_repulsion_cache_scaled(self, N: int, init_dist: float) -> dict:
        return {"closest": np.full(N, init_dist, dtype=np.float32)}

    def _repulsion_from_cache(self, cache: dict, eps: float = _EPS) -> np.ndarray:
        return np.log(1.0 / (cache["closest"] + eps), dtype=np.float32)

    def _update_repulsion_cache_chunked(self, cache: dict, cand_feat: np.ndarray, new_feat: np.ndarray, chunk_size: int) -> None:
        closest = cache["closest"]
        for start in range(0, cand_feat.shape[0], chunk_size):
            sl = slice(start, min(start + chunk_size, cand_feat.shape[0]))
            d = np.abs(cand_feat[sl] - new_feat[None, :]).sum(axis=1, dtype=np.float32)
            closest[sl] = np.minimum(closest[sl], d)

    # ---------- Lightweight random projection for the grid ----------
    def _make_projection(self, D: int, d: int) -> np.ndarray:
        rng = np.random.default_rng(self.grid_proj_seed)
        return rng.normal(size=(D, d)).astype(np.float32, copy=False)

    def _project_feats(self, X: np.ndarray, R: np.ndarray) -> np.ndarray:
        return (X @ R).astype(np.float32, copy=False)

    # ---------- Grid hashing (sparse buckets; memory-safe) ----------
    def _grid_normalize(self, feats: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        fmin = feats.min(axis=0)
        fmax = feats.max(axis=0)
        frng = np.maximum(fmax - fmin, 1e-12)
        X = (feats - fmin) / frng
        return X.astype(np.float32, copy=False), fmin.astype(np.float32), frng.astype(np.float32)

    def _grid_build_sparse(self, feats_norm: np.ndarray, bins: int) -> dict:
        """Return dict: cell_key(tuple ints) → np.int32 indices. No L×d bin matrix kept."""
        L = feats_norm.shape[0]
        buckets: dict[tuple, list] = {}
        Z = np.clip(feats_norm, 0.0, 1.0 - np.finfo(np.float32).eps)
        for i in range(L):
            key = tuple((Z[i] * bins).astype(np.int32))
            if key in buckets:
                buckets[key].append(i)
            else:
                buckets[key] = [i]
        return {k: np.asarray(v, dtype=np.int32) for k, v in buckets.items()}

    def _grid_enumerate_offsets(self, d: int, radius: int) -> list[tuple]:
        if radius <= 0:
            return [tuple(0 for _ in range(d))]
        if radius > 1 or d > 8:
            return [tuple(0 for _ in range(d))]  # guard combinatorial blow-up
        from itertools import product
        return list(product([-1, 0, 1], repeat=d))

    def _grid_neighbors(self, buckets: dict, x_bin: np.ndarray, bins: int, radius: int,
                        max_neighbors: int, L: int, selected_mask: np.ndarray) -> np.ndarray:
        d = x_bin.size
        out = []
        for off in self._grid_enumerate_offsets(d, radius):
            nb = np.clip(x_bin + np.array(off, dtype=np.int32), 0, bins - 1)
            ids = buckets.get(tuple(nb))
            if ids is not None:
                out.append(ids)
        if not out:
            return np.empty(0, dtype=np.int32)
        I = np.concatenate(out)
        if selected_mask is not None and selected_mask.size == L:
            I = I[~selected_mask[I.astype(np.intp)]]
        if I.size > max_neighbors:
            I = I[:max_neighbors]
        return I

    def _update_cache_with_subset(self, cache: dict, feats_pool: np.ndarray, new_feat: np.ndarray, subset_ids: np.ndarray) -> None:
        if subset_ids.size == 0:
            return
        I = subset_ids.astype(np.intp, copy=False)
        d = np.abs(feats_pool[I] - new_feat[None, :]).sum(axis=1, dtype=np.float32)
        cache["closest"][I] = np.minimum(cache["closest"][I], d)


    # ==========================================================================
    #                               API
    # ==========================================================================
    def select( self, objectives, features, size: Optional[int]=None) -> np.ndarray:
        r"""
        Stochastically select a Pareto‐aware subset of candidates.

        This method implements a two‐temperature probabilistic Pareto sampler with
        optional diversity repulsion and repetition penalization.  The selection
        probability is computed in three stages:

        1. **Objective fusion**  
           Given raw objectives \\(f_{ik}\\) for candidates \\(i=1,\dots,N\\), \\(k=1,\dots,K\\):
           a. **Shift** to non‐negative:  
              .. math::
                 f'_{ik} = f_{ik} \;-\; \min_{i}(f_{ik}),
                 \quad f'_{ik}\ge0.
           b. **Optional normalization** (zero‐mean, unit‐variance per objective):  
              .. math::
                 \tilde f_{ik} = \frac{f'_{ik} - \mu_k}{\sigma_k}.
           c. **Boltzmann fusion** at objective‐temperature \\(T_{\rm obj}\\):  
              .. math::
                 F_i = -T_{\rm obj}\,\ln\!\Bigl(\sum_{k=1}^K w_k \,\exp\bigl(\,-\,\tfrac{f'_{ik}}{T_{\rm obj}}\bigr)\Bigr),
              where \\(w_k\\) are objective weights (\\(\sum_k w_k=1\\)).

        2. **Cost assembly**  
           Starting from fused scores \\(F_i\\), add:
           - **Diversity repulsion** (if \\(\lambda>0\\)):  
             .. math::
               R_i = \mathrm{repulsion\_score}\bigl(\mathbf{x}_i,\,X_{\rm sel}\bigr),
               \quad
               C_i = F_i \;-\;\lambda\,R_i,
           - **Repetition penalty** (if enabled, with per‐candidate count \\(c_i\\)):  
             in log‐space by adding  
             .. math::
               \Delta \ell_i = \ln(1 - p(c_i)),
             so that final sampling logit is  
             \\(\ell_i = -C_i/T_{\rm samp} + \Delta \ell_i.\\)

        3. **Sampling**  
           Draw without replacement via the Gumbel–Max trick at sampling temperature
           \\(T_{\rm samp}\\):  
           .. math::
             g_i \sim \mathrm{Gumbel}(0,1),\quad
             \hat \ell_i = \frac{-C_i}{T_{\rm samp}} + g_i + \ln(1-p(c_i)),
             \quad
             \text{select }i^* = \arg\max_i \hat \ell_i.
           Repeat until `size` distinct indices are chosen, updating repetition counts
           and repulsion set after each pick. Finally, apply a “cooling” step:
           .. math::
             c_i \leftarrow \max\{c_i - \gamma,\,0\}.

        :param objectives:
            Array of shape \\((N,K)\\) with raw objective values (minimization).
        :type objectives: numpy.ndarray
        :param features:
            Array of shape \\((N,D)\\) with feature vectors used for diversity repulsion.
        :type features: numpy.ndarray
        :param size:
            Number of distinct candidates to select; defaults to `self.size`.
        :type size: int, optional
        :returns:
            Array of length `size` containing the selected candidate indices.
        :rtype: numpy.ndarray

        :raises ValueError:
            If inputs are not 2-D, shapes mismatch, `size` not in \\([1,N]\\), or contain non-finite values.
        """

        # ---------- Input validation ----------
        # Ensure float64 precision
        # Ensure correct dtype and shapes 
        # Sanity checks
        size = int(size or self.size)

        objectives, features, size = self._sanity_check(objectives, features, size, repare=True)
        
        N, K = objectives.shape
        method = self.selection_method

        if method == 'nsga3':
            sel_idx = self.NSGA3(objectives=objectives, features=features, size=size)

        elif method == 'pareto_rank':   
            sel_idx = self.NS(objectives=objectives, features=features, size=size)

        else:
            # ---------- ---------- Pre‑compute common terms ---------- ----------
            # Otherwise: stochastic two-temperature Pareto sampler
            # ===== original code continues =====
            # 2) Prepare weights
            # weights
            w = np.ones(K, dtype=np.float64) / K if self.weights is None else np.asarray(self.weights, dtype=np.float64)
            if w.size != K:
                raise ValueError("weights length mismatch")

            # sanitize and normalize
            w = np.nan_to_num(w, nan=0.0, posinf=0.0, neginf=0.0)  # drop NaN/±inf to 0
            w[w < 0.0] = 0.0                                       # enforce non-negativity
            s = w.sum(dtype=np.float64)
            w = (np.ones(K)/K) if (not np.isfinite(s) or s <= _EPS) else (w / s)

            # 3) Zero‐baseline and optional normalization
            # For big-data path we need just f_min (chunked)
            f_min = self._estimate_shift(objectives)

            sel_feat = np.empty((0, features.shape[1]))
            sel_idx: list[int] = []

            # optional normalization
            #if self.normalize_objectives:
            #    f_adj = self._normalize_objectives(f_adj)

            # robust reweighting (kills constant objectives)
            #w = self._effective_weights(f_adj, w, tol=1e-12, beta=1.0)

            # 4) Initialize or pad counts
            if isinstance(self.counts, np.ndarray):
                self.counts = np.pad(self.counts, (0, max(0, N - self.counts.size)), mode='constant')
            else:
                self.counts = np.zeros(N, dtype=np.float32)
            self.counts[self.counts<0] = 0
            self.counts = (np.zeros(N, dtype=np.float32) if not isinstance(self.counts, np.ndarray) 
               else np.pad(self.counts.clip(min=0).astype(np.float32),
                           (0, max(0, N - self.counts.size)),
                           mode='constant')[:N])
            
            sel_idx: list[int] = []
            sel_feat = np.empty((0, features.shape[1]))


            if method == 'boltzmann_bigdata':
                sel_idx = self.boltzmann_bigdata(objectives=objectives, features=features, f_min=f_min, w=w, size=size)

            elif method == 'roulette':
                f_adj = objectives - f_min
                sel_idx = self.roulette(features=features, objectives=objectives, f_adj=f_adj, sel_feat=sel_feat, size=size)

            elif method == 'boltzmann':   
                f_adj = objectives - f_min
                sel_idx = self.boltzmann(features=features, objectives=objectives, f_adj=f_adj, sel_feat=sel_feat, size=size, w=w)

            elif method == 'greedy':
                f_adj = objectives - f_min
                sel_idx = self.greedy(features=features, f_adj=f_adj, sel_feat=sel_feat, size=size, w=w)

            elif method == 'tournament':
                f_adj = objectives - f_min
                sel_idx = self.tournament(features=features, f_adj=f_adj, sel_feat=sel_feat, size=size, w=w)


        return np.asarray(sel_idx, dtype=int)

    # ===================================================================
    #                         Mode: NSGA‑III
    # ===================================================================
    def NSGA3(self, objectives, features, size):
        """
        """
        # ===== NSGA-III selection: non-dominated sort + reference-point niching =====

        N, K = objectives.shape
        fronts = self._non_dominated_sort(objectives)
        selected: list[int] = []
        # fill entire fronts until last
        for front in fronts:
            if len(selected) + len(front) <= size:
                selected.extend(front)
                continue
            # need to fill remaining via niching
            rem = size - len(selected)
            ref_dirs = self._generate_reference_dirs(K, self.divisions)
            niche_sel = self._reference_point_niching(objectives, front, ref_dirs, rem)
            selected.extend(niche_sel)
            break

        return np.asarray(selected, dtype=int)

    # ===================================================================
    #                         Mode: Non‑dominated sort only
    # ===================================================================
    def NS(self, objectives, features, size):
        """
        """
        # ===== Simple non-dominated sort =====

        fronts = self._non_dominated_sort(objectives)
        selected: list[int] = []
        for front in fronts:
            for idx in front:
                if len(selected) < size:
                    selected.append(idx)
                else:
                    break
            if len(selected) >= size:
                break

        return np.asarray(selected, dtype=int)


    # ===================================================================
    #                         Mode: *Roulette‑wheel*
    # ===================================================================
    def roulette(self, features, objectives, f_adj, sel_feat, size,):
        """
        """
        # ===== roulette + repetition + repulsion =====
        sel_idx: list[int] = []
        N, K = objectives.shape

        for _ in range(size):
            cost = np.sum(f_adj, axis=1)
            # Diversity repulsion term
            if self.repulsion_weight > 0 and sel_feat.size:
                cost += self.repulsion_weight * _repulsion_score(
                    features, sel_feat, self.metric, self.repulsion_mode)

            # Convert to fitness (higher‑is‑better)
            
            fitness = -cost
            if fitness.ndim > 1:  # Safety: ensure 1‑D for broadcasting
                fitness = fitness.ravel()

            # Repetition penalty (multiplicative on fitness)
            if self.repetition_penalty:
                penalty_mask = 1.0 - self._penalty(self.counts)
                fitness *= penalty_mask

            # Zero out already picked indices
            if sel_idx:
                fitness[sel_idx] = 0.0

            probs = self._probs_sanity_check(fitness)
            if sel_idx:
                probs[sel_idx] = 0.0
                s = probs.sum()
                if s <= 0.0:
                    avail = np.setdiff1d(np.arange(N), np.asarray(sel_idx), assume_unique=False)
                    probs[avail] = 1.0 / avail.size
                else:
                    probs /= s

            idx = int(self._rng.choice(N, p=probs))
            sel_idx.append(idx)
            self.counts[idx] += 1
            if self.repulsion_weight > 0:
                sel_feat = np.vstack((sel_feat, features[idx]))

        # Cooling
        self.counts[self.counts > self.cooling_rate] -= self.cooling_rate
        return np.asarray(sel_idx, dtype=int)

    # ===================================================================
    #.   Mode: *stochastic* / *boltzmann selection* BOLTZMANN 
    # ===================================================================
    def boltzmann(self, features, objectives, f_adj, sel_feat, size, w):
        """
        Boltzmann selector using helper methods:
          - _fused_objective for stable multi-objective fusion
          - _add_repulsion for diversity term
          - _repetition_logit_penalty for log-space repetition control
        Sampling is via Gumbel–Max without replacement (masking selected as -inf). 
        """
        sel_idx: list[int] = []
        N, K = objectives.shape

        # 1) Base fused objective once per round (depends only on f_adj, w, T_obj)
        F = self._fused_objective(f_adj, w)  # lower is better
        '''
        # will underflow (every entry in exps becomes zero) so that all fused‐objective 
        # scores collapse to essentially the same constant. Once your costs are all identical, 
        # sampling (even with a “softmax‐style” np.exp(logits - logits.max())) will be 
        # effectively uniform––hence the completely random picks you observe.
        exps = np.exp(-f_adj / T_obj)  [! Direct]
        Z = exps.dot(w)  [! Direct]
        F = -T_obj * np.log(Z + _EPS) [! Direct]
        cost = F.copy() [! Direct]
        '''

        for _ in range(size):
            # 2) Assemble cost = fused + repulsion (repulsion depends on current sel_feat)
            cost = self._add_repulsion(F, features, sel_feat)

            # 3) Build sampling logits
            T_s = self.sampling_temperature + _EPS
            logits = -cost / T_s  # higher logits => higher prob

            # 4) Repetition penalty in log-space
            logits += self._repetition_logit_penalty()
            '''
            Why this works
            Exact zeroing: whenever your penalty function returns 1.0, log1p(-1.0) is -inf. 
            An -inf logit will always lose in the Gumbel–Max arg-max, so that candidate’s 
            probability is exactly zero.
            Smooth down-weighting: for in-between values 0<p<1, you’re effectively multiplying 
            the unnormalized weight by (1−p), which reduces but does not entirely kill off that item.
            No buried epsilon: by not adding + _EPS inside the log, you allow true log(0)-> -inf
            '''

            # 5) Without replacement: forbid already selected indices
            if sel_idx:
                logits[sel_idx] = -np.inf

            # 6) Safety: if everything is -inf (can happen with extreme penalties),
            #    fall back to uniform over remaining candidates.
            if not np.isfinite(logits).any():
                mask = np.ones(N, dtype=bool)
                mask[sel_idx] = False
                logits = np.full(N, -np.inf, dtype=np.float64)
                logits[mask] = 0.0  # equal logits -> uniform after Gumbel

            # 7) Gumbel–Max draw
            # Draw one index via Gumbel–Max
            # Gumbel(0,1) samples = -log(-log(U))
            u = self._rng.random(size=N)
            gumbels = -np.log(-np.log(u + _EPS) + _EPS)
            idx = int(np.argmax(logits + gumbels))

            # 8) Record and update state
            sel_idx.append(idx)
            self.counts[idx] += 1
            if self.repulsion_weight > 0:
                sel_feat = np.vstack((sel_feat, features[idx]))

        # 9) Cooling
        self.counts[self.counts > self.cooling_rate] -= self.cooling_rate

        return np.asarray(sel_idx, dtype=int)

    # ===================================================================
    #.   Mode: *stochastic* / *boltzmann selection* BOLTZMANN BIGDATA 
    # ===================================================================
    def boltzmann_bigdata(self, objectives, features, f_min, w, size):
        """
        Two-stage large-N selection (CPU-only, no external libs):
          1) Screen: streaming fused objective -> keep top-L indices (lower is better)
          2) Select: Boltzmann with a min-distance repulsion cache updated only for
             candidates in the same/adjacent grid cells of a small projected space.
        """
        N, K = objectives.shape
        print(N, K)
        
        # ---- Stage 1: screen to top-L by fused objective ----
        idx_L, F_L = self._preselect_topL(objectives, f_min, w)  # (L,), (L,)
        feats_L = features[idx_L].astype(np.float32 if self.use_float32 else np.float64, copy=False)

        # Local repetition counts for the L-pool
        if isinstance(self.counts, np.ndarray) and self.counts.size >= N:
            counts_L = self.counts[idx_L].astype(np.float32, copy=True)
        else:
            counts_L = np.zeros(idx_L.size, dtype=np.float32)

        sel_local: list[int] = []
        sel_global: list[int] = []

        # ---- Repulsion cache with finite baseline ----
        init_d = self._estimate_l1_scale(feats_L, sample=min(2048, feats_L.shape[0]))
        rep_cache = self._init_repulsion_cache_scaled(idx_L.size, init_d)

        # ---- Build grid index (NumPy-only; memory-safe) ----
        use_grid = (self.neighbor_backend or "grid").lower() == "grid"
        if use_grid:
            if self.grid_use_projection and feats_L.shape[1] > int(self.grid_proj_dim):
                R = self._make_projection(D=feats_L.shape[1], d=int(self.grid_proj_dim))
                feats_grid = self._project_feats(feats_L, R)           # (L,d)
            else:
                R = None
                feats_grid = feats_L                                   # (L,D) if D is already small
            feats_norm, fmin_g, frng_g = self._grid_normalize(feats_grid)
            grid_buckets = self._grid_build_sparse(feats_norm, self.grid_bins)
            selected_mask = np.zeros(idx_L.size, dtype=bool)
        else:
            selected_mask = None
            R = None
            feats_norm = None
            fmin_g = frng_g = None
            grid_buckets = None

        T_s = self.sampling_temperature + _EPS

        for t in range(size):
            # Base cost (lower is better)
            cost = F_L.copy()

            # Diversity repulsion from cache
            if self.repulsion_weight > 0 and len(sel_local) > 0:
                rep = self._repulsion_from_cache(rep_cache)
                cost += self.repulsion_weight * rep

            # Repetition penalty (local slice only)
            if self.repetition_penalty:
                old_counts = self.counts
                self.counts = counts_L
                logits = -cost / T_s + self._repetition_logit_penalty()
                self.counts = old_counts
            else:
                logits = -cost / T_s

            # Forbid already selected
            if sel_local:
                logits[sel_local] = -np.inf

            # Safety fallback
            if not np.isfinite(logits).any():
                mask = np.ones(idx_L.size, dtype=bool)
                if sel_local:
                    mask[sel_local] = False
                logits = np.full(idx_L.size, -np.inf, dtype=np.float32)
                logits[mask] = 0.0

            # Gumbel–Max draw (native gumbel)
            i_local = int(np.argmax(logits + self._rng.gumbel(size=idx_L.size)))
            sel_local.append(i_local)
            gidx = int(idx_L[i_local])
            sel_global.append(gidx)
            if selected_mask is not None:
                selected_mask[i_local] = True

            # Update repetition counts
            counts_L[i_local] += 1.0
            if isinstance(self.counts, np.ndarray) and self.counts.size >= N:
                self.counts[gidx] += 1.0

            # ---- Repulsion cache update (approx local) ----
            if self.repulsion_weight > 0 and ((t + 1) % self.repulsion_update_stride == 0):
                xstar = feats_L[i_local]

                if use_grid:
                    xg = (xstar @ R).astype(np.float32) if (R is not None) else xstar.astype(np.float32)
                    z  = np.clip((xg - fmin_g) / frng_g, 0.0, 1.0 - np.finfo(np.float32).eps)
                    xbin = np.floor(z * self.grid_bins).astype(np.int32)
                    nbr_ids = self._grid_neighbors(
                        buckets=grid_buckets,
                        x_bin=xbin,
                        bins=self.grid_bins,
                        radius=int(self.grid_radius),
                        max_neighbors=int(self.grid_max_neighbors),
                        L=idx_L.size,
                        selected_mask=selected_mask
                    )
                    if nbr_ids.size:
                        self._update_cache_with_subset(rep_cache, feats_L, xstar, nbr_ids)
                    elif self.grid_fallback_every and ((t + 1) % int(self.grid_fallback_every) == 0):
                        self._update_repulsion_cache_chunked(rep_cache, feats_L, xstar, self.chunk_size)
                else:
                    # Pure vectorised fallback on entire L-pool
                    self._update_repulsion_cache_chunked(rep_cache, feats_L, xstar, self.chunk_size)

        # Cooling: touch only selected items (no global sweep)
        if isinstance(self.counts, np.ndarray) and self.counts.size >= N and self.cooling_rate > 0:
            self.counts[sel_global] = np.maximum(0.0, self.counts[sel_global] - self.cooling_rate)

        return np.asarray(sel_global, dtype=int)

    # ----------------------------------------------------------------------
    #                            Sanity checks
    # ----------------------------------------------------------------------
    def _sanity_check(
        self,
        obj: np.ndarray,
        feat: np.ndarray,
        size: int,
        repare: bool = False,
    ) -> tuple[np.ndarray, np.ndarray, int]:
        if obj.ndim != 2 or feat.ndim != 2:
            raise ValueError("`objectives` and `features` must be 2-D arrays")
        if obj.shape[0] != feat.shape[0]:
            raise ValueError("Number of rows in objectives and features must match")

        if not (np.isfinite(obj).all() and np.isfinite(feat).all()):
            if repare:
                obj = np.asarray(obj, dtype=np.float64)
                feat = np.asarray(feat, dtype=np.float64)
                obj[~np.isfinite(obj)] = 0.0
                feat[~np.isfinite(feat)] = 0.0
            else:
                raise ValueError("Inputs contain NaN or infinite values")

        if not (1 <= size <= obj.shape[0]):
            size = obj.shape[0] if repare else (_ for _ in ()).throw(ValueError("`size` must be between 1 and N"))

        return obj, feat, size

    @staticmethod
    def _probs_sanity_check(probs: np.ndarray) -> np.ndarray:
        """Force a 1‑D probability vector into a valid simplex.

        * Replace NaNs with 0
        * Clamp negatives to 0 (can arise from round‑off in fitness)
        * If the vector is all‑zeros, revert to a uniform distribution
        * Finally, normalise so that `probs.sum() == 1`
        """
        probs = np.nan_to_num(probs, nan=0.0, copy=False)
        probs[probs < 0.0] = 0.0
        total = probs.sum()
        if np.isclose(total, 0.0):
            probs.fill(1.0 / probs.size)
        else:
            probs /= total
        return probs

    # ----------------------------------------------------------------------
    #                        Non‑dominated sorting helpers
    # ----------------------------------------------------------------------
    def _non_dominated_sort(self, objectives: np.ndarray) -> list[list[int]]:
        """
        Perform non-dominated sorting on a set of objective vectors.

        This method assigns each candidate a Pareto-front rank by iteratively
        identifying non-dominated points and peeling them off.

        :param objectives: Array of shape (N, K) containing objective values for N candidates.
                           Lower values are considered better.
        :type objectives: numpy.ndarray
        :returns: A list of Pareto fronts; each front is a list of candidate indices.
                  Front 0 contains non-dominated points (rank 1), front 1 contains points
                  dominated only by those in front 0, etc.
        :rtype: List[List[int]]
        """
        N, K = objectives.shape
        domination_counts = np.zeros(N, dtype=int)
        dominated_sets = [set() for _ in range(N)]
        fronts: list[list[int]] = []

        for i in range(N):
            for j in range(N):
                if i == j:
                    continue
                if np.all(objectives[i] <= objectives[j]) and np.any(objectives[i] < objectives[j]):
                    dominated_sets[i].add(j)
                elif np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):
                    domination_counts[i] += 1

        current_front = [i for i in range(N) if domination_counts[i] == 0]
        while current_front:
            fronts.append(current_front)
            next_front: list[int] = []
            for p in current_front:
                for q in dominated_sets[p]:
                    domination_counts[q] -= 1
                    if domination_counts[q] == 0:
                        next_front.append(q)
            current_front = next_front

        return fronts

    # ----------------------------------------------------------------------
    #                          NSGA‑III helpers
    # ----------------------------------------------------------------------
    def _generate_reference_dirs(self, M: int, H: int) -> np.ndarray:
        """
        Generate reference directions on the M-objective simplex using the Das–Dennis method.

        :param M: Number of objectives (dimensionality of the simplex).
        :type M: int
        :param H: Number of divisions along each axis for constructing the reference grid.
                  Total reference directions = comb(H + M - 1, M - 1).
        :type H: int
        :returns: Array of shape (num_dirs, M) with each row a reference direction vector.
        :rtype: numpy.ndarray
        """
        def gen(curr: list[int], left: int, dims: int):
            if dims == 1:
                yield curr + [left]
            else:
                for k in range(left + 1):
                    yield from gen(curr + [k], left - k, dims - 1)

        dirs = np.array(list(gen([], H, M)), dtype=float)
        dirs /= (H + _EPS)
        return dirs

    def _reference_point_niching(
        self,
        objectives: np.ndarray,
        front: list[int],
        ref_dirs: np.ndarray,
        rem: int
    ) -> list[int]:
        """
        Perform reference-point niching selection on a Pareto front.

        Each candidate in the given front is associated with the closest reference
        direction, and up to `rem` candidates are chosen to maximize diversity.

        :param objectives: Full objective matrix of shape (N, K) for normalization.
        :type objectives: numpy.ndarray
        :param front: List of indices belonging to the target Pareto front.
        :type front: List[int]
        :param ref_dirs: Array of reference directions of shape (num_dirs, K).
        :type ref_dirs: numpy.ndarray
        :param rem: Number of candidates to select from this front.
        :type rem: int
        :returns: List of selected candidate indices of length `rem`.
        :rtype: List[int]
        """
        # Normalize objectives to [0,1]
        f_min = objectives.min(axis=0)
        f_max = objectives.max(axis=0)
        f_norm = (objectives - f_min) / (f_max - f_min + _EPS)

        # Unit ref_dirs
        r_norm = ref_dirs / (np.linalg.norm(ref_dirs, axis=1, keepdims=True) + _EPS)

        # Compute perpendicular distances
        dists = np.full((len(front), len(r_norm)), np.inf)
        for i, idx in enumerate(front):
            for j, r in enumerate(r_norm):
                proj = np.dot(f_norm[idx], r) * r
                dists[i, j] = np.linalg.norm(f_norm[idx] - proj)

        # Associate each front member to nearest direction
        assoc = np.argmin(dists, axis=1)

        niche_count = np.zeros(len(r_norm), dtype=int)
        selected: list[int] = []
        candidates = list(range(len(front)))

        for _ in range(rem):
            # find directions with minimal niche count among candidates
            avail_dirs = set(assoc[c] for c in candidates)
            min_count = min(niche_count[list(avail_dirs)])
            best_dirs = [d for d in avail_dirs if niche_count[d] == min_count]
            # pick first best direction
            d_sel = best_dirs[0]
            # candidates in that niche
            niche_cands = [c for c in candidates if assoc[c] == d_sel]
            # choose the one with smallest distance
            c_star = min(niche_cands, key=lambda idx: dists[idx, d_sel])
            selected.append(front[c_star])
            niche_count[d_sel] += 1
            candidates.remove(c_star)

        return selected


    # ===================================================================
    #                         Mode: GREEDY
    # ===================================================================
    def greedy(self, features, f_adj, sel_feat, size, w):
        """
        Deterministic selection: at each step pick the minimum fused cost + repulsion + repetition cost.
        """
        N = f_adj.shape[0]
        F = self._fused_objective(f_adj, w)         # base fused costs (lower is better)
        selected: list[int] = []

        for _ in range(size):
            # Start from fused objective
            cost = F.copy()

            # Add repulsion based on current selections
            cost = self._add_repulsion(cost, features, sel_feat)

            # Add repetition cost
            cost = self._add_repetition_cost(cost)

            # Mask already-selected
            if selected:
                cost[selected] = np.inf

            i = int(np.argmin(cost))
            selected.append(i)
            self.counts[i] += 1

            if self.repulsion_weight > 0:
                sel_feat = np.vstack((sel_feat, features[i]))

        # Cooling
        self.counts[self.counts > self.cooling_rate] -= self.cooling_rate
        return np.asarray(selected, dtype=int)

    # ===================================================================
    #                      Mode: TOURNAMENT
    # ===================================================================
    def tournament(self, features, f_adj, sel_feat, size, w):
        """
        Tournament selection with fused multi-objective cost:
        - sample a pool of 'tournament_size' candidates (without replacement from remaining),
        - pick the one with minimum cost in the pool,
        - update repulsion/repetition and repeat.
        """
        N = f_adj.shape[0]
        F = self._fused_objective(f_adj, w)
        selected: list[int] = []

        for _ in range(size):
            # compute costs once per round; repulsion depends on current sel_feat,
            # repetition depends on current counts
            base_cost = F.copy()
            base_cost = self._add_repulsion(base_cost, features, sel_feat)
            base_cost = self._add_repetition_cost(base_cost)

            # build the available index set
            if selected:
                mask = np.ones(N, dtype=bool)
                mask[selected] = False
                avail = np.nonzero(mask)[0]
            else:
                avail = np.arange(N)

            # --- auto tournament size from temperature ---
            t = self._tournament_size_from_temperature(avail.size)

            # draw pool and pick best within pool
            pool = self._rng.choice(avail, size=t, replace=False)

            # choose best in the pool
            i = int(pool[np.argmin(base_cost[pool])])
            selected.append(i)
            self.counts[i] += 1

            if self.repulsion_weight > 0:
                sel_feat = np.vstack((sel_feat, features[i]))

        # Cooling
        self.counts[self.counts > self.cooling_rate] -= self.cooling_rate
        return np.asarray(selected, dtype=int)

    def _tournament_size_from_temperature(self, avail_count: int) -> int:
        """
        Map sampling_temperature -> tournament size in [t_min, min(t_max, avail_count)].
        - T_samp = 0      -> t ≈ t_max  (max exploitation)
        - T_samp = T0     -> t ≈ (t_min + t_max)/2
        - T_samp >> T0    -> t → t_min  (max exploration)
        """
        T  = max(float(self.sampling_temperature), 0.0)
        T0 = max(float(self.t_center_temperature), _EPS)
        k  = max(float(self.t_shape), _EPS)

        # logistic-like decay: t(T) = t_min + (t_max - t_min) / (1 + (T/T0)^k)
        t_cont = self.t_min + (self.t_max - self.t_min) / (1.0 + (T / T0) ** k)

        # clip to available pool and round to int
        t_clipped = int(np.clip(np.round(t_cont), self.t_min, min(self.t_max, avail_count)))
        return max(1, t_clipped)


    def plot_diagnostics(
        self,
        objectives: np.ndarray,
        features: np.ndarray,
        obj_temps: Sequence[float] = (0.0001, 0.001, 0.01, 0.1, 1),
        samp_temps: Sequence[float] = (0.0001, 0.001, 0.01, 0.1, 1),
    ) -> None:
        """
        Show diagnostics grid:
        Top row: varying objective temperatures.
        Bottom row: varying sampling temperatures.
        """
        import matplotlib.pyplot as plt
        # Prepare base kwargs for clone
        base_kwargs = dict(
            weights=self.weights,
            repulsion_weight=self.repulsion_weight,
            normalize_objectives=self.normalize_objectives,
            repetition_penalty=self.repetition_penalty,
            size=self.size,
            repulsion_mode=self.repulsion_mode,
            metric=self.metric,
            random_seed=self.random_seed,
            sampling_temperature=self.sampling_temperature,
        )
        fig, axes = plt.subplots(
            2,
            max(len(obj_temps), len(samp_temps)),
            figsize=(5 * max(len(obj_temps), len(samp_temps)), 8),
        )
        # Objective temp row
        for i, T in enumerate(obj_temps):
            sampler = Selector(
                **{**base_kwargs, 'sampling_temperature': T}
            )
            sampler.repulsion_weight = 0.0
            sampler.max_count = 10
            ax = axes[0, i]
            ax.scatter(objectives[:,0], objectives[:,1], alpha=0.6, s=2)

            for n in range(10):
                idx = sampler.select(objectives, features, size=40)
                ax.scatter(objectives[idx,0], objectives[idx,1], marker='x', s=30, label=f"T_obj={T}", alpha=0.1)

            ax.set_title(f"Objective Temp = {T}")
            #ax.legend()

        # Sampling temp row
        for i, T in enumerate(samp_temps):
            sampler = Selector(
                **{**base_kwargs, 'objective_temperature': self.objective_temperature,
                   'sampling_temperature': T}
            )
            sampler.repulsion_weight = 0.0001
            idx = sampler.select(objectives, features, size=10)
            ax = axes[1, i]
            ax.scatter(features[:,0], features[:,1], alpha=0.3)
            ax.scatter(features[idx,0], features[idx,1], marker='x', s=100, label=f"T_samp={T}")
            ax.set_title(f"Sampling Temp = {T}")
            #ax.legend()
        fig.suptitle("Sampler Diagnostics", fontsize=16)
        plt.tight_layout()
        #plt.show()

# ----------------------------------------------------------------------
# Unit tests
# ----------------------------------------------------------------------
class _SamplerTest(unittest.TestCase):
    def setUp(self):

        def generate_pareto_front(    
            N: int,
            df1: float = 2.0,
            df2: Optional[float] = None
            ) -> tuple[np.ndarray, np.ndarray]:
            """
            Generate N synthetic points from Chi-squared distributions for objectives.
            """
            rng = np.random.default_rng()
            f1 = rng.chisquare(df1, size=N)
            df2 = df1 if df2 is None else df2
            f2 = rng.chisquare(df2, size=N)
            objectives = np.vstack((f1, f2)).T
            features = objectives.copy()
            return objectives, features

        self.N, self.K, self.D = 1000, 2, 5
        rng = np.random.default_rng(7)
        #self.obj = rng.normal(loc=-5.0, scale=2.0, size=(self.N, self.K))
        #self.feat = rng.normal(size=(self.N, self.K))
        self.obj, self.feat = generate_pareto_front(self.N)


        rng = np.random.default_rng(7)
        self.N, self.K = 1000, 2
        self.obj = rng.gamma(shape=2.0, scale=1.0, size=(self.N, self.K))
        self.feat = self.obj + rng.normal(scale=0.1, size=(self.N, self.K))


    def test_shape_and_uniqueness(self):
        sampler = Selector(size=10, random_seed=0)
        idx = sampler.select(self.obj, self.feat)
        self.assertEqual(idx.size, 10)
        self.assertEqual(len(np.unique(idx)), 10)

    def test_diagnostics_runs(self):
        sampler = Selector(size=5, random_seed=0)
        # Should produce plots without error
        sampler.plot_diagnostics(self.obj, self.feat)

    def test_objective_normalization(self):
        sampler = Selector(normalize_objectives=True, size=5, random_seed=3)
        idx = sampler.select(self.obj, self.feat)
        self.assertEqual(len(idx), 5)

    def test_sampling_temperature_smears_distribution(self):
        phys_T = 1.0
        low_ts = Selector(
            objective_temperature=phys_T,
            sampling_temperature=0.1,
            size=1,
            random_seed=1
        )
        high_ts = Selector(
            objective_temperature=phys_T,
            sampling_temperature=10.0,
            size=1,
            random_seed=1
        )
        f_min = self.obj.min(axis=0)
        f_adj = self.obj - f_min
        T_obj = phys_T + _EPS
        exps = np.exp(-f_adj / T_obj)
        Z = exps.dot(np.ones(self.K)/self.K)
        F = -T_obj * np.log(Z + _EPS)
        def p_dist(ts):
            logits = -F / (ts + _EPS)
            p = np.exp(logits - logits.max())
            return p / p.sum()
        p_low = p_dist(low_ts.sampling_temperature)
        p_high = p_dist(high_ts.sampling_temperature)
        self.assertGreater(p_low.max(), p_high.max())

    def test_repulsion_increases_diversity(self):
        no_rep = Selector(repulsion_weight=0.0, size=5, random_seed=2)
        rep = Selector(repulsion_weight=1.0, size=5, random_seed=2)
        idx_n = no_rep.select(self.obj, self.feat)
        idx_r = rep.select(self.obj, self.feat)
        d_n = pairwise_distances(self.feat[idx_n]).mean()
        d_r = pairwise_distances(self.feat[idx_r]).mean()
        self.assertGreaterEqual(d_r, d_n)

    def test_roulette_runs(self):
        sampler = Selector(size=15, selection_method='roulette', random_seed=1)
        idx = sampler.select(self.obj, self.feat)
        self.assertEqual(idx.size, 15)
        self.assertEqual(len(np.unique(idx)), 15)

    def test_selection_probability_grid(self):
        """La probabilidad en la cuadrícula 2-D debe sumar 1 y decaer con el coste."""
        T_obj, T_s = 1.0, 1.0
        w = np.array([0.5, 0.5])          # pesos iguales
        grid_size = 50
        f_min, f_max = 0.0, 10.0

        # Crear la rejilla de costes
        f1 = np.linspace(f_min, f_max, grid_size)
        f2 = np.linspace(f_min, f_max, grid_size)
        F1, F2 = np.meshgrid(f1, f2)      # shape = (grid_size, grid_size)

        # Fusión de objetivos (log-sum-exp estable)
        log_w = np.log(w)
        a = np.stack([-F1 / T_obj + log_w[0],
                      -F2 / T_obj + log_w[1]], axis=-1)
        m   = np.max(a, axis=-1, keepdims=True)
        lse = m + np.log(np.sum(np.exp(a - m), axis=-1, keepdims=True))
        F_fused = -T_obj * lse.squeeze()  # shape = (grid_size, grid_size)

        # Logits y probabilidades
        logits = -F_fused / T_s
        P = np.exp(logits - logits.max())  # evitar overflow
        P /= P.sum()                       # normalizar

        # --- Asserts ---
        self.assertAlmostEqual(P.sum(), 1.0, places=6,
                               msg="La distribución no está normalizada")
        self.assertGreater(P[0, 0], P[-1, -1],
                           msg="La esquina de bajo coste no es la más probable")

    def test_roulette_no_duplicates_on_uniform_fallback(self):
        # Make all costs identical to force fallback
        obj = np.ones_like(self.obj)
        feat = np.ones_like(self.feat)
        sampler = Selector(size=20, selection_method='roulette', repulsion_weight=0.0, random_seed=0)
        idx = sampler.select(obj, feat)
        assert len(np.unique(idx)) == idx.size

    def test_tournament_size_monotone_vs_temperature(self):
        sel = Selector()
        avail = 100
        sel.sampling_temperature = 0.0
        t0 = sel._tournament_size_from_temperature(avail)
        sel.sampling_temperature = 10.0
        t1 = sel._tournament_size_from_temperature(avail)
        assert t0 >= t1 and sel.t_min <= t1 <= sel.t_max

    def test_boltzmann_ignores_degenerate_objective(self):
        rng = np.random.default_rng(0)
        N = 200
        # obj1 varies, obj2 is constant
        obj1 = rng.gamma(shape=2.0, scale=1.0, size=N)
        obj2 = np.full(N, 10.0)
        obj = np.c_[obj1, obj2]
        feat = obj1[:,None]  # any features
        sel = Selector(size=20, selection_method='boltzmann',
                       normalize_objectives=False, random_seed=1)
        idx = sel.select(obj, feat)
        # Expect correlation: selected have lower obj1 than population median
        assert np.median(obj1[idx]) <= np.median(obj1) 

    def test_boltzmann_bigdata_runs(self):
        sampler = Selector(
            selection_method='boltzmann_bigdata',
            preselect_size=200, chunk_size=10_000,
            grid_bins=16, grid_proj_dim=8, grid_radius=0,
            size=20, random_seed=1, repulsion_weight=1.0
        )
        idx = sampler.select(self.obj, self.feat)
        self.assertEqual(idx.size, 20)
        self.assertEqual(len(np.unique(idx)), 20)

    def test_boltzmann_bigdata_reasonable_quality(self):
        # Compare fused scores of selected vs population (should be better than median)
        sampler = Selector(selection_method='boltzmann_bigdata', preselect_size=500, size=30, random_seed=0)
        f_min = self.obj.min(axis=0); f_adj = self.obj - f_min
        F_all = sampler._fused_objective(f_adj, np.ones(self.K)/self.K)
        idx = sampler.select(self.obj, self.feat)
        self.assertLessEqual(np.median(F_all[idx]), np.median(F_all))

if __name__ == "__main__":
    unittest.main()
