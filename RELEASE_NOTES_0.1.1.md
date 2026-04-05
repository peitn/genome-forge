# genomeforge 0.1.1

## Summary

`0.1.1` is the first repo-ready stabilization release of `genomeforge`, a Python-based DSL compiler for genome-defined modular systems.

This release turns the project from a good prototype into a verified minimal compiler pipeline with:

- working module execution via `python -m genomeforge.cli`
- consistent generated package layout under `<out_dir>/<project_name>/`
- end-to-end compile/import/instantiate coverage
- a connected multi-module routing example
- cleaned repository metadata and documentation

## Highlights

- Fixed CLI module execution
- Fixed generated package/import consistency
- Added end-to-end runtime import tests
- Added connected routing example
- Added changelog, license, and improved README

## Recommended GitHub release title

`genomeforge v0.1.1 — first repo-ready compiler snapshot`

## Recommended GitHub release body

This release establishes the first repo-ready baseline for `genomeforge`.

It includes the two key stabilization fixes:

1. `python -m genomeforge.cli ...` now runs correctly
2. generated projects are now emitted as real Python packages under `<out_dir>/<project_name>/`

It also adds end-to-end compile/import/instantiate coverage and a second connected example proving that module routing works in practice.

Test status for this snapshot:

- 5/5 PASS

This version is intended as the first credible base for future DSL, runtime, and evolutionary-system expansion.
