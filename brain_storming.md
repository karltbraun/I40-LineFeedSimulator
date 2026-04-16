# General thoughts about this simulator

## Objective

Demonstration of the capabilities when having real-time (or near real-time) data from the production line kept in a readily accessible UNS mechanism such as an MQTT broker.

Simulate a simple production run, tracking units produced, waste created, stoppages, calculating OEE, waste count, and tracking line speed against specified line speed per SKU.

## Setup

```text
Recipe: {
    SKU: int,
    recommended_Line_Speed: int
},
Schedule: {
    SKU: int,
    Nbr_Units: int,
},
Edge: {
    Current_SKU: int,
    Current_Line_Speed: int,
    Current_Unit_Count: int,
    Current_state: int
}

State_mapping: {
    0: "Idle",
    1: "Setup",
    2: "Running",
    5: "Stop",
    9: "Changeover"
}
```

## Schedule Production Run

- Set state to Setup
- Set Edge.Current_SKU to new SKU
- Set Edge.Current_Line_Speed to the recommended line speed for the new SKU
- Set Edge.Current_Unit_Count to 0
- Set state to running
- Initiate production run

## Simulator

### Scheduler

- Initialize and Setup

```text
    while note STOPPED:
        Get next production order in queue
        Send it to MES
```

### MES

```text
    Set SKU
    Set NBR_UNITS
    Set Line_Speed
    Set Expected_Production_Rate
    Set Expected_Waste_Rate
    Set Expected_OEE
    Start Production
```

### Production

```text
Production(SKU, NBR_UNITS, Line_Speed, Expected_Production_Rate, Expected_Waste_Rate, Expected_OEE):

    Set SKU
    Set NBR_UNITS
    Set Line_Speed
    Set Expected_Production_Rate
    Set Expected_Waste_Rate
    Set Expected_OEE

    unit_count = 0
    waste_count = 0
    initialize_waste_rate
    initialize_oee

    while unit_count < NBR_UNITS:
        sample_line_speed
        update_average_line_speeds # current, 1 min, 5 min, run
        update_oee

        result = product_1_unit

        if not result:
            # rejected
            increase waste_count
            continue

    increase unit_count



```

- set units to 0
- set lines speed # this will be the recommended line speed +/- some random delta
- while units <= Units_to_produce # where does this come from?
  - increment unit count
  - determine if waste or not
    - Handle according to waste process
  - wait for wait_period # this must be determined by line speed per SKU
  - repeat

## Dashboard

- SKU
- State
- Unit count
- Line Speed
  - Recommended Line Speed
  - Current Line Speed
  - Delta
  - Display alarm if Delta exceeds some threshold
