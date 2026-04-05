from .nodes import ProjectNode, LoweredProject, LoweredModule, Route, AdaptRuleNode

class LoweringPass:
    def _inject(self, target_list, new_items, kind, mod_name):
        for n in new_items:
            key = getattr(n, 'signal', getattr(n, 'name', None))
            ext = {getattr(i, 'signal', getattr(i, 'name', None)) for i in target_list}
            if key in ext:
                raise Exception(f"Conflict in {mod_name}: duplicate {kind} '{key}'")
            target_list.append(n)

    def lower(self, ast: ProjectNode, bodies: dict) -> LoweredProject:
        for p in ast.plasmids:
            for b in p.behaviors: b.body = bodies.get(b.body, b.body)
            for h in p.handlers: h.body = bodies.get(h.body, h.body)
        for m in ast.modules:
            for b in m.behaviors: b.body = bodies.get(b.body, b.body)
            for h in m.handlers: h.body = bodies.get(h.body, h.body)
        t_map = {t.name: t for t in ast.traits}
        p_map = {p.name: p for p in ast.plasmids}
        l_modules = []
        for mod in ast.modules:
            states, behs, hands, mets = list(mod.states), list(mod.behaviors), list(mod.handlers), list(mod.metrics)
            for t_name in mod.extends:
                self._inject(states, t_map[t_name].states, 'state', mod.name)
            for p_name in mod.uses:
                self._inject(states, p_map[p_name].states, 'state', mod.name)
                self._inject(behs, p_map[p_name].behaviors, 'behavior', mod.name)
                self._inject(hands, p_map[p_name].handlers, 'handler', mod.name)
                self._inject(mets, p_map[p_name].metrics, 'metric', mod.name)
            l_modules.append(LoweredModule(mod.name, mod.kind, states, mod.inputs, mod.outputs, behs, hands, mets))
        routes = [Route(c.src_module, c.src_signal, c.dst_module, c.dst_signal) for c in ast.connections]
        rules = []
        for a in ast.adaptations:
            for r in a.rules:
                rules.append(AdaptRuleNode(a.target_module, r.metric, r.operator, r.threshold, r.target_state, r.target_value))
        return LoweredProject(ast.name, ast.version, l_modules, routes, rules)
