"""Pinch detection with hysteresis (a Schmitt trigger).

Two thresholds instead of one:
  - become active when the ratio falls BELOW `enter_below`
  - become inactive only when the ratio rises ABOVE `exit_above`
Between the two the state is unchanged, so noise inside that band cannot
toggle drawing on and off.
"""
from __future__ import annotations

import math

from ..config import PINCH_ENTER_BELOW, PINCH_EXIT_ABOVE


class PinchDetector:
    def __init__(
        self,
        enter_below: float = PINCH_ENTER_BELOW,
        exit_above: float = PINCH_EXIT_ABOVE,
    ) -> None:
        if not enter_below < exit_above:
            raise ValueError("enter_below must be smaller than exit_above")
        self.enter_below = enter_below
        self.exit_above = exit_above
        self.active = False

    def update(self, pinch_ratio: float | None) -> bool:
        """Feed one pinch ratio. Returns whether a pinch is currently active."""
        if pinch_ratio is None or not math.isfinite(pinch_ratio):
            self.active = False      # invalid data is never evidence of a pinch
            return False
        if self.active:
            if pinch_ratio > self.exit_above:
                self.active = False
        elif pinch_ratio < self.enter_below:
            self.active = True
        return self.active

    def reset(self) -> None:
        self.active = False
