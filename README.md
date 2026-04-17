# LineFeed Simulator

Simulates a fresh-foods raw-product-dump production line (NewCo / Soledad facility) and streams real-time metrics via MQTT → Telegraf → InfluxDB 3 → Grafana.

The core demo story: a line operator running the cutter feed faster than the SKU 102 recipe specifies, causing cumulative equipment damage — visible live on the dashboard as the speed delta climbs.

---

## Prerequisites

- [uv](https://docs.astral.sh/uv/) Python package manager
- I40-Stack running (`../I40-Stack/`) — `start-lfs` handles this automatically

---

## Starting the Demo

**Recommended — starts I40-Stack if needed, then runs the simulator:**

```bash
./start-lfs --speed 5 --loop
```

**Direct — if I40-Stack is already running:**

```bash
uv run python main.py --speed 5 --loop
```

**Background:**

```bash
./start-lfs --speed 5 --loop &
```

### Options

| Flag                 | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `--speed MULTIPLIER` | Compress sim time (e.g. `5` = 5× faster than real-time) |
| `--loop`             | Repeat the order schedule indefinitely until stopped    |
| `--config PATH`      | Path to config file (default: `config.toml`)            |

At `--speed 5` one full schedule cycle (SKU 101 → 102 → 103) takes about **3 minutes** of wall-clock time.

---

## Stopping the Demo

**Foreground:** press `Ctrl-C`

**Background:**

```bash
kill $(pgrep -f "main.py")
```

Both methods trigger a graceful shutdown: the line state is published as `IDLE` and the MQTT connection is cleanly closed.

---

## Grafana Dashboard

Open: **http://localhost:3000/d/linefeed-v1/**

The dashboard auto-refreshes and shows:

- Current line state and SKU
- Live and historical cutter feed speed vs. recommended
- Speed delta % (watch this climb during the SKU 102 run)
- OEE Availability and downtime events

---

## Order Schedule (default `config.toml`)

| Order | SKU | Name              | Sim Duration | Notes                                                  |
| ----- | --- | ----------------- | ------------ | ------------------------------------------------------ |
| 1     | 101 | Fresh Cut Lettuce | 300 s        | Normal run                                             |
| 2     | 102 | Shredded Cabbage  | 420 s        | **22% overspeed bias** kicks in at 40% through the run |
| 3     | 103 | Diced Onion       | 240 s        | Normal run                                             |
