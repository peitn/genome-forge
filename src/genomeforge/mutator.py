import copy, random

class GenomeMutator:
    def __init__(self, mutation_rate=0.8):
        self.mutation_rate = mutation_rate
        self.operators = ['>', '<', '>=', '<=', '==']
    def mutate(self, ast, mutant_name: str):
        mutant = copy.deepcopy(ast)
        mutant.name = mutant_name
        for adapt in mutant.adaptations:
            for rule in adapt.rules:
                if random.random() < self.mutation_rate:
                    self._mutate_rule(rule)
        if random.random() < 0.20:
            self._mutate_architecture(mutant)
        return mutant
    def _mutate_rule(self, rule):
        if random.choice(['threshold', 'operator']) == 'threshold':
            delta = random.choice([-90,-75,-50,-25,-10,-5,-1,1,5,10,25,50])
            rule.threshold = max(0, min(150, rule.threshold + delta))
        else:
            new_ops = [o for o in self.operators if o != rule.operator]
            rule.operator = random.choice(new_ops)
    def _mutate_architecture(self, ast):
        available_plasmids = [p.name for p in ast.plasmids]
        if not available_plasmids: return
        mempool = next((m for m in ast.modules if m.name == 'Mempool'), None)
        if not mempool: return
        action = random.choice(['add', 'remove'])
        chosen = random.choice(available_plasmids)
        if action == 'add' and chosen not in mempool.uses:
            mempool.uses.append(chosen)
        elif action == 'remove' and chosen in mempool.uses:
            mempool.uses.remove(chosen)
