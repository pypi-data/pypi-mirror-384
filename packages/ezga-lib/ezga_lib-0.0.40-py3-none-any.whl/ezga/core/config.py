# src/bansga/core/config.py
from __future__ import annotations
from typing import Any, Optional, Sequence, Tuple, List, Dict, Union, Callable, Literal, Annotated
import warnings
from enum import Enum

from pydantic import (
    BaseModel, Field, PositiveInt, NonNegativeInt,
    field_validator, model_validator, ConfigDict
)

class SelectionMethod(str, Enum):
    BOLTZMANN = "boltzmann"
    BOLTZMANN_BIGDATA = "boltzmann_bigdata"
    GREEDY     = "greedy"
    ROULETTE   = "roulette"
    TOURNAMENT = "tournament"
    NSGA3   = "nsga3"
    NS = "nondominated_sorted"

class HashMethod(str, Enum):
    RDF    = "rdf"
    TSF    = "tsf"
    RBF    = "rbf"

# ---------- Sub-models ---------- #
class HiSEParams(BaseModel):
    """Hierarchical Supercell Escalation (HiSE) coarse-to-fine settings."""
    supercells: List[Tuple[int, int, int]] = Field(
        ..., description="Sequence of supercells, e.g. [[1,1,1],[2,1,1],[2,2,1]]"
    )

    # >>> I/O 
    input_from: Literal["final_dataset", "latest_generation"] = Field(
        "final_dataset",
        description="Where to read previous stage input from: final_dataset (root config.xyz) "
                    "or latest_generation (scan generation/*/config.xyz)."
    )
    stage_dir_pattern: str = Field(
        "supercell_{a}_{b}_{c}",
        description="Subdirectory name per stage under GAConfig.output_path."
    )
    restart: bool = Field(
        True, description="Skip stages already complete; resume partial if possible."
    )

    # Overrides each stage: p.ej., foreigners, thermostat, etc.
    overrides: Optional[Dict[str, List[Any]]] = Field(
        None,
        description="Stage-specific overrides by key path (dot-notation) → list of values per stage."
    )

    # Carry semantics (si además quieres propagar poblaciones, opcional)
    carry: Literal["pareto", "elites", "all"] = "all"
    reseed_fraction: float = 1.0
    lift_method: Literal["tile"] = "tile"

    @field_validator("supercells")
    @classmethod
    def _validate_supercells(cls, v):
        if not v:
            raise ValueError("supercells must be a non-empty list")
        for t in v:
            if len(t) != 3 or any(int(x) < 1 for x in t):
                raise ValueError(f"Invalid supercell {t!r}")
        return [tuple(int(x) for x in t) for t in v]

class PopulationParams(BaseModel):
    dataset_path: str = None # 'config.xyz'
    template_path: str = None
    db_path: str = None
    db_ro_path: str = None
    
    filter_duplicates: bool = True
    size_limit: Optional[Union[int, None]] = None
    constraints: Optional[List[Union[Callable[..., bool], Dict[str, Any]]]] = None

    ef_bounds: Optional[Tuple[float, float]] = None
    collision_factor: Optional[float] = 0.80
    blacklist : Optional[List[str,]] = None
    fetch_limit: Optional[Union[int, None]] = None, 

class ThermostatParams(BaseModel):
    initial_temperature: float = 1.0
    decay_rate: float = 0.005
    period: PositiveInt = 30
    temperature_bounds: Tuple[float, float] = (0.0, 1.1)
    max_stall_offset: float = 1.0
    stall_growth_rate: float = 0.01
    constant_temperature: bool = False

class EvaluatorParams(BaseModel):
    features_funcs: Any = None
    objectives_funcs: Any = None
    debug: bool = False

class SelectionParams(BaseModel):
    size: int = 256
    weights: Optional[Sequence[float]] = None
    repulsion_weight: float = 1.0
    repetition_penalty: bool = True
    objective_temperature: float = 1.0
    repulsion_mode: str = "min"
    composition_repulsion_weight: float = 0.0  # β: strength of composition multiplicity penalty
    composition_decimals: int = 0              # rounding for float features when comparing compositions
    metric: str = "euclidean"
    random_seed: Union[int, None] = None
    steepness: float = 10.0
    max_count: PositiveInt = 50
    cooling_rate: float = 0.1
    counts: Optional[List[Any]] = None
    normalize_objectives: bool = False
    sampling_temperature: float = 1.0
    selection_method: SelectionMethod = SelectionMethod.BOLTZMANN
    divisions: PositiveInt = 12

class VariationParams(BaseModel):
    initial_mutation_rate: float = 2.0
    min_mutation_rate: float = 1.0
    max_prob: float = 0.95
    min_prob: float = 0.01
    use_magnitude_scaling: bool = True
    alpha: float = 0.01
    crossover_probability: float = 0.1

class SimulatorParams(BaseModel):
    mode: str = 'sampling'
    calculator: Optional[Any] = None

class ConvergenceParams(BaseModel):
    objective_threshold: float = 0.01
    feature_threshold: float = 0.01
    stall_threshold: PositiveInt = int(1e5)
    information_driven: bool = False
    detailed_record: bool = True
    convergence_type: str = 'and'

class AgenticParams(BaseModel):
    hash_name: str = "sha256"
    shared_dir: Optional[str] = None
    shard_width: int = 2
    persist_seen: bool = False
    poll_interval: float = 2.0
    max_buffer: int = 7
    max_retained: int = None
    auto_publish: bool = True
    fetch_every:int = 7

class PhysicalModelCfg(BaseModel):
    T_mode: str
    calculator: Any     # dejas Any (o str) y lo resuelves en la factory

class HashMapParams(BaseModel):
    method: str = 'tsf'
    r_max: Optional[float] = 6.0
    bin_width: Optional[float] = 0.5
    density_grid: Optional[float] = 1e-4
    e_grid: Optional[float] = 1e-11
    v_grid: Optional[float] = 1e-1
    symprec: Optional[float] = 1e-3

# --- Per-method configs -----------------------------------------------------
class _HashBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

class TSFHashCfg(_HashBase):
    method: Literal["tsf"] = "tsf"
    kmax: int = 3
    modes: Optional[List[Tuple[int, int, int]]] = None
    per_species: bool = True
    ps_grid: float = 1e-1
    lattice_grid: float = 2e-2
    e_grid: float = 1e-3
    v_grid: float = 1e-2
    include_energy: bool = True
    include_volume: bool = True
    use_spglib: bool = False
    symprec: float = 1e-3
    angle_tolerance: float = -1.0
    chunk_size: int = 50000
    debug: bool = False

    @field_validator("modes")
    @classmethod
    def _modes_or_none_nonempty(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("modes must be None or a non-empty list")
        return v

class RDFHashCfg(_HashBase):
    method: Literal["rdf"] = "rdf"
    r_max: float = 10.0
    bin_width: float = 0.02
    density_grid: float = 1e-4
    e_grid: float = 1e-2
    v_grid: float = 1e-2
    symprec: float = 1e-3
    debug: bool = False

class RBFHashCfg(_HashBase):
    method: Literal["rbf"] = "rbf"
    number_of_bins: int = 200
    bin_volume_normalize: bool = False
    number_of_atoms_normalize: bool = False
    density_normalize: bool = False
    e_grid: float = 1e-2
    v_grid: float = 1e-2
    symprec: float = 1e-3
    debug: bool = False

# Discriminated union (by "method")
HashMapConfig = Annotated[
    Union[RDFHashCfg, TSFHashCfg, RBFHashCfg],
    Field(discriminator="method"),
]

# ---------- Modelo principal ---------- #
class GAConfig(BaseModel):
    """Top-level configuration for EZGA (validated via Pydantic v2)."""

    # Strict mode: forbid unknown fields; re-validate on attribute assignment.
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        populate_by_name=True,  # helpful if you add aliases later
    )

    initial_generation: NonNegativeInt = 0
    max_generations: PositiveInt = 100
    min_size_for_filter: int = 10
    foreigners: int = 0

    save_logs: bool = True
    output_path: str = '.'
    resume: bool = True
    resume_mode: str = "folders_all"  # "folders_all" | "folders" | "snapshot"

    population: PopulationParams = Field(default_factory=PopulationParams)
    thermostat: ThermostatParams = Field(default_factory=ThermostatParams)
    evaluator: EvaluatorParams = Field(default_factory=EvaluatorParams)

    multiobjective: SelectionParams = Field(default_factory=SelectionParams)

    variation: VariationParams = Field(default_factory=VariationParams)
    mutation_funcs: List[Any] = Field(default_factory=list)
    crossover_funcs: List[Any] = Field(default_factory=list)

    simulator: SimulatorParams = Field(default_factory=SimulatorParams)
    convergence: ConvergenceParams = Field(default_factory=ConvergenceParams)
    
    hashmap: HashMapConfig = Field(default_factory=TSFHashCfg)

    agentic: AgenticParams = Field(default_factory=AgenticParams)

    hise: Optional[HiSEParams] = Field(default=None, description="Hierarchical Supercell Escalation (coarse-to-fine) settings.")
    generative_model: Any = None

    #objective_funcs: List[Any] = Field(default_factory=callable)
    #features_funcs: Any = None

    # extras “legacy”
    initial_population: Optional[List[Any]] = None

    debug: bool = False
    rng: Optional[int] = None

    # --------- Custom validators --------- #
    @field_validator("foreigners", mode="before")
    @classmethod
    def cast_foreigners_int(cls, v):
        return int(v) if v is not None else 0

    '''
    @model_validator(mode="after")
    def check_relationships(self):
        m = self.multiobjective.size
        if self.min_size_for_filter < m:
            warnings.warn(
                f"min_size_for_filter ({self.min_size_for_filter}) < size ({m}); "
                f"auto-setting min_size_for_filter={m}"
            )
            return self.model_copy(update={"min_size_for_filter": m})
        return self
    '''