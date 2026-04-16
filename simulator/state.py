from enum import IntEnum


class LineState(IntEnum):
    IDLE = 0
    SETUP = 1
    RUNNING = 2
    STOP = 5
    CHANGEOVER = 9

    @property
    def label(self) -> str:
        return {
            LineState.IDLE: "Idle",
            LineState.SETUP: "Setup",
            LineState.RUNNING: "Running",
            LineState.STOP: "Stop",
            LineState.CHANGEOVER: "Changeover",
        }[self]
