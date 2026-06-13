import os
import subprocess
from datetime import datetime, timedelta

def get_git_metric(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def get_commit_activity():
    # Last 7 days commit counts
    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    commit_counts = {day: 0 for day in days}

    try:
        output = subprocess.check_output(
            ["git", "log", "--since=7.days.ago", "--date=short", "--pretty=format:%ad"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in output.splitlines():
            if line.strip():
                try:
                    date_val = datetime.strptime(line.strip(), "%Y-%m-%d").date()
                    if date_val in commit_counts:
                        commit_counts[date_val] += 1
                except ValueError:
                    continue
    except Exception:
        pass

    return days, [commit_counts[d] for d in days]

def generate_svg():
    # Calculate stats
    start_date = datetime(2026, 6, 12).date()
    uptime_days = (datetime.now().date() - start_date).days
    if uptime_days < 1:
        uptime_days = 1

    total_commits_str = get_git_metric(["git", "rev-list", "--count", "all"]) or get_git_metric(["git", "rev-list", "--count", "HEAD"])
    try:
        total_commits = int(total_commits_str)
    except ValueError:
        total_commits = 15

    # Simulated JVM Memory Usage % based on commits (stable, realistic range: 55% - 78%)
    memory_pct = 55 + (total_commits % 24)

    # Simulated Garbage Collection runs
    gc_runs = max(1, total_commits // 4)

    # Get last 7 days of commits
    days, commits = get_commit_activity()

    # Draw CPU sparkline path
    # X range: 220 to 412 (step 32)
    # Y range: 70 (high activity/low Y) to 120 (no activity/high Y)
    max_c = max(commits) if max(commits) > 0 else 1
    points = []
    x_start = 220
    x_step = 32
    for idx, c in enumerate(commits):
        x = x_start + idx * x_step
        y = 120 - int((c / max_c) * 45)
        points.append((x, y))

    polyline_points = " ".join(f"{x},{y}" for x, y in points)

    # Dash offset for memory circular bar (circumference = 2 * pi * 30 = 188.5)
    circumference = 188.5
    dashoffset = circumference - (circumference * memory_pct / 100)

    # Generate points circles SVG tags
    circles_svg = ""
    for idx, (x, y) in enumerate(points):
        if idx == len(points) - 1:
            # Highlight today's point with a pulse glow
            circles_svg += f"""
    <circle cx="{x}" cy="{y}" r="4.5" fill="#10b981" filter="url(#glow-node)" />
    <circle cx="{x}" cy="{y}" r="8" fill="none" stroke="#10b981" stroke-width="1" opacity="0.5" />"""
        else:
            circles_svg += f'<circle cx="{x}" cy="{y}" r="3" fill="#00d2ff" stroke="#0b0f19" stroke-width="0.75" />'

    # SVG template (No Gradients)
    svg_template = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 210" width="520" height="210">
  <defs>
    <!-- Glow Filters (Using Solid Colors) -->
    <filter id="glow-heavy" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="3.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>

    <filter id="glow-node" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="1.5" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Card Border & Background (Solid Colors) -->
  <rect x="1" y="1" width="518" height="208" rx="12" fill="#0b0f19" stroke="#30363d" stroke-width="1.75" />

  <!-- Header Section -->
  <text x="20" y="27" fill="#9ca3af" font-family="Courier New, monospace" font-size="11" font-weight="bold" letter-spacing="1.5">[ SYSTEM DIAGNOSTICS :: PROFILE LOGS ]</text>
  
  <!-- Glowing Status Badge -->
  <g transform="translate(390, 13)">
    <rect x="-5" y="-3" width="110" height="20" rx="4" fill="#061712" stroke="#047857" stroke-width="1"/>
    <circle cx="8" cy="7" r="3.5" fill="#10b981" filter="url(#glow-node)" />
    <text x="19" y="10.5" fill="#10b981" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="9" font-weight="bold" letter-spacing="0.5">SERVICE_ACTIVE</text>
  </g>

  <!-- Separator Line -->
  <line x1="20" y1="41" x2="500" y2="41" stroke="#1f2937" stroke-width="1" />

  <!-- LEFT SECTION: HEAP MEMORY RADIAL GAUGE -->
  <g transform="translate(20, 50)">
    <!-- Section Title -->
    <text x="10" y="16" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="10" font-weight="bold" letter-spacing="0.5">HEAP MEMORY LOAD</text>
    
    <!-- Outer Decorative Dotted Tech Ring -->
    <circle cx="65" cy="65" r="36" fill="none" stroke="#374151" stroke-dasharray="3 5" stroke-width="0.75" opacity="0.6" />

    <!-- Circular Gauge Background -->
    <circle cx="65" cy="65" r="30" fill="none" stroke="#1f2937" stroke-width="6.5" />
    
    <!-- Circular Gauge Progress (Solid Emerald Green) -->
    <circle cx="65" cy="65" r="30" fill="none" stroke="#10b981" stroke-width="6.5" 
            stroke-dasharray="{circumference}" stroke-dashoffset="{dashoffset}" 
            stroke-linecap="round" transform="rotate(-90 65 65)" filter="url(#glow-node)" />
            
    <!-- Value Text Inside Circle -->
    <text x="65" y="69" fill="#ffffff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="12" font-weight="bold" text-anchor="middle">{memory_pct}%</text>
    <text x="65" y="110" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="9" text-anchor="middle" font-weight="bold" letter-spacing="0.5">ALLOCATED</text>
  </g>

  <!-- MIDDLE SEPARATOR -->
  <line x1="175" y1="60" x2="175" y2="145" stroke="#1f2937" stroke-width="1.5" />

  <!-- RIGHT SECTION: CPU LOAD & ACTIVITY -->
  <g transform="translate(185, 50)">
    <!-- Section Title -->
    <text x="15" y="16" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="10" font-weight="bold" letter-spacing="0.5">CPU LOAD (COMMIT RATE / 7D)</text>
    
    <!-- Graph Grid Lines -->
    <line x1="35" y1="125" x2="227" y2="125" stroke="#1f2937" stroke-width="1" />
    <line x1="35" y1="100" x2="227" y2="100" stroke="#1f2937" stroke-dasharray="2 3" stroke-width="0.75" opacity="0.5" />
    <line x1="35" y1="75" x2="227" y2="75" stroke="#1f2937" stroke-dasharray="2 3" stroke-width="0.75" opacity="0.5" />
    
    <!-- Sparkline Line (Solid Emerald Green) -->
    <path d="M {polyline_points.replace(' ', ' L ')}" fill="none" stroke="#10b981" stroke-width="2.25" filter="url(#glow-node)" />

    <!-- Sparkline Nodes -->
    {circles_svg}
    
    <!-- Sparkline Labels -->
    <text x="35" y="138" fill="#6b7280" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold">7D AGO</text>
    <text x="227" y="138" fill="#10b981" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold" text-anchor="end">TODAY</text>
  </g>

  <!-- Footer Stats Separator -->
  <line x1="20" y1="168" x2="500" y2="168" stroke="#1f2937" stroke-width="1" />

  <!-- FOOTER DIAGNOSTICS CARDS -->
  <g transform="translate(20, 175)">
    <!-- Active Beans Card -->
    <g transform="translate(0, 0)">
      <rect x="0" y="0" width="140" height="22" rx="5" fill="#111827" stroke="#1f2937" stroke-width="1"/>
      <text x="8" y="14" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8.5" font-weight="bold" letter-spacing="0.5">ACTIVE BEANS</text>
      <rect x="110" y="4" width="22" height="14" rx="3" fill="#061712" />
      <text x="121" y="14" fill="#10b981" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="9" font-weight="bold" text-anchor="middle">3</text>
    </g>

    <!-- GC Runs Card -->
    <g transform="translate(162, 0)">
      <rect x="0" y="0" width="130" height="22" rx="5" fill="#111827" stroke="#1f2937" stroke-width="1"/>
      <text x="8" y="14" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8.5" font-weight="bold" letter-spacing="0.5">GC RUNS</text>
      <rect x="95" y="4" width="28" height="14" rx="3" fill="#201007" />
      <text x="109" y="14" fill="#f97316" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="9" font-weight="bold" text-anchor="middle">{gc_runs}</text>
    </g>

    <!-- System Uptime Card -->
    <g transform="translate(315, 0)">
      <rect x="0" y="0" width="165" height="22" rx="5" fill="#111827" stroke="#1f2937" stroke-width="1"/>
      <text x="8" y="14" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8.5" font-weight="bold" letter-spacing="0.5">SYSTEM UPTIME</text>
      <rect x="105" y="4" width="52" height="14" rx="3" fill="#08172e" />
      <text x="131" y="14" fill="#3b82f6" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="9" font-weight="bold" text-anchor="middle">{uptime_days}D</text>
    </g>
  </g>
</svg>
"""
    # Create assets dir if not exist
    os.makedirs("assets", exist_ok=True)
    with open("assets/jvm-monitor.svg", "w", encoding="utf-8") as f:
        f.write(svg_template)
    print("JVM Monitor SVG successfully generated at assets/jvm-monitor.svg")

if __name__ == "__main__":
    generate_svg()
