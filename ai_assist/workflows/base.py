from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Param:
    name: str
    label: str
    kind: str            # int / float / money / pct / bool / choice
    default: Any
    group: str = '约束'   # 目标 / 约束 / 算法
    help: str = ''
    min: float | None = None
    max: float | None = None
    choices: list | None = None

    def clean(self, raw):
        if raw is None or raw == '':
            return self.default
        if self.kind == 'bool':
            return str(raw).lower() in ('1', 'true', 'on', 'yes')
        if self.kind == 'choice':
            vals = [c[0] for c in (self.choices or [])]
            return raw if raw in vals else self.default
        try:
            v = float(raw)
        except (TypeError, ValueError):
            return self.default
        if self.min is not None:
            v = max(v, self.min)
        if self.max is not None:
            v = min(v, self.max)
        return int(round(v)) if self.kind == 'int' else v

    def as_dict(self):
        return {k: getattr(self, k) for k in ('name', 'label', 'kind', 'default', 'group', 'help', 'min', 'max', 'choices')}


@dataclass
class RunContext:
    tenant: Any
    params: dict
    as_of: dt.date
    brand: Any = None
    user: Any = None


@dataclass
class RunResult:
    summary: dict
    suggestions: list[dict] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class Workflow:
    key = ''
    label = ''
    cycle = 'day'
    objective = ''
    pain_point = ''
    role = ''
    params: list[Param] = []

    def clean_params(self, raw: dict | None) -> dict:
        raw = raw or {}
        return {p.name: p.clean(raw.get(p.name)) for p in self.params}

    def run(self, ctx: RunContext) -> RunResult:  # pragma: no cover
        raise NotImplementedError


def yuan(x: float) -> str:
    if abs(x) >= 10000:
        return f'¥{x / 10000:.2f} 万'
    return f'¥{x:,.0f}'
