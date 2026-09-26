from __future__ import annotations

import json
import os
import shlex
import subprocess
import threading

import rumps


PROJECT_DIR = os.path.expanduser("~/MacTap")
MENU_BAR_ICON = os.path.join(PROJECT_DIR, "assets", "MacTapMenuBarTemplate.png")
PYTHON = os.path.join(PROJECT_DIR, ".venv", "bin", "python")
DETECTOR = os.path.join(PROJECT_DIR, "detector.py")
LOG_FILE = os.path.join(PROJECT_DIR, "mactap.log")
PID_FILE = os.path.join(PROJECT_DIR, "mactap.pid")
CONFIG_FILE = os.path.join(PROJECT_DIR, "config.json")


def load_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"shortcut_name": "MacTap Action"}


def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=2)


class MacTapApp(rumps.App):

    def __init__(self):
        super().__init__("MacTap", icon=MENU_BAR_ICON, template=True)

        config = load_config()
        shortcut = config.get("shortcut_name", "MacTap Action")

        self.quit_requested = False
        self.starting = False
        self.stopping = False

        self.status_item = rumps.MenuItem("● Detection: OFF")

        self.shortcut_item = rumps.MenuItem(
            f"Double Tap → {shortcut}",
            callback=self.choose_shortcut
        )

        self.menu = [
            self.status_item,
            None,

            rumps.MenuItem(
                "Start Detection",
                callback=self.start_detection
            ),

            rumps.MenuItem(
                "Stop Detection",
                callback=self.stop_detection
            ),

            None,

            self.shortcut_item,

            rumps.MenuItem(
                "Test Double Tap Shortcut",
                callback=self.test_shortcut
            ),

            rumps.MenuItem(
                "Triple Tap → Voice"
            ),

            None,

            rumps.MenuItem(
                "Quit MacTap",
                callback=self.quit_app
            ),
        ]

        self.status_timer = rumps.Timer(
            self.refresh_status,
            0.5
        )
        self.status_timer.start()

    # =========================================================
    # Status
    # =========================================================

    def get_detector_pid(self):
        try:
            with open(PID_FILE, "r") as file:
                return int(file.read().strip())
        except (FileNotFoundError, ValueError, OSError):
            return None

    def is_running(self):
        pid = self.get_detector_pid()

        if pid is None:
            return False

        result = subprocess.run(
            ["/bin/ps", "-p", str(pid), "-o", "command="],
            capture_output=True,
            text=True
        )

        command = result.stdout.strip()

        return (
            result.returncode == 0
            and DETECTOR in command
        )

    def refresh_status(self, _):
        running = self.is_running()

        if self.starting:
            self.status_item.title = "● Starting..."
        elif self.stopping:
            self.status_item.title = "● Stopping..."
        elif running:
            self.status_item.title = "● Detection: ON"
        else:
            self.status_item.title = "● Detection: OFF"

        if self.quit_requested and not running and not self.stopping:
            rumps.quit_application()

    # =========================================================
    # AppleScript
    # =========================================================

    @staticmethod
    def apple_quote(text: str) -> str:
        escaped = text.replace("\\", "\\\\")
        escaped = escaped.replace('"', '\\"')
        return f'"{escaped}"'

    def run_as_admin(self, shell_command: str):
        script = (
            "do shell script "
            + self.apple_quote(shell_command)
            + " with administrator privileges"
        )

        return subprocess.run(
            [
                "/usr/bin/osascript",
                "-e",
                script
            ],
            capture_output=True,
            text=True
        )

    # =========================================================
    # Detection start
    # =========================================================

    def start_detection(self, _):

        if self.starting or self.stopping:
            return

        if self.is_running():
            self.status_item.title = "● Detection: ON"
            return

        self.starting = True

        threading.Thread(
            target=self._start_detection_worker,
            daemon=True
        ).start()

    def _start_detection_worker(self):

        app_pid = os.getpid()

        project = shlex.quote(PROJECT_DIR)
        python = shlex.quote(PYTHON)
        detector = shlex.quote(DETECTOR)
        log_file = shlex.quote(LOG_FILE)
        pid_file = shlex.quote(PID_FILE)

        shell_command = f"""
cd {project}
rm -f {pid_file}

PYTHONUNBUFFERED=1 "{PYTHON}" -u "{DETECTOR}" >> {log_file} 2>&1 </dev/null &
DETECTOR_PID=$!

echo "$DETECTOR_PID" > {pid_file}

(
    while /bin/ps -p {app_pid} >/dev/null 2>&1 \
        && /bin/kill -0 "$DETECTOR_PID" >/dev/null 2>&1
    do
        /bin/sleep 1
    done

    if /bin/kill -0 "$DETECTOR_PID" >/dev/null 2>&1
    then
        /bin/kill -TERM "$DETECTOR_PID" 2>/dev/null || true
        /bin/sleep 0.5
        /bin/kill -KILL "$DETECTOR_PID" 2>/dev/null || true
    fi

    /bin/rm -f {pid_file}
) >/dev/null 2>&1 &
"""

        result = self.run_as_admin(shell_command)

        self.starting = False

        if result.returncode != 0:
            print(
                "MacTap start failed:",
                result.stderr.strip()
            )

    # =========================================================
    # Detection stop
    # =========================================================

    def stop_detection(self, _, notify=True):

        if self.stopping:
            return

        if not self.is_running():
            self.status_item.title = "● Detection: OFF"
            return

        self.stopping = True

        threading.Thread(
            target=self._stop_detection_worker,
            daemon=True
        ).start()

    def _stop_detection_worker(self):

        pid = self.get_detector_pid()

        if pid is None:
            self.stopping = False
            return

        pid_file = shlex.quote(PID_FILE)

        shell_command = f"""
PID={pid}

if /bin/ps -p "$PID" -o command= \
    | /usr/bin/grep -F "{DETECTOR}" >/dev/null 2>&1
then
    /bin/kill -TERM "$PID" 2>/dev/null || true
    /bin/sleep 0.5
    /bin/kill -KILL "$PID" 2>/dev/null || true
fi

/bin/rm -f {pid_file}
"""

        result = self.run_as_admin(shell_command)

        if result.returncode != 0:
            print(
                "MacTap stop failed:",
                result.stderr.strip()
            )

        self.stopping = False

    # =========================================================
    # Shortcut settings
    # =========================================================

    def choose_shortcut(self, _):

        config = load_config()
        current = config.get(
            "shortcut_name",
            "MacTap Action"
        )

        script = (
            'display dialog '
            '"Shortcut to run on Double Tap:" '
            f'default answer "{current}" '
            'buttons {"Cancel", "Save"} '
            'default button "Save"'
        )

        try:
            result = subprocess.run(
                [
                    "/usr/bin/osascript",
                    "-e",
                    script
                ],
                capture_output=True,
                text=True,
                check=True
            )

            output = result.stdout.strip()

            if "text returned:" not in output:
                return

            shortcut = output.split(
                "text returned:",
                1
            )[1].strip()

            if not shortcut:
                return

            # Verify that the Shortcut actually exists.
            verify = subprocess.run(
                [
                    "/usr/bin/shortcuts",
                    "view",
                    shortcut
                ],
                capture_output=True,
                text=True
            )

            if verify.returncode != 0:
                rumps.alert(
                    title="Shortcut not found",
                    message=(
                        f'No Shortcut named "{shortcut}" '
                        "was found."
                    )
                )
                return

            config["shortcut_name"] = shortcut
            save_config(config)

            self.shortcut_item.title = (
                f"Double Tap → {shortcut}"
            )

            rumps.notification(
                "MacTap",
                "Double Tap updated",
                f"Shortcut: {shortcut}"
            )

        except subprocess.CalledProcessError:
            pass

    def test_shortcut(self, _):

        config = load_config()
        shortcut = config.get(
            "shortcut_name",
            "MacTap Action"
        )

        result = subprocess.run(
            [
                "/usr/bin/shortcuts",
                "run",
                shortcut
            ],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            rumps.notification(
                "MacTap",
                "Shortcut executed",
                shortcut
            )
        else:
            error = result.stderr.strip()

            rumps.alert(
                title="Shortcut failed",
                message=(
                    f"Could not run:\n{shortcut}\n\n"
                    f"{error}"
                )
            )

    # =========================================================
    # Quit
    # =========================================================

    def quit_app(self, _):

        self.quit_requested = True

        if self.is_running():
            self.stop_detection(None)
        else:
            rumps.quit_application()


if __name__ == "__main__":
    MacTapApp().run()
