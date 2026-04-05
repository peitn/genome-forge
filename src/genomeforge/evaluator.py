import sys, importlib.util
from pathlib import Path

class GenomeEvaluator:
    def __init__(self, compiler): self.compiler = compiler
    def evaluate(self, ast, out_dir: Path, bodies: dict) -> dict:
        project_dir = out_dir / ast.name
        module_name = f"{ast.name}.system"
        try:
            self.compiler.compile_ast(ast, bodies, str(project_dir))
        except Exception as e:
            return {'fitness': -1000.0, 'status': 'compile_error', 'error': str(e)}
        try:
            sys.path.insert(0, str(out_dir))
            spec = importlib.util.spec_from_file_location(module_name, str(project_dir / 'system.py'))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
            cls_name = f"{ast.name.replace('_', ' ').title().replace(' ', '')}System"
            system = getattr(mod, cls_name)()
        except Exception as e:
            return {'fitness': -500.0, 'status': 'import_error', 'error': str(e)}
        finally:
            if sys.path and sys.path[0] == str(out_dir):
                sys.path.pop(0)
        return self._run_workload(system)
    def _run_workload(self, system) -> dict:
        try:
            traffic_schedule = [0,0,1,2,0,12,0,0,1,0,0,5,0,0,0,15,2,1,0,0,0,0,8,3,0,0,0,4,0,14,0,0,0,0,0,0,0]
            for tx_count in traffic_schedule:
                for _ in range(tx_count):
                    system.wallet.create_transaction('alice', 10)
                system.clock.tick_world()
                system.tick()
            delivered_tx = system.ledger.total_tx
            blocks_created = len(system.ledger.blocks)
            stuck_tx = len(system.mempool.transactions)
            wait_time = system.mempool.time_since_last_flush
            has_compression = 'is_compressed' in system.mempool.__dict__
            has_crypto = 'is_secure' in system.mempool.__dict__
            tx_reward = 12.0 if has_crypto else 10.0
            block_cost = 20.0 if has_compression else 40.0
            reward = delivered_tx * tx_reward
            cost = blocks_created * block_cost
            stuck_penalty = stuck_tx * 20.0
            overtime_penalty = max(0, wait_time - 3) * 25.0
            arch_tax = (10.0 if has_compression else 0.0) + (10.0 if has_crypto else 0.0)
            fitness = reward - cost - stuck_penalty - overtime_penalty - arch_tax
            return {
                'fitness': float(fitness), 'delivered': delivered_tx, 'blocks': blocks_created,
                'stuck': stuck_tx, 'wait_time': wait_time, 'compressed': has_compression,
                'secure': has_crypto, 'status': 'ok'
            }
        except Exception as e:
            return {'fitness': -1000.0, 'status': 'runtime_error', 'error': str(e)}
