import os
import subprocess
from datetime import datetime, timedelta, timezone

def get_git_metric(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""

def get_commit_activity():
    # Last 7 days commit counts (in IST)
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    today = ist_now.date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    commit_counts = {day: 0 for day in days}

    try:
        # Get commit dates in ISO format with timezone info to align with IST
        output = subprocess.check_output(
            ["git", "log", "--since=7.days.ago", "--date=iso", "--pretty=format:%ad"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in output.splitlines():
            if line.strip():
                try:
                    dt_str = line.strip().split()[0]
                    date_val = datetime.strptime(dt_str, "%Y-%m-%d").date()
                    if date_val in commit_counts:
                        commit_counts[date_val] += 1
                except Exception:
                    continue
    except Exception:
        pass

    return days, [commit_counts[d] for d in days]

def get_commit_streaks_and_today():
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    today = ist_now.date()
    yesterday = today - timedelta(days=1)
    
    current_streak = 0
    max_streak = 0
    commits_today = 0
    
    try:
        # Get commit dates in ISO format
        output = subprocess.check_output(
            ["git", "log", "--date=iso", "--pretty=format:%ad"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        dates = []
        for line in output.splitlines():
            if line.strip():
                try:
                    dt_str = line.strip().split()[0]
                    date_val = datetime.strptime(dt_str, "%Y-%m-%d").date()
                    dates.append(date_val)
                except Exception:
                    continue
        
        # Sort unique dates oldest to newest
        unique_dates = sorted(list(set(dates)))
        
        if unique_dates:
            # Count commits today
            commits_today = sum(1 for d in dates if d == today)
            
            # Calculate streaks
            streaks = []
            current = 1
            for i in range(1, len(unique_dates)):
                diff = (unique_dates[i] - unique_dates[i-1]).days
                if diff == 1:
                    current += 1
                elif diff > 1:
                    streaks.append(current)
                    current = 1
            streaks.append(current)
            max_streak = max(streaks)
            
            # Calculate current active streak
            if unique_dates[-1] in (today, yesterday):
                curr_active = 1
                for i in range(len(unique_dates) - 1, 0, -1):
                    diff = (unique_dates[i] - unique_dates[i-1]).days
                    if diff == 1:
                        curr_active += 1
                    elif diff > 1:
                        break
                current_streak = curr_active
            else:
                current_streak = 0
        else:
            current_streak = 0
            max_streak = 0
            commits_today = 0
    except Exception:
        pass
        
    return max(1, current_streak), max(1, max_streak), commits_today

def get_last_commits():
    try:
        output = subprocess.check_output(
            ["git", "log", "-3", "--pretty=format:%h|%s"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        commits = []
        for line in output.splitlines():
            if line.strip():
                parts = line.strip().split("|", 1)
                h = parts[0]
                msg = parts[1] if len(parts) > 1 else ""
                # Truncate message to avoid overflow in terminal box
                if len(msg) > 34:
                    msg = msg[:31] + "..."
                commits.append((h, msg))
        while len(commits) < 3:
            commits.append(("0000000", "no commit found"))
        return commits
    except Exception:
        return [("0000000", "no commit found")] * 3

def generate_svg():
    # Calculate real stats
    streak, max_streak, commits_today = get_commit_streaks_and_today()
    
    # Current time in Asia/Kolkata (IST is UTC + 5:30)
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    last_update_str = ist_now.strftime("%H:%M IST")

    total_commits_str = get_git_metric(["git", "rev-list", "--count", "all"]) or get_git_metric(["git", "rev-list", "--count", "HEAD"])
    try:
        total_commits = int(total_commits_str)
    except ValueError:
        total_commits = 15

    # Simulated JVM Memory Usage % based on commits (stable, realistic range: 55% - 78%)
    memory_pct = 55 + (total_commits % 24)

    # Get last 7 days of commits
    days, commits = get_commit_activity()

    # Draw CPU sparkline path
    # X range: 25 to 295 (step 45) relative to group translate(185, 45)
    # Y range: 35 (high activity/low Y) to 69 (no activity/high Y)
    max_c = max(commits) if max(commits) > 0 else 1
    points = []
    x_start = 25
    x_step = 45
    for idx, c in enumerate(commits):
        x = x_start + idx * x_step
        y = 69 - int((c / max_c) * 34)
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

    # Fetch last 3 commits
    last_commits = get_last_commits()
    commit_lines_svg = ""
    for idx, (h, msg) in enumerate(last_commits):
        y_pos = 118 + idx * 12
        commit_lines_svg += f"""
      <text x="25" y="{y_pos}" fill="#c9d1d9" font-family="Courier New, monospace" font-size="7.5" font-weight="bold">
        <tspan fill="#6b7280">*</tspan> <tspan fill="#58a6ff">{h}</tspan> <tspan fill="#6b7280">|</tspan> <tspan fill="#8b949e">{msg}</tspan>
      </text>"""

    # SVG template (No Gradients)
    svg_template = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 520 260" width="520" height="260">
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
  <rect x="1" y="1" width="518" height="258" rx="12" fill="#0b0f19" stroke="#30363d" stroke-width="1.75" />

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
  <g transform="translate(20, 45)">
    <!-- Section Title -->
    <text x="10" y="15" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="10" font-weight="bold" letter-spacing="0.5">HEAP MEMORY LOAD</text>
    
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
    <text x="65" y="115" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="9" text-anchor="middle" font-weight="bold" letter-spacing="0.5">ALLOCATED</text>
    <text x="65" y="135" fill="#6b7280" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold" text-anchor="middle" letter-spacing="0.5">GC: G1GC | ACTIVE: TRUE</text>
  </g>

  <!-- MIDDLE SEPARATOR -->
  <line x1="175" y1="55" x2="175" y2="205" stroke="#1f2937" stroke-width="1.5" />

  <!-- RIGHT SECTION: CPU LOAD & ACTIVITY -->
  <g transform="translate(185, 45)">
    <!-- Section Title -->
    <text x="15" y="15" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="10" font-weight="bold" letter-spacing="0.5">CPU LOAD (COMMIT RATE / 7D)</text>
    
    <!-- Graph Grid Lines -->
    <line x1="25" y1="69" x2="295" y2="69" stroke="#1f2937" stroke-width="1" />
    <line x1="25" y1="52" x2="295" y2="52" stroke="#1f2937" stroke-dasharray="2 3" stroke-width="0.75" opacity="0.5" />
    <line x1="25" y1="35" x2="295" y2="35" stroke="#1f2937" stroke-dasharray="2 3" stroke-width="0.75" opacity="0.5" />
    
    <!-- Sparkline Line (Solid Emerald Green) -->
    <path d="M {polyline_points.replace(' ', ' L ')}" fill="none" stroke="#10b981" stroke-width="2.25" filter="url(#glow-node)" />

    <!-- Sparkline Nodes -->
    {circles_svg}
    
    <!-- Sparkline Labels -->
    <text x="25" y="84" fill="#6b7280" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold">7D AGO</text>
    <text x="295" y="84" fill="#10b981" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold" text-anchor="end">TODAY</text>
    
    <!-- Commit Log Terminal Box -->
    <rect x="15" y="95" width="295" height="60" rx="4" fill="#0d1117" stroke="#1f2937" stroke-width="1" />
    
    <!-- Terminal Title / Control Dots -->
    <circle cx="25" cy="103" r="2.5" fill="#ef4444" />
    <circle cx="32" cy="103" r="2.5" fill="#f59e0b" />
    <circle cx="39" cy="103" r="2.5" fill="#10b981" />
    <text x="49" y="106" fill="#6b7280" font-family="Courier New, monospace" font-size="7" font-weight="bold">bash - git log -n 3</text>
    
    <!-- Terminal Commits -->
    {commit_lines_svg}
  </g>

  <!-- Footer Stats Separator -->
  <line x1="20" y1="215" x2="500" y2="215" stroke="#1f2937" stroke-width="1" />

  <!-- FOOTER DIAGNOSTICS CARDS -->
  <g transform="translate(20, 222)">
    <!-- Active Beans Card -->
    <g transform="translate(0, 0)">
      <rect x="0" y="0" width="145" height="22" rx="5" fill="#111827" stroke="#1f2937" stroke-width="1"/>
      <text x="8" y="14" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold" letter-spacing="0.5">ACTIVE BEANS</text>
      <rect x="90" y="4" width="50" height="14" rx="3" fill="#061712" />
      <text x="115" y="14" fill="#10b981" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8.5" font-weight="bold" text-anchor="middle">{streak}D / {max_streak}D</text>
    </g>

    <!-- GC Runs Card -->
    <g transform="translate(160, 0)">
      <rect x="0" y="0" width="140" height="22" rx="5" fill="#111827" stroke="#1f2937" stroke-width="1"/>
      <text x="8" y="14" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold" letter-spacing="0.5">GC RUNS</text>
      <rect x="105" y="4" width="30" height="14" rx="3" fill="#201007" />
      <text x="120" y="14" fill="#f97316" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8.5" font-weight="bold" text-anchor="middle">{commits_today}</text>
    </g>

    <!-- System Update Card -->
    <g transform="translate(315, 0)">
      <rect x="0" y="0" width="165" height="22" rx="5" fill="#111827" stroke="#1f2937" stroke-width="1"/>
      <text x="8" y="14" fill="#9ca3af" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8" font-weight="bold" letter-spacing="0.5">SYSTEM UPDATE</text>
      <rect x="105" y="4" width="55" height="14" rx="3" fill="#08172e" />
      <text x="132.5" y="14" fill="#3b82f6" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Arial,sans-serif" font-size="8.5" font-weight="bold" text-anchor="middle">{last_update_str}</text>
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
