# Changelog

## 0.1.1 - 2026-04-05

### Added
- End-to-end compile/import/instantiate test coverage
- Second example genome with multi-module routing
- Additional E2E test for a connected system
- LICENSE file
- Repo-ready README improvements

### Changed
- `Compiler.compile()` now emits generated packages to `<out_dir>/<project_name>/`
- CLI now prints the actual compiled package path
- README quick start now matches real behavior

### Fixed
- `python -m genomeforge.cli ...` now works because `main()` is called when executed as a module
- Generated package layout is now consistent with absolute imports in templates
