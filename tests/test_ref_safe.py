"""Guards for git-ref-safe branch names.

A registry package may be named `adafruit/Adafruit NeoPixel`. Interpolated
straight into a branch name that produced a ref git refuses, so the update was
resolved and then silently dropped -- no PR, no failure, the run stayed green.
"""

import subprocess

import pytest

from piobot.piobot import ref_safe

# Every one of these is a real dependency from the firmware repos this runs on.
REAL_PACKAGES = [
    "adafruit/Adafruit NeoPixel",
    "sparkfun/SparkFun BME280",
    "sparkfun/SparkFun MAX1704x Fuel Gauge Arduino Library",
    "bblanchon/ArduinoJson",
    "bodmer/TFT_eSPI",
    "esp32async/ESPAsyncWebServer",
]


def check_ref_format(ref: str) -> bool:
    """Ask git itself, rather than reimplementing its rules in the assertion."""
    return (
        subprocess.run(
            ["git", "check-ref-format", f"refs/heads/{ref}"],
            capture_output=True,
            check=False,
        ).returncode
        == 0
    )


@pytest.mark.parametrize("package", REAL_PACKAGES)
def test_real_packages_produce_valid_refs(package):
    ref = f"dependabot/platformio/{ref_safe(package)}-{ref_safe('1.15.5')}"
    assert check_ref_format(ref), ref


@pytest.mark.parametrize("bad", ["~", "^", ":", "?", "*", "[", "\\", " "])
def test_characters_git_rejects_are_replaced(bad):
    assert check_ref_format(f"dependabot/platformio/{ref_safe(f'owner/na{bad}me')}-1.0.0")


def test_the_slash_between_owner_and_name_survives():
    # The branch layout is deliberately nested; flattening it would orphan the
    # branches of every package already being tracked.
    assert ref_safe("adafruit/Adafruit NeoPixel") == "adafruit/Adafruit-NeoPixel"


def test_space_free_names_are_unchanged():
    # Existing branches must keep their names, or every open PR is superseded.
    for name in ("bodmer/TFT_eSPI", "bblanchon/ArduinoJson", "esp32async/AsyncTCP"):
        assert ref_safe(name) == name


def test_versions_pass_through():
    for version in ("1.15.5", "55.03.312-1", "2.0.9"):
        assert ref_safe(version) == version


def test_sequences_git_rejects_even_though_the_characters_are_legal():
    assert ".." not in ref_safe("owner/na..me")
    assert not ref_safe("owner/name.lock").endswith(".lock")
    assert check_ref_format(f"dependabot/platformio/{ref_safe('owner/na..me')}-1.0.0")


def test_a_name_of_only_illegal_characters_still_yields_something():
    assert ref_safe("***") == "package"
