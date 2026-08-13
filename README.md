# The False Green. Locating the Clause-Level Boundary Between Process Conformance and Legal Compliance under Articles 9 and 12 of the EU AI Act

Code accompanying the MSc MISDI dissertation at the London School of Economics and Political Science.

Candidate number: 66961

The project implements a three-stage process-mining artefact for examining when procedural obligations under Articles 9 and 12 of the EU AI Act can be represented as computable process conditions. The artefact is used as an analytical instrument rather than as a legal compliance certification tool.

The pipeline consists of:

1. construction of reference models for the observable obligations in Articles 9 & 12
2. abstraction of raw event labels onto the vocabulary of those models and
3. alignment-based conformance checking of the resulting traces.

The evaluation uses synthetic event logs (emphasised in section 3.4) with known ground truth to distinguish structural non-compliance from cases in which a process is structurally complete but substantively deficient.

## Repository contents

### Core pipeline

- `reference_model.py`  
  Defines the executable reference models for Articles 9 & 12 and converts them to petri-nets using PM4Py.

- `vocabulary.py`  
  Contains the closed activity vocabulary, surface forms and supporting lexical information used by the abstraction stage.

- `synthetic_logs.py`  
  Generates the three synthetic event-log conditions used in the evaluation.

- `abstraction.py`  
  Implements the dictionary, deterministic retrieval, language-model and hybrid abstraction methods.

- `conformance.py`  
  Projects abstracted traces onto the two model alphabets and performs alignment-based conformance checking.

- `pipeline.py`  
  Runs the main evaluation from log generation through abstraction and conformance checking.

### Validation and sensitivity analysis

- `validation.py`  
  Performs the clause-level structural probes used to compare predicted checkability with the behaviour of the executable models.

- `sensitivity.py`  
  Examines sensitivity to the conformance threshold and retrieval similarity cutoff.

- `debug_llm.py`  
  Diagnostic script for comparing language-model mappings with deterministic retrieval mappings.

### Coding and inter-coder reliability

- `clause_grid_coordinates.csv`  
  Contains the clause-level construct-space coordinates used in the validation analysis.

- `coder_1.csv`
- `coder_2.csv`  
  Coding sheets used for the inter-coder reliability analysis reported in the dissertation.

- `kappa.py`  
  Supporting script for the inter-coder reliability calculation.

### Generated results

- `trace_results.csv`  
  Trace-level fitness values and final conformance verdicts.

- `validation_results.csv`  
  Clause-level validation classifications and probe results.

- `validation_grid.png`  
  Clause-level validation figure.

- `sensitivity.png`  
  Threshold and retrieval-cutoff sensitivity analysis.

## Environment

The experiments were run with Python and the following package versions:

```text
pm4py==2.7.22.5
matplotlib==3.11.0
numpy==2.5.0
pandas==3.0.3
anthropic==0.117.0
```

The exact versions are also recorded in `requirements.txt`.

Create a Python environment and install the dependencies with:

```bash
pip install -r requirements.txt
```

## Reproducing the main results

The headline results reported in the dissertation use the deterministic retrieval mapper. No external API or generative model is required for this run.

Run:

```bash
python pipeline.py --n 50 --seed 7 --mapper retrieval
```

The main evaluation uses 50 traces for each of Logs A, B and C and a random seed of 7.

The pipeline writes the trace-level results to:

```text
trace_results.csv
```

and also performs the clause-level validation, producing:

```text
validation_results.csv
validation_grid.png
```

The sensitivity analysis can be reproduced separately with:

```bash
python sensitivity.py
```

which produces:

```text
sensitivity.png
```

## Stage 1: Reference models

The two executable reference models are constructed manually from Articles 9 and 12.

The Article 9 net contains:

```text
23 places
19 transitions
17 visible transitions
46 arcs
```

The Article 12 net contains:

```text
18 places
10 transitions
8 visible transitions
34 arcs
```

Only obligations whose satisfaction can be represented through observable activity occurrence, order or presence are included in the executable nets. Open-textured obligations that require substantive judgement are deliberately not converted into process constraints.

## Stage 2: Log abstraction

Raw event labels do not necessarily use the same terminology as the reference models. Stage 2 therefore maps each raw label onto one activity from a closed set of 25 permitted activities or leaves it unmapped.

Four abstraction approaches are implemented.

### Dictionary

The dictionary baseline accepts direct matches to the known vocabulary. It is included as a simple comparison with the more flexible mapping approaches.

### Deterministic retrieval

The main reproducible evaluation uses a deterministic retrieval mapper. It compares raw labels with known surface forms and applies a similarity cutoff of:

```text
theta = 0.72
```

This mapper requires no network connection or external language model.

### Language-model mapper

A language-model mapper is provided for the diagnostic abstraction experiment.

The implementation uses:

```text
Claude Opus 4.8
model ID: claude-opus-4-8
```

The model receives a single user prompt without a system prompt. The prompt lists the 25 permitted activities with short explanatory glosses, provides eight few-shot examples and asks the model to map the raw label onto the closed vocabulary. The maximum response length is 40 tokens.

No sampling parameter is explicitly set.

### Hybrid mapper

The hybrid mapper uses deterministic retrieval for labels that can be resolved reliably and delegates otherwise unmapped labels to the language model.

The LLM and hybrid experiments require an Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

For example:

```bash
python pipeline.py --n 50 --seed 7 --mapper hybrid --novel 0.4
```

API credentials are not stored in the repository.

## Stage 3: Conformance checking

Each abstracted trace contains activities associated with both Articles 9 & 12. It is therefore projected separately onto the activity alphabet of each reference model.

Alignment-based conformance checking is performed in PM4Py using state-equation A* alignment.

Trace fitness is based on the alignment cost relative to the corresponding worst-case cost.

A trace is classified as conforming when both projected fitness values exceed:

```text
tau = 0.999
```

A separate presence check is retained as a baseline to distinguish failures caused by missing activities from failures that are only visible through process structure or event ordering.

## Clause-level validation

The validation stage compares two independently constructed views of operationalisability.

First, the clauses of Articles 9 and 12 are positioned in a construct space based on their descriptive-to-normative and abstract-to-granular characteristics.

Second, the executable models are probed to determine whether removing a corresponding operational activity produces a detectable process deviation.

The resulting comparison distinguishes structural, dual, open and permissive clauses.

The coding coordinates and supporting inter-coder materials are included in the repository to make this part of the analysis inspectable.

## Reproducibility

The principal deterministic results can be reproduced without an external service.

Key settings are:

```text
Random seed:                   7
Traces per log:                50
Retrieval cutoff:              0.72
Conformance threshold:         0.999
Main mapper:                   retrieval
Language model:                Claude Opus 4.8
Language-model max tokens:     40
```

Exact Python package versions are pinned in `requirements.txt`.

The LLM and hybrid runs are supplementary abstraction experiments and require access to the external Anthropic API. They are not required to reproduce the headline deterministic retrieval results.