# Requirements — LineFeed Simulator

## Objective

Demonstrate the value of real-time production data flowing through a Unified Namespace (UNS) into a live dashboard.

The specific story: a line operator is running the raw-product cutter feed faster than the recipe specifies, causing equipment damage. This demo shows how that deviation — and other key production metrics — become immediately visible when data is captured and routed through a modern I40 stack.

**Audience:** VP of IT and a senior IT analyst. Familiar with fresh-foods manufacturing from an IT perspective; limited OT background. The demo must be clear, credible, and visually compelling without requiring OT expertise to interpret.

---

## Simulated Facility

**Company:** NewCo  
**Site:** Soledad  
**Area:** Raw Product Dump — raw product (fresh produce) is unloaded from bins and crates onto a conveyor feeding into cutters. There are no scales or standard unit containers; product is tracked by crate/bin barcode scan for traceability only.

---

## Architecture & Data Flow

```
Python Simulator
      │
      │  MQTT publish
      ▼
Mosquitto (i40-mosquitto, port 1883)
      │
      │  subscribe
      ▼
Telegraf (i40-telegraf)
      │
      │  write
      ▼
InfluxDB 3 (i40-influxdb, port 8181)
      │
      │  query
      ▼
Grafana Dashboard (i40-grafana, port 3000)
```

All services are defined in `../I40-Demo/docker-compose.m3.yml` and run on the local M3 MacBook. The stack is accessible remotely via Tailscale VPN.

The simulator is a standalone Python process that connects to Mosquitto and drives all topic updates. No Node-RED flows are required for this project (Telegraf handles the MQTT → InfluxDB path directly), though Node-RED remains available in the stack for future use.

---

## Simulator

### Language

Python 3.11+. Runs as a standalone script/process outside of Docker (connects to the local Mosquitto port).

### Components

| Component             | Responsibility                                                                                                                                  |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Scheduler**         | Holds the production schedule (ordered list of production orders). Dispatches the next order when the line is idle.                             |
| **MES**               | Receives an order from the Scheduler. Sets up the line (state → Setup, loads recipe, resets counters), then hands off to the Production engine. |
| **Production Engine** | Runs the production loop: ticks line speed, evaluates stoppages, publishes MQTT updates on each tick.                                           |
| **MQTT Publisher**    | Thin wrapper around `paho-mqtt`. All MQTT writes go through here.                                                                               |

### Simulation Speed

The simulator runs with a configurable **speed multiplier** (default `1.0` = real-time). A multiplier of `10` compresses time by 10×, useful for running a full schedule during a demo. The multiplier scales tick intervals; all timestamps published to MQTT remain wall-clock time.

### Production Orders (Schedule)

3–5 orders at startup, each specifying:

- `SKU` (int)
- `Run_Duration` (seconds) — how long the production run lasts before changeover

### Recipes

One recipe per SKU, specifying:

- `Recommended_Line_Speed` (units/min)
- `Expected_Waste_Rate` (fraction, e.g. 0.03 = 3%)

### Line Speed Behavior

- At run start, actual line speed is set to `Recommended_Line_Speed ± random delta`.
- Each tick, speed drifts slightly (bounded random walk).
- To demonstrate the core scenario, one SKU's run will include a sustained period where speed is pushed significantly above the recommended value (configurable bias, e.g. +15–25%).
- Published metrics: current speed, recommended speed, delta (absolute and %), rolling averages (1-min, 5-min, run average).

### Stoppages

- Frequency: Poisson-distributed (configurable mean interval per run).
- Duration: Exponentially distributed (configurable mean).
- Type: untyped for now (reason codes are a future revision).
- During a stoppage: state → `Stop`, line speed → 0, production pauses.
- Recovery: state → `Running`, line speed returns to pre-stoppage value ± small delta.

### Changeover

- Triggered between production orders.
- State → `Changeover` for a fixed configurable duration (default 60 sim-seconds).
- Line speed → 0 during changeover.
- After changeover: Scheduler dispatches next order.

### State Machine

| Code | Label      | Description                        |
| ---- | ---------- | ---------------------------------- |
| 0    | Idle       | No active order; waiting           |
| 1    | Setup      | Loading recipe, resetting counters |
| 2    | Running    | Active production                  |
| 5    | Stop       | Unplanned stoppage                 |
| 9    | Changeover | Between production orders          |

---

## UNS — Topic Structure

### Line-level topics — `NewCo/Soledad/RawProductDump/Line1/`

| Topic                       | Type   | Description                            |
| --------------------------- | ------ | -------------------------------------- |
| `.../State`                 | int    | Current state code (0/1/2/5/9)         |
| `.../StateLabel`            | string | Human-readable state label             |
| `.../SKU`                   | int    | Current SKU in production              |
| `.../OEE/Availability`      | float  | Availability (0.0–1.0) for current run |
| `.../Downtime/TotalSeconds` | int    | Cumulative stoppage seconds this run   |
| `.../Downtime/EventCount`   | int    | Number of stoppages this run           |

### Cell-level topics — `NewCo/Soledad/RawProductDump/Line1/CutterFeed/`

| Topic                       | Type  | Description                            |
| --------------------------- | ----- | -------------------------------------- |
| `.../LineSpeed/Current`     | float | Instantaneous line speed (units/min)   |
| `.../LineSpeed/Recommended` | float | Recipe-specified speed for current SKU |
| `.../LineSpeed/Delta`       | float | Current − Recommended (units/min)      |
| `.../LineSpeed/DeltaPct`    | float | Delta as % of Recommended              |
| `.../LineSpeed/Avg1Min`     | float | 1-minute rolling average speed         |
| `.../LineSpeed/Avg5Min`     | float | 5-minute rolling average speed         |
| `.../LineSpeed/AvgRun`      | float | Average speed since run start          |

---

## OEE

For this area (Raw Product Dump), OEE is limited to **Availability**. Quality and Performance tracking are not feasible with current instrumentation.

**Availability = (Scheduled Run Time − Downtime) / Scheduled Run Time**

- Scheduled Run Time: elapsed time from state `Running` start to order completion (excluding Setup and Changeover time).
- Downtime: cumulative seconds in state `Stop` during the run.
- Published to MQTT on each tick and on every state transition.

Performance tracking is deferred pending identification of a measurable throughput signal.

---

## Grafana Dashboard

One dashboard: **LineFeed — Raw Product Dump / Line 1**

### Panels

| Panel                      | Type                          | Primary metric                                 |
| -------------------------- | ----------------------------- | ---------------------------------------------- |
| Current State              | Stat (color-coded)            | `StateLabel`                                   |
| Current SKU                | Stat                          | `SKU`                                          |
| Line Speed vs. Recommended | Gauge + threshold             | `Current`, `Recommended`, `Delta`              |
| Line Speed — Historical    | Time-series                   | `Current`, `Recommended`, `Avg1Min`, `Avg5Min` |
| Speed Delta %              | Time-series + alert threshold | `DeltaPct`                                     |
| OEE Availability           | Gauge                         | `Availability`                                 |
| Downtime Events            | Stat                          | `EventCount`                                   |
| Total Downtime             | Stat                          | `TotalSeconds`                                 |

**Alert:** Speed Delta % exceeding a configurable threshold (e.g. +10%) should visually alarm on the dashboard (panel color change / annotation).

---

## Configuration

The simulator will read from a config file (YAML or TOML) specifying:

- MQTT broker host/port
- Speed multiplier
- Stoppage frequency (mean interval) and duration (mean)
- Speed bias parameters (for the "too-fast" scenario)
- Speed alert threshold
- SKU recipes and production schedule

### Mosquitto Broker

- Host Address: 100.95.134.66 (localhost Tailscale VPN address)
- Host Port: 1883 (standard MQTT port)
- Username: none
- Password: none

---

## Out of Scope (this version)

- Unit count and waste count tracking (no standard unit containers; no measurable throughput signal at this stage)
- Reason codes for stoppages
- Quality / OEE Quality component
- Performance / OEE Performance component
- Crate/bin barcode scan simulation
- Wash flume / downstream area simulation
- Ignition integration (available in stack but not used here)
- Node-RED flows for this project
