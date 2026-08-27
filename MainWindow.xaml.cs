using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Media;
using System.Windows.Threading;

namespace RAMPilot;

public partial class MainWindow : Window
{
    [StructLayout(LayoutKind.Sequential)]
    private struct MEMORYSTATUSEX { public uint Length; public uint MemoryLoad; public ulong TotalPhys; public ulong AvailPhys; public ulong TotalPageFile; public ulong AvailPageFile; public ulong TotalVirtual; public ulong AvailVirtual; public ulong AvailExtendedVirtual; }
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool GlobalMemoryStatusEx(ref MEMORYSTATUSEX lpBuffer);
    [DllImport("psapi.dll", SetLastError = true)] private static extern bool EmptyWorkingSet(IntPtr hProcess);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern IntPtr OpenProcess(uint access, bool inherit, uint pid);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    private const uint PROCESS_SET_QUOTA = 0x0100, PROCESS_QUERY_LIMITED_INFORMATION = 0x1000;

    private readonly DispatcherTimer timer = new() { Interval = TimeSpan.FromSeconds(2) };
    private bool autoBoost;
    private DateTime lastBoost = DateTime.MinValue;
    private DateTime? pressureStart;
    private readonly Dictionary<string,string> appNames = new(StringComparer.OrdinalIgnoreCase)
    {
        ["chrome.exe"]="Google Chrome", ["msedge.exe"]="Microsoft Edge", ["firefox.exe"]="Mozilla Firefox", ["brave.exe"]="Brave Browser",
        ["discord.exe"]="Discord", ["code.exe"]="Visual Studio Code", ["robloxplayerbeta.exe"]="Roblox", ["robloxstudiobeta.exe"]="Roblox Studio",
        ["steam.exe"]="Steam", ["steamwebhelper.exe"]="Steam Web Helper", ["explorer.exe"]="File Explorer", ["msmpeng.exe"]="Microsoft Defender Antivirus",
        ["supportassistagent.exe"]="Dell SupportAssist", ["dell.coreservices.client.exe"]="Dell Core Services", ["memcompression"]="Windows Memory Compression",
        ["dwm.exe"]="Desktop Window Manager", ["searchhost.exe"]="Windows Search"
    };

    public MainWindow()
    {
        InitializeComponent();
        timer.Tick += (_, _) => RefreshStats();
        Loaded += (_, _) => { RefreshStats(); timer.Start(); };
        Closed += (_, _) => timer.Stop();
    }

    private static double Gb(ulong bytes) => bytes / 1073741824.0;
    private string Friendly(string? exe) => exe != null && appNames.TryGetValue(exe, out var name) ? name : (exe ?? "Unknown").Replace(".exe", "", StringComparison.OrdinalIgnoreCase).Replace("_", " ").Trim();

    private void RefreshStats()
    {
        var mem = new MEMORYSTATUSEX { Length = (uint)Marshal.SizeOf<MEMORYSTATUSEX>() };
        GlobalMemoryStatusEx(ref mem);
        var used = mem.TotalPhys - mem.AvailPhys;
        Hero.Text = $"{mem.MemoryLoad}% used";
        Detail.Text = $"{Gb(mem.AvailPhys):F2} GB available of {Gb(mem.TotalPhys):F2} GB";
        Available.Text = $"{Gb(mem.AvailPhys):F2} GB";
        Total.Text = $"{Gb(mem.TotalPhys):F1} GB";
        Cpu.Text = $"{Process.GetProcesses().Where(p => { try { return p.ProcessName.Length > 0; } catch { return false; } }).Count()}";
        AutoState.Text = autoBoost ? "ON" : "OFF";
        Health.Text = mem.AvailPhys < 1073741824 ? "● MEMORY PRESSURE" : mem.AvailPhys < 2147483648 ? "● WATCH" : "● HEALTHY";
        Health.Foreground = new SolidColorBrush((Color)ColorConverter.ConvertFromString(mem.AvailPhys < 1073741824 ? "#FF667A" : mem.AvailPhys < 2147483648 ? "#F5B94C" : "#36D399"));

        var rows = new List<AppRow>();
        foreach (var p in Process.GetProcesses())
        {
            try { var bytes = (ulong)p.WorkingSet64; if (bytes >= 50 * 1024 * 1024) rows.Add(new AppRow(Friendly(p.ProcessName + ".exe"), $"{Gb(bytes):F2} GB", p.Id)); }
            catch { }
            finally { p.Dispose(); }
        }
        Apps.ItemsSource = rows.OrderByDescending(x => x.Bytes).Take(12).ToList();
        Count.Text = $"Showing {Math.Min(12, rows.Count)} highest-memory applications";

        if (autoBoost && mem.AvailPhys < 1073741824)
        {
            pressureStart ??= DateTime.UtcNow;
            if (DateTime.UtcNow - pressureStart.Value >= TimeSpan.FromSeconds(12) && DateTime.UtcNow - lastBoost >= TimeSpan.FromSeconds(60))
                StartBoost(true);
        }
        else if (mem.AvailPhys >= 1879048192) pressureStart = null;
    }

    private void Boost_Click(object sender, RoutedEventArgs e) => StartBoost(false);
    private void StartBoost(bool automatic)
    {
        if (DateTime.UtcNow - lastBoost < TimeSpan.FromSeconds(5)) return;
        lastBoost = DateTime.UtcNow; BoostButton.IsEnabled = false; Footer.Text = automatic ? "RAMPilot • Auto Boost reclaiming eligible memory…" : "RAMPilot • Reclaiming eligible working-set memory…";
        Task.Run(() =>
        {
            int ok = 0, attempted = 0;
            foreach (var p in Process.GetProcesses().OrderByDescending(x => { try { return x.WorkingSet64; } catch { return 0; } }).Take(20))
            {
                try
                {
                    if (p.Id == Environment.ProcessId || p.ProcessName.Equals("System", StringComparison.OrdinalIgnoreCase)) continue;
                    attempted++; var h = OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_LIMITED_INFORMATION, false, (uint)p.Id);
                    if (h != IntPtr.Zero) { if (EmptyWorkingSet(h)) ok++; CloseHandle(h); }
                }
                catch { }
                finally { p.Dispose(); }
            }
            Dispatcher.Invoke(() => { BoostButton.IsEnabled = true; Footer.Text = $"Boost complete • {ok}/{attempted} requests accepted"; RefreshStats(); });
        });
    }
    private void Auto_Click(object sender, RoutedEventArgs e)
    {
        autoBoost = !autoBoost; AutoButton.Content = autoBoost ? "🤖  AUTO BOOST: ON" : "🤖  AUTO BOOST: OFF"; AutoButton.Background = new SolidColorBrush((Color)ColorConverter.ConvertFromString(autoBoost ? "#164B3D" : "#17213A")); Footer.Text = autoBoost ? "RAMPilot • Auto Boost watching for sustained memory pressure" : "RAMPilot • Automatic Boost is OFF";
    }
    private void Nav_Click(object sender, RoutedEventArgs e) { }
}
public record AppRow(string Name, string Memory, int Pid) { public double Bytes => double.TryParse(Memory.Replace(" GB", ""), out var v) ? v : 0; }
