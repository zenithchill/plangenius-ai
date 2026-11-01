"""
Full End-to-End Integration Test for PlanGenius AI.
Simulates all user interactions and workflows across the entire platform.
"""

import unittest
import json
from app import app
import storage
import ai_engine


class TestPlanGeniusE2E(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        storage.reset_to_samples()

    def test_complete_wedding_flow(self):
        print("\n--- Testing Wedding Lifecycle Flow ---")
        # 1. Generate wedding plan
        params = {
            "eventType": "wedding",
            "title": "Maya & Julian's Mountain Lodge Wedding",
            "subType": "Rustic Alpine Romance",
            "date": "2027-08-21",
            "location": "Aspen Pine Crest Lodge, CO",
            "guestCount": 125,
            "totalBudget": 42000,
            "currency": "$",
            "theme": "Cozy alpine lodge with warm pine, white florals, and crackling stone hearths",
            "priorities": "Outdoor sunset ceremony, farm-to-table feast, live mountain bluegrass band",
            "dietaryNotes": "Vegetarian and dairy-free options"
        }
        gen_resp = self.client.post("/api/generate", json={"params": params, "autoSave": True})
        self.assertEqual(gen_resp.status_code, 200)
        data = gen_resp.get_json()
        self.assertTrue(data.get("success"))
        event = data.get("event")
        event_id = event.get("id")
        self.assertTrue(event_id)
        self.assertEqual(event.get("title"), params["title"])
        self.assertEqual(len(event.get("colorPalette", [])), 5)
        self.assertGreaterEqual(len(event.get("creativeIdeas", [])), 4)
        self.assertGreaterEqual(len(event.get("budgetItems", [])), 8)
        self.assertGreaterEqual(len(event.get("timelineMilestones", [])), 6)
        self.assertGreaterEqual(len(event.get("runOfShow", [])), 8)
        print(f"✓ Wedding plan created with ID: {event_id}")

        # 2. Update a budget item (mark as deposit paid)
        b_item = event["budgetItems"][0]
        b_item["status"] = "deposit_paid"
        b_item["actual"] = 5000
        save_resp = self.client.post("/api/events", json=event)
        self.assertEqual(save_resp.status_code, 200)
        print("✓ Budget item updated and saved")

        # 3. Add a milestone task
        event["timelineMilestones"].append({
            "id": "m_custom_1",
            "phase": "2 Weeks Out",
            "task": "Pick up custom wood mountain guestbook",
            "completed": True,
            "dueDate": "2027-08-07"
        })
        self.client.post("/api/events", json=event)
        print("✓ Custom milestone added")

        # 4. Draft AI Vendor Inquiry Email
        vendor = event["vendors"][0]
        email_resp = self.client.post("/api/vendor-email", json={"vendor": vendor, "event": event})
        self.assertEqual(email_resp.status_code, 200)
        email_data = email_resp.get_json()
        self.assertIn("Subject:", email_data.get("email"))
        self.assertIn("Maya & Julian", email_data.get("email"))
        print("✓ Vendor inquiry email generated")

        # 5. Query Co-pilot Chat
        chat_resp = self.client.post("/api/chat", json={
            "messages": [{"role": "user", "content": "How can I cut 15% from this lodge wedding budget?"}],
            "currentEvent": event
        })
        self.assertEqual(chat_resp.status_code, 200)
        reply = chat_resp.get_json().get("reply", "")
        self.assertTrue(len(reply) > 20)
        print("✓ AI Co-pilot responded to budget query:", reply[:50].replace("\n", " "), "...")

        # 6. Export iCalendar
        ics_resp = self.client.get(f"/api/events/{event_id}/export-ics")
        self.assertEqual(ics_resp.status_code, 200)
        ics_text = ics_resp.data.decode("utf-8")
        self.assertIn("BEGIN:VCALENDAR", ics_text)
        self.assertIn("Maya & Julian", ics_text)
        print("✓ iCalendar (.ics) export verified")

    def test_complete_birthday_flow(self):
        print("\n--- Testing Birthday Lifecycle Flow ---")
        # 1. Generate kids birthday
        b_params = {
            "eventType": "birthday",
            "title": "Zoe's Enchanted Fairy Garden 6th Birthday",
            "subType": "Kids Fantasy Adventure",
            "date": "2027-04-18",
            "location": "Botanical Conservatory Pavilion",
            "guestCount": 24,
            "totalBudget": 1100,
            "currency": "$",
            "theme": "Enchanted Fairy Forest with Butterfly Wings & Pixie Dust",
            "priorities": "Face painter, whimsical fairy tea party, scavenger hunt",
            "dietaryNotes": "Nut-free"
        }
        res = self.client.post("/api/generate", json={"params": b_params, "autoSave": True})
        self.assertEqual(res.status_code, 200)
        event = res.get_json().get("event")
        self.assertEqual(event["eventType"], "birthday")
        self.assertIn("Fairy", event["title"])
        print("✓ Birthday plan generated")

        # 2. Test extra ideas endpoint
        ideas_res = self.client.post("/api/extra-ideas", json={"category": "general", "event": event})
        self.assertEqual(ideas_res.status_code, 200)
        self.assertGreater(len(ideas_res.get_json().get("ideas", [])), 0)
        print("✓ Extra creative ideas generated")

    def test_complete_community_flow(self):
        print("\n--- Testing Community Event Lifecycle Flow ---")
        c_params = {
            "eventType": "community",
            "title": "Downtown Arts & Cultural Block Party",
            "subType": "Neighborhood Arts & Music Festival",
            "date": "2027-10-02",
            "location": "Main Street Pedestrian Plaza",
            "guestCount": 600,
            "totalBudget": 18000,
            "currency": "$",
            "theme": "Unite Through Art & Sound",
            "priorities": "Showcase local artists, 12 food trucks, all-day acoustic stage",
            "dietaryNotes": "Diverse dietary food trucks"
        }
        res = self.client.post("/api/generate", json={"params": c_params, "autoSave": True})
        self.assertEqual(res.status_code, 200)
        event = res.get_json().get("event")
        self.assertEqual(event["eventType"], "community")
        # Verify permit & safety line items exist
        categories = [it["category"] for it in event["budgetItems"]]
        self.assertIn("Permits & Safety", categories)
        print("✓ Community festival generated with municipal permits & safety allocations")


if __name__ == "__main__":
    unittest.main()
