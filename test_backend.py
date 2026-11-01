"""
Backend Test Suite for PlanGenius AI
Tests storage, AI generators, Flask REST endpoints, security headers, and input validation.
"""

import unittest
import json
import os
from app import app
import storage
import ai_engine


class TestPlanGeniusBackend(unittest.TestCase):
    """Comprehensive test case for PlanGenius AI REST backend and business logic."""

    def setUp(self):
        self.client = app.test_client()
        storage.reset_to_samples()

    def test_health_check(self):
        """Test health check monitoring endpoint."""
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "PlanGenius AI API")
        self.assertIn("libraries", data)

    def test_pydantic_schema_validation(self):
        """Verify Pydantic models validate and reject invalid schemas."""
        from models import EventPlanModel
        # Valid event model
        ev = EventPlanModel(
            title="Valid Gala Event",
            date="2027-09-15",
            guestCount=100,
            totalBudget=15000.0
        )
        self.assertEqual(ev.title, "Valid Gala Event")
        self.assertEqual(ev.totalBudget, 15000.0)

        # Rejects empty title
        with self.assertRaises(Exception):
            EventPlanModel(title="   ", date="2027-09-15")

        # Rejects negative guest count
        with self.assertRaises(Exception):
            EventPlanModel(title="Valid", date="2027-09-15", guestCount=-5)


    def test_security_headers(self):
        """Verify that production-grade security headers are present on all responses."""
        resp = self.client.get("/api/events")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "SAMEORIGIN")
        self.assertEqual(resp.headers.get("X-XSS-Protection"), "1; mode=block")
        self.assertEqual(resp.headers.get("Referrer-Policy"), "strict-origin-when-cross-origin")

    def test_list_events(self):
        """Test listing saved events returns correct schema and seeded samples."""
        resp = self.client.get("/api/events")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("events", [])), 3)

    def test_get_event(self):
        """Test fetching a specific event by ID."""
        resp = self.client.get("/api/events/evt-wedding-tuscan")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        event = data.get("event")
        self.assertEqual(event.get("eventType"), "wedding")
        self.assertIn("budgetItems", event)
        self.assertIn("timelineMilestones", event)
        self.assertIn("runOfShow", event)
        self.assertIn("vendors", event)
        self.assertIn("creativeIdeas", event)
        self.assertIn("colorPalette", event)

    def test_get_nonexistent_event(self):
        """Test that requesting an invalid event ID returns 404."""
        resp = self.client.get("/api/events/evt-nonexistent-999")
        self.assertEqual(resp.status_code, 404)
        data = resp.get_json()
        self.assertFalse(data.get("success"))

    def test_local_ai_plan_generation(self):
        """Test intelligent offline generation across Wedding, Birthday, and Community types."""
        # Wedding
        w_params = {
            "eventType": "wedding",
            "title": "Sam & Alex Waterfront Wedding",
            "subType": "Coastal Modern",
            "date": "2027-07-20",
            "location": "Seaside Haven Resort",
            "guestCount": 110,
            "totalBudget": 25000,
            "currency": "$",
            "theme": "Coastal Minimalist",
            "priorities": "Scenic sunset ceremony, seafood bar",
            "dietaryNotes": "Shellfish allergy warning on labels"
        }
        w_plan = ai_engine.generate_local_event_plan(w_params)
        self.assertEqual(w_plan["eventType"], "wedding")
        self.assertGreater(len(w_plan["budgetItems"]), 5)
        self.assertGreater(len(w_plan["timelineMilestones"]), 4)
        self.assertGreater(len(w_plan["runOfShow"]), 5)
        self.assertGreater(len(w_plan["creativeIdeas"]), 2)
        self.assertEqual(len(w_plan["colorPalette"]), 5)

        # Birthday
        b_params = {
            "eventType": "birthday",
            "title": "Liam's Dinosaur 5th Birthday",
            "subType": "Kids Dinosaur Safari",
            "date": "2027-05-15",
            "location": "Jurassic Park Hall",
            "guestCount": 20,
            "totalBudget": 900,
            "currency": "$",
            "theme": "Prehistoric Discovery",
            "priorities": "Fossil digging game, dinosaur cake",
            "dietaryNotes": "Nut-free"
        }
        b_plan = ai_engine.generate_local_event_plan(b_params)
        self.assertEqual(b_plan["eventType"], "birthday")
        self.assertGreater(len(b_plan["budgetItems"]), 4)

        # Community
        c_params = {
            "eventType": "community",
            "title": "Greenfield Summer Hackathon & Showcase",
            "subType": "Tech Showcase & Community Demo",
            "date": "2027-10-10",
            "location": "Greenfield Innovation Hub",
            "guestCount": 200,
            "totalBudget": 8000,
            "currency": "$",
            "theme": "Code for Good",
            "priorities": "High-speed wifi, pizza & boba, sponsor demos",
            "dietaryNotes": "Vegan pizza options"
        }
        c_plan = ai_engine.generate_local_event_plan(c_params)
        self.assertEqual(c_plan["eventType"], "community")
        self.assertGreater(len(c_plan["budgetItems"]), 5)

    def test_copilot_chat(self):
        """Test conversational Co-pilot advice generation with context grounding."""
        event = storage.get_event("evt-wedding-tuscan")
        resp = self.client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "How can I reduce my budget by 15%?"}],
            "currentEvent": event,
            "provider": "local"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Budget Reduction", data.get("reply", ""))

    def test_vendor_email_draft(self):
        """Test drafting bespoke vendor outreach letters."""
        event = storage.get_event("evt-wedding-tuscan")
        vendor = event["vendors"][0]
        resp = self.client.post("/api/vendor-email", json={
            "vendor": vendor,
            "event": event
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIn("Subject:", data.get("email"))
        self.assertIn(vendor["name"], data.get("email"))

    def test_extra_ideas_generator(self):
        """Test brainstorming additional creative ideas."""
        event = storage.get_event("evt-wedding-tuscan")
        resp = self.client.post("/api/extra-ideas", json={
            "category": "decor",
            "event": event
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertIsInstance(data.get("ideas"), list)
        self.assertGreaterEqual(len(data.get("ideas")), 1)

    def test_export_ics(self):
        """Test RFC 5545 iCalendar stream generation."""
        resp = self.client.get("/api/events/evt-wedding-tuscan/export-ics")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "text/calendar; charset=utf-8")
        ics_text = resp.data.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", ics_text)
        self.assertIn("END:VCALENDAR", ics_text)
        self.assertIn("BEGIN:VEVENT", ics_text)
        self.assertIn("Elena & Marcus", ics_text)

    def test_save_and_delete_event(self):
        """Test creating, reading, updating, and deleting an event lifecycle."""
        new_event = {
            "title": "Test Pop-Up Dinner Party",
            "eventType": "birthday",
            "date": "2027-11-20",
            "totalBudget": 1500,
            "budgetItems": [],
            "timelineMilestones": [],
            "runOfShow": [],
            "vendors": []
        }
        # Save
        save_resp = self.client.post("/api/events", json=new_event)
        self.assertEqual(save_resp.status_code, 200)
        saved = save_resp.get_json().get("event")
        event_id = saved.get("id")
        self.assertTrue(event_id)

        # Verify get
        get_resp = self.client.get(f"/api/events/{event_id}")
        self.assertEqual(get_resp.status_code, 200)

        # Delete
        del_resp = self.client.delete(f"/api/events/{event_id}")
        self.assertEqual(del_resp.status_code, 200)

        # Verify deleted
        get_again = self.client.get(f"/api/events/{event_id}")
        self.assertEqual(get_again.status_code, 404)

    def test_invalid_event_save_returns_400(self):
        """Test that saving an event without title returns 400 Bad Request."""
        resp = self.client.post("/api/events", json={"totalBudget": 5000})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("title is required", data.get("error", ""))

    def test_groq_key_validation(self):
        """Test empty Groq API key returns 400 validation error."""
        resp = self.client.post("/api/test-groq-key", json={"apiKey": ""})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("cannot be empty", data.get("error"))

    def test_groq_provider_routing_and_fallback(self):
        """Test that invalid keys trigger clear fallback or helpful error reporting."""
        params = {
            "eventType": "wedding",
            "title": "Groq Alpine Nuptials",
            "subType": "Modern Winter Romance",
            "date": "2027-12-15",
            "location": "Vail Pine Cabin",
            "guestCount": 75,
            "totalBudget": 30000,
            "currency": "$"
        }
        resp = self.client.post("/api/generate", json={
            "params": params,
            "provider": "groq",
            "apiKey": "gsk_invalid_test_key_for_fallback",
            "model": "llama-3.3-70b-versatile"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertEqual(data.get("event", {}).get("eventType"), "wedding")

        # Chat with invalid groq key reports error rather than silent prebuilt message
        chat_resp = self.client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "How can I reduce expenses?"}],
            "provider": "groq",
            "apiKey": "gsk_invalid_test_key_for_fallback",
            "model": "qwen/qwen3.8-27b",
            "currentEvent": data.get("event")
        })
        self.assertEqual(chat_resp.status_code, 200)
        self.assertTrue(chat_resp.get_json().get("success"))
        self.assertIn("Groq", chat_resp.get_json().get("reply"))

    def test_reset_samples_endpoint(self):
        """Test resetting storage to sample dataset."""
        resp = self.client.post("/api/reset-samples")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("events", [])), 4)


if __name__ == "__main__":
    unittest.main()
