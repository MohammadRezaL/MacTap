import subprocess


def single_tap():
    print("SINGLE TAP ACTION")


def double_tap():
    print("DOUBLE TAP → Opening Calculator")
    subprocess.Popen(["open", "-a", "Calculator"])


def triple_tap():
    print("TRIPLE TAP ACTION")
