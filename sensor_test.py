from macimu import IMU
import csv
import time

OUTPUT_FILE = "accel_data.csv"
DURATION = 20


def main():
    print("Starting accelerometer...")
    print(f"Recording for {DURATION} seconds.\n")
    print("Do this:")
    print("1. Keep the MacBook still for a few seconds.")
    print("2. Tap the aluminum body near the trackpad twice.")
    print("3. Try a few single taps too.\n")

    with IMU() as imu, open(OUTPUT_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "x", "y", "z"])

        start_time = time.time()
        sample_count = 0

        while time.time() - start_time < DURATION:
            samples = imu.read_accel_timed()

            for sample in samples:
                writer.writerow([
                    sample.t,
                    sample.x,
                    sample.y,
                    sample.z,
                ])
                sample_count += 1

            time.sleep(0.01)

    print(f"\nFinished. Saved {sample_count} samples to {OUTPUT_FILE}.")


if __name__ == "__main__":
    main()
