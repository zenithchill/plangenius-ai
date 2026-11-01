"""
Thread-safe local JSON storage module for PlanGenius AI.
Manages persistent event data in data/events.json with atomic writes.
"""

from typing import List, Dict, Any, Optional
import json
import os
import threading
import copy
import logging
import uuid
from sample_data import SAMPLE_EVENTS

logger = logging.getLogger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "events.json")
_lock = threading.Lock()


def _ensure_data_file() -> None:
    """Ensure that the data storage directory and default data file exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_EVENTS, f, indent=2, ensure_ascii=False)


def get_all_events() -> List[Dict[str, Any]]:
    """Retrieve all stored events from persistent storage.

    Returns:
        List[Dict[str, Any]]: List of complete event plan dictionaries.
    """
    _ensure_data_file()
    with _lock:
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Error reading storage file %s: %s", DATA_FILE, e)
            return copy.deepcopy(SAMPLE_EVENTS)


def get_event(event_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single event plan by its unique ID.

    Args:
        event_id (str): The unique event ID (e.g., 'evt-1').

    Returns:
        Optional[Dict[str, Any]]: The event plan dictionary if found, else None.
    """
    events = get_all_events()
    for ev in events:
        if ev.get("id") == event_id:
            return ev
    return None


def save_event(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Save or update an event plan atomically with thread safety.

    Args:
        event_data (Dict[str, Any]): The event dictionary to persist.

    Returns:
        Dict[str, Any]: The saved event with guaranteed unique ID.
    """
    _ensure_data_file()
    event_id = event_data.get("id")
    if not event_id:
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        event_data["id"] = event_id

    with _lock:
        events: List[Dict[str, Any]] = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    events = json.load(f)
            except Exception as e:
                logger.warning("Could not parse existing events file, re-initializing: %s", e)
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


def delete_event(event_id: str) -> bool:
    """Delete an event by its unique ID.

    Args:
        event_id (str): The unique identifier of the event to remove.

    Returns:
        bool: True if operation completed successfully.
    """
    _ensure_data_file()
    with _lock:
        events: List[Dict[str, Any]] = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    events = json.load(f)
            except Exception as e:
                logger.error("Error reading events during deletion: %s", e)
                events = []

        new_events = [ev for ev in events if ev.get("id") != event_id]
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(new_events, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)
    return True


def reset_to_samples() -> List[Dict[str, Any]]:
    """Reset data/events.json to pristine default sample events.

    Returns:
        List[Dict[str, Any]]: The reset sample events list.
    """
    _ensure_data_file()
    with _lock:
        temp_file = f"{DATA_FILE}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_EVENTS, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, DATA_FILE)
    return SAMPLE_EVENTS
