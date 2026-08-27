import time
from datetime import datetime

import psutil


REFRESH_SECONDS = 2
TOP_PROCESSES = 10


def gb(value):
    return value / (1024 ** 3)


def show_status():
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)

    print("\033[2J\033[H", end="")

    print("=" * 72)
    print("RAMPilot — Step 1 | Read-Only System Monitor")
    print("=" * 72)

    print(f"Updated: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print()

    print(
        f"RAM:       {gb(memory.used):.2f} / "
        f"{gb(memory.total):.2f} GB "
        f"({memory.percent:.1f}%)"
    )

    print(f"Available: {gb(memory.available):.2f} GB")
    print(f"CPU:       {cpu:.1f}%")

    print()
    print(f"Top {TOP_PROCESSES} processes by RAM")
    print("-" * 72)
    print(f"{'PID':>7}  {'RAM':>9}  {'%':>6}  Process")
    print("-" * 72)

    processes = []

    for process in psutil.process_iter(
        ["pid", "name", "memory_info"]
    ):
        try:
            ram = process.info["memory_info"].rss

            processes.append(
                (
                    ram,
                    process.info["pid"],
                    process.info["name"] or "Unknown",
                )
            )

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            pass

    for ram, pid, name in sorted(
        processes,
        reverse=True
    )[:TOP_PROCESSES]:

        percentage = (ram / memory.total) * 100

        print(
            f"{pid:>7}  "
            f"{gb(ram):>7.2f} GB  "
            f"{percentage:>5.1f}%  "
            f"{name}"
        )

    print()
    print("READ-ONLY MODE")
    print("No applications are being closed or modified.")
    print("Press Ctrl+C to stop.")


def main():
    psutil.cpu_percent(interval=None)

    try:
        while True:
            show_status()
            time.sleep(REFRESH_SECONDS)

    except KeyboardInterrupt:
        print("\nRAMPilot stopped safely.")


if __name__ == "__main__":
    main()
