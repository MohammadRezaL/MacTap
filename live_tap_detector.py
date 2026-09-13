from macimu import IMU
import math
import time

THRESHOLD_DELTA = 0.025
COOLDOWN = 0.20


def magnitude(sample):
    return math.sqrt(
        sample.x ** 2 +
        sample.y ** 2 +
        sample.z ** 2
    )


print("MacTap live detector")
print("--------------------")
print("Keep the Mac still for 2 seconds.")
print("Then tap the aluminum chassis.")
print("Press Ctrl+C to stop.\n")

values = []
last_detection = 0

with IMU() as imu:
    try:
        print("Calibrating...")

        for sample in imu.stream_accel_timed():
            values.append(magnitude(sample))

            if len(values) >= 100:
                break

        baseline = sum(values) / len(values)

        print(f"Baseline: {baseline:.3f} g")
        print(
            f"Tap threshold: "
            f"{baseline + THRESHOLD_DELTA:.3f} g\n"
        )

        for sample in imu.stream_accel_timed():
            value = magnitude(sample)
            now = time.monotonic()

            if value >= baseline + THRESHOLD_DELTA:
                if now - last_detection >= COOLDOWN:
                    print(
                        f"TAP CANDIDATE | "
                        f"{value:.3f} g | "
                        f"+{value - baseline:.3f} g"
                    )
                    last_detection = now

    except KeyboardInterrupt:
        print("\nStopped.")
