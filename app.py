"""
PlanGenius AI - Flask Backend Server
Serves the REST API and modern single page web application.
"""

import os
import json
import datetime
from flask import Flask, request, jsonify, send_from_directory, Response
import storage
import ai_engine

app = Flask(__name__, static_folder="static", static_url_path="")


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/events", methods=["GET"])
def list_events():
    events = storage.get_all_events()
    # Return light summary list or full list
    return jsonify({"success": True, "events": events})


@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id):
    ev = storage.get_event(event_id)
    if not ev:
        return jsonify({"success": False, "error": "Event not found"}), 404
    return jsonify({"success": True, "event": ev})


@app.route("/api/events", methods=["POST"])
def save_event():
    data = request.get_json() or {}
    if not data.get("title"):
        return jsonify({"success": False, "error": "Event title is required"}), 400
    saved = storage.save_event(data)
    return jsonify({"success": True, "event": saved})


@app.route("/api/events/<event_id>", methods=["DELETE"])
def delete_event(event_id):
    success = storage.delete_event(event_id)
    return jsonify({"success": success})


@app.route("/api/generate", methods=["POST"])
def generate_plan():
    req = request.get_json() or {}
    provider = req.get("provider", "groq")
    api_key = req.get("apiKey", "")
    model = req.get("model", "")
    params = req.get("params", {})

    try:
        plan = ai_engine.generate_event_plan(params, provider=provider, api_key=api_key, model=model)
        # Optionally auto-save
        if req.get("autoSave", True):
            saved = storage.save_event(plan)
            return jsonify({"success": True, "event": saved, "isLocal": not bool(api_key)})
        return jsonify({"success": True, "event": plan, "isLocal": not bool(api_key)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat():
    req = request.get_json() or {}
    messages = req.get("messages", [])
    current_event = req.get("currentEvent", None)
    provider = req.get("provider", "groq")
    api_key = req.get("apiKey", "")
    model = req.get("model", "")

    try:
        reply = ai_engine.generate_copilot_response(messages, current_event=current_event, provider=provider, api_key=api_key, model=model)
        return jsonify({"success": True, "reply": reply})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vendor-email", methods=["POST"])
def vendor_email():
    req = request.get_json() or {}
    vendor = req.get("vendor", {})
    event = req.get("event", {})
    provider = req.get("provider", "groq")
    api_key = req.get("apiKey", "")
    model = req.get("model", "")

    try:
        email_content = ai_engine.generate_vendor_email(vendor, event, provider=provider, api_key=api_key, model=model)
        return jsonify({"success": True, "email": email_content})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/extra-ideas", methods=["POST"])
def extra_ideas():
    req = request.get_json() or {}
    category = req.get("category", "general")
    event = req.get("event", {})
    provider = req.get("provider", "groq")
    api_key = req.get("apiKey", "")
    model = req.get("model", "")

    try:
        ideas = ai_engine.generate_extra_ideas(category, event, provider=provider, api_key=api_key, model=model)
        return jsonify({"success": True, "ideas": ideas})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reset-samples", methods=["POST"])
def reset_samples():
    events = storage.reset_to_samples()
    return jsonify({"success": True, "events": events})


@app.route("/api/test-gemini-key", methods=["POST"])
def test_key():
    req = request.get_json() or {}
    api_key = req.get("apiKey", "").strip()
    model = req.get("model", "gemini-2.5-flash").strip()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key cannot be empty"}), 400

    try:
        res = ai_engine.call_gemini_api("Hello! Respond with 'OK' if you can read this.", api_key=api_key, model=model)
        return jsonify({"success": True, "message": "Key is valid and connected to Gemini!", "response": res})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/test-groq-key", methods=["POST"])
def test_groq_key():
    req = request.get_json() or {}
    api_key = req.get("apiKey", "").strip()
    model = req.get("model", "qwen/qwen3.8-27b").strip()
    if not api_key:
        return jsonify({"success": False, "error": "Groq API key cannot be empty"}), 400

    try:
        models = ai_engine.get_groq_models(api_key)
        if models and model not in models:
            model = models[0]
        res = ai_engine.call_groq_api("Hello! Respond with 'OK' if you can read this.", api_key=api_key, model=model)
        return jsonify({
            "success": True,
            "message": f"Connected to Groq using {model}!",
            "models": models,
            "response": res
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/events/<event_id>/export-ics", methods=["GET"])
def export_ics(event_id):
    ev = storage.get_event(event_id)
    if not ev:
        return "Event not found", 404

    ics_content = _build_ics_string(ev)
    safe_title = "".join(c for c in ev.get("title", "event") if c.isalnum() or c in ("-", "_")).rstrip()
    filename = f"{safe_title}_schedule.ics"

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _build_ics_string(event):
    """Generate standard RFC 5545 iCalendar data."""
    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    event_date_str = event.get("date", datetime.date.today().strftime("%Y-%m-%d"))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//PlanGenius AI//Event Master Schedule//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{event.get('title', 'Event Plan')}",
        "X-WR-TIMEZONE:UTC"
    ]

    # Add run of show items
    run_of_show = event.get("runOfShow", [])
    for idx, item in enumerate(run_of_show):
        time_text = item.get("time", "")
        # Try to parse time e.g. "05:00 PM"
        dt_start_str = _parse_date_and_time(event_date_str, time_text)

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:ros-{event.get('id')}-{idx}-{now_str}",
            f"DTSTAMP:{now_str}",
            f"DTSTART:{dt_start_str}",
            f"SUMMARY:{item.get('activity', 'Scheduled Item')}",
            f"DESCRIPTION:Lead: {item.get('responsible', 'Lead')} | Event: {event.get('title')}",
            f"LOCATION:{item.get('location', event.get('location', ''))}",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ])

    # Add milestone due dates as reminder events
    milestones = event.get("timelineMilestones", [])
    for idx, m in enumerate(milestones):
        due = m.get("dueDate", event_date_str).replace("-", "")
        lines.extend([
            "BEGIN:VEVENT",
            f"UID:mile-{event.get('id')}-{idx}-{now_str}",
            f"DTSTAMP:{now_str}",
            f"DTSTART;VALUE=DATE:{due}",
            f"SUMMARY:[Milestone] {m.get('task', 'Task')}",
            f"DESCRIPTION:Phase: {m.get('phase', 'Timeline')} | Event: {event.get('title')}",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def _parse_date_and_time(date_str, time_str):
    """Convert '2027-06-18' and '05:00 PM' to '20270618T170000Z'"""
    try:
        t_parsed = datetime.datetime.strptime(time_str.strip(), "%I:%M %p")
        d_parsed = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
        dt = datetime.datetime(d_parsed.year, d_parsed.month, d_parsed.day, t_parsed.hour, t_parsed.minute)
        return dt.strftime("%Y%m%dT%H%M%SZ")
    except Exception:
        # Fallback to date only
        clean_date = date_str.replace("-", "")
        return f"{clean_date}T120000Z"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"PlanGenius AI Server running at http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
