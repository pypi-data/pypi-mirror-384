#!/usr/bin/env python3
import re
import shlex
import subprocess
import curses
import time
import click
import socket

def run_cmd(cmd, timeout=10):
    try:
        # Prepend sudo for smartctl/nvme/btrfs commands
        if cmd.startswith(('smartctl', 'nvme', 'btrfs')):
            cmd = f"sudo {cmd}"
        p = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout + p.stderr
    except Exception as e:
        return 1, str(e)

def list_devices():
    rc, out = run_cmd("smartctl --scan")
    if rc != 0:
        return [], out
    devs = []
    for line in out.splitlines():
        m = re.search(r'(/dev/\S+)', line)
        if m:
            devs.append(m.group(1))
    return devs, None

def nvme_critical(dev):
    rc, out = run_cmd(f"nvme smart-log {dev}")
    if rc != 0:
        rc2, out2 = run_cmd(f"nvme smart-log --output-format=json {dev}")
        if rc2 == 0:
            out = out2
    m = re.search(r'critical[_ ]warning\s*[:=]\s*(\d+)', out, re.IGNORECASE)
    if m:
        return int(m.group(1)), out
    m2 = re.search(r'"critical_warning"\s*:\s*(\d+)', out)
    if m2:
        return int(m2.group(1)), out
    return None, out

def smart_errors(dev):
    rc, out = run_cmd(f"smartctl -l error {dev}")
    if rc != 0:
        return None, out
    if re.search(r'no\s+errors\s+logged', out, re.IGNORECASE):
        return False, out
    for ln in out.splitlines():
        if re.search(r'\d{4}-\d{2}-\d{2}', ln) or re.search(r'Error', ln, re.IGNORECASE):
            return True, ln.strip()
    content = "\n".join([l for l in out.splitlines() if l.strip()])
    return (True, content.splitlines()[0]) if content else (False, out)

def get_btrfs_partitions():
    rc, out = run_cmd("btrfs filesystem show")
    if rc != 0:
        return [], f"btrfs-cmd-fail: {out[:50]}"
    partitions = []
    for line in out.splitlines():
        # Look for 'path /dev/...' in btrfs output
        m = re.search(r'path\s+(/dev/\S+)', line)
        if m:
            partitions.append(m.group(1))
    return partitions, None

def get_btrfs_mountpoint(device):
    """Find mountpoint for a btrfs device"""
    rc, out = run_cmd(f"findmnt -n -o TARGET -S {device}")
    if rc == 0 and out.strip():
        return out.strip().splitlines()[0]
    return None

def check_btrfs_scrub_status(device):
    """Check if btrfs scrub is running and get error summary"""
    mountpoint = get_btrfs_mountpoint(device)
    if not mountpoint:
        return "unmounted", ""

    rc, out = run_cmd(f"btrfs scrub status {mountpoint}")
    if rc != 0:
        return "unknown", ""

    # Extract error summary - preserve it even during running state
    error_summary = ""
    error_match = re.search(r'Error summary:\s*(.+)', out)
    if error_match:
        error_summary = error_match.group(1).strip()

    # Look for Status: line
    status_match = re.search(r'Status:\s*(\w+)', out)
    if status_match:
        status = status_match.group(1).lower()
        if status == "running":
            # For running scrub, try to extract percentage
            percent_match = re.search(r'Bytes scrubbed:.*?\((\d+\.?\d*)%\)', out)
            if percent_match:
                percentage = percent_match.group(1)
                return f"running ({percentage}%)", error_summary if error_summary != "" else "in progress"
            else:
                return "running", error_summary if error_summary != "" else "in progress"
        elif status == "finished":
            return "idle", error_summary
        elif status == "aborted":
            return "aborted", error_summary
        else:
            return status, error_summary
    elif "no scrub running" in out.lower():
        return "idle", "never run"
    else:
        return "unknown", ""

def start_btrfs_scrub(device):
    """Start btrfs scrub on device"""
    mountpoint = get_btrfs_mountpoint(device)
    if not mountpoint:
        return "Device not mounted"

    rc, out = run_cmd(f"btrfs scrub start {mountpoint}")
    if rc == 0:
        return "Scrub started"
    else:
        return f"Scrub failed: {out[:50]}"

def get_device_size(device):
    """Get device size in GB"""
    # For NVMe devices, convert /dev/nvme0 to /dev/nvme0n1 for size detection
    size_device = device
    if device.startswith('/dev/nvme'):
        # Check if it's a controller device (nvmeX) vs namespace device (nvmeXnY)
        last_part = device.split('/')[-1]
        if re.match(r'nvme\d+$', last_part):  # Matches nvme0, nvme1, etc. (controller)
            # Convert /dev/nvme0 to /dev/nvme0n1
            size_device = device + 'n1'

    # Use -d flag to show only the device itself, not partitions
    rc, out = run_cmd(f"lsblk -b -n -d -o SIZE {size_device}")
    if rc != 0:
        return ""

    try:
        size_bytes = int(out.strip())
        size_gb = size_bytes / (1024**3)  # Convert to GB
        if size_gb < 1:
            return f"{size_gb:.1f}GB"
        else:
            return f"{size_gb:.0f}GB"
    except (ValueError, ZeroDivisionError):
        return ""

def start_smart_test(device):
    """Start short SMART test on device"""
    rc, out = run_cmd(f"smartctl -t short {device}")
    if rc == 0:
        return "SMART test started"
    elif "Can't start self-test without aborting current test" in out:
        # Extract percentage if available
        percent_match = re.search(r'\((\d+)%\s+completed\)', out)
        if percent_match:
            return f"Test already running ({percent_match.group(1)}% completed)"
        else:
            return "Test already running"
    else:
        return f"SMART test failed: {out[:50]}"

def get_smart_test_status(device):
    """Get SMART self-test status"""
    # First check if a test is currently running using smartctl -a
    rc, out = run_cmd(f"smartctl -a {device}")
    if rc == 0:
        lines = out.splitlines()

        # Check for NVMe self-test status format first
        if "nvme" in device:
            for line in lines:
                if "Self-test status:" in line:
                    # NVMe format: "Self-test status: Short self-test in progress (24% completed)"
                    if "No self-test in progress" in line:
                        # No active test, check the log for most recent result
                        break
                    elif "in progress" in line:
                        # Extract percentage if available
                        progress_match = re.search(r'\((\d+)%\s+completed\)', line)
                        if progress_match:
                            return f"{progress_match.group(1)}%"
                        else:
                            return "running"
                    elif "Completed without error" in line:
                        return "completed"
                    elif "aborted" in line.lower():
                        return "aborted"
                    elif "error" in line.lower() or "fail" in line.lower():
                        return "error"
                    elif "No self-tests have been logged" in line:
                        return "never run"

            # If no active test found for NVMe, check the Self-test Log for completed tests
            for line in lines:
                if "Self-test Log" in line:
                    # Found the log section, look for the most recent test result (Num 0)
                    for j, log_line in enumerate(lines[lines.index(line):], start=lines.index(line)):
                        if re.search(r'^\s*0\s+', log_line.strip()):  # Most recent test entry
                            if "Completed without error" in log_line:
                                return "completed"
                            elif "Aborted" in log_line:
                                return "aborted"
                            elif "error" in log_line.lower() or "fail" in log_line.lower():
                                return "error"
                            break
                    break

            # If no tests found in NVMe log, return never run
            return "never run"

        # Look for SATA current test execution status
        for i, line in enumerate(lines):
            if "Self-test execution status:" in line and "Self-test routine in progress" in line:
                # Look for percentage in the current line or next few lines
                remaining_match = re.search(r'(\d+)%\s+of\s+test\s+remaining', line)
                if remaining_match:
                    remaining = int(remaining_match.group(1))
                    progress = 100 - remaining
                    return f"{progress}%"

                # Check next few lines for the percentage
                for j in range(i + 1, min(i + 3, len(lines))):
                    next_line = lines[j].strip()
                    remaining_match = re.search(r'(\d+)%\s+of\s+test\s+remaining', next_line)
                    if remaining_match:
                        remaining = int(remaining_match.group(1))
                        progress = 100 - remaining
                        return f"{progress}%"

                return "running"

    # Check completed test results in self-test log
    rc, out = run_cmd(f"smartctl -l selftest {device}")
    if rc != 0:
        return "unknown"

    lines = out.splitlines()
    for line in lines:
        # Look for test result lines in the self-test log (most recent first)
        if re.search(r'#\s*1\s+', line):
            # Parse the most recent test entry
            if "Completed without error" in line:
                return "completed"
            elif "Aborted by host" in line:
                return "aborted"
            elif "error" in line.lower() or "failed" in line.lower():
                return "error"
            else:
                # Other completed status
                return "unknown"

    # No test entries found
    return "never run"

def check_btrfs_errors(device):
    """Check btrfs filesystem health"""
    # Try device stats first - this is the most reliable way to check if btrfs is mounted
    rc, out = run_cmd(f"btrfs device stats {device}")

    if rc == 0:
        # Device is mounted - parse device stats output
        error_count = 0
        for line in out.splitlines():
            if re.search(r'\.(read_io_errs|write_io_errs|flush_io_errs|corruption_errs|generation_errs)\s+\d+', line):
                # Extract the error count
                m = re.search(r'\s+(\d+)$', line)
                if m and int(m.group(1)) > 0:
                    error_count += int(m.group(1))

        scrub_status, scrub_errors = check_btrfs_scrub_status(device)

        if error_count == 0:
            return "No errors", "-", scrub_status, scrub_errors
        else:
            return f"btrfs errors: {error_count}", str(error_count), scrub_status, scrub_errors

    elif "is not a mounted btrfs device" in out or "not a mounted btrfs" in out:
        # Device is not mounted - use readonly check
        rc2, out2 = run_cmd(f"btrfs check --readonly {device}")
        if rc2 != 0:
            if "no valid btrfs" in out2.lower():
                return "not-btrfs", "-", "", ""
            else:
                return "btrfs-check-fail", "?", "", ""

        # Parse check output for errors
        if "no error found" in out2.lower() or "found 0 errors" in out2:
            return "No errors", "-", "unmounted", ""
        elif "error" in out2.lower() or "corruption" in out2.lower():
            return "btrfs check errors", "!", "unmounted", ""
        else:
            return "btrfs check unclear", "?", "unmounted", ""

    else:
        # Some other error with device stats
        return "btrfs-stats-fail", "?", "unknown", ""

def gather():
    devs, err = list_devices()
    rows = []
    if err:
        return rows, err

    # Get btrfs partitions
    btrfs_parts, btrfs_err = get_btrfs_partitions()
    if btrfs_err:
        rows.append({"device": "btrfs-scan-fail", "partition": "", "size": "", "type": "btrfs", "test": "", "errors": btrfs_err[:60], "crit": "?", "scrub": "", "scrub_errors": ""})

    # Group partitions by device
    device_partitions = {}
    for partition in btrfs_parts:
        # Extract device name (e.g., /dev/sda from /dev/sda5)
        for d in devs:
            if partition.startswith(d):
                if d not in device_partitions:
                    device_partitions[d] = []
                device_partitions[d].append(partition)
                break

    # Process each device
    for d in devs:
        row = {"device": d, "partition": "", "size": "", "type": "", "test": "", "errors": "Unknown", "crit": "-", "scrub": "", "scrub_errors": ""}
        row["size"] = get_device_size(d)
        if "nvme" in d:
            row["type"] = "nvme"
            row["test"] = get_smart_test_status(d)
            crit, raw = nvme_critical(d)
            if crit is None:
                row["errors"] = "nvme-read-fail"
                row["crit"] = "?"
            else:
                row["crit"] = str(crit)
                row["errors"] = "No errors" if crit == 0 else f"critical_warning={crit}"
        else:
            row["type"] = "disk"
            row["test"] = get_smart_test_status(d)
            has_err, summary = smart_errors(d)
            if has_err is None:
                row["errors"] = "smartctl-fail"
            elif has_err is False:
                row["errors"] = "No errors"
            else:
                row["errors"] = ("Errors: " + (summary if isinstance(summary, str) else str(summary)))[:60]
        rows.append(row)

        # Add btrfs partitions for this device
        if d in device_partitions:
            for partition in device_partitions[d]:
                # Check btrfs-specific errors and scrub status
                btrfs_errors, btrfs_crit, scrub_status, scrub_error_summary = check_btrfs_errors(partition)
                btrfs_row = {
                    "device": "",  # Empty device column for partitions
                    "partition": partition,
                    "size": get_device_size(partition),
                    "type": "btrfs",
                    "test": "",  # No SMART test for partitions
                    "errors": btrfs_errors,
                    "crit": btrfs_crit,
                    "scrub": scrub_status,
                    "scrub_errors": scrub_error_summary
                }
                rows.append(btrfs_row)

    return rows, None

def init_colors_safe():
    """Return tuple (ok, green_attr, red_attr, hdr_attr). Do not raise."""
    try:
        if not curses.has_colors():
            return False, 0, 0, 0
        curses.start_color()
    except Exception:
        return False, 0, 0, 0

    # try use_default_colors, but don't fail if not present
    bg = None
    try:
        curses.use_default_colors()
        bg = -1
    except Exception:
        bg = curses.COLOR_BLACK

    try:
        # Try different bg values if -1 fails
        for candidate_bg in (bg, curses.COLOR_BLACK):
            try:
                curses.init_pair(1, curses.COLOR_GREEN, candidate_bg)
                curses.init_pair(2, curses.COLOR_RED, candidate_bg)
                curses.init_pair(3, curses.COLOR_CYAN, candidate_bg)
                curses.init_pair(4, curses.COLOR_YELLOW, candidate_bg)
                # success
                return True, curses.color_pair(1), curses.color_pair(2), curses.color_pair(3) | curses.A_BOLD, curses.color_pair(4)
            except Exception:
                # try next candidate
                continue
    except Exception:
        pass
    return False, 0, 0, 0, 0

def safe_addnstr(win, y, x, s, n=None, attr=0):
    """Wrap addnstr to ignore curses errors (like writing outside)."""
    try:
        if n is None:
            win.addstr(y, x, s, attr)
        else:
            win.addnstr(y, x, s, n, attr)
    except Exception:
        try:
            # try without attr
            if n is None:
                win.addstr(y, x, s)
            else:
                win.addnstr(y, x, s, n)
        except Exception:
            pass

def draw(stdscr, rows, cursor_row=0, info=None):
    curses.curs_set(0)
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    color_ok, green, red, hdr, yellow = init_colors_safe()
    header = ["DEVICE", "PARTITION", "SIZE", "TYPE", "TEST", "ERRORS", "CRIT_WARN", "SCRUB", "SCRUB_ERRORS"]
    # compute widths safely
    max_err = max((len(r["errors"]) for r in rows), default=10)
    max_dev = max((len(r.get("device", "")) for r in rows), default=10)
    max_part = max((len(r.get("partition", "")) for r in rows), default=10)
    max_size = max((len(r.get("size", "")) for r in rows), default=6)
    max_test = max((len(r.get("test", "")) for r in rows), default=8)
    max_scrub = max((len(r.get("scrub", "")) for r in rows), default=8)
    max_scrub_err = max((len(r.get("scrub_errors", "")) for r in rows), default=12)
    col_w = [max(8, min(16, max_dev)),
             max(8, min(16, max_part)),
             max(6, min(8, max_size)),
             5,
             max(6, min(10, max_test)),
             max(8, min(12, max_err)),
             7,
             max(6, min(16, max_scrub)),
             max(10, min(14, max_scrub_err))]
    x = 0
    for i, htxt in enumerate(header):
        safe_addnstr(stdscr, 0, x, htxt[:col_w[i]].ljust(col_w[i]), col_w[i], hdr)
        x += col_w[i] + 1
    for idx, r in enumerate(rows, start=1):
        if idx >= h - 2:
            break
        x = 0
        ok = (r["errors"] == "No errors" and (r["crit"] in ("-", "0")))
        color = green if ok and color_ok else (red if not ok and color_ok else 0)

        # Add cursor highlight
        is_cursor = (idx - 1 == cursor_row)  # idx-1 because rows start at 1
        cursor_attr = curses.A_REVERSE if is_cursor else 0

        safe_addnstr(stdscr, idx, x, r.get("device", "")[:col_w[0]].ljust(col_w[0]), col_w[0], cursor_attr)
        x += col_w[0] + 1
        safe_addnstr(stdscr, idx, x, r.get("partition", "")[:col_w[1]].ljust(col_w[1]), col_w[1], cursor_attr)
        x += col_w[1] + 1
        safe_addnstr(stdscr, idx, x, r.get("size", "")[:col_w[2]].rjust(col_w[2]), col_w[2], cursor_attr)
        x += col_w[2] + 1
        safe_addnstr(stdscr, idx, x, r["type"][:col_w[3]].ljust(col_w[3]), col_w[3], cursor_attr)
        x += col_w[3] + 1
        # Color test status
        test_text = r.get("test", "")
        test_color = 0
        if color_ok and test_text:
            if "completed" in test_text.lower():
                test_color = green
            elif "aborted" in test_text.lower():
                test_color = yellow
            elif test_text.endswith("%"):
                test_color = yellow
            elif "error" in test_text.lower():
                test_color = red
        safe_addnstr(stdscr, idx, x, test_text[:col_w[4]].ljust(col_w[4]), col_w[4], test_color | cursor_attr)
        x += col_w[4] + 1
        safe_addnstr(stdscr, idx, x, r["errors"][:col_w[5]].ljust(col_w[5]), col_w[5], color | cursor_attr)
        x += col_w[5] + 1
        safe_addnstr(stdscr, idx, x, r["crit"][:col_w[6]].rjust(col_w[6]), col_w[6], color | cursor_attr)
        x += col_w[6] + 1
        # Color scrub status (running = yellow, idle = normal)
        scrub_text = r.get("scrub", "")
        scrub_color = 0
        if color_ok and "running" in scrub_text.lower():
            scrub_color = yellow
        safe_addnstr(stdscr, idx, x, scrub_text[:col_w[7]].ljust(col_w[7]), col_w[7], scrub_color | cursor_attr)
        x += col_w[7] + 1
        # Color scrub errors (no errors = green, errors = red)
        scrub_err_text = r.get("scrub_errors", "")
        scrub_err_color = 0
        if color_ok and scrub_err_text:
            if "no errors" in scrub_err_text.lower():
                scrub_err_color = green
            elif "error" in scrub_err_text.lower() and scrub_err_text not in ("", "running", "never run"):
                scrub_err_color = red
        safe_addnstr(stdscr, idx, x, scrub_err_text[:col_w[8]].ljust(col_w[8]), col_w[8], scrub_err_color | cursor_attr)
    footer = "q:quit  r:refresh  ↑↓:navigate  s:scrub  t:test"
    hostname = socket.gethostname()

    if info:
        # ensure footer fits width with hostname on right
        info_text = f"  INFO: {info}"
        available_space = w - len(footer) - len(hostname) - 4  # 4 for spacing
        if available_space > 0:
            info_text = info_text[:available_space]
            footer_line = f"{footer}{info_text}".ljust(w - len(hostname) - 2) + f" {hostname}"
        else:
            footer_line = footer.ljust(w - len(hostname) - 2) + f" {hostname}"
        safe_addnstr(stdscr, h - 1, 0, footer_line[:w], w, curses.A_REVERSE)
    else:
        footer_line = footer.ljust(w - len(hostname) - 2) + f" {hostname}"
        safe_addnstr(stdscr, h - 1, 0, footer_line[:w], w, curses.A_REVERSE)
    stdscr.refresh()

@click.command()
@click.option("--interval", "-i", default=0, help="Auto-refresh interval seconds (0 = manual).")
def main(interval):
    """TUI for smartctl / nvme smart-log"""
    def loop(stdscr):
        stdscr.nodelay(True)
        rows, err = gather()
        cursor_row = 0
        draw(stdscr, rows, cursor_row, err)
        last_refresh = time.time()
        last_user_action = time.time()
        AUTO_REFRESH_INTERVAL = 5  # Auto-refresh every 5 seconds

        while True:
            try:
                k = stdscr.getch()
            except KeyboardInterrupt:
                break

            current_time = time.time()

            if k == ord('q'):
                break
            elif k == curses.KEY_UP and cursor_row > 0:
                cursor_row -= 1
                draw(stdscr, rows, cursor_row, err)
                last_user_action = current_time
            elif k == curses.KEY_DOWN and cursor_row < len(rows) - 1:
                cursor_row += 1
                draw(stdscr, rows, cursor_row, err)
                last_user_action = current_time
            elif k == ord('s') and 0 <= cursor_row < len(rows):
                # Start scrub on selected btrfs partition
                selected_row = rows[cursor_row]
                if selected_row["type"] == "btrfs" and selected_row.get("partition"):
                    partition = selected_row["partition"]
                    result = start_btrfs_scrub(partition)
                    draw(stdscr, rows, cursor_row, f"Scrub on {partition}: {result}")
                    # Refresh data to update scrub status
                    time.sleep(1)  # Give scrub time to start
                    rows, err = gather()
                    cursor_row = min(cursor_row, len(rows) - 1) if rows else 0
                    draw(stdscr, rows, cursor_row, f"Scrub on {partition}: {result}")
                else:
                    device_name = selected_row.get('device', '') or selected_row.get('partition', '')
                    draw(stdscr, rows, cursor_row, f"Scrub only works on btrfs partitions (selected: {device_name})")
                last_user_action = current_time
            elif k == ord('t') and 0 <= cursor_row < len(rows):
                # Start SMART test on selected disk device
                selected_row = rows[cursor_row]
                if selected_row.get("device") and selected_row["type"] in ("disk", "nvme"):
                    device = selected_row["device"]
                    result = start_smart_test(device)
                    draw(stdscr, rows, cursor_row, f"SMART test on {device}: {result}")
                    # Refresh data to update test status
                    time.sleep(1)  # Give test time to start
                    rows, err = gather()
                    cursor_row = min(cursor_row, len(rows) - 1) if rows else 0
                    draw(stdscr, rows, cursor_row, f"SMART test on {device}: {result}")
                else:
                    device_name = selected_row.get('device', '') or selected_row.get('partition', '')
                    draw(stdscr, rows, cursor_row, f"SMART test only works on disk devices (selected: {device_name})")
                last_user_action = current_time
            elif k == ord('r') or (interval and (current_time - last_refresh) >= interval):
                rows, err = gather()
                # Keep cursor in bounds after refresh
                cursor_row = min(cursor_row, len(rows) - 1) if rows else 0
                draw(stdscr, rows, cursor_row, err)
                last_refresh = current_time
                last_user_action = current_time

            # Auto-refresh every 5 seconds (only if no user action in last 2 seconds)
            elif (current_time - last_refresh) >= AUTO_REFRESH_INTERVAL and (current_time - last_user_action) >= 2:
                rows, err = gather()
                cursor_row = min(cursor_row, len(rows) - 1) if rows else 0
                draw(stdscr, rows, cursor_row, err)
                last_refresh = current_time

            time.sleep(0.1)
    curses.wrapper(loop)

if __name__ == "__main__":
    main()
