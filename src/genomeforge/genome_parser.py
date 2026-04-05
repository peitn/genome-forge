from lark import Lark, Transformer, v_args
from .nodes import *

GRAMMAR = r'''
start: project_decl compile_decl trait_decl* plasmid_decl* module_decl* connect_decl* adapt_decl*
project_decl: "project" CNAME "v" NUMBER
compile_decl: "compile" CNAME
trait_decl: "trait" CNAME "{" state_decl* "}"
plasmid_decl: "plasmid" CNAME "{" plasmid_item* "}"
?plasmid_item: state_decl | behavior_decl | handler_decl | metric_decl
module_decl: "module" CNAME ":" CNAME extends_clause? uses_clause? "{" module_item* "}"
extends_clause: "extends" CNAME ("," CNAME)*
uses_clause: "uses" CNAME ("," CNAME)*
?module_item: in_decl | out_decl | state_decl | behavior_decl | handler_decl | metric_decl
in_decl: "in" CNAME
out_decl: "out" CNAME
state_decl: "state" CNAME ":" CNAME "=" value
metric_decl: "metric" CNAME "=" /[^\n]+/
behavior_decl: "behavior" CNAME "(" [param_list] ")" "->" CNAME BODY_PLACEHOLDER
handler_decl: "on" CNAME "(" [param_list] ")" BODY_PLACEHOLDER
BODY_PLACEHOLDER: /__BODY_\d+__/
connect_decl: "connect" CNAME "." CNAME "->" CNAME "." CNAME
adapt_decl: "adapt" CNAME "{" adapt_rule* "}"
adapt_rule: "if" CNAME COMP_OP NUMBER "set" CNAME "=" value
param_list: param ("," param)*
param: CNAME ":" CNAME
COMP_OP: ">" | "<" | ">=" | "<=" | "=="
?value: NUMBER -> number
    | ESCAPED_STRING -> string
    | "true" -> true_val
    | "false" -> false_val
    | "[]" -> empty_list
    | "{}" -> empty_dict
%import common.CNAME
%import common.NUMBER
%import common.ESCAPED_STRING
%import common.WS
%ignore WS
'''

genome_parser = Lark(GRAMMAR, start='start', parser='lalr')

@v_args(inline=True)
class GenomeTransformer(Transformer):
    def string(self, s): return s[1:-1]
    def number(self, n): return float(n) if '.' in str(n) else int(n)
    def true_val(self): return True
    def false_val(self): return False
    def empty_list(self): return []
    def empty_dict(self): return {}
    def extends_clause(self, *names): return ('extends', [str(n) for n in names])
    def uses_clause(self, *names): return ('uses', [str(n) for n in names])
    def param(self, name, type_name): return ParamNode(str(name), str(type_name))
    def param_list(self, *params): return list(params)
    def state_decl(self, name, type_name, value): return StateNode(str(name), str(type_name), value)
    def metric_decl(self, name, expr_token): return MetricNode(str(name), str(expr_token).strip())
    def trait_decl(self, name, *states): return TraitNode(str(name), list(states))
    def plasmid_decl(self, name, *items):
        p = PlasmidNode(str(name))
        for i in items:
            if isinstance(i, StateNode): p.states.append(i)
            elif isinstance(i, BehaviorNode): p.behaviors.append(i)
            elif isinstance(i, HandlerNode): p.handlers.append(i)
            elif isinstance(i, MetricNode): p.metrics.append(i)
        return p
    def in_decl(self, name): return ('in', str(name))
    def out_decl(self, name): return ('out', str(name))
    def behavior_decl(self, name, p_or_ret, ret_or_body, b_ph=None):
        if b_ph is None: p, r, b = [], p_or_ret, ret_or_body
        else: p, r, b = p_or_ret, ret_or_body, b_ph
        if p is None: p = []
        return BehaviorNode(str(name), p, str(r), str(b))
    def handler_decl(self, name, p_or_body, b_ph=None):
        if b_ph is None: p, b = [], p_or_body
        else: p, b = p_or_body, b_ph
        if p is None: p = []
        return HandlerNode(str(name), p, str(b))
    def module_decl(self, name, kind, *items):
        mod = ModuleNode(str(name), str(kind))
        for i in items:
            if isinstance(i, tuple) and i[0] == 'extends': mod.extends.extend(i[1])
            elif isinstance(i, tuple) and i[0] == 'uses': mod.uses.extend(i[1])
            elif isinstance(i, tuple) and i[0] == 'in': mod.inputs.append(i[1])
            elif isinstance(i, tuple) and i[0] == 'out': mod.outputs.append(i[1])
            elif isinstance(i, StateNode): mod.states.append(i)
            elif isinstance(i, BehaviorNode): mod.behaviors.append(i)
            elif isinstance(i, HandlerNode): mod.handlers.append(i)
            elif isinstance(i, MetricNode): mod.metrics.append(i)
        return mod
    def connect_decl(self, sm, ss, dm, ds): return ConnectionNode(str(sm), str(ss), str(dm), str(ds))
    def adapt_rule(self, metric, op, threshold, target_state, value):
        return AdaptRuleNode('', str(metric), str(op), float(threshold), str(target_state), value)
    def adapt_decl(self, target, *rules): return AdaptNode(str(target), list(rules))
    def project_decl(self, name, version): return (str(name), str(version))
    def compile_decl(self, backend): return str(backend)
    def start(self, *items):
        project = ProjectNode(name=items[0][0], version=items[0][1], backend=items[1])
        for i in items[2:]:
            if isinstance(i, TraitNode): project.traits.append(i)
            elif isinstance(i, PlasmidNode): project.plasmids.append(i)
            elif isinstance(i, ModuleNode): project.modules.append(i)
            elif isinstance(i, ConnectionNode): project.connections.append(i)
            elif isinstance(i, AdaptNode): project.adaptations.append(i)
        return project
