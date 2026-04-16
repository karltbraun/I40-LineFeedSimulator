from __future__ import annotations

import logging
from collections import deque

from .config import Config, Order
from .mes import MES
from .mqtt_publisher import MqttPublisher

logger = logging.getLogger(__name__)


class Scheduler:
    def __init__(self, cfg: Config, publisher: MqttPublisher) -> None:
        self._cfg = cfg
        self._mes = MES(cfg, publisher)
        self._queue: deque[Order] = deque(cfg.schedule)

    def run(self) -> None:
        first = True
        while self._queue:
            order = self._queue.popleft()
            recipe = self._cfg.recipe_for(order.sku)
            logger.info("Starting order: SKU %d (%s), duration %ds", order.sku, recipe.name, order.run_duration)

            if not first:
                self._mes.changeover()
            first = False

            self._mes.execute(order)
            logger.info("Completed order: SKU %d", order.sku)

        self._mes.idle()
        logger.info("Schedule complete — line idle")
