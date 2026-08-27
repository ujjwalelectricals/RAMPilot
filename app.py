"""RAMPilot Step 4 - automatic memory optimization dashboard."""

import threading
import tkinter as tk
from tkinter import ttk

import psutil

from boost import boost
from auto_boost import AutoBoostController

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
    "chrome.exe": "Google Chrome", "msedge.exe": "Microsoft Edge", "firefox.exe": "Mozilla Firefox",
    "brave.exe": "Brave Browser", "discord.exe": "Discord", "code.exe": "Visual Studio Code",
    "robloxplayerbeta.exe": "Roblox", "robloxstudiobeta.exe": "Roblox Studio", "steam.exe": "Steam",
    "steamwebhelper.exe": "Steam Web Helper", "explorer.exe": "File Explorer", "searchhost.exe": "Windows Search",
    "startmenuexperiencehost.exe": "Start Menu", "shellexperiencehost.exe": "Windows Shell Experience",
    "runtimebroker.exe": "Runtime Broker", "dwm.exe": "Desktop Window Manager",
    "msmpeng.exe": "Microsoft Defender Antivirus", "supportassistagent.exe": "Dell SupportAssist",
    "dell.techhub.instrumentation.subagent.exe": "Dell TechHub", "dell.coreservices.client.exe": "Dell Core Services",
    "memcompression": "Windows Memory Compression", "system": "Windows System",
}


def gb(value): return value / (1024 ** 3)


def friendly_name(exe):
    key = (exe or "").lower()
    if key in APP_NAMES: return APP_NAMES[key]
    return (exe or "Unknown").removesuffix(".exe").replace("_", " ").replace("-", " ").title()


class RAMPilotApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RAMPilot — Smart PC Optimizer")
        self.geometry("1080x720")
        self.minsize(900, 620)
        self.configure(bg=BG)
        self.boosting = False
        self.auto = AutoBoostController(self.set_footer)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self._configure_style()
        self._build_ui()
        psutil.cpu_percent(interval=None)
        self.after(250, self.refresh)

    def _configure_style(self):
        style = ttk.Style(self); style.theme_use("clam")
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=34, borderwidth=0, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background=PANEL_2, foreground=MUTED, relief="flat", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#20345f")], foreground=[("selected", TEXT)])

    def card(self, parent, **kwargs):
        return tk.Frame(parent, bg=PANEL, highlightthickness=1, highlightbackground=BORDER, **kwargs)

    def _build_ui(self):
        sidebar = tk.Frame(self, bg="#0d1528", width=190); sidebar.pack(side="left", fill="y"); sidebar.pack_propagate(False)
        tk.Label(sidebar, text="⚡", font=("Segoe UI Emoji", 25), bg="#0d1528", fg=ACCENT).pack(pady=(30,2))
        tk.Label(sidebar, text="RAMPilot", font=("Segoe UI",20,"bold"), bg="#0d1528", fg=TEXT).pack()
        tk.Label(sidebar, text="SMART PC OPTIMIZER", font=("Segoe UI",7,"bold"), bg="#0d1528", fg=MUTED).pack(pady=(2,35))
        for text in ("⌂  Overview", "◉  Memory", "▦  Processes", "⚙  Settings"):
            tk.Label(sidebar, text=text, anchor="w", font=("Segoe UI",11), bg="#0d1528", fg=TEXT, padx=25, pady=13).pack(fill="x")
        tk.Label(sidebar, text="STEP 4", font=("Segoe UI",8,"bold"), bg="#0d1528", fg=MUTED).pack(side="bottom", pady=(0,4))
        tk.Label(sidebar, text="Automatic Memory Control", font=("Segoe UI",8), bg="#0d1528", fg="#52627f").pack(side="bottom", pady=(0,20))

        content = tk.Frame(self, bg=BG); content.pack(side="left", fill="both", expand=True, padx=28, pady=25)
        top = tk.Frame(content, bg=BG); top.pack(fill="x")
        tk.Label(top, text="PC Overview", font=("Segoe UI",25,"bold"), bg=BG, fg=TEXT).pack(side="left")
        self.status = tk.Label(top, text="● HEALTHY", font=("Segoe UI",10,"bold"), bg=BG, fg=GOOD); self.status.pack(side="right", pady=10)

        hero = self.card(content); hero.pack(fill="x", pady=(20,14))
        left = tk.Frame(hero, bg=PANEL); left.pack(side="left", fill="both", expand=True, padx=25, pady=23)
        tk.Label(left, text="Memory health", font=("Segoe UI",11,"bold"), bg=PANEL, fg=MUTED).pack(anchor="w")
        self.hero_value = tk.Label(left, text="--", font=("Segoe UI",34,"bold"), bg=PANEL, fg=TEXT); self.hero_value.pack(anchor="w")
        self.hero_detail = tk.Label(left, text="Checking memory…", font=("Segoe UI",10), bg=PANEL, fg=MUTED); self.hero_detail.pack(anchor="w")
        button_frame = tk.Frame(hero, bg=PANEL); button_frame.pack(side="right", padx=28, pady=25)
        self.boost_button = tk.Button(button_frame, text="⚡  BOOST", command=self.start_boost, font=("Segoe UI",13,"bold"), bg=ACCENT, fg="white", activebackground="#7aa1ff", relief="flat", bd=0, padx=28, pady=13, cursor="hand2"); self.boost_button.pack()
        self.auto_button = tk.Button(button_frame, text="🤖  AUTO BOOST: OFF", command=self.toggle_auto, font=("Segoe UI",9,"bold"), bg=PANEL_2, fg=TEXT, activebackground="#26385f", relief="flat", bd=0, padx=18, pady=9, cursor="hand2"); self.auto_button.pack(pady=(9,0))

        metrics = tk.Frame(content, bg=BG); metrics.pack(fill="x", pady=(0,14))
        self.metric_ram = self.metric_card(metrics,"MEMORY","--","Available RAM")
        self.metric_cpu = self.metric_card(metrics,"CPU","--","Current load")
        self.metric_total = self.metric_card(metrics,"TOTAL RAM","--","Installed memory")
        self.metric_state = self.metric_card(metrics,"AUTO","OFF","Optimizer state")

        proc = self.card(content); proc.pack(fill="both", expand=True)
        header = tk.Frame(proc,bg=PANEL); header.pack(fill="x", padx=20,pady=(16,10))
        tk.Label(header,text="Active applications",font=("Segoe UI",14,"bold"),bg=PANEL,fg=TEXT).pack(side="left")
        self.process_count=tk.Label(header,text="",font=("Segoe UI",9),bg=PANEL,fg=MUTED); self.process_count.pack(side="right")
        self.tree=ttk.Treeview(proc,columns=("app","ram","pid"),show="headings")
        for col,title in (("app","APPLICATION"),("ram","MEMORY"),("pid","PID")): self.tree.heading(col,text=title)
        self.tree.column("app",anchor="w",width=360); self.tree.column("ram",anchor="e",width=110); self.tree.column("pid",anchor="e",width=90)
        self.tree.pack(fill="both",expand=True,padx=12,pady=(0,12))
        self.footer=tk.Label(content,text="RAMPilot • Automatic Boost is OFF",font=("Segoe UI",8),bg=BG,fg=MUTED); self.footer.pack(pady=(7,0))

    def metric_card(self,parent,title,value,subtitle):
        frame=self.card(parent); frame.pack(side="left",fill="both",expand=True,padx=(0,10))
        tk.Label(frame,text=title,font=("Segoe UI",8,"bold"),bg=PANEL,fg=MUTED).pack(anchor="w",padx=16,pady=(13,0))
        value_label=tk.Label(frame,text=value,font=("Segoe UI",18,"bold"),bg=PANEL,fg=TEXT); value_label.pack(anchor="w",padx=16)
        tk.Label(frame,text=subtitle,font=("Segoe UI",8),bg=PANEL,fg=MUTED).pack(anchor="w",padx=16,pady=(0,13))
        return value_label

    def refresh(self):
        memory=psutil.virtual_memory(); cpu=psutil.cpu_percent(interval=None)
        self.hero_value.config(text=f"{memory.percent:.1f}% used")
        self.hero_detail.config(text=f"{gb(memory.available):.2f} GB available of {gb(memory.total):.2f} GB")
        self.metric_ram.config(text=f"{gb(memory.available):.2f} GB"); self.metric_cpu.config(text=f"{cpu:.1f}%"); self.metric_total.config(text=f"{gb(memory.total):.1f} GB")
        self.metric_state.config(text="ON" if self.auto.enabled else "OFF")
        if memory.available < 1*1024**3: self.status.config(text="● MEMORY PRESSURE",fg=DANGER)
        elif memory.available < 2*1024**3: self.status.config(text="● WATCH",fg=WARN)
        else: self.status.config(text="● HEALTHY",fg=GOOD)
        processes=[]
        for p in psutil.process_iter(["pid","name","memory_info"]):
            try: processes.append((p.info["memory_info"].rss,p.info["pid"],friendly_name(p.info["name"])))
            except (psutil.NoSuchProcess,psutil.AccessDenied,psutil.ZombieProcess): pass
        processes.sort(reverse=True)
        for item in self.tree.get_children(): self.tree.delete(item)
        for rss,pid,name in processes[:12]: self.tree.insert("","end",values=(name,f"{gb(rss):.2f} GB",pid))
        self.process_count.config(text=f"Showing {min(12,len(processes))} highest-memory applications")
        self.after(REFRESH_MS,self.refresh)

    def start_boost(self):
        if self.boosting: return
        self.boosting=True; self.boost_button.config(text="⚡  BOOSTING…",state="disabled",bg="#435276"); self.set_footer("RAMPilot • Safely reclaiming eligible working-set memory…")
        threading.Thread(target=self._run_boost,daemon=True).start()

    def _run_boost(self):
        try:
            result=boost(); message=f"Boost complete • {result.succeeded}/{result.attempted} requests accepted"
        except Exception as exc: message=f"Boost unavailable • {exc}"
        self.after(0,lambda:self.finish_boost(message))

    def finish_boost(self,message):
        self.boosting=False; self.boost_button.config(text="⚡  BOOST",state="normal",bg=ACCENT); self.set_footer(message)

    def toggle_auto(self):
        if self.auto.enabled:
            self.auto.stop(); self.auto_button.config(text="🤖  AUTO BOOST: OFF",bg=PANEL_2)
        else:
            self.auto.start(); self.auto_button.config(text="🤖  AUTO BOOST: ON",bg="#164b3d")

    def set_footer(self,message):
        self.footer.config(text=message)

    def close(self):
        self.auto.stop(); self.destroy()


if __name__ == "__main__": RAMPilotApp().mainloop()
