from pathlib import Path
from genomeforge import Compiler
from genomeforge.cli import main
import sys


def test_compile_creates_project_package(tmp_path):
    source = Path('examples/minimal.genome').read_text(encoding='utf-8')
    out = Compiler().compile(source, str(tmp_path))
    assert out == tmp_path / 'minimal'
    assert (out / 'system.py').exists()
    assert (out / 'runtime' / 'bus.py').exists()
    assert (out / 'modules' / 'wallet.py').exists()


def test_cli_module_execution_creates_nested_project_dir(tmp_path, monkeypatch, capsys):
    source_path = Path('examples/minimal.genome').resolve()
    monkeypatch.setattr(sys, 'argv', ['genomeforge.cli', str(source_path), '--out', str(tmp_path)])
    main()
    captured = capsys.readouterr()
    assert 'Compiled to' in captured.out
    assert (tmp_path / 'minimal' / 'system.py').exists()
