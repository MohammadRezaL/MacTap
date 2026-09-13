from __future__ import annotations

import csv
import math
from dataclasses import dataclass


INPUT_FILE = "accel_data.csv"

THRESHOLD = 1.05
MIN_TAP_GAP = 0.15      # seconds
MAX_TAP_GAP = 0.45      # seconds
REFRACTORY = 0.12       # seconds


@dataclass
class Tap:
    time: float
    strength: float


def load_data() -> list[dict[str, float]]:
    data = []

    with open(INPUT_FILE, newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            data.append({
                "t": float(row["timestamp"]),
                "x": float(row["x"]),
                "y": float(row["y"]),
                "z": float(row["z"]),
            })

    return data


def magnitude(sample: dict[str, float]) -> float:
    return math.sqrt(
        sample["x"] ** 2
        + sample["y"] ** 2
        + sample["z"] ** 2
    )


def detect_peaks(data: list[dict[str, float]]) -> list[Tap]:
    taps: list[Tap] = []
    last_tap_time = -float("inf")

    magnitudes = [magnitude(sample) for sample in data]

    for i in range(1, len(magnitudes) - 1):
        current = magnitudes[i]

        is_peak = (
            current >= THRESHOLD
            and current >= magnitudes[i - 1]
            and current >= magnitudes[i + 1]
        )

        if not is_peak:
            continue

        timestamp = data[i]["t"]

        # Ignore ringing immediately after an impact.
        if timestamp - last_tap_time < REFRACTORY:
            continue

        taps.append(Tap(timestamp, current))
        last_tap_time = timestamp

    return taps


def classify_taps(taps: list[Tap]) -> list[tuple[str, list[Tap]]]:
    events = []

    i = 0

    while i < len(taps):
        group = [taps[i]]
        j = i + 1

        while j < len(taps):
            gap = taps[j].time - group[-1].time

            if gap < MIN_TAP_GAP:
                j += 1
                continue

            if gap <= MAX_TAP_GAP:
                group.append(taps[j])
                j += 1
            else:
                break

        count = len(group)

        if count == 1:
            label = "SINGLE TAP"
        elif count == 2:
            label = "DOUBLE TAP"
        else:
            label = f"{count}-TAP"

        events.append((label, group))
        i = j

    return events


def main():
    data = load_data()

    if not data:
        print("No sensor data found.")
        return

    taps = detect_peaks(data)
    events = classify_taps(taps)

    start_time = data[0]["t"]

    print("\nDetected events:")
    print("-" * 50)

    for label, group in events:
        times = [
            f"{tap.time - start_time:.3f}s"
            for tap in group
        ]

        strengths = [
            f"{tap.strength:.3f}g"
            for tap in group
        ]

        print(f"{label}")
        print(f"  times:    {', '.join(times)}")
        print(f"  strength: {', '.join(strengths)}")
        print()

    print("-" * 50)
    print(f"Total detected events: {len(events)}")


if __name__ == "__main__":
    main()
