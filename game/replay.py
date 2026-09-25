from __future__ import annotations

from dataclasses import dataclass

import pygame

from game.boccia import Boccia
from game.jack import Jack


@dataclass(frozen=True)
class ReplayBall:
    x: float
    y: float
    radius: int
    color: tuple[int, int, int]
    owner_key: str


@dataclass(frozen=True)
class ReplayFrame:
    balls: tuple[ReplayBall, ...]
    jack_x: float
    jack_y: float
    jack_radius: int


@dataclass(frozen=True)
class ShotReplay:
    frames: tuple[ReplayFrame, ...]
    capture_fps: float

    @property
    def available(self) -> bool:
        return len(self.frames) >= 2


class ReplayRecorder:
    def __init__(
        self,
        capture_fps: float = 30.0,
        max_frames: int = 450,
    ) -> None:
        self.capture_fps = max(5.0, float(capture_fps))
        self.max_frames = max(30, int(max_frames))
        self._frames: list[ReplayFrame] = []
        self._accumulator = 0.0
        self._active = False

    def start(
        self,
        balls: list[Boccia],
        jack: Jack,
    ) -> None:
        self._frames = []
        self._accumulator = 0.0
        self._active = True
        self._append_frame(balls, jack)

    def capture(
        self,
        balls: list[Boccia],
        jack: Jack,
        dt: float,
        force: bool = False,
    ) -> None:
        if not self._active:
            return

        self._accumulator += max(0.0, dt)
        interval = 1.0 / self.capture_fps

        if force or self._accumulator >= interval:
            self._accumulator %= interval
            self._append_frame(balls, jack)

    def finish(
        self,
        balls: list[Boccia],
        jack: Jack,
    ) -> ShotReplay:
        if self._active:
            self._append_frame(balls, jack)
        self._active = False
        return ShotReplay(
            frames=tuple(self._frames),
            capture_fps=self.capture_fps,
        )

    def _append_frame(
        self,
        balls: list[Boccia],
        jack: Jack,
    ) -> None:
        if len(self._frames) >= self.max_frames:
            return

        frame = ReplayFrame(
            balls=tuple(
                ReplayBall(
                    x=float(ball.position.x),
                    y=float(ball.position.y),
                    radius=int(ball.radius),
                    color=tuple(ball.color),
                    owner_key=ball.owner_key,
                )
                for ball in balls
            ),
            jack_x=float(jack.position.x),
            jack_y=float(jack.position.y),
            jack_radius=int(jack.radius),
        )

        if self._frames and frame == self._frames[-1]:
            return
        self._frames.append(frame)
