from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from .lowering import LoweringPass
from .preprocessor import GenomePreprocessor
from .genome_parser import genome_parser, GenomeTransformer


def py_class_name(value: str) -> str:
    return ''.join(p[:1].upper() + p[1:] for p in value.replace('-', '_').split('_') if p)

RUNTIME_BASE = """#!/usr/bin/env python3
class BaseModule:
    def __init__(self, bus, name: str):
        self.bus = bus
        self.name = name
        self.runtime_state = {}
    def emit(self, signal: str, *args, **kwargs):
        self.bus.emit(self.name, signal, *args, **kwargs)
    def evaluate_metric(self, metric_name: str):
        raise KeyError(f\"Metric not implemented: {metric_name}\")
"""
RUNTIME_BUS = """#!/usr/bin/env python3
class EventBus:
    def __init__(self):
        self.routes = {}
        self.modules = {}
    def register(self, module):
        self.modules[module.name] = module
    def add_route(self, src_mod, src_signal, dst_mod, dst_signal):
        key = f\"{src_mod}.{src_signal}\"
        self.routes.setdefault(key, []).append((dst_mod, dst_signal))
    def emit(self, src_mod, signal, *args, **kwargs):
        key = f\"{src_mod}.{signal}\"
        for dst_mod, dst_signal in self.routes.get(key, []):
            if dst_mod in self.modules:
                getattr(self.modules[dst_mod], f\"handle_{dst_signal}\")(*args, **kwargs)
"""
RUNTIME_ADAPT = """#!/usr/bin/env python3
from dataclasses import dataclass
from typing import Any
@dataclass
class AdaptiveRule:
    target_module: str
    metric: str
    operator: str
    threshold: float
    target_state: str
    target_value: Any
class AdaptiveRuntime:
    def __init__(self): self.rules = []
    def add_rule(self, rule): self.rules.append(rule)
    def evaluate(self, modules):
        for r in self.rules:
            try: val = modules[r.target_module].evaluate_metric(r.metric)
            except KeyError: continue
            if self._comp(val, r.operator, r.threshold):
                modules[r.target_module].runtime_state[r.target_state] = r.target_value
    @staticmethod
    def _comp(l, op, r):
        if op == '>': return l > r
        if op == '<': return l < r
        if op == '>=': return l >= r
        if op == '<=': return l <= r
        if op == '==': return l == r
        return False
"""

class Compiler:
    def __init__(self, templates_dir: str | None = None):
        if templates_dir is None:
            templates_dir = str(Path(__file__).parent / 'templates')
        self.env = Environment(loader=FileSystemLoader(templates_dir))
        self.env.filters['repr'] = repr
        self.env.filters['py_class_name'] = py_class_name

    def compile_ast(self, ast, bodies: dict, out_dir: str):
        ir = LoweringPass().lower(ast, bodies)
        out = Path(out_dir)
        for d in ['runtime', 'modules']:
            (out / d).mkdir(parents=True, exist_ok=True)
            (out / d / '__init__.py').touch()
        (out / '__init__.py').touch()
        (out / 'runtime/base.py').write_text(RUNTIME_BASE)
        (out / 'runtime/bus.py').write_text(RUNTIME_BUS)
        (out / 'runtime/adaptive.py').write_text(RUNTIME_ADAPT)
        mod_tpl = self.env.get_template('module.py.j2')
        for m in ir.modules:
            (out / 'modules' / f'{m.name.lower()}.py').write_text(mod_tpl.render(mod=m, project=ir))
        (out / 'system.py').write_text(self.env.get_template('system.py.j2').render(project=ir))
        return out

    def compile(self, source: str, out_dir: str):
        clean_dsl, bodies = GenomePreprocessor().extract_bodies(source)
        ast = GenomeTransformer().transform(genome_parser.parse(clean_dsl))
        package_dir = Path(out_dir) / ast.name
        self.compile_ast(ast, bodies, str(package_dir))
        return package_dir
