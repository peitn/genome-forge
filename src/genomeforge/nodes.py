from dataclasses import dataclass, field
from typing import Any, List

@dataclass
class ParamNode:
    name: str
    type_name: str

@dataclass
class StateNode:
    name: str
    type_name: str
    default_value: Any

@dataclass
class BehaviorNode:
    name: str
    params: List[ParamNode]
    return_var: str
    body: str

@dataclass
class HandlerNode:
    name: str
    params: List[ParamNode]
    body: str

@dataclass
class MetricNode:
    name: str
    expression: str

@dataclass
class TraitNode:
    name: str
    states: List[StateNode] = field(default_factory=list)

@dataclass
class PlasmidNode:
    name: str
    states: List[StateNode] = field(default_factory=list)
    behaviors: List[BehaviorNode] = field(default_factory=list)
    handlers: List[HandlerNode] = field(default_factory=list)
    metrics: List[MetricNode] = field(default_factory=list)

@dataclass
class ModuleNode:
    name: str
    kind: str
    extends: List[str] = field(default_factory=list)
    uses: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    states: List[StateNode] = field(default_factory=list)
    behaviors: List[BehaviorNode] = field(default_factory=list)
    handlers: List[HandlerNode] = field(default_factory=list)
    metrics: List[MetricNode] = field(default_factory=list)

@dataclass
class ConnectionNode:
    src_module: str
    src_signal: str
    dst_module: str
    dst_signal: str

@dataclass
class AdaptRuleNode:
    target_module: str
    metric: str
    operator: str
    threshold: float
    target_state: str
    target_value: Any

@dataclass
class AdaptNode:
    target_module: str
    rules: List[AdaptRuleNode] = field(default_factory=list)

@dataclass
class ProjectNode:
    name: str
    version: str
    backend: str
    traits: List[TraitNode] = field(default_factory=list)
    plasmids: List[PlasmidNode] = field(default_factory=list)
    modules: List[ModuleNode] = field(default_factory=list)
    connections: List[ConnectionNode] = field(default_factory=list)
    adaptations: List[AdaptNode] = field(default_factory=list)

@dataclass
class Route:
    src_module: str
    src_signal: str
    dst_module: str
    dst_signal: str

@dataclass
class LoweredModule:
    name: str
    kind: str
    states: List[StateNode]
    inputs: List[str]
    outputs: List[str]
    behaviors: List[BehaviorNode]
    handlers: List[HandlerNode]
    metrics: List[MetricNode]

@dataclass
class LoweredProject:
    name: str
    version: str
    modules: List[LoweredModule]
    routes: List[Route]
    adapt_rules: List[AdaptRuleNode]
