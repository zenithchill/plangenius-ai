"""
Thread-safe local JSON storage module for PlanGenius AI.
Manages persistent event data in data/events.json.
"""

import json
import os
import threading
import copy
from sample_data import SAMPLE_EVENTS

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "events.json")
_lock = threading.Lock()


def _ensure_data_file():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_EVENTS, f, indent=2, ensure_ascii=False)


def get_all_events():
    _ensure_data_file()
    with _lock:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading {DATA_FILE}: {e}")
            return copy.deepcopy(SAMPLE_EVENTS)


def get_event(event_id):
    events = get_all_events()
    for ev in events:
        if ev.get("id") == event_id:
            return ev
    return None


def save_event(event_data):
    """Save or update an event."""
    _ensure_data_file()
    event_id = event_data.get("id")
    if not event_id:
        import uuid
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        event_data["id"] = event_id

    with _lock:
        events = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    events = json.load(f)
            except Exception:
                events = []

        found = False
        for idx, ev in enumerate(events):
            if ev.get("id") == event_id:
                events[idx] = event_data
                found = True
                break
        if not found:
            events.insert(0, event_data)

        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)

    return event_data


def delete_event(event_id):
    """Delete an event by ID."""
    _ensure_data_file()
    with _lock:
        events = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    events = json.load(f)
            except Exception:
                events = []

        new_events = [ev for ev in events if ev.get("id") != event_id]
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(new_events, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)
    return True


def reset_to_samples():
    """Reset data/events.json to pristine default sample events."""
    _ensure_data_file()
    with _lock:
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_EVENTS, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)
    return SAMPLE_EVENTS
