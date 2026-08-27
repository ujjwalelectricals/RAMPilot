"""RAMPilot Step 3 - polished PC Manager-style dashboard."""

import threading
import tkinter as tk
from tkinter import ttk

import psutil

from boost import boost

REFRESH_MS = 2000
BG = "#0b1020"
PANEL = "#11182b"
PANEL_2 = "#17213a"
BORDER = "#263452"
TEXT = "#f4f7ff"
MUTED = "#91a0bd"
ACCENT = "#5b8cff"
GOOD = "#36d399"
WARN = "#f5b94c"
DANGER = "#ff667a"

APP_NAMES = {
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "firefox.exe": "Mozilla Firefox",
    "brave.exe": "Brave Browser",
    "discord.exe": "Discord",
    "code.exe": "Visual Studio Code",
    "robloxplayerbeta.exe": "Roblox",
    "robloxstudiobeta.exe": "Roblox Studio",
    "steam.exe": "Steam",
    "steamwebhelper.exe": "Steam Web Helper",
    "explorer.exe": "File Explorer",
    "searchhost.exe": "Windows Search",
    "startmenuexperiencehost.exe": "Start Menu",
    "shellexperiencehost.exe": "Windows Shell Experience",
    "runtimebroker.exe": "Runtime Broker",
    "dwm.exe": "Desktop Window Manager",
    "msmpeng.exe": "Microsoft Defender Antivirus",
    "supportassistagent.exe": "Dell SupportAssist",
    "dell.techhub.instrumentation.subagent.exe": "Dell TechHub",
    "dell.coreservices.client.exe": "Dell Core Services",
    "memcompression": "Windows Memory Compression",
    "system": "Windows System",
}


def gb(value):
    return value / (1024 ** 3)


def friendly_name(exe):
    key = (exe or "").lower()
    if key in APP_NAMES:
        return APP_NAMES[key]
    clean = (exe or "Unknown").removesuffix(".exe")
    return clean.replace("_", " ").replace("-", " ").title()


class RAMPilotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAMPilot — Smart PC Optimizer")
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.configure(bg=BG)
        self.boosting = False
        self.last_status = "Ready"
        self._configure_style()
        self._build_ui()
        psutil.cpu_percent(interval=None)
        self.after(250, self.refresh)

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT,
                        rowheight=34, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED,
                        relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#20345f")], foreground=[("selected", TEXT)])
        style.configure("Horizontal.TProgressbar", troughcolor="#202b45", background=ACCENT,
                        borderwidth=0, thickness=10)

    def card(self, parent, **kwargs):
        return tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, **kwargs)

    def _build_ui(self):
        # Sidebar
        sidebar = tk.Frame(self, bg="#0d1528", width=190)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="⚡", font=("Segoe UI Emoji", 25), bg="#0d1528", fg=ACCENT).pack(pady=(30, 2))
        tk.Label(sidebar, text="RAMPilot", font=("Segoe UI", 20, "bold"), bg="#0d1528", fg=TEXT).pack()
        tk.Label(sidebar, text="SMART PC OPTIMIZER", font=("Segoe UI", 7, "bold"), bg="#0d1528", fg=MUTED).pack(pady=(2, 35))

        for text in ("⌂  Overview", "◉  Memory", "▦  Processes", "⚙  Settings"):
            tk.Label(sidebar, text=text, anchor="w", font=("Segoe UI", 11), bg="#0d1528", fg=TEXT,
                     padx=25, pady=13).pack(fill="x")

        tk.Label(sidebar, text="STEP 3", font=("Segoe UI", 8, "bold"), bg="#0d1528", fg=MUTED).pack(side="bottom", pady=(0, 4))
        tk.Label(sidebar, text="Windows Boost Engine", font=("Segoe UI", 8), bg="#0d1528", fg="#52627f").pack(side="bottom", pady=(0, 20))

        content = tk.Frame(self, bg=BG)
        content.pack(side="left", fill="both", expand=True, padx=28, pady=25)

        top = tk.Frame(content, bg=BG)
        top.pack(fill="x")
        tk.Label(top, text="PC Overview", font=("Segoe UI", 25, "bold"), bg=BG, fg=TEXT).pack(side="left")
        self.status = tk.Label(top, text="● HEALTHY", font=("Segoe UI", 10, "bold"), bg=BG, fg=GOOD)
        self.status.pack(side="right", pady=10)

        # Hero
        hero = self.card(content)
        hero.pack(fill="x", pady=(20, 14))

        left = tk.Frame(hero, bg=PANEL)
        left.pack(side="left", fill="both", expand=True, padx=25, pady=23)
        tk.Label(left, text="Memory health", font=("Segoe UI", 11, "bold"), bg=PANEL, fg=MUTED).pack(anchor="w")
        self.hero_value = tk.Label(left, text="--", font=("Segoe UI", 34, "bold"), bg=PANEL, fg=TEXT)
        self.hero_value.pack(anchor="w", pady=(2, 0))
        self.hero_detail = tk.Label(left, text="Checking memory…", font=("Segoe UI", 10), bg=PANEL, fg=MUTED)
        self.hero_detail.pack(anchor="w")

        self.boost_button = tk.Button(hero, text="⚡  BOOST", command=self.start_boost,
                                      font=("Segoe UI", 13, "bold"), bg=ACCENT, fg="white",
                                      activebackground="#7aa1ff", activeforeground="white",
                                      relief="flat", bd=0, padx=28, pady=15, cursor="hand2")
        self.boost_button.pack(side="right", padx=28, pady=30)

        # Metric cards
        metrics = tk.Frame(content, bg=BG)
        metrics.pack(fill="x", pady=(0, 14))
        self.metric_ram = self.metric_card(metrics, "MEMORY", "--", "Available RAM")
        self.metric_cpu = self.metric_card(metrics, "CPU", "--", "Current load")
        self.metric_total = self.metric_card(metrics, "TOTAL RAM", "--", "Installed memory")
        self.metric_free = self.metric_card(metrics, "STATUS", "READY", "Optimizer state")

        # Processes
        proc = self.card(content)
        proc.pack(fill="both", expand=True)
        header = tk.Frame(proc, bg=PANEL)
        header.pack(fill="x", padx=20, pady=(16, 10))
        tk.Label(header, text="Active applications", font=("Segoe UI", 14, "bold"), bg=PANEL, fg=TEXT).pack(side="left")
        self.process_count = tk.Label(header, text="", font=("Segoe UI", 9), bg=PANEL, fg=MUTED)
        self.process_count.pack(side="right")

        self.tree = ttk.Treeview(proc, columns=("app", "ram", "pid"), show="headings")
        self.tree.heading("app", text="APPLICATION")
        self.tree.heading("ram", text="MEMORY")
        self.tree.heading("pid", text="PID")
        self.tree.column("app", anchor="w", width=360)
        self.tree.column("ram", anchor="e", width=110)
        self.tree.column("pid", anchor="e", width=90)
        self.tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.footer = tk.Label(content, text="RAMPilot • Read-only monitoring + conservative Boost", font=("Segoe UI", 8), bg=BG, fg=MUTED)
        self.footer.pack(pady=(7, 0))

    def metric_card(self, parent, title, value, subtitle):
        frame = self.card(parent)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Label(frame, text=title, font=("Segoe UI", 8, "bold"), bg=PANEL, fg=MUTED).pack(anchor="w", padx=16, pady=(13, 0))
        value_label = tk.Label(frame, text=value, font=("Segoe UI", 18, "bold"), bg=PANEL, fg=TEXT)
        value_label.pack(anchor="w", padx=16, pady=(1, 0))
        tk.Label(frame, text=subtitle, font=("Segoe UI", 8), bg=PANEL, fg=MUTED).pack(anchor="w", padx=16, pady=(0, 13))
        return value_label

    def refresh(self):
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=None)

        self.hero_value.config(text=f"{memory.percent:.1f}% used")
        self.hero_detail.config(text=f"{gb(memory.available):.2f} GB available of {gb(memory.total):.2f} GB")
        self.metric_ram.config(text=f"{gb(memory.available):.2f} GB")
        self.metric_cpu.config(text=f"{cpu:.1f}%")
        self.metric_total.config(text=f"{gb(memory.total):.1f} GB")
        self.metric_free.config(text="BOOSTING" if self.boosting else "READY")

        if memory.available < 1 * 1024**3:
            self.status.config(text="● MEMORY PRESSURE", fg=DANGER)
        elif memory.available < 2 * 1024**3:
            self.status.config(text="● WATCH", fg=WARN)
        else:
            self.status.config(text="● HEALTHY", fg=GOOD)

        processes = []
        for process in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                rss = process.info["memory_info"].rss
                processes.append((rss, process.info["pid"], friendly_name(process.info["name"])))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        processes.sort(reverse=True)

        for item in self.tree.get_children():
            self.tree.delete(item)
        for rss, pid, name in processes[:12]:
            self.tree.insert("", "end", values=(name, f"{gb(rss):.2f} GB", pid))
        self.process_count.config(text=f"Showing {min(12, len(processes))} highest-memory applications")

        self.after(REFRESH_MS, self.refresh)

    def start_boost(self):
        if self.boosting:
            return
        self.boosting = True
        self.boost_button.config(text="⚡  BOOSTING…", state="disabled", bg="#435276")
        self.footer.config(text="RAMPilot • Safely asking Windows to reclaim eligible working-set memory…", fg=ACCENT)
        threading.Thread(target=self._run_boost, daemon=True).start()

    def _run_boost(self):
        try:
            result = boost()
            message = f"Boost complete • Windows accepted {result.succeeded}/{result.attempted} trim requests"
        except Exception as exc:
            message = f"Boost unavailable: {exc}"
        self.after(0, lambda: self.finish_boost(message))

    def finish_boost(self, message):
        self.boosting = False
        self.boost_button.config(text="⚡  BOOST", state="normal", bg=ACCENT)
        self.footer.config(text=message, fg=GOOD if "complete" in message else DANGER)


if __name__ == "__main__":
    RAMPilotApp().mainloop()
