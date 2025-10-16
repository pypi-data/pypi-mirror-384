# EZGA — Evolutionary Structure Explorer (ezga-lib)

A modular **multi-objective genetic algorithm** (GA) framework for **atomistic structure exploration**, with first-class YAML configuration, plugin-style extensibility, and a **Hierarchical Supercell Escalation (HiSE)** workflow for coarse-to-fine supercell searches.

> PyPI name: `ezga-lib`
> CLI entry point: `ezga` (via `ezga.cli.run:app`)
> License: GPL-3.0-only

---

## Features

* **Clean YAML → Runtime**: Pydantic-v2 validated configs; dotted imports & factory specs are materialized into live Python callables.
* **Multi-objective selection**: Boltzmann (default) plus alternative methods; repulsion & diversity control.
* **Rich variation operators**: Tunable mutation, crossover, and user-defined operators.
* **ASE integration**: Simple shorthand to wrap ASE calculators.
* **HiSE manager**: Orchestrates multi-stage, coarse-to-fine supercell exploration. Lifts previous results via:

  * `tile` (Partition-based `generate_supercell`),
  * `best_compatible` (find largest divisor supercell among previous stages),
  * `ase` (fallback tiling using ASE).
* **Agentic mailbox**: Stage-scoped shared directory for multi-agent workflows.
* **Pretty CLI summaries**: Rich panels with compact configuration overviews.

---

## Installation

### From source (recommended during development)

```bash
git clone <your-repo-url>
cd ezga
pip install -U pip
pip install -e .
```

This installs the `ezga` command line app.

### From PyPI (when available)

```bash
pip install ezga-lib
```

---

## Quick Start

Create a minimal `ezga.yaml`:

```yaml
max_generations: 100
output_path: demo/run

population:
  dataset_path: config.xyz
  filter_duplicates: true

evaluator:
  features_funcs:
    factory: ezga.selection.features:feature_composition_vector
    args: [["C","H"]]         # features are composition counts
  objectives_funcs:
    - ezga.selection.objective:objective_energy

multiobjective:
  size: 256
  selection_method: boltzmann
  sampling_temperature: 0.9
  objective_temperature: 0.6
  random_seed: 73

variation:
  initial_mutation_rate: 3.0
  crossover_probability: 0.1

simulator:
  mode: sampling
  calculator:
    type: ase
    class: ase.calculators.lj:LennardJones
    kwargs: { epsilon: 0.0103, sigma: 3.4 }  # ASE params
```

Run:

```bash
ezga validate -c ezga.yaml --strict
ezga once -c ezga.yaml
```

---

## CLI

```
ezga once -c <config.yaml>
ezga validate -c <config.yaml> [--strict]
```

* `once`: Runs a single GA or delegates to **HiSE** if the YAML has an `hise` block.
* `validate`: Validates and prints a rich summary; `--strict` also builds the engine to catch wiring errors.

---

## Configuration

### GAConfig (high level)

* `population`: dataset paths, constraints, duplicate filtering, …
* `evaluator`: `features_funcs`, `objectives_funcs` (dotted, factory, or list)
* `multiobjective`: selection params (size, method, temperatures, metric, …)
* `variation`: mutation & crossover knobs
* `simulator`: mode & calculator (ASE shorthand supported)
* `convergence`, `hashmap`, `agentic`: execution support
* `hise` (optional): HiSE manager block (see below)

All sections are validated by Pydantic-v2; unknown fields are forbidden.

### Dotted imports & factories

Anywhere you need a callable/object, you can write:

* **Dotted string**: `"package.module:attr"` or `"package.module.attr"`
* **Factory spec**:

  ```yaml
  key:
    factory: "pkg.mod:build_something"
    args: [1, 2]
    kwargs: { flag: true }
  ```
* **ASE shorthand** (calculator only):

  ```yaml
  simulator:
    mode: sampling
    calculator:
      type: ase
      class: ase.calculators.lj:LennardJones
      kwargs: { epsilon: 0.0103, sigma: 3.4 }
  ```

The loader resolves these into live Python objects before the run.

---

## Constraints (Design of Experiments)

You can provide constraint generators as factories. Example using a custom generator:

```yaml
population:
  constraints:
    - factory: ezga.DoE.DoE:ConstraintGenerator.sum_in_range
      args: [["C", "H"], 100, 100]
```

> **Tip**
> Use `ezga.DoE.DoE:ConstraintGenerator.sum_in_range` (colon form).
> Avoid `ezga.DoE.DoE.ConstraintGenerator:sum_in_range` (that treats `ConstraintGenerator` as a module path).

If your constraint generator expects feature **names**, you can register a name→index mapping in your code (e.g., after features are known):

```python
from ezga.DoE.DoE import ConstraintGenerator
ConstraintGenerator.set_name_mapping({"C": 0, "H": 1})
```

---

## HiSE — Hierarchical Supercell Escalation

HiSE runs a sequence of stages over growing supercells and **replaces** the base input at each stage with a lifted dataset derived from previous results.

### Example

```yaml
hise:
  supercells:
    - [1,1,1]
    - [2,1,1]
    - [2,2,1]

  input_from: final_dataset            # or: latest_generation
  stage_dir_pattern: "supercell_{a}_{b}_{c}"
  restart: false
  carry: all
  reseed_fraction: 1.0
  lift_method: tile                    # tile | best_compatible | ase

  overrides:
    multiobjective.size:               [10, 20, 30]
    max_generations:                   [ 2,  3,  5]
    variation.initial_mutation_rate:   [ 1,  2,  3]
    population.constraints:
      - factory: ezga.DoE.DoE:ConstraintGenerator.sum_in_range
        args: [['C', 'H'], 100, 100]
      - factory: ezga.DoE.DoE:ConstraintGenerator.sum_in_range
        args: [['C', 'H'], 200, 200]
      - factory: ezga.DoE.DoE:ConstraintGenerator.sum_in_range
        args: [['C', 'H'], 400, 400]
```

### Lift methods

* **`tile`**: Partition-based lifting using
  `container.AtomPositionManager.generate_supercell(repeat=(ra, rb, rc))`
  (requires `sage_lib.partition.Partition`).
* **`best_compatible`**: Scans *all* previous stages and picks the largest supercell (by volume) that divides the target coordinate-wise; lifts via Partition.
* **`ase`**: Simple tiling via `ASE.Atoms.repeat`. No Partition dependency (fallback).

### Input source

* `final_dataset`: uses `stage_root/config.xyz`
* `latest_generation`: concatenates `stage_root/generation/*/config.xyz`

### Stage directories

For each supercell `(a,b,c)` the HiSE manager creates:

```
<output_path>/
  supercell_{a}_{b}_{c}/
    input_lifted.xyz           # if lifting writes to disk
    config.xyz                 # final dataset (engine may write this)
    generation/...
```

### Agentic shared dir

If `agentic.shared_dir` is set in the base config, each stage receives a **stage-scoped** mailbox:

```
<base_shared>/<relative_stage_dir>/
```

All agents of a given stage share this directory.

---

## Directory Layout (source tree)

```
src/ezga/
  cli/
    run.py                    # Typer app (ezga entry point)
    runners.py                # once / validate / hise dispatchers
  core/
    config.py                 # GAConfig + submodels (Pydantic v2)
    engine.py                 # GA main loop
    population.py             # population & DoE validation
  selection/
    features.py, objective.py # feature/ objective factories
  DoE/
    DoE.py                    # ConstraintGenerator and DoE
  hise/
    manager.py                # HiSE orchestrator
  io/
    config_loader.py          # YAML loader & materializer
  simulator/
    ase_calculator.py         # ASE adapter (shorthand support)
```

---

## Logging & Output

* Logs and artifacts are written under `output_path` (and per-stage subdirs in HiSE).
* The CLI prints a rich summary of the configuration before running.

---

## Developing

### Tests

We use `pytest`. Example structure:

```
tests/
  test_loader.py
  test_hise_manager.py
  test_constraints.py
  conftest.py
```

Run:

```bash
pip install -e ".[test]"   # if you add an extra in pyproject
pytest -q
```

Example unit test for loader materialization:

```python
# tests/test_loader.py
from ezga.io.config_loader import _materialize_factories

def test_factory_resolution():
    spec = {"factory": "math:prod", "args": [[2,3,4]]}
    fn = _materialize_factories(spec)
    assert callable(fn)
    assert fn([2,3,4]) == 24
```

### Code style

* Type hints everywhere.
* Docstrings follow **Google style**.
* Avoid side effects in import time; factories should be cheap to resolve.

---

## Troubleshooting

* **`TypeError: 'dict' object is not callable`**
  You likely passed a factory **dict** (not materialized) directly into a runtime component. Ensure your keys live in the YAML under sections that the loader post-processes, or put them under `hise.overrides` if you need stage-specific values. The loader will materialize `population.constraints`, `evaluator.*`, `mutation_funcs`, `crossover_funcs`, and `simulator.calculator`.

* **`ModuleNotFoundError` or wrong dotted form**
  Use colon form: `pkg.mod:attr` (preferred). For our DoE example:
  `ezga.DoE.DoE:ConstraintGenerator.sum_in_range`.

* **Pydantic model errors**
  Ensure `pydantic>=2.x` is installed. Unknown fields are rejected (`extra='forbid'`).

* **Permission error exporting `input_lifted.xyz`**
  Ensure the path is writable. The exporter writes a new file; if you manage files manually, don’t open the same file elsewhere.

---

## Roadmap

* Additional selection methods & visual diagnostics.
* More HiSE lift strategies (symmetry-aware mapping).
* Native viewers for generation trajectories.
* Optional async physics backends.

---

## Citation

If this software helps your research, please cite the repository (add DOI when available).

---

## License

GPL-3.0-only. See `LICENSE`.

---

## Acknowledgments

* **ASE** for atomistic infrastructure.
* **pydantic**, **typer**, **ruamel.yaml**, **rich** for the developer experience.
* **sage\_lib** for partition and supercell lifting utilities.
