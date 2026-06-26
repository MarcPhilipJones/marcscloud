"""Visualize FP300 occupancy history from Home Assistant."""
import json
import os
import sys
from datetime import datetime, timedelta, timezone

# Try fetching fresh data via REST API
import urllib.request

BASE_URL = "http://192.168.0.111:8123"
TOKEN = os.environ.get("HA_TOKEN", "")
ENTITY = "binary_sensor.presence_multi_sensor_fp300_occupancy"

def fetch_history():
    start = (datetime.now(timezone.utc) - timedelta(days=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
    end = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{BASE_URL}/api/history/period/{start}?end_time={end}&filter_entity_id={ENTITY}&no_attributes"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    })
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def parse_records(data):
    records = data[0]
    events = []
    for r in records:
        ts = r["last_changed"]
        # Parse ISO format
        if "+" in ts:
            dt = datetime.fromisoformat(ts)
        else:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        state = r["state"]
        events.append((dt, state))
    return events

def analyze(events):
    print(f"\n{'='*60}")
    print(f"  FP300 Occupancy Summary")
    print(f"{'='*60}")
    print(f"  Data range: {events[0][0].strftime('%Y-%m-%d %H:%M')} → {events[-1][0].strftime('%Y-%m-%d %H:%M')}")
    print(f"  Total state changes: {len(events)}")

    # Calculate occupied/unoccupied durations
    total_occupied = timedelta()
    total_unoccupied = timedelta()
    daily_occupied = {}
    daily_sessions = {}

    for i in range(len(events) - 1):
        dt, state = events[i]
        next_dt = events[i + 1][0]
        duration = next_dt - dt
        day = dt.strftime("%Y-%m-%d")

        if state == "on":
            total_occupied += duration
            daily_occupied[day] = daily_occupied.get(day, timedelta()) + duration
            daily_sessions[day] = daily_sessions.get(day, 0) + 1
        else:
            total_unoccupied += duration

    # Handle last event to now
    last_dt, last_state = events[-1]
    now = datetime.now(timezone.utc)
    remaining = now - last_dt
    if last_state == "on":
        total_occupied += remaining
        day = last_dt.strftime("%Y-%m-%d")
        daily_occupied[day] = daily_occupied.get(day, timedelta()) + remaining
        daily_sessions[day] = daily_sessions.get(day, 0) + 1

    total = total_occupied + total_unoccupied
    occ_pct = (total_occupied.total_seconds() / total.total_seconds() * 100) if total.total_seconds() > 0 else 0

    print(f"\n  Total occupied:   {format_duration(total_occupied)} ({occ_pct:.1f}%)")
    print(f"  Total unoccupied: {format_duration(total_unoccupied)} ({100-occ_pct:.1f}%)")

    # Daily breakdown
    print(f"\n{'='*60}")
    print(f"  Daily Occupancy Breakdown")
    print(f"{'='*60}")
    print(f"  {'Date':<12} {'Occupied':<12} {'Sessions':<10} {'Timeline (00:00 → 24:00)'}")
    print(f"  {'─'*12} {'─'*12} {'─'*10} {'─'*48}")

    all_days = sorted(set(e[0].strftime("%Y-%m-%d") for e in events))
    for day in all_days:
        occ = daily_occupied.get(day, timedelta())
        sess = daily_sessions.get(day, 0)
        hours = occ.total_seconds() / 3600
        timeline = build_timeline(events, day)
        print(f"  {day:<12} {hours:>5.1f}h       {sess:>3}       {timeline}")

    # Hourly heatmap
    print(f"\n{'='*60}")
    print(f"  Hourly Occupancy Heatmap")
    print(f"{'='*60}")
    print_heatmap(events, all_days)

    # Session details
    print(f"\n{'='*60}")
    print(f"  Occupancy Sessions (on→off)")
    print(f"{'='*60}")
    print(f"  {'Start':<20} {'End':<20} {'Duration'}")
    print(f"  {'─'*20} {'─'*20} {'─'*12}")
    session_start = None
    for dt, state in events:
        if state == "on":
            session_start = dt
        elif state == "off" and session_start:
            dur = dt - session_start
            print(f"  {session_start.strftime('%m-%d %H:%M'):<20} {dt.strftime('%m-%d %H:%M'):<20} {format_duration(dur)}")
            session_start = None
    if session_start:
        print(f"  {session_start.strftime('%m-%d %H:%M'):<20} {'(ongoing)':<20} {format_duration(now - session_start)}")

def build_timeline(events, day):
    """Build a 48-char timeline bar for a day (each char = 30 min)."""
    bar = [' '] * 48
    day_events = [(dt, s) for dt, s in events if dt.strftime("%Y-%m-%d") == day]

    # Determine initial state at midnight
    day_start = datetime.fromisoformat(f"{day}T00:00:00+00:00")
    initial_state = "off"
    all_before = [(dt, s) for dt, s in events if dt < day_start]
    if all_before:
        initial_state = all_before[-1][1]

    # Fill the bar
    for slot in range(48):
        slot_start = day_start + timedelta(minutes=slot * 30)
        slot_end = slot_start + timedelta(minutes=30)

        # Find state at this slot
        state = initial_state
        for dt, s in events:
            if dt <= slot_start:
                state = s
            elif dt < slot_end:
                # Transition within slot
                if s == "on":
                    state = "on"
                break

        if state == "on":
            bar[slot] = '█'
        else:
            bar[slot] = '░'

    return ''.join(bar)

def print_heatmap(events, all_days):
    """Print hourly occupancy percentage across all days."""
    hourly_counts = {h: 0 for h in range(24)}
    hourly_total = {h: 0 for h in range(24)}

    for day in all_days:
        day_start = datetime.fromisoformat(f"{day}T00:00:00+00:00")
        for hour in range(24):
            hour_start = day_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)

            # Check if occupied during this hour
            state = "off"
            occupied_seconds = 0
            prev_dt = hour_start
            for dt, s in events:
                if dt <= hour_start:
                    state = s
                elif dt < hour_end:
                    if state == "on":
                        occupied_seconds += (dt - prev_dt).total_seconds()
                    state = s
                    prev_dt = dt
                elif dt >= hour_end:
                    break
            if state == "on":
                occupied_seconds += (hour_end - prev_dt).total_seconds()

            if occupied_seconds > 0:
                hourly_counts[hour] += occupied_seconds / 3600
            hourly_total[hour] += 1

    print(f"\n  Hour  Avg Occ%  Bar")
    print(f"  ────  ────────  {'─'*40}")
    for h in range(24):
        if hourly_total[h] > 0:
            avg = (hourly_counts[h] / hourly_total[h]) * 100
        else:
            avg = 0
        bar_len = int(avg / 2.5)
        bar = '█' * bar_len + '░' * (40 - bar_len)
        print(f"  {h:02d}:00  {avg:5.1f}%    {bar}")

def format_duration(td):
    total_sec = int(td.total_seconds())
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    if hours > 0:
        return f"{hours}h {minutes}m"
    return f"{minutes}m"

if __name__ == "__main__":
    print("Fetching FP300 occupancy history from Home Assistant...")
    try:
        data = fetch_history()
    except Exception as e:
        print(f"API fetch failed: {e}")
        # Fallback to saved file
        path = os.path.join(os.path.dirname(__file__), "..", "logs", "fp300_history.json")
        data = json.load(open(path))

    events = parse_records(data)
    if not events:
        print("No occupancy data found!")
        sys.exit(1)

    analyze(events)
