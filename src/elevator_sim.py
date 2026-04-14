from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional, Tuple

import numpy as np
import pandas as pd
import simpy


TrafficMode = Literal["up_peak", "down_peak", "mixed"]


@dataclass(frozen=True)
class SimParams:
    seed: int = 42
    sim_minutes: int = 60
    floors: int = 10  # floors indexed 0..floors-1
    elevators: int = 1
    elevator_capacity: int = 8
    seconds_per_floor: float = 3.0
    door_seconds: float = 6.0  # open+close total
    board_seconds_per_person: float = 1.0
    alight_seconds_per_person: float = 1.0
    mean_interarrival_seconds: float = 8.0
    traffic_mode: TrafficMode = "mixed"
    snapshot_every_seconds: int = 10


@dataclass
class PassengerRecord:
    pid: int
    t_request: float
    t_board: Optional[float]
    t_drop: Optional[float]
    origin: int
    dest: int
    assigned_elevator: int


class ElevatorSystem:
    """
    Minimal 'vize' sürümü:
    - Kat başına kuyruk (FIFO)
    - Basit dispatch: her asansör boştayken en eski bekleyen yolcunun katına gider.
    - Aynı katta bekleyenlerden, kapasite elverdiğince aynı yöne gidenleri alır.

    Final için geliştirme alanları:
    - yön bazlı toplama, nearest-car, destination control
    - öncelikler, bakım/arızalar, zonlama
    """

    def __init__(self, env: simpy.Environment, params: SimParams):
        self.env = env
        self.p = params
        self.rng = np.random.default_rng(params.seed)

        self.queues: List[simpy.Store] = [simpy.Store(env) for _ in range(params.floors)]
        self.records: List[PassengerRecord] = []
        self._pid = 0

        # elevator state
        self.e_pos: List[int] = [0 for _ in range(params.elevators)]
        self.e_busy: List[bool] = [False for _ in range(params.elevators)]
        self.e_load: List[int] = [0 for _ in range(params.elevators)]

        # stats snapshots
        self.snapshots: List[Dict[str, float]] = []

        for eid in range(params.elevators):
            env.process(self._elevator_process(eid))

        env.process(self._arrival_process())
        env.process(self._snapshot_process())

    def _choose_trip(self) -> Optional[Tuple[int, int]]:
        """
        Returns (origin_floor, index_in_queue) for the oldest passenger in the building.
        """
        oldest_t = None
        oldest_floor = None
        for f, q in enumerate(self.queues):
            if len(q.items) == 0:
                continue
            first = q.items[0]
            if oldest_t is None or first["t_request"] < oldest_t:
                oldest_t = first["t_request"]
                oldest_floor = f
        if oldest_floor is None:
            return None
        return oldest_floor, 0

    def _sample_od(self) -> Tuple[int, int]:
        floors = self.p.floors
        mode = self.p.traffic_mode

        if mode == "up_peak":
            origin = 0
            dest = int(self.rng.integers(1, floors))
        elif mode == "down_peak":
            origin = int(self.rng.integers(1, floors))
            dest = 0
        else:
            origin = int(self.rng.integers(0, floors))
            dest = int(self.rng.integers(0, floors - 1))
            if dest >= origin:
                dest += 1
        return origin, dest

    def _arrival_process(self):
        while True:
            dt = float(self.rng.exponential(self.p.mean_interarrival_seconds))
            yield self.env.timeout(dt)

            origin, dest = self._sample_od()
            pid = self._pid
            self._pid += 1
            passenger = {
                "pid": pid,
                "t_request": float(self.env.now),
                "origin": origin,
                "dest": dest,
            }
            yield self.queues[origin].put(passenger)

    def _travel(self, eid: int, target_floor: int):
        cur = self.e_pos[eid]
        floors_to_move = abs(target_floor - cur)
        if floors_to_move > 0:
            yield self.env.timeout(floors_to_move * self.p.seconds_per_floor)
        self.e_pos[eid] = target_floor

    def _door_cycle(self):
        yield self.env.timeout(self.p.door_seconds)

    def _elevator_process(self, eid: int):
        while True:
            trip = self._choose_trip()
            if trip is None:
                yield self.env.timeout(1)
                continue

            origin, _ = trip
            self.e_busy[eid] = True

            # go pick up
            yield from self._travel(eid, origin)
            yield from self._door_cycle()

            # board: take up to capacity, prioritize same-direction with first passenger
            boarded: List[dict] = []
            if len(self.queues[origin].items) > 0:
                first = self.queues[origin].items[0]
                direction = np.sign(first["dest"] - origin)

                while self.e_load[eid] < self.p.elevator_capacity and len(self.queues[origin].items) > 0:
                    cand = self.queues[origin].items[0]
                    cand_dir = np.sign(cand["dest"] - origin)
                    if cand_dir != direction:
                        break
                    boarded.append((yield self.queues[origin].get()))
                    self.e_load[eid] += 1

            if len(boarded) > 0:
                yield self.env.timeout(len(boarded) * self.p.board_seconds_per_person)

            # serve in direction order (simple): sorted stops
            if len(boarded) == 0:
                self.e_busy[eid] = False
                continue

            stops = sorted({pax["dest"] for pax in boarded})
            if stops[0] < origin:
                stops = sorted(stops, reverse=True)

            # create records once boarded
            t_board = float(self.env.now)
            for pax in boarded:
                self.records.append(
                    PassengerRecord(
                        pid=int(pax["pid"]),
                        t_request=float(pax["t_request"]),
                        t_board=t_board,
                        t_drop=None,
                        origin=int(pax["origin"]),
                        dest=int(pax["dest"]),
                        assigned_elevator=eid,
                    )
                )

            # drop off
            for stop in stops:
                yield from self._travel(eid, int(stop))
                yield from self._door_cycle()

                dropping = [r for r in self.records if r.assigned_elevator == eid and r.t_drop is None and r.dest == stop]
                if dropping:
                    yield self.env.timeout(len(dropping) * self.p.alight_seconds_per_person)
                    t_drop = float(self.env.now)
                    for r in dropping:
                        r.t_drop = t_drop
                        self.e_load[eid] -= 1

            self.e_busy[eid] = False

    def _snapshot_process(self):
        while True:
            yield self.env.timeout(self.p.snapshot_every_seconds)
            row: Dict[str, float] = {
                "t": float(self.env.now),
                "total_queue": float(sum(len(q.items) for q in self.queues)),
            }
            for f in range(self.p.floors):
                row[f"q_{f}"] = float(len(self.queues[f].items))
            for eid in range(self.p.elevators):
                row[f"e{eid}_pos"] = float(self.e_pos[eid])
                row[f"e{eid}_load"] = float(self.e_load[eid])
                row[f"e{eid}_busy"] = float(1 if self.e_busy[eid] else 0)
            self.snapshots.append(row)


def run_simulation(params: SimParams) -> Dict[str, object]:
    env = simpy.Environment()
    system = ElevatorSystem(env, params)
    env.run(until=params.sim_minutes * 60)

    df_snap = pd.DataFrame(system.snapshots)
    df_pax = pd.DataFrame([r.__dict__ for r in system.records])

    if not df_pax.empty:
        df_pax["wait_s"] = df_pax["t_board"] - df_pax["t_request"]
        df_pax["system_s"] = df_pax["t_drop"] - df_pax["t_request"]

    metrics: Dict[str, float] = {
        "generated_passengers": float(system._pid),
        "served_passengers": float(len(df_pax)),
    }
    if not df_pax.empty:
        waits = df_pax["wait_s"].to_numpy()
        metrics.update(
            {
                "wait_mean_s": float(np.mean(waits)),
                "wait_p50_s": float(np.percentile(waits, 50)),
                "wait_p90_s": float(np.percentile(waits, 90)),
                "wait_p95_s": float(np.percentile(waits, 95)),
                "wait_over_60s_rate": float(np.mean(waits > 60)),
            }
        )
    else:
        metrics.update(
            {
                "wait_mean_s": float("nan"),
                "wait_p50_s": float("nan"),
                "wait_p90_s": float("nan"),
                "wait_p95_s": float("nan"),
                "wait_over_60s_rate": float("nan"),
            }
        )

    return {
        "params": params,
        "metrics": metrics,
        "snapshots": df_snap,
        "passengers": df_pax,
    }

