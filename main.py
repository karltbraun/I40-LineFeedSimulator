from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from simulator.config import load
from simulator.mqtt_publisher import MqttPublisher
from simulator.scheduler import Scheduler

console = Console()

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(console=console, show_path=False)],
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="LineFeed Simulator")
    parser.add_argument(
        "--config", type=Path, default=Path("config.toml"),
        help="Path to TOML config file (default: config.toml)"
    )
    parser.add_argument(
        "--speed", type=float, default=None, metavar="MULTIPLIER",
        help="Speed multiplier override (e.g. 10 = 10x faster than real-time)"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Repeat the schedule indefinitely until Ctrl-C"
    )
    args = parser.parse_args()

    cfg = load(args.config, speed_override=args.speed)
    publisher = MqttPublisher(cfg.mqtt.host, cfg.mqtt.port)

    def shutdown(sig, frame):  # noqa: ANN001
        console.print("\n[yellow]Shutting down...[/yellow]")
        try:
            publisher.disconnect()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    console.rule("[bold cyan]LineFeed Simulator")
    console.print(f"  Config:    {args.config}")
    console.print(f"  Broker:    {cfg.mqtt.host}:{cfg.mqtt.port}")
    console.print(f"  Speed:     {cfg.simulator.speed_multiplier}x")
    console.print(f"  Orders:    {len(cfg.schedule)}")
    console.print(f"  Loop:      {'yes' if args.loop else 'no'}")
    console.rule()

    publisher.connect()
    while True:
        Scheduler(cfg, publisher).run()
        if not args.loop:
            break
        logger.info("Schedule complete — restarting")
    publisher.disconnect()
    console.print("[green]Schedule complete.[/green]")


if __name__ == "__main__":
    main()
