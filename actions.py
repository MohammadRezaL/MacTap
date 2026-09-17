import os
import pwd
import subprocess
from pathlib import Path


SHORTCUT_NAME = "MacTap Action"

AUDIO_FILE = (
    Path(__file__).resolve().parent
    / "sounds"
    / "triple_tap.mp3"
)


def get_console_user():
    username = subprocess.check_output(
        ["/usr/bin/stat", "-f", "%Su", "/dev/console"],
        text=True
    ).strip()

    user_info = pwd.getpwnam(username)

    return username, user_info.pw_uid


def run_as_user(command):
    """
    Run a macOS user action as the currently logged-in user.
    The detector itself runs as root because the accelerometer
    requires elevated access.
    """
    username, _ = get_console_user()

    return subprocess.Popen(
        [
            "/usr/bin/sudo",
            "-u",
            username,
            *command,
        ]
    )


def single_tap():
    print("SINGLE TAP ACTION")


def double_tap():
    print(f"DOUBLE TAP → Running Shortcut: {SHORTCUT_NAME}")

    run_as_user([
        "/usr/bin/shortcuts",
        "run",
        SHORTCUT_NAME,
    ])


def triple_tap():
    print("TRIPLE TAP → Playing audio")

    run_as_user([
        "/usr/bin/afplay",
        str(AUDIO_FILE),
    ])
