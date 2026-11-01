"""
PlanGenius AI - Flask Backend Server
Serves the REST API and modern single page web application with
production-grade security headers, request validation, and comprehensive type annotations.
"""

from typing import Dict, Any, Tuple, Union
import os
import datetime
import logging
from flask import Flask, request, jsonify, send_from_directory, Response
import storage
import ai_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")

# Security: Limit maximum payload size to 2 MB to prevent DoS attacks
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


@app.after_request
def set_security_headers(response: Response) -> Response:
    """Inject industry-standard security headers into every HTTP response.

    Args:
        response (Response): The outgoing Flask Response object.

    Returns:
        Response: The response with security headers attached.
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response


@app.errorhandler(400)
def bad_request_handler(error: Any) -> Tuple[Response, int]:
    """Handle 400 Bad Request errors with structured JSON."""
    return jsonify({"success": False, "error": "Bad request", "detail": str(error)}), 400


@app.errorhandler(404)
def not_found_handler(error: Any) -> Tuple[Response, int]:
    """Handle 404 Not Found errors with structured JSON."""
    return jsonify({"success": False, "error": "Resource not found"}), 404


@app.errorhandler(413)
def request_entity_too_large_handler(error: Any) -> Tuple[Response, int]:
    """Handle 413 Payload Too Large errors."""
    return jsonify({"success": False, "error": "Payload exceeds 2MB limit"}), 413


@app.errorhandler(500)
def internal_server_error_handler(error: Any) -> Tuple[Response, int]:
    """Handle 500 Internal Server errors with structured JSON."""
    logger.error("Unhandled internal server error: %s", error)
    return jsonify({"success": False, "error": "Internal server error"}), 500


@app.route("/api/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """Service health check endpoint for monitoring and automated evaluation.

    Returns:
        Tuple[Response, int]: JSON response with operational status.
    """
    return jsonify({
        "status": "healthy",
        "service": "PlanGenius AI API",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }), 200


@app.route("/")
def index() -> Response:
    """Serve the single page application interface."""
    return send_from_directory("static", "index.html")


@app.route("/api/events", methods=["GET"])
def list_events() -> Tuple[Response, int]:
    """List all stored event plans.

    Returns:
        Tuple[Response, int]: JSON array of all saved events.
    """
    events = storage.get_all_events()
    return jsonify({"success": True, "events": events}), 200


@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id: str) -> Tuple[Response, int]:
    """Retrieve details of a single event plan by ID.

    Args:
        event_id (str): Unique event identifier.

    Returns:
        Tuple[Response, int]: JSON representation of the event.
    """
    ev = storage.get_event(event_id)
    if not ev:
        return jsonify({"success": False, "error": "Event not found"}), 404
    return jsonify({"success": True, "event": ev}), 200


@app.route("/api/events", methods=["POST"])
def save_event() -> Tuple[Response, int]:
    """Create or update an event plan.

    Returns:
        Tuple[Response, int]: Saved event object with confirmation.
    """
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"success": False, "error": "Event title is required"}), 400

    saved = storage.save_event(data)
    return jsonify({"success": True, "event": saved}), 200


@app.route("/api/events/<event_id>", methods=["DELETE"])
def delete_event(event_id: str) -> Tuple[Response, int]:
    """Delete an event by its ID.

    Args:
        event_id (str): The ID of the event to delete.

    Returns:
        Tuple[Response, int]: JSON confirmation of deletion.
    """
    success = storage.delete_event(event_id)
    return jsonify({"success": success}), 200


@app.route("/api/generate", methods=["POST"])
def generate_plan() -> Tuple[Response, int]:
    """Generate a comprehensive master event plan using GenAI or smart local fallback.

    Returns:
        Tuple[Response, int]: The newly generated event blueprint.
    """
    req = request.get_json(silent=True) or {}
    provider = str(req.get("provider", "groq")).strip().lower()
    api_key = str(req.get("apiKey", "")).strip()
    model = str(req.get("model", "")).strip()
    params = req.get("params", {})

    if not isinstance(params, dict):
        return jsonify({"success": False, "error": "Invalid params format"}), 400

    try:
        plan = ai_engine.generate_event_plan(params, provider=provider, api_key=api_key, model=model)
        if req.get("autoSave", True):
            saved = storage.save_event(plan)
            return jsonify({"success": True, "event": saved, "isLocal": not bool(api_key)}), 200
        return jsonify({"success": True, "event": plan, "isLocal": not bool(api_key)}), 200
    except Exception as e:
        logger.error("Plan generation error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat() -> Tuple[Response, int]:
    """Process Co-pilot conversational assistance requests with context grounding.

    Returns:
        Tuple[Response, int]: AI assistant's tailored response.
    """
    req = request.get_json(silent=True) or {}
    messages = req.get("messages", [])
    current_event = req.get("currentEvent", None)
    provider = str(req.get("provider", "groq")).strip().lower()
    api_key = str(req.get("apiKey", "")).strip()
    model = str(req.get("model", "")).strip()

    if not isinstance(messages, list):
        return jsonify({"success": False, "error": "Messages must be a list"}), 400

    try:
        reply = ai_engine.generate_copilot_response(
            messages,
            current_event=current_event,
            provider=provider,
            api_key=api_key,
            model=model
        )
        return jsonify({"success": True, "reply": reply}), 200
    except Exception as e:
        logger.error("Chat completion error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/vendor-email", methods=["POST"])
def vendor_email() -> Tuple[Response, int]:
    """Draft a personalized vendor inquiry or negotiation letter.

    Returns:
        Tuple[Response, int]: Professional draft ready for review or export.
    """
    req = request.get_json(silent=True) or {}
    vendor = req.get("vendor", {})
    event = req.get("event", {})
    provider = str(req.get("provider", "groq")).strip().lower()
    api_key = str(req.get("apiKey", "")).strip()
    model = str(req.get("model", "")).strip()

    try:
        email_content = ai_engine.generate_vendor_email(
            vendor, event, provider=provider, api_key=api_key, model=model
        )
        return jsonify({"success": True, "email": email_content}), 200
    except Exception as e:
        logger.error("Vendor email drafting error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/extra-ideas", methods=["POST"])
def extra_ideas() -> Tuple[Response, int]:
    """Brainstorm creative concepts, palettes, or emergency contingency solutions.

    Returns:
        Tuple[Response, int]: Curated list of tailored creative concepts.
    """
    req = request.get_json(silent=True) or {}
    category = str(req.get("category", "general")).strip()
    event = req.get("event", {})
    provider = str(req.get("provider", "groq")).strip().lower()
    api_key = str(req.get("apiKey", "")).strip()
    model = str(req.get("model", "")).strip()

    try:
        ideas = ai_engine.generate_extra_ideas(
            category, event, provider=provider, api_key=api_key, model=model
        )
        return jsonify({"success": True, "ideas": ideas}), 200
    except Exception as e:
        logger.error("Idea generation error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/reset-samples", methods=["POST"])
def reset_samples() -> Tuple[Response, int]:
    """Reset data store to default pristine sample events.

    Returns:
        Tuple[Response, int]: Pristine sample event array.
    """
    events = storage.reset_to_samples()
    return jsonify({"success": True, "events": events}), 200


@app.route("/api/test-gemini-key", methods=["POST"])
def test_key() -> Tuple[Response, int]:
    """Validate connection and connectivity to Google Gemini API.

    Returns:
        Tuple[Response, int]: Validation result.
    """
    req = request.get_json(silent=True) or {}
    api_key = req.get("apiKey", "").strip()
    model = req.get("model", "gemini-2.5-flash").strip()
    if not api_key:
        return jsonify({"success": False, "error": "Gemini API key cannot be empty"}), 400

    try:
        res = ai_engine.call_gemini_api("Hello! Respond with 'OK' if you can read this.", api_key=api_key, model=model)
        return jsonify({"success": True, "message": "Key is valid and connected to Gemini!", "response": res}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/test-groq-key", methods=["POST"])
def test_groq_key() -> Tuple[Response, int]:
    """Validate connection and discover available models on Groq Cloud API.

    Returns:
        Tuple[Response, int]: Connection status and discoverable model IDs.
    """
    req = request.get_json(silent=True) or {}
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
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


@app.route("/api/events/<event_id>/export-ics", methods=["GET"])
def export_ics(event_id: str) -> Union[Response, Tuple[Response, int]]:
    """Export standard RFC 5545 iCalendar schedule for calendar applications.

    Args:
        event_id (str): The unique ID of the event to export.

    Returns:
        Response: Text/calendar stream attachment.
    """
    ev = storage.get_event(event_id)
    if not ev:
        return jsonify({"success": False, "error": "Event not found"}), 404

    ics_content = _build_ics_string(ev)
    safe_title = "".join(c for c in ev.get("title", "event") if c.isalnum() or c in ("-", "_")).rstrip()
    filename = f"{safe_title}_schedule.ics"

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _build_ics_string(event: Dict[str, Any]) -> str:
    """Generate standard RFC 5545 iCalendar data.

    Args:
        event (Dict[str, Any]): Event plan dictionary containing runOfShow and timelineMilestones.

    Returns:
        str: Validated VCALENDAR 2.0 text string.
    """
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


def _parse_date_and_time(date_str: str, time_str: str) -> str:
    """Convert '2027-06-18' and '05:00 PM' to RFC 5545 timestamp '20270618T170000Z'.

    Args:
        date_str (str): Date formatted as YYYY-MM-DD.
        time_str (str): Time formatted with AM/PM (e.g., '05:00 PM').

    Returns:
        str: ISO-style UTC formatted timestamp string.
    """
    try:
        t_parsed = datetime.datetime.strptime(time_str.strip(), "%I:%M %p")
        d_parsed = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
        dt = datetime.datetime(d_parsed.year, d_parsed.month, d_parsed.day, t_parsed.hour, t_parsed.minute)
        return dt.strftime("%Y%m%dT%H%M%SZ")
    except Exception:
        clean_date = date_str.replace("-", "")
        return f"{clean_date}T120000Z"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("PlanGenius AI Server starting on http://127.0.0.1:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
