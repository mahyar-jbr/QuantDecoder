"""Print the versions of the main tools and which torch devices work on this machine.

Run from the repository root: uv run python scripts/check_env.py
"""

import platform
from importlib.metadata import version

import torch

PACKAGES = ("stim", "pymatching", "sinter", "torch", "numpy", "matplotlib")
DEVICES_BEST_FIRST = ("cuda", "mps", "cpu")


def is_reported(device: str) -> bool:
    """Return True if torch says the device is available here."""
    if device == "cuda":
        return torch.cuda.is_available()
    if device == "mps":
        return torch.backends.mps.is_available()
    return True


def runs_correctly(device: str) -> bool:
    """Return True if a small matrix product on the device matches the same product on the CPU."""
    generator = torch.Generator().manual_seed(0)
    a = torch.randn(64, 64, generator=generator)
    b = torch.randn(64, 64, generator=generator)
    try:
        result = (a.to(device) @ b.to(device)).cpu()
    except RuntimeError:
        return False
    return torch.allclose(result, a @ b, rtol=1e-3, atol=1e-3)


def main() -> None:
    print(f"{'python':<12}{platform.python_version()} on {platform.system()} {platform.machine()}")
    for name in PACKAGES:
        print(f"{name:<12}{version(name)}")

    print()
    print(f"{'device':<8}{'reported':<10}works")
    working = []
    for device in DEVICES_BEST_FIRST:
        reported = is_reported(device)
        works = reported and runs_correctly(device)
        if works:
            working.append(device)
        works_text = "yes" if works else ("no" if reported else "-")
        print(f"{device:<8}{'yes' if reported else 'no':<10}{works_text}")

    if not working:
        raise SystemExit("No device passed the check.")
    print()
    print(f"Best device here: {working[0]}")


if __name__ == "__main__":
    main()
