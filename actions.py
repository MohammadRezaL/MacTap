import os
import subprocess
from pathlib import Path


SHORTCUT_NAME = "MacTap Action"

AUDIO_FILE = (
    Path(__file__).resolve().parent
    / "sounds"
    / "triple_tap.mp3"
)


def run_as_user(command):
    """
    Our sensor prototype currently runs with sudo.
    Run user-facing macOS commands as the original logged-in user.
    """
    username = os.environ.get("SUDO_USER")

    if username:
        return subprocess.Popen(
            ["sudo", "-u", username] + command
        )

    return subprocess.Popen(command)


def single_tap():
    print("SINGLE TAP")


def double_tap():
    print(f"DOUBLE TAP → Running Shortcut: {SHORTCUT_NAME}")

    run_as_user([
        "shortcuts",
        "run",
        SHORTCUT_NAME,
    ])


def triple_tap():
    print("TRIPLE TAP → Playing audio")

    run_as_user([
        "afplay",
        str(AUDIO_FILE),
    ])
