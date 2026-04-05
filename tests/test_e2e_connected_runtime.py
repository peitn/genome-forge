from pathlib import Path
import sys

from genomeforge import Compiler


def test_e2e_connected_compile_import_instantiate_and_route(tmp_path):
    source = Path('examples/connected.genome').read_text(encoding='utf-8')

    package_dir = Compiler().compile(source, str(tmp_path))
    assert package_dir == tmp_path / 'connected'
    assert (package_dir / 'system.py').exists()

    sys.path.insert(0, str(tmp_path))
    try:
        from connected.system import ConnectedSystem
        system = ConnectedSystem()
        tx = system.wallet.create_transaction('alice', 10)
    finally:
        if sys.path and sys.path[0] == str(tmp_path):
            sys.path.pop(0)

    assert type(system).__name__ == 'ConnectedSystem'
    assert tx['to'] == 'alice'
    assert system.ledger.total_tx == 1
    assert 'alice' in system.ledger.last_tx
