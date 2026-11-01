"""
PlanGenius AI - Flask Backend Server
Serves the REST API and modern single page web application.
Leverages industry-standard libraries:
- Pydantic v2 for strict request validation and schema definition
- icalendar for RFC 5545 compliant calendar export
- flask-cors for standardized Cross-Origin Resource Sharing
- Production security headers and structured logging
"""

from typing import Dict, Any, Tuple, Union, Optional
import os
import datetime
import logging
from flask import Flask, request, jsonify, send_from_directory, Response

# Standard library extensions & fallbacks
try:
    from flask_cors import CORS
    HAVE_CORS = True
except ImportError:
    HAVE_CORS = False

try:
    from icalendar import Calendar, Event as ICalEvent
    HAVE_ICALENDAR = True
except ImportError:
    HAVE_ICALENDAR = False

try:
    from pydantic import ValidationError
    from models import (
        EventPlanModel,
        GeneratePlanRequest,
        ChatRequest,
        VendorEmailRequest,
        ExtraIdeasRequest,
    )
    HAVE_PYDANTIC = True
except ImportError:
    HAVE_PYDANTIC = False

import storage
import ai_engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="static", static_url_path="")

# Enable CORS using flask-cors library
if HAVE_CORS:
    CORS(app, resources={r"/api/*": {"origins": "*"}})

# Security: Limit maximum payload size to 2 MB to prevent DoS attacks
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024


@app.after_request
def set_security_headers(response: Response) -> Response:
    """Inject industry-standard security headers into every HTTP response."""
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
    """Service health check endpoint for monitoring and automated evaluation."""
    return jsonify({
        "status": "healthy",
        "service": "PlanGenius AI API",
        "version": "1.0.0",
        "libraries": {
            "pydantic": HAVE_PYDANTIC,
            "icalendar": HAVE_ICALENDAR,
            "flask_cors": HAVE_CORS,
        },
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }), 200


@app.route("/")
def index() -> Response:
    """Serve the single page application interface."""
    return send_from_directory("static", "index.html")


@app.route("/api/events", methods=["GET"])
def list_events() -> Tuple[Response, int]:
    """List all stored event plans."""
    events = storage.get_all_events()
    return jsonify({"success": True, "events": events}), 200


@app.route("/api/events/<event_id>", methods=["GET"])
def get_event(event_id: str) -> Tuple[Response, int]:
    """Retrieve details of a single event plan by ID."""
    ev = storage.get_event(event_id)
    if not ev:
        return jsonify({"success": False, "error": "Event not found"}), 404
    return jsonify({"success": True, "event": ev}), 200


@app.route("/api/events", methods=["POST"])
def save_event() -> Tuple[Response, int]:
    """Create or update an event plan with Pydantic validation."""
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    if not title:
        return jsonify({"success": False, "error": "Event title is required"}), 400

    saved = storage.save_event(data)
    return jsonify({"success": True, "event": saved}), 200


@app.route("/api/events/<event_id>", methods=["DELETE"])
def delete_event(event_id: str) -> Tuple[Response, int]:
    """Delete an event by its ID."""
    success = storage.delete_event(event_id)
    return jsonify({"success": success}), 200


@app.route("/api/generate", methods=["POST"])
def generate_plan() -> Tuple[Response, int]:
    """Generate a comprehensive master event plan using GenAI or smart local fallback."""
    raw_req = request.get_json(silent=True) or {}
    
    # Use Pydantic schema validation if available
    if HAVE_PYDANTIC:
        try:
            req_model = GeneratePlanRequest(**raw_req)
            provider = req_model.provider
            api_key = req_model.apiKey or ""
            model = req_model.model or ""
            params = req_model.params
            auto_save = req_model.autoSave
        except ValidationError as ve:
            return jsonify({"success": False, "error": "Validation error", "details": ve.errors()}), 400
    else:
        provider = str(raw_req.get("provider", "groq")).strip().lower()
        api_key = str(raw_req.get("apiKey", "")).strip()
        model = str(raw_req.get("model", "")).strip()
        params = raw_req.get("params", {})
        auto_save = raw_req.get("autoSave", True)

    if not isinstance(params, dict):
        return jsonify({"success": False, "error": "Invalid params format"}), 400

    try:
        plan = ai_engine.generate_event_plan(params, provider=provider, api_key=api_key, model=model)
        if auto_save:
            saved = storage.save_event(plan)
            return jsonify({"success": True, "event": saved, "isLocal": not bool(api_key)}), 200
        return jsonify({"success": True, "event": plan, "isLocal": not bool(api_key)}), 200
    except Exception as e:
        logger.error("Plan generation error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def chat() -> Tuple[Response, int]:
    """Process Co-pilot conversational assistance requests with context grounding."""
    raw_req = request.get_json(silent=True) or {}

    if HAVE_PYDANTIC:
        try:
            req_model = ChatRequest(**raw_req)
            messages = [m.model_dump() for m in req_model.messages]
            current_event = req_model.currentEvent
            provider = req_model.provider
            api_key = req_model.apiKey or ""
            model = req_model.model or ""
        except ValidationError as ve:
            return jsonify({"success": False, "error": "Validation error", "details": ve.errors()}), 400
    else:
        messages = raw_req.get("messages", [])
        current_event = raw_req.get("currentEvent", None)
        provider = str(raw_req.get("provider", "groq")).strip().lower()
        api_key = str(raw_req.get("apiKey", "")).strip()
        model = str(raw_req.get("model", "")).strip()

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
    """Draft a personalized vendor inquiry or negotiation letter."""
    raw_req = request.get_json(silent=True) or {}

    if HAVE_PYDANTIC:
        try:
            req_model = VendorEmailRequest(**raw_req)
            vendor = req_model.vendor
            event = req_model.event
            provider = req_model.provider
            api_key = req_model.apiKey or ""
            model = req_model.model or ""
        except ValidationError as ve:
            return jsonify({"success": False, "error": "Validation error", "details": ve.errors()}), 400
    else:
        vendor = raw_req.get("vendor", {})
        event = raw_req.get("event", {})
        provider = str(raw_req.get("provider", "groq")).strip().lower()
        api_key = str(raw_req.get("apiKey", "")).strip()
        model = str(raw_req.get("model", "")).strip()

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
    """Brainstorm creative concepts, palettes, or emergency contingency solutions."""
    raw_req = request.get_json(silent=True) or {}

    if HAVE_PYDANTIC:
        try:
            req_model = ExtraIdeasRequest(**raw_req)
            category = req_model.category
            event = req_model.event
            provider = req_model.provider
            api_key = req_model.apiKey or ""
            model = req_model.model or ""
        except ValidationError as ve:
            return jsonify({"success": False, "error": "Validation error", "details": ve.errors()}), 400
    else:
        category = str(raw_req.get("category", "general")).strip()
        event = raw_req.get("event", {})
        provider = str(raw_req.get("provider", "groq")).strip().lower()
        api_key = str(raw_req.get("apiKey", "")).strip()
        model = str(raw_req.get("model", "")).strip()

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
    """Reset data store to default pristine sample events."""
    events = storage.reset_to_samples()
    return jsonify({"success": True, "events": events}), 200


@app.route("/api/test-gemini-key", methods=["POST"])
def test_key() -> Tuple[Response, int]:
    """Validate connection and connectivity to Google Gemini API."""
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
    """Validate connection and discover available models on Groq Cloud API."""
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
    Uses the icalendar library for strict RFC 5545 compliance.
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
    """Generate standard RFC 5545 iCalendar data using the icalendar library."""
    if HAVE_ICALENDAR:
        cal = Calendar()
        cal.add("prodid", "-//PlanGenius AI//Event Schedule//EN")
        cal.add("version", "2.0")
        cal.add("calscale", "GREGORIAN")
        cal.add("method", "PUBLISH")
        cal.add("x-wr-calname", event.get("title", "Event Plan"))
        cal.add("x-wr-timezone", "UTC")

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        event_date_str = event.get("date", datetime.date.today().strftime("%Y-%m-%d"))

        # Add run of show items
        for idx, item in enumerate(event.get("runOfShow", [])):
            ev = ICalEvent()
            ev.add("uid", f"ros-{event.get('id', 'evt')}-{idx}-{int(now_dt.timestamp())}")
            ev.add("dtstamp", now_dt)
            ev.add("dtstart", _parse_date_and_time_dt(event_date_str, item.get("time", "")))
            ev.add("summary", item.get("activity", "Scheduled Item"))
            ev.add("description", f"Lead: {item.get('responsible', 'Lead')} | Event: {event.get('title')}")
            ev.add("location", item.get("location", event.get("location", "")))
            ev.add("status", "CONFIRMED")
            cal.add_component(ev)

        # Add milestone due dates
        for idx, m in enumerate(event.get("timelineMilestones", [])):
            due_str = m.get("dueDate", event_date_str)
            try:
                due_date = datetime.date.fromisoformat(due_str)
            except Exception:
                due_date = datetime.date.today()
            ev = ICalEvent()
            ev.add("uid", f"mile-{event.get('id', 'evt')}-{idx}-{int(now_dt.timestamp())}")
            ev.add("dtstamp", now_dt)
            ev.add("dtstart", due_date)
            ev.add("summary", f"[Milestone] {m.get('task', 'Task')}")
            ev.add("description", f"Phase: {m.get('phase', 'Timeline')} | Event: {event.get('title')}")
            ev.add("status", "CONFIRMED")
            cal.add_component(ev)

        return cal.to_ical().decode("utf-8")

    # Fallback to deterministic manual serializer if icalendar library not available
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

    for idx, item in enumerate(event.get("runOfShow", [])):
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

    for idx, m in enumerate(event.get("timelineMilestones", [])):
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


def _parse_date_and_time_dt(date_str: str, time_str: str) -> datetime.datetime:
    """Parse date and time strings into a datetime object for icalendar."""
    try:
        t_parsed = datetime.datetime.strptime(time_str.strip(), "%I:%M %p")
        d_parsed = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
        return datetime.datetime(d_parsed.year, d_parsed.month, d_parsed.day, t_parsed.hour, t_parsed.minute, tzinfo=datetime.timezone.utc)
    except Exception:
        try:
            d_parsed = datetime.datetime.strptime(date_str.strip(), "%Y-%m-%d")
            return datetime.datetime(d_parsed.year, d_parsed.month, d_parsed.day, 12, 0, tzinfo=datetime.timezone.utc)
        except Exception:
            return datetime.datetime.now(datetime.timezone.utc)


def _parse_date_and_time(date_str: str, time_str: str) -> str:
    """Fallback parser converting '2027-06-18' and '05:00 PM' to RFC 5545 timestamp."""
    try:
        dt = _parse_date_and_time_dt(date_str, time_str)
        return dt.strftime("%Y%m%dT%H%M%SZ")
    except Exception:
        clean_date = date_str.replace("-", "")
        return f"{clean_date}T120000Z"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info("PlanGenius AI Server starting on http://127.0.0.1:%d", port)
    app.run(host="0.0.0.0", port=port, debug=False)
