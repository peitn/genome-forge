# genomeforge

> A small but verified Python DSL compiler for genome-defined modular systems.

`genomeforge` is a Python library and development environment for a custom DSL that describes modular, evolvable systems as genomes. It includes:

- preprocessing of embedded code blocks into placeholders
- Lark-based parsing into AST nodes
- lowering into a semantic IR
- Jinja2 code generation into runnable Python systems
- mutation/evaluation helpers for evolutionary search

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m genomeforge.cli examples/baseline.genome --out generated
```

This creates a real Python package under:

```text
generated/baseline/
```

## Generated package structure

A compiled project is emitted as a normal Python package:

```text
generated/
└── baseline/
    ├── __init__.py
    ├── system.py
    ├── runtime/
    │   ├── __init__.py
    │   ├── adaptive.py
    │   ├── base.py
    │   └── bus.py
    └── modules/
        ├── __init__.py
        └── wallet.py
```

## How to import

Add the output root directory to `PYTHONPATH` or `sys.path`, then import the generated package by project name:

```python
import sys
sys.path.insert(0, "generated")

from baseline.system import BaselineSystem
system = BaselineSystem()
```

## How to run

The generated system can be instantiated directly from Python:

```python
import sys
sys.path.insert(0, "generated")

from baseline.system import BaselineSystem
system = BaselineSystem()
system.tick()
```

You can also compile a more connected example:

```bash
python -m genomeforge.cli examples/connected.genome --out generated
```

## Examples

- `examples/baseline.genome` — minimal single-module compilation target
- `examples/connected.genome` — multi-module example with `connect` routing and handlers

## Layout

- `src/genomeforge/` library code
- `examples/` sample genomes
- `.vscode/` development environment
- `tests/` smoke and E2E tests
- `LICENSE` project license
- `CHANGELOG.md` release notes

## Note

This package is an extracted, library-oriented form of the experimental genome DSL and evolutionary compiler built in this chat session.
