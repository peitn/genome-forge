from pathlib import Path
import sys

from genomeforge import Compiler


def test_e2e_compile_import_and_instantiate(tmp_path):
    source = Path('examples/minimal.genome').read_text(encoding='utf-8')

    package_dir = Compiler().compile(source, str(tmp_path))
    assert package_dir == tmp_path / 'minimal'
    assert (package_dir / 'system.py').exists()

    sys.path.insert(0, str(tmp_path))
    try:
        from minimal.system import MinimalSystem
        system = MinimalSystem()
    finally:
        if sys.path and sys.path[0] == str(tmp_path):
            sys.path.pop(0)

    assert type(system).__name__ == 'MinimalSystem'
    assert hasattr(system, 'wallet')
    assert hasattr(system, 'bus')
    assert hasattr(system, 'runtime')
