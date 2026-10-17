import pytest

from backend.app.vision.pinch_detector import PinchDetector


def make():
    return PinchDetector(enter_below=0.25, exit_above=0.45)


def count_transitions(states):
    """Number of on/off changes, starting from an initial 'off'."""
    prev, n = False, 0
    for s in states:
        if s != prev:
            n += 1
        prev = s
    return n


def test_starts_inactive():
    assert make().active is False


def test_activates_below_enter_threshold():
    assert make().update(0.10) is True


def test_does_not_activate_inside_the_band():
    d = make()
    assert d.update(0.30) is False
    assert d.update(0.44) is False


def test_stays_active_inside_the_band():
    d = make()
    d.update(0.10)
    assert d.update(0.30) is True
    assert d.update(0.44) is True


def test_releases_above_exit_threshold():
    d = make()
    d.update(0.10)
    assert d.update(0.46) is False


def test_does_not_reactivate_until_below_enter_again():
    d = make()
    d.update(0.10)
    d.update(0.60)                      # released
    assert d.update(0.30) is False      # inside the band: still off
    assert d.update(0.20) is True       # below enter: on again


@pytest.mark.parametrize("bad", [None, float("nan"), float("inf")])
def test_invalid_ratio_releases_the_pinch(bad):
    d = make()
    d.update(0.10)
    assert d.update(bad) is False
    assert d.active is False
    assert d.update(0.30) is False      # and does not silently resume


def test_reset_clears_state():
    d = make()
    d.update(0.10)
    d.reset()
    assert d.active is False


@pytest.mark.parametrize("enter,exit_", [(0.45, 0.25), (0.3, 0.3)])
def test_invalid_thresholds_are_rejected(enter, exit_):
    with pytest.raises(ValueError):
        PinchDetector(enter_below=enter, exit_above=exit_)


def test_hysteresis_removes_flicker_that_a_single_threshold_causes():
    # A firm pinch whose ratio is disturbed by noise around 0.30.
    noisy = [0.10, 0.12, 0.29, 0.33, 0.28, 0.34, 0.27, 0.35, 0.11, 0.10]

    single = [r < 0.30 for r in noisy]
    d = make()
    hysteresis = [d.update(r) for r in noisy]

    assert count_transitions(single) >= 4      # the flicker bug
    assert count_transitions(hysteresis) == 1  # on once, never drops out
