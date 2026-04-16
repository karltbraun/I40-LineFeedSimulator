from __future__ import annotations

import time

from .config import Config, Order
from .mqtt_publisher import MqttPublisher
from .production import ProductionEngine


class MES:
    """Receives production orders, sets up the line, and runs each order."""

    def __init__(self, cfg: Config, publisher: MqttPublisher) -> None:
        self._cfg = cfg
        self._engine = ProductionEngine(cfg, publisher)

    def execute(self, order: Order) -> None:
        recipe = self._cfg.recipe_for(order.sku)
        multiplier = self._cfg.simulator.speed_multiplier

        # Setup phase
        self._engine.set_setup(recipe)
        time.sleep(5.0 / multiplier)

        # Production phase
        self._engine.run_order(order, recipe)

    def changeover(self) -> None:
        multiplier = self._cfg.simulator.speed_multiplier
        duration = self._cfg.changeover.duration_seconds
        self._engine.set_changeover()
        time.sleep(duration / multiplier)

    def idle(self) -> None:
        self._engine.set_idle()
