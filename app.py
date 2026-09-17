from pathlib import Path
import subprocess
import rumps


PROJECT_DIR = Path(__file__).resolve().parent
PYTHON = PROJECT_DIR / ".venv" / "bin" / "python"
DETECTOR = PROJECT_DIR / "detector.py"
LOG_FILE = PROJECT_DIR / "mactap.log"


class MacTapApp(rumps.App):

    def __init__(self):
        super().__init__("MacTap")

        self.status_item = rumps.MenuItem("● Detection: OFF")

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
            rumps.MenuItem("Double Tap → Shortcut"),
            rumps.MenuItem("Triple Tap → Voice"),
            None,
            rumps.MenuItem(
                "Quit MacTap",
                callback=self.quit_app
            ),
        ]

    def start_detection(self, _):
        if self.is_running():
            rumps.notification(
                "MacTap",
                "Already running",
                "Tap detection is already active."
            )
            self.status_item.title = "● Detection: ON"
            return

        command = (
            f'cd "{PROJECT_DIR}" && '
            f'"{PYTHON}" "{DETECTOR}" '
            f'> "{LOG_FILE}" 2>&1 &'
        )

        script = (
            'do shell script '
            + self.apple_quote(command)
            + ' with administrator privileges'
        )

        try:
            subprocess.run(
                ["/usr/bin/osascript", "-e", script],
                check=True
            )

            self.status_item.title = "● Detection: ON"

            rumps.notification(
                "MacTap",
                "Detection started",
                "Double tap → Shortcut\n"
                "Triple tap → Voice"
            )

        except subprocess.CalledProcessError as error:
            print(error)

            rumps.notification(
                "MacTap",
                "Could not start",
                "Check mactap.log"
            )

    def stop_detection(self, _):
        script = (
            'do shell script '
            + self.apple_quote(
                f'/usr/bin/pkill -f "{DETECTOR}" || true'
            )
            + ' with administrator privileges'
        )

        try:
            subprocess.run(
                ["/usr/bin/osascript", "-e", script],
                check=True
            )
        finally:
            self.status_item.title = "● Detection: OFF"

            rumps.notification(
                "MacTap",
                "Detection stopped",
                ""
            )

    def is_running(self):
        result = subprocess.run(
            ["/usr/bin/pgrep", "-f", str(DETECTOR)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return result.returncode == 0

    @staticmethod
    def apple_quote(text):
        escaped = text.replace("\\", "\\\\")
        escaped = escaped.replace('"', '\\"')
        return f'"{escaped}"'

    def quit_app(self, _):
        if self.is_running():
            self.stop_detection(None)

        rumps.quit_application()


if __name__ == "__main__":
    MacTapApp().run()
