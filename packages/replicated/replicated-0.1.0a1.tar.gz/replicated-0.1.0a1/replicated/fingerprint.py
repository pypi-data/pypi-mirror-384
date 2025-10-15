import hashlib
import platform
import subprocess


def get_machine_fingerprint() -> str:
    """
    Get a unique machine fingerprint based on platform.

    Returns a SHA256 hash of the platform-specific identifier.
    """
    system = platform.system().lower()
    identifier = ""
    try:
        if system == "darwin":
            # macOS: Use IOPlatformUUID
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "IOPlatformUUID" in line:
                        identifier = line.split('"')[3]
                        break
        elif system == "linux":
            # Linux: Use D-Bus machine ID
            try:
                with open("/var/lib/dbus/machine-id", "r") as f:
                    identifier = f.read().strip()
            except FileNotFoundError:
                try:
                    with open("/etc/machine-id", "r") as f:
                        identifier = f.read().strip()
                except FileNotFoundError:
                    pass
        elif system == "windows":
            # Windows: Use Machine GUID from registry
            result = subprocess.run(
                [
                    "reg",
                    "query",
                    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography",
                    "/v",
                    "MachineGuid",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if "MachineGuid" in line:
                        identifier = line.split()[-1]
                        break
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, OSError):
        pass

    # Fallback: use a combination of system info
    if not identifier:
        import uuid

        identifier = str(uuid.getnode())  # MAC address as fallback

    # Hash the identifier for privacy
    return hashlib.sha256(identifier.encode()).hexdigest()
