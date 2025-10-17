# cell-eval

## Description

This package provides a comprehensive suite of metrics for evaluating the performance of models that predict cellular responses to perturbations at the single-cell level. It can be used either as a command-line tool or as a Python module.

## Installation

Distribution with [`uv`](https://docs.astral.sh/uv/)

```bash
# install from pypi
uv pip install -U cell-eval

# install from github directly
uv pip install -U git+https://github.com/arcinstitute/cell-eval

# install cli with uv tool
uv tool install -U git+https://github.com/arcinstitute/cell-eval

# Check installation
cell-eval --help
```

## Usage

To get started you'll need to have two anndata files.

1. a predicted anndata (`adata_pred`).
2. a real anndata to compare against (`adata_real`).

### Prep (VCC)

To prepare an anndata for [VCC evaluation](https://virtualcellchallenge.org/) you can use the `cell-eval prep` command.
This will strip the anndata to bare essentials, compress it, adjust naming conventions, and ensure compatibility with the evaluation framework.

This step is optional for downstream usage, but recommended for optimal performance and compatibility.

Run this on your predicted anndata:

```bash
cell-eval prep \
    -i <your/path/to>.h5ad \
    -g <expected_genelist>
```

### Run

To run an evaluation between two anndatas you can use the `cell-eval run` command.

This will run [differential expression](https://github.com/arcinstitute/pdex) for each anndata and then run a suite of
evaluation metrics to compare the two (select your suite of metrics with the `--profile` flag).

To save time you can submit precomputed differential expression results, see the `cell-eval run --help` menu for more information.

```bash
cell-eval run \
    -ap <your/path/to/pred>.h5ad \
    -ar <your/path/to/real>.h5ad \
    --num-threads 64 \
    --profile full
```

To run this as a python module you will need to use the `MetricsEvaluator` class.

```python
from cell_eval import MetricsEvaluator
from cell_eval.data import build_random_anndata, downsample_cells

adata_real = build_random_anndata()
adata_pred = downsample_cells(adata_real, fraction=0.5)
evaluator = MetricsEvaluator(
    adata_pred=adata_pred,
    adata_real=adata_real,
    control_pert="control",
    pert_col="perturbation",
    num_threads=64,
)
(results, agg_results) = evaluator.compute()
```

This will give you metric evaluations for each perturbation individually (`results`) and aggregated results over all perturbations (`agg_results`).

### Score

To normalize your scores against a baseline you can run the `cell-eval score` command.

This accepts two `agg_results.csv` (or `agg_results` objects in python) as input.

```bash
cell-eval score \
    --user-input <your/path/to/user>/agg_results.csv \
    --base-input <your/path/to/base>/agg_results.csv
```

Or from python:

```python
from cell_eval import score_agg_metrics

user_input = "./cell-eval-user/agg_results.csv"
base_input = "./cell-eval-base/agg_results.csv"
output_path = "./score.csv"

score_agg_metrics(
    results_user=user_input,
    results_base=base_input,
    output=output_path,
)
```

## Library Design

The metrics are built using the python registry pattern. This allows for easy extension for new metrics with a well-typed interface.

Take a look at existing metrics in `cell_eval.metrics` to get started.

## Development

This work is open-source and welcomes contributions. Feel free to submit a pull request or open an issue.

## Citation

Any publication that uses this source code should cite the [State paper](https://arcinstitute.org/manuscripts/State).
