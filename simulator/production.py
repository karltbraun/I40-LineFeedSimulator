from __future__ import annotations

import math
import random
import time

from .config import Config, Order, Recipe
from .mqtt_publisher import MqttPublisher
from .speed_tracker import SpeedTracker
from .state import LineState
from .topics import TOPICS


class ProductionEngine:
    def __init__(self, cfg: Config, publisher: MqttPublisher) -> None:
        self._cfg = cfg
        self._pub = publisher
        self._tracker = SpeedTracker()
        self._state = LineState.IDLE

    def run_order(self, order: Order, recipe: Recipe) -> None:
        """Execute a single production order, blocking until complete."""
        multiplier = self._cfg.simulator.speed_multiplier
        tick = self._cfg.simulator.tick_interval
        run_duration = order.run_duration
        stoppage_cfg = self._cfg.stoppages

        set_speed = recipe.recommended_line_speed * (1.0 + recipe.speed_setpoint_pct)
        speed = set_speed
        self._tracker.reset()

        scheduled_time = 0.0
        downtime_seconds = 0.0
        downtime_events = 0
        elapsed = 0.0

        self._set_state(LineState.RUNNING, recipe)

        while elapsed < run_duration:
            tick_start = time.monotonic()

            # --- Stoppage check (Poisson) ---
            p_stop = 1.0 - math.exp(-tick / stoppage_cfg.mean_interval_seconds)
            if random.random() < p_stop:
                duration = random.expovariate(1.0 / stoppage_cfg.mean_duration_seconds)
                self._set_state(LineState.STOP, recipe, speed=0.0)
                time.sleep(duration / multiplier)
                downtime_seconds += duration
                downtime_events += 1
                self._set_state(LineState.RUNNING, recipe)
                # Small drift after recovery
                speed += random.gauss(0, recipe.recommended_line_speed * 0.02)

            # --- Speed update (mean-reverting around setpoint) ---
            target = set_speed
            reversion = 0.15 * (target - speed)
            noise = random.gauss(0.0, recipe.recommended_line_speed * 0.012 * math.sqrt(tick))
            speed += reversion + noise
            speed = max(recipe.recommended_line_speed * 0.3,
                        min(speed, recipe.recommended_line_speed * 2.5))

            # --- Rolling averages ---
            self._tracker.add(speed)

            # --- OEE Availability ---
            scheduled_time += tick
            availability = (scheduled_time - downtime_seconds) / scheduled_time if scheduled_time > 0 else 1.0

            # --- Derived speed metrics ---
            delta = speed - recipe.recommended_line_speed
            delta_pct = (delta / recipe.recommended_line_speed * 100.0) if recipe.recommended_line_speed else 0.0

            # --- Publish all topics ---
            self._pub.publish(TOPICS["speed_current"],     round(speed, 2))
            self._pub.publish(TOPICS["speed_set"],         round(set_speed, 2))
            self._pub.publish(TOPICS["speed_recommended"], round(recipe.recommended_line_speed, 2))
            self._pub.publish(TOPICS["speed_delta"],       round(delta, 2))
            self._pub.publish(TOPICS["speed_delta_pct"],   round(delta_pct, 2))
            self._pub.publish(TOPICS["speed_avg_1min"],    round(self._tracker.avg_1min, 2))
            self._pub.publish(TOPICS["speed_avg_5min"],    round(self._tracker.avg_5min, 2))
            self._pub.publish(TOPICS["speed_avg_run"],     round(self._tracker.avg_run, 2))
            self._pub.publish(TOPICS["availability"],      round(availability, 4))
            self._pub.publish(TOPICS["downtime_total"],    int(downtime_seconds))
            self._pub.publish(TOPICS["downtime_events"],   downtime_events)

            elapsed += tick
            sleep_time = tick / multiplier - (time.monotonic() - tick_start)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def set_idle(self) -> None:
        self._set_state(LineState.IDLE)

    def set_setup(self, recipe: Recipe) -> None:
        self._set_state(LineState.SETUP, recipe)

    def set_changeover(self) -> None:
        self._set_state(LineState.CHANGEOVER)
        self._pub.publish(TOPICS["speed_current"], 0.0)

    def _set_state(self, state: LineState, recipe: Recipe | None = None, speed: float | None = None) -> None:
        self._state = state
        self._pub.publish(TOPICS["state"],       int(state))
        self._pub.publish(TOPICS["state_label"], state.label)
        if recipe is not None:
            self._pub.publish(TOPICS["sku"], recipe.sku)
        if speed is not None:
            self._pub.publish(TOPICS["speed_current"], round(speed, 2))
