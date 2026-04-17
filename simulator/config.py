from __future__ import annotations

import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MqttConfig:
    host: str = "100.100.164.105"
    port: int = 1883


@dataclass
class SimulatorConfig:
    speed_multiplier: float = 1.0
    tick_interval: float = 1.0


@dataclass
class StoppageConfig:
    mean_interval_seconds: float = 300.0
    mean_duration_seconds: float = 30.0


@dataclass
class ChangeoverConfig:
    duration_seconds: float = 60.0


@dataclass
class AlertsConfig:
    speed_delta_pct_threshold: float = 10.0


@dataclass
class Recipe:
    sku: int
    name: str
    recommended_line_speed: float
    speed_setpoint_pct: float = 0.0  # fractional offset from recommended (0.10 = +10%, -0.05 = -5%)


@dataclass
class Order:
    sku: int
    run_duration: float  # seconds


@dataclass
class Config:
    mqtt: MqttConfig = field(default_factory=MqttConfig)
    simulator: SimulatorConfig = field(default_factory=SimulatorConfig)
    stoppages: StoppageConfig = field(default_factory=StoppageConfig)
    changeover: ChangeoverConfig = field(default_factory=ChangeoverConfig)
    alerts: AlertsConfig = field(default_factory=AlertsConfig)
    recipes: list[Recipe] = field(default_factory=list)
    schedule: list[Order] = field(default_factory=list)

    def recipe_for(self, sku: int) -> Recipe:
        for r in self.recipes:
            if r.sku == sku:
                return r
        raise KeyError(f"No recipe for SKU {sku}")


def load(path: Path, speed_override: float | None = None) -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)

    cfg = Config(
        mqtt=MqttConfig(**raw.get("mqtt", {})),
        simulator=SimulatorConfig(**raw.get("simulator", {})),
        stoppages=StoppageConfig(**raw.get("stoppages", {})),
        changeover=ChangeoverConfig(**raw.get("changeover", {})),
        alerts=AlertsConfig(**raw.get("alerts", {})),
        recipes=[Recipe(**r) for r in raw.get("recipes", [])],
        schedule=[Order(**o) for o in raw.get("schedule", [])],
    )

    if speed_override is not None:
        cfg.simulator.speed_multiplier = speed_override

    return cfg
