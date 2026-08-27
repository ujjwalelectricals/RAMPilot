"""RAMPilot Step 4 - conservative automatic boost controller.

The controller only runs a boost after sustained low available memory. It has
cooldowns and hysteresis so it does not repeatedly trim working sets. Apps are
never terminated, suspended, or force-closed by this module.
"""

import time
import threading

import psutil

from boost import boost


# Defaults are intentionally conservative for an 8 GB-class machine.
PRESSURE_GB = 1.0
RECOVERY_GB = 1.75
PRESSURE_SECONDS = 12
COOLDOWN_SECONDS = 60


class AutoBoostController:
    def __init__(self, on_event=None):
        self.on_event = on_event or (lambda message: None)
        self.enabled = False
        self._thread = None
        self._stop = threading.Event()
        self._pressure_since = None
        self._last_boost = 0.0

    def start(self):
        if self.enabled:
            return
        self.enabled = True
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self.on_event("Auto Boost ON • watching for sustained memory pressure")

    def stop(self):
        self.enabled = False
        self._stop.set()
        self._pressure_since = None
        self.on_event("Auto Boost OFF")

    def _loop(self):
        while not self._stop.wait(2):
            available = psutil.virtual_memory().available
            now = time.monotonic()

            if available >= RECOVERY_GB * 1024**3:
                self._pressure_since = None
                continue

            if available < PRESSURE_GB * 1024**3:
                if self._pressure_since is None:
                    self._pressure_since = now
                    self.on_event("Memory pressure detected • confirming…")
                    continue

                sustained = now - self._pressure_since >= PRESSURE_SECONDS
                cooled_down = now - self._last_boost >= COOLDOWN_SECONDS
                if sustained and cooled_down:
                    self._last_boost = now
                    self._pressure_since = None
                    self.on_event("Auto Boost • reclaiming eligible memory…")
                    try:
                        result = boost()
                        self.on_event(
                            f"Auto Boost complete • {result.succeeded}/{result.attempted} requests accepted"
                        )
                    except Exception as exc:
                        self.on_event(f"Auto Boost unavailable • {exc}")
            else:
                # Between pressure and recovery: keep watching, but don't act.
                if self._pressure_since is None:
                    continue
