from __future__ import annotations

import math
import time
from collections import deque

from macimu import IMU
from actions import single_tap, double_tap, triple_tap


BASELINE_WINDOW = 40
MIN_PROMINENCE = 0.015
MIN_PEAK = 1.045

REFRACTORY = 0.20
GESTURE_TIMEOUT = 0.50


def magnitude(sample):
    return math.sqrt(
        sample.x ** 2 +
        sample.y ** 2 +
        sample.z ** 2
    )


def median(values):
    values = sorted(values)

    if not values:
        return 1.0

    return values[len(values) // 2]


def run_action(count):
    if count == 1:
        single_tap()
    elif count == 2:
        double_tap()
    elif count == 3:
        triple_tap()


print("MacTap")
print("------")
print("Calibrating...")
print("Double tap → Calculator")
print("Press Ctrl+C to stop.\n")


with IMU() as imu:

    baseline_values = []

    for sample in imu.stream_accel_timed():
        baseline_values.append(magnitude(sample))

        if len(baseline_values) >= BASELINE_WINDOW:
            break

    recent_values = deque(
        baseline_values,
        maxlen=BASELINE_WINDOW
    )

    peak_buffer = deque(maxlen=3)

    last_candidate = -float("inf")
    gesture = []

    print(f"Baseline: {median(baseline_values):.4f} g")
    print("Ready.\n")

    try:

        for sample in imu.stream_accel_timed():

            t = sample.t
            value = magnitude(sample)

            recent_values.append(value)
            baseline = median(recent_values)

            peak_buffer.append((t, value))

            # Finish current gesture after timeout.
            if gesture and t - last_candidate > GESTURE_TIMEOUT:
                count = len(gesture)

                print(f">>> {count}-tap gesture")

                run_action(count)

                gesture.clear()

            if len(peak_buffer) < 3:
                continue

            previous = peak_buffer[0]
            current = peak_buffer[1]
            following = peak_buffer[2]

            peak_time, peak_value = current

            # Local maximum.
            if peak_value < previous[1]:
                continue

            if peak_value < following[1]:
                continue

            prominence = peak_value - baseline

            if peak_value < MIN_PEAK:
                continue

            if prominence < MIN_PROMINENCE:
                continue

            # Suppress vibration immediately after a detected impact.
            if peak_time - last_candidate < REFRACTORY:
                continue

            gesture.append({
                "time": peak_time,
                "strength": peak_value,
                "prominence": prominence,
            })

            last_candidate = peak_time

            print(
                f"candidate {len(gesture)} | "
                f"{peak_value:.4f} g | "
                f"+{prominence:.4f} g"
            )

    except KeyboardInterrupt:

        if gesture:
            run_action(len(gesture))

        print("\nStopped.")
