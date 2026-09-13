import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv("accel_data.csv")

magnitude = np.sqrt(
    df["x"]**2 +
    df["y"]**2 +
    df["z"]**2
)

time = df["timestamp"] - df["timestamp"].iloc[0]

plt.figure(figsize=(14, 5))
plt.plot(time, magnitude)
plt.axhline(1.05, linestyle="--", label="Detection threshold")
plt.xlabel("Time (seconds)")
plt.ylabel("Acceleration magnitude (g)")
plt.title("MacBook Accelerometer Recording")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("accelerometer_plot.png", dpi=150)

print("Saved accelerometer_plot.png")
