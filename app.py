"""RAMPilot Step 2 - PC Manager-style desktop dashboard.

Read-only UI: no processes are terminated and no Windows settings are changed.
"""

import tkinter as tk
from tkinter import ttk
import psutil

REFRESH_MS = 2000

BG = "#f5f7fb"
CARD = "#ffffff"
TEXT = "#172033"
MUTED = "#68738a"
ACCENT = "#2563eb"
GOOD = "#16a34a"
WARN = "#d97706"
DANGER = "#dc2626"


def gb(value):
    return value / (1024 ** 3)


class RAMPilotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAMPilot")
        self.geometry("900x650")
        self.minsize(760, 560)
        self.configure(bg=BG)

        self._configure_style()
        self._build_ui()
        self.after(300, self.refresh)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor="#e7ebf2", background=ACCENT, borderwidth=0, thickness=10)

    def _card(self, parent):
        frame = tk.Frame(parent, bg=CARD, highlightthickness=1, highlightbackground="#e3e7ef")
        return frame

    def _build_ui(self):
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=28, pady=(24, 8))

        tk.Label(header, text="RAMPilot", font=("Segoe UI", 25, "bold"), bg=BG, fg=TEXT).pack(side="left")
        tk.Label(header, text="Smart PC health", font=("Segoe UI", 11), bg=BG, fg=MUTED).pack(side="left", padx=(12, 0), pady=(10, 0))

        self.status_label = tk.Label(header, text="● HEALTHY", font=("Segoe UI", 10, "bold"), bg=BG, fg=GOOD)
        self.status_label.pack(side="right", pady=(8, 0))

        main = tk.Frame(self, bg=BG)
        main.pack(fill="both", expand=True, padx=28, pady=10)

        left = self._card(main)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left, text="PC Health", font=("Segoe UI", 15, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=22, pady=(20, 3))
        tk.Label(left, text="Real-time system overview", font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(anchor="w", padx=22)

        ram_row = tk.Frame(left, bg=CARD)
        ram_row.pack(fill="x", padx=22, pady=(28, 4))
        tk.Label(ram_row, text="Memory", font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT).pack(side="left")
        self.ram_value = tk.Label(ram_row, text="--", font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT)
        self.ram_value.pack(side="right")

        self.ram_bar = ttk.Progressbar(left, maximum=100, mode="determinate")
        self.ram_bar.pack(fill="x", padx=22, pady=(0, 4))
        self.ram_detail = tk.Label(left, text="", font=("Segoe UI", 9), bg=CARD, fg=MUTED)
        self.ram_detail.pack(anchor="w", padx=22)

        cpu_row = tk.Frame(left, bg=CARD)
        cpu_row.pack(fill="x", padx=22, pady=(24, 4))
        tk.Label(cpu_row, text="CPU", font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT).pack(side="left")
        self.cpu_value = tk.Label(cpu_row, text="--", font=("Segoe UI", 11, "bold"), bg=CARD, fg=TEXT)
        self.cpu_value.pack(side="right")
        self.cpu_bar = ttk.Progressbar(left, maximum=100, mode="determinate")
        self.cpu_bar.pack(fill="x", padx=22)

        note = tk.Label(left, text="Read-only monitoring • Boost is not enabled yet", font=("Segoe UI", 9), bg=CARD, fg=MUTED)
        note.pack(anchor="w", padx=22, pady=(28, 22))

        right = self._card(main)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        tk.Label(right, text="Memory Usage", font=("Segoe UI", 15, "bold"), bg=CARD, fg=TEXT).pack(anchor="w", padx=22, pady=(20, 3))
        tk.Label(right, text="Top processes by working-set memory", font=("Segoe UI", 10), bg=CARD, fg=MUTED).pack(anchor="w", padx=22, pady=(0, 12))

        columns = ("process", "memory")
        self.tree = ttk.Treeview(right, columns=columns, show="headings", height=14)
        self.tree.heading("process", text="Process")
        self.tree.heading("memory", text="RAM")
        self.tree.column("process", anchor="w", width=220)
        self.tree.column("memory", anchor="e", width=90)
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 18))

        self.footer = tk.Label(self, text="RAMPilot • Monitoring every 2 seconds", font=("Segoe UI", 9), bg=BG, fg=MUTED)
        self.footer.pack(pady=(0, 14))

    def refresh(self):
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)

        self.ram_value.config(text=f"{memory.percent:.1f}%")
        self.ram_bar["value"] = memory.percent
        self.ram_detail.config(text=f"{gb(memory.used):.2f} GB used  •  {gb(memory.available):.2f} GB available  •  {gb(memory.total):.2f} GB total")

        self.cpu_value.config(text=f"{cpu:.1f}%")
        self.cpu_bar["value"] = cpu

        if memory.available < 1 * (1024 ** 3):
            self.status_label.config(text="● MEMORY PRESSURE", fg=DANGER)
        elif memory.available < 2 * (1024 ** 3):
            self.status_label.config(text="● WATCH", fg=WARN)
        else:
            self.status_label.config(text="● HEALTHY", fg=GOOD)

        processes = []
        for process in psutil.process_iter(["name", "memory_info"]):
            try:
                rss = process.info["memory_info"].rss
                processes.append((rss, process.info["name"] or "Unknown"))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

        for item in self.tree.get_children():
            self.tree.delete(item)

        for rss, name in sorted(processes, reverse=True)[:12]:
            self.tree.insert("", "end", values=(name, f"{gb(rss):.2f} GB"))

        self.after(REFRESH_MS, self.refresh)


if __name__ == "__main__":
    psutil.cpu_percent(interval=None)
    app = RAMPilotApp()
    app.mainloop()
