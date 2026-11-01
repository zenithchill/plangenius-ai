"""
Backend Test Suite for PlanGenius AI
Tests storage, AI generators, and Flask REST endpoints.
"""

import unittest
import json
import os
from app import app
import storage
import ai_engine


class TestPlanGeniusBackend(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        storage.reset_to_samples()

    def test_list_events(self):
        resp = self.client.get("/api/events")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data.get("success"))
        self.assertGreaterEqual(len(data.get("events", [])), 3)

    def test_get_event(self):
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

    def test_local_ai_plan_generation(self):
        # Test wedding
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

        # Test birthday
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

        # Test community
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

    def test_export_ics(self):
        resp = self.client.get("/api/events/evt-wedding-tuscan/export-ics")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, "text/calendar; charset=utf-8")
        ics_text = resp.data.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", ics_text)
        self.assertIn("END:VCALENDAR", ics_text)
        self.assertIn("BEGIN:VEVENT", ics_text)
        self.assertIn("Elena & Marcus", ics_text)

    def test_save_and_delete_event(self):
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

    def test_groq_key_validation(self):
        # Empty key should return 400
        resp = self.client.post("/api/test-groq-key", json={"apiKey": ""})
        self.assertEqual(resp.status_code, 400)
        data = resp.get_json()
        self.assertFalse(data.get("success"))
        self.assertIn("cannot be empty", data.get("error"))

    def test_groq_provider_routing_and_fallback(self):
        # When groq provider is requested with a mock key or empty key, it falls back cleanly
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

        # Chat with invalid groq key reports error rather than prebuilt mock
        chat_resp = self.client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "How can I reduce expenses?"}],
            "provider": "groq",
            "apiKey": "gsk_invalid_test_key_for_fallback",
            "model": "qwen/qwen3.8-27b",
            "currentEvent": data.get("event")
        })
        self.assertEqual(chat_resp.status_code, 200)
        self.assertTrue(chat_resp.get_json().get("success"))
        # Must report Groq API Error rather than silent prebuilt message
        self.assertIn("Groq", chat_resp.get_json().get("reply"))

        # Explicit local engine test
        local_resp = self.client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "How can I reduce expenses?"}],
            "provider": "local",
            "currentEvent": data.get("event")
        })
        self.assertEqual(local_resp.status_code, 200)
        self.assertIn("Budget Reduction", local_resp.get_json().get("reply"))


if __name__ == "__main__":
    unittest.main()
