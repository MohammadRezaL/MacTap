import json
import subprocess
from pathlib import Path
from urllib.parse import quote


PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = PROJECT_DIR / "config.json"
AUDIO_FILE = PROJECT_DIR / "sounds" / "triple_tap.mp3"


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"shortcut_name": "MacTap Action"}


def get_console_user():
    return subprocess.check_output(
        ["/usr/bin/stat", "-f", "%Su", "/dev/console"],
        text=True
    ).strip()


def get_console_uid(username):
    return subprocess.check_output(
        ["/usr/bin/id", "-u", username],
        text=True
    ).strip()


def run_as_user(command):
    username = get_console_user()
    uid = get_console_uid(username)

    return subprocess.Popen(
        [
            "/bin/launchctl",
            "asuser",
            uid,
            *command,
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def single_tap():
    print("SINGLE TAP ACTION")


def double_tap():
    config = load_config()
    shortcut_name = config.get(
        "shortcut_name",
        "MacTap Action"
    )

    print(
        f"DOUBLE TAP → Running Shortcut: "
        f"{shortcut_name}"
    )

    # Apple-supported Shortcuts URL scheme.
    encoded_name = quote(
        shortcut_name,
        safe=""
    )

    url = (
        "shortcuts://run-shortcut"
        f"?name={encoded_name}"
    )

    try:
        run_as_user([
            "/usr/bin/open",
            url,
        ])
    except Exception as error:
        print(
            f"Shortcut launch error: {error}"
        )


def triple_tap():
    print("TRIPLE TAP → Playing voice")

    try:
        run_as_user([
            "/usr/bin/afplay",
            str(AUDIO_FILE),
        ])
    except Exception as error:
        print(
            f"Audio launch error: {error}"
        )
