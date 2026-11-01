"""
Intelligent Planning Engine and Multi-Model AI Orchestration for PlanGenius AI.
Provides high-fidelity deterministic local planning logic, official Groq Cloud SDK,
and Google Gemini API orchestration.
"""

from typing import List, Dict, Any, Optional
import json
import uuid
import datetime
import urllib.request
import urllib.error
import os
import logging
from pathlib import Path

# Use python-dotenv library to cleanly load environment
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).resolve().parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

# Use official groq library when available
try:
    from groq import Groq
    HAVE_GROQ_SDK = True
except ImportError:
    HAVE_GROQ_SDK = False

logger = logging.getLogger(__name__)

DEFAULT_GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
DEFAULT_GROQ_MODEL = "qwen/qwen3.8-27b"


def call_gemini_api(prompt: str, system_instruction: str = "", api_key: str = "", model: str = "gemini-2.5-flash", json_mode: bool = False) -> str:
    """Call Google Generative AI REST API with given model and key."""
    if not api_key:
        raise ValueError("Missing Gemini API Key")

    model_name = model.strip()
    if not model_name.startswith("gemini-"):
        model_name = "gemini-2.5-flash"

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 4096
        }
    }

    if json_mode:
        payload["generationConfig"]["responseMimeType"] = "application/json"

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            candidates = resp_data.get("candidates", [])
            if candidates and "content" in candidates[0]:
                parts = candidates[0]["content"].get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini API Error ({e.code}): {error_msg}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Gemini API: {str(e)}")


def call_groq_api(prompt: str, system_instruction: str = "", api_key: str = "", model: str = "qwen/qwen3.8-27b", json_mode: bool = False) -> str:
    """Call Groq Cloud API with given model and key using official Groq SDK with failover."""
    if not api_key:
        raise ValueError("Missing Groq API Key")

    model_name = model.strip() if model else "qwen/qwen3.8-27b"
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    # Use official Groq SDK client
    if HAVE_GROQ_SDK:
        try:
            client = Groq(api_key=api_key.strip())
            kwargs = {
                "model": model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 750,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            completion = client.chat.completions.create(**kwargs)
            choice = completion.choices[0] if completion.choices else None
            return choice.message.content if choice and choice.message else ""
        except Exception as e:
            err_str = str(e)
            if "json_validate_failed" in err_str and json_mode:
                logger.info("Groq json_validate_failed. Retrying in raw prompt mode...")
                return call_groq_api(prompt, system_instruction=system_instruction, api_key=api_key, model=model_name, json_mode=False)
            for alt_model in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]:
                if alt_model != model_name and ("rate_limit" in err_str.lower() or "429" in err_str or "model_not_found" in err_str.lower()):
                    logger.info("Groq %s rate limit reached. Auto-failing over to %s...", model_name, alt_model)
                    return call_groq_api(prompt, system_instruction=system_instruction, api_key=api_key, model=alt_model, json_mode=json_mode)
            raise RuntimeError(f"Groq API Error: {err_str}")

    # Fallback to standard urllib implementation
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": model_name,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 750
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key.strip()}",
            "User-Agent": "PlanGenius/1.0 (compatible; Mozilla/5.0)"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=35) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            choices = resp_data.get("choices", [])
            if choices and "message" in choices[0]:
                return choices[0]["message"].get("content", "")
            return ""
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8", errors="ignore")
        if "json_validate_failed" in error_msg and json_mode:
            logger.info("Groq json_validate_failed. Retrying in raw prompt mode...")
            return call_groq_api(prompt, system_instruction=system_instruction, api_key=api_key, model=model_name, json_mode=False)
        for alt_model in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]:
            if alt_model != model_name and (e.code == 429 or "rate_limit" in error_msg or "model_not_found" in error_msg):
                logger.info("Groq %s issue (%s). Auto-failing over to %s...", model_name, e.code, alt_model)
                return call_groq_api(prompt, system_instruction=system_instruction, api_key=api_key, model=alt_model, json_mode=json_mode)
        raise RuntimeError(f"Groq API Error ({e.code}): {error_msg}")
    except Exception as e:
        raise RuntimeError(f"Failed to connect to Groq API: {str(e)}")


def get_groq_models(api_key: str) -> List[str]:
    """Fetch available models from Groq Cloud using official Groq SDK with fallback."""
    if not api_key:
        return []

    if HAVE_GROQ_SDK:
        try:
            client = Groq(api_key=api_key.strip())
            models_data = client.models.list()
            models = []
            for m in models_data.data:
                mid = m.id
                if "whisper" not in mid and "guard" not in mid and "orpheus" not in mid:
                    models.append(mid)
            return models
        except Exception as e:
            logger.warning("Groq SDK models list error, falling back to REST: %s", e)

    url = "https://api.groq.com/openai/v1/models"
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key.strip()}",
            "User-Agent": "PlanGenius/1.0 (compatible; Mozilla/5.0)"
        }
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        models = []
        for m in data.get("data", []):
            mid = m.get("id", "")
            if "whisper" not in mid and "guard" not in mid and "orpheus" not in mid:
                models.append(mid)
        return models



def _calculate_due_dates(target_date_str, offsets_in_days):
    """Generate due dates based on target date and negative day offsets."""
    try:
        target = datetime.datetime.strptime(target_date_str, "%Y-%m-%d").date()
    except Exception:
        target = datetime.date.today() + datetime.timedelta(days=180)

    result = []
    for days_before in offsets_in_days:
        due = target - datetime.timedelta(days=days_before)
        result.append(due.strftime("%Y-%m-%d"))
    return result


def generate_local_event_plan(params):
    """
    Generate an intelligent, comprehensive master plan locally
    without needing an external API key.
    """
    event_type = params.get("eventType", "wedding").lower()
    title = params.get("title", "").strip() or f"Special {event_type.capitalize()} Celebration"
    sub_type = params.get("subType", "").strip()
    target_date = params.get("date", (datetime.date.today() + datetime.timedelta(days=120)).strftime("%Y-%m-%d"))
    location = params.get("location", "Scenic Local Venue")
    guest_count = int(params.get("guestCount", 80))
    total_budget = float(params.get("totalBudget", 10000))
    currency = params.get("currency", "$")
    theme = params.get("theme", "Modern Elegance")
    priorities = params.get("priorities", "Atmosphere, food quality, guest delight")
    dietary_notes = params.get("dietaryNotes", "Vegetarian and gluten-free options available")

    event_id = f"evt-{uuid.uuid4().hex[:8]}"

    if event_type == "wedding":
        plan = _build_wedding_plan(
            event_id, title, sub_type, target_date, location,
            guest_count, total_budget, currency, theme, priorities, dietary_notes
        )
    elif event_type == "birthday":
        plan = _build_birthday_plan(
            event_id, title, sub_type, target_date, location,
            guest_count, total_budget, currency, theme, priorities, dietary_notes
        )
    else:  # community or other
        plan = _build_community_plan(
            event_id, title, sub_type, target_date, location,
            guest_count, total_budget, currency, theme, priorities, dietary_notes
        )

    return plan


def _build_wedding_plan(event_id, title, sub_type, target_date, location, guests, budget, currency, theme, priorities, dietary):
    if not sub_type:
        sub_type = "Modern Romantic Celebration"

    # Allocations
    alloc = {
        "Venue & Rentals": 0.26,
        "Catering & Bar": 0.32,
        "Photography & Video": 0.14,
        "Flowers & Decor": 0.10,
        "Music & Entertainment": 0.07,
        "Attire & Beauty": 0.05,
        "Stationery & Favors": 0.02,
        "Contingency": 0.04
    }

    budget_items = [
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Venue & Rentals", "name": f"Ceremony & Reception Venue Rental ({guests} guests)", "estimated": round(budget * alloc["Venue & Rentals"] * 0.85), "actual": 0, "status": "pending", "notes": "Includes access for setup, sound curfew and venue coordinator"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Venue & Rentals", "name": "Tables, Chairs, Linens & Place Settings Rental", "estimated": round(budget * alloc["Venue & Rentals"] * 0.15), "actual": 0, "status": "pending", "notes": "Upgraded cross-back wooden chairs and linen napkins"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Catering & Bar", "name": f"Plated or Family-Style Dinner ({guests} guests)", "estimated": round(budget * alloc["Catering & Bar"] * 0.72), "actual": 0, "status": "pending", "notes": f"Includes appetizer stations, main courses ({dietary}), and dessert"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Catering & Bar", "name": "Beverage Package & Signature Cocktails", "estimated": round(budget * alloc["Catering & Bar"] * 0.28), "actual": 0, "status": "pending", "notes": "4.5 hours service with professional mixologists"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Photography & Video", "name": "Lead Photographer & Assistant (8-10 Hours)", "estimated": round(budget * alloc["Photography & Video"] * 0.70), "actual": 0, "status": "pending", "notes": "High-res gallery, timeline consultation, print release"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Photography & Video", "name": "Cinematic 4K Highlight Reel", "estimated": round(budget * alloc["Photography & Video"] * 0.30), "actual": 0, "status": "pending", "notes": "Includes drone aerials (weather permitting) and full speeches audio"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Flowers & Decor", "name": "Ceremony Arch, Bouquets & Boutonnieres", "estimated": round(budget * alloc["Flowers & Decor"] * 0.55), "actual": 0, "status": "pending", "notes": "Curated palette with seasonal florals"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Flowers & Decor", "name": "Guest Tables Centerpieces & Mood Lighting", "estimated": round(budget * alloc["Flowers & Decor"] * 0.45), "actual": 0, "status": "pending", "notes": "Warm candlelight hurricanes and lush runners"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Music & Entertainment", "name": "Ceremony Sound, Cocktail Hour & Reception DJ/MC", "estimated": round(budget * alloc["Music & Entertainment"]), "actual": 0, "status": "pending", "notes": "Wireless lapel mic for officiant and dance lighting package"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Attire & Beauty", "name": "Bridal/Partner Hair & Makeup Trial + Day-of", "estimated": round(budget * alloc["Attire & Beauty"] * 0.50), "actual": 0, "status": "pending", "notes": "On-site bridal suite glam team"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Attire & Beauty", "name": "Attire Alterations & Accessories", "estimated": round(budget * alloc["Attire & Beauty"] * 0.50), "actual": 0, "status": "pending", "notes": "Veils, cuff links, pressing, and emergency bustle kit"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Stationery & Favors", "name": "Invitations, Day-Of Signage & Guest Favors", "estimated": round(budget * alloc["Stationery & Favors"]), "actual": 0, "status": "pending", "notes": "Custom seating chart display and personalized keepsake favors"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Contingency", "name": "Contingency & Incidentals Reserve", "estimated": round(budget * alloc["Contingency"]), "actual": 0, "status": "pending", "notes": "Reserve for vendor gratuities, weather alternatives, or last-minute additions"}
    ]

    due_dates = _calculate_due_dates(target_date, [270, 180, 90, 45, 14, 2, 0])

    timeline = [
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "9+ Months Out", "task": "Finalize venue, secure wedding date, and establish budget guardrails", "completed": False, "dueDate": due_dates[0]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "6 Months Out", "task": "Contract core vendors: Photographer, Caterer, DJ, and Florist", "completed": False, "dueDate": due_dates[1]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "3 Months Out", "task": "Mail formal invitations, conduct menu tasting, order wedding rings", "completed": False, "dueDate": due_dates[2]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "6 Weeks Out", "task": "Finalize music cue lists, order ceremony stationery, book beauty trials", "completed": False, "dueDate": due_dates[3]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "2 Weeks Out", "task": "Submit final guest headcount to caterer and build final table seating plan", "completed": False, "dueDate": due_dates[4]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "2 Days Before", "task": "Pick up attire, drop off decor at venue, hold rehearsal dinner & ceremony run-through", "completed": False, "dueDate": due_dates[5]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "Wedding Day", "task": "Relax and celebrate! Follow day-of run of show schedule.", "completed": False, "dueDate": due_dates[6]}
    ]

    run_of_show = [
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "10:30 AM", "activity": "Hair & Makeup styling starts in Bridal Suite", "responsible": "Lead Stylist & Wedding Party", "location": "Bridal Suite"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "01:00 PM", "activity": "Photographer arrives: Detail shots (rings, dress, invites, shoes)", "responsible": "Photographer", "location": "Suites & Grounds"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "02:30 PM", "activity": "Couple 'First Look' & Romantic Couple Portraits", "responsible": "Coordinator & Photographer", "location": "Courtyard Garden"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "03:45 PM", "activity": "Wedding Party & Immediate Family Group Photos", "responsible": "Photographer", "location": "Garden Terrace"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "04:30 PM", "activity": "Guest Arrival: Welcome drink station & acoustic prelude music", "responsible": "Catering Lead & Musicians", "location": "Ceremony Entry"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "05:00 PM", "activity": "Ceremony Processional & Vows Exchange", "responsible": "Officiant & Couple", "location": "Main Lawn"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "05:40 PM", "activity": "Cocktail Hour: Passed hors d'oeuvres & signature cocktails", "responsible": "Catering & DJ", "location": "Veranda"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "06:50 PM", "activity": "Guests seated; Grand Entrance & Welcome Toast", "responsible": "DJ & Couple", "location": "Reception Hall"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "07:15 PM", "activity": "Dinner Service & Speeches / Toasts", "responsible": "Catering & Speakers", "location": "Reception Hall"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "08:30 PM", "activity": "First Dance & Parent Dances", "responsible": "DJ & Couple", "location": "Dance Floor"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "08:45 PM", "activity": "Dance Floor Officially Opens & Dessert Display Unveiled", "responsible": "DJ", "location": "Dance Floor"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "11:00 PM", "activity": "Grand Sparkler Send-off & After-party departure", "responsible": "Coordinator", "location": "Main Exit"}
    ]

    vendors = [
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Venue", "name": f"{location} Manager", "contact": "events@venuebooking.com", "phone": "(555) 234-5678", "status": "contacted", "quoted": round(budget * 0.25), "notes": "Checking package inclusions for sound and curfew"},
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Catering", "name": "Artisan Harvest Catering", "contact": "catering@artisangroup.com", "phone": "(555) 876-5432", "status": "to_research", "quoted": round(budget * 0.30), "notes": "Requesting sample tasting menu"},
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Photography", "name": "Fine Art Storytelling Co.", "contact": "hello@fineartphoto.com", "phone": "(555) 432-1098", "status": "to_research", "quoted": round(budget * 0.14), "notes": "Checking availability for chosen date"},
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Floral & Decor", "name": "Botanical Studio Designs", "contact": "flora@botanicaldesign.com", "phone": "(555) 654-9870", "status": "to_research", "quoted": round(budget * 0.10), "notes": "Send color palette and ceremony arch concept"},
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Entertainment", "name": "Vibe Elevation DJ & Live Sound", "contact": "booking@vibedj.com", "phone": "(555) 345-6789", "status": "to_research", "quoted": round(budget * 0.07), "notes": "Includes lapel mics and dance floor lighting"}
    ]

    color_palette = [
        {"name": "Sage Whisper", "hex": "#8A9A86"},
        {"name": "Dusty Rose Quartz", "hex": "#D8A47F"},
        {"name": "Warm Ivory Silk", "hex": "#F9F6F0"},
        {"name": "Burnished Bronze", "hex": "#A27035"},
        {"name": "Deep Forest Spruce", "hex": "#2C402E"}
    ]

    creative_ideas = [
        {
            "title": "Interactive Audio Guestbook Telephone",
            "category": "Guest Experience",
            "description": "Place a vintage rotary telephone on an antique console table where guests pick up the receiver, hear a recorded welcome from the couple, and leave heartfelt voice messages and blessings after the tone."
        },
        {
            "title": f"Signature Couple Cocktails: 'The His & Hers Duo'",
            "category": "Food & Beverage",
            "description": "Serve two custom creations: (1) A refreshing botanical gin spritz with elderflower, cucumber, and prosecco; (2) An artisanal smoked bourbon smash with blackberry puree and fresh thyme sprigs."
        },
        {
            "title": "Late-Night Comfort Bites Surprise",
            "category": "Catering Highlight",
            "description": "Surprise late-night dancers at 9:45 PM with miniature gourmet smashburger sliders, truffle shoestring french fries in paper cones, and warm churros with spiced chocolate dipping sauce."
        },
        {
            "title": "Living Seed-Paper Escort Card Display",
            "category": "Eco-Friendly Decor",
            "description": "Calligraphed escort tags pressed with wildflower seeds hung from a wooden trellis with mini brass clips. Guests plant the cards at home to bloom memory gardens."
        },
        {
            "title": "Golden Hour Acoustic Sunset Intermezzo",
            "category": "Music & Atmosphere",
            "description": "As the sun dips toward the horizon, have an acoustic guitarist gently transition the ambiance with mellow, stripped-down renditions of 90s/00s love classics while guests enjoy dessert."
        }
    ]

    return {
        "id": event_id,
        "title": title,
        "eventType": "wedding",
        "subType": sub_type,
        "date": target_date,
        "location": location,
        "guestCount": guests,
        "totalBudget": budget,
        "currency": currency,
        "theme": theme,
        "priorities": priorities,
        "dietaryNotes": dietary,
        "colorPalette": color_palette,
        "creativeIdeas": creative_ideas,
        "budgetItems": budget_items,
        "timelineMilestones": timeline,
        "runOfShow": run_of_show,
        "vendors": vendors
    }


def _build_birthday_plan(event_id, title, sub_type, target_date, location, guests, budget, currency, theme, priorities, dietary):
    is_kids = any(k in sub_type.lower() or k in title.lower() or k in theme.lower() for k in ["kid", "child", "7th", "1st", "boy", "girl", "space", "safari", "superhero", "dinosaur", "magic"])
    if not sub_type:
        sub_type = "Kids Themed Party" if is_kids else "Milestone Birthday Celebration"

    if is_kids:
        alloc = {
            "Entertainment & Games": 0.30,
            "Food, Snacks & Cake": 0.32,
            "Decor, Balloons & Lights": 0.18,
            "Favors & Activity Packs": 0.12,
            "Contingency": 0.08
        }
        palette = [
            {"name": "Electric Cyan", "hex": "#00B4D8"},
            {"name": "Bright Solar Yellow", "hex": "#FFB703"},
            {"name": "Vibrant Tangerine", "hex": "#FB8500"},
            {"name": "Cosmic Royal Blue", "hex": "#023E8A"},
            {"name": "Pure Cloud White", "hex": "#F8F9FA"}
        ]
    else:
        alloc = {
            "Venue & Lounge": 0.35,
            "Catering & Craft Bar": 0.35,
            "Music & Entertainment": 0.15,
            "Decor & Ambience": 0.10,
            "Contingency": 0.05
        }
        palette = [
            {"name": "Midnight Noir", "hex": "#1A1A24"},
            {"name": "Gilded Metallic Gold", "hex": "#D4AF37"},
            {"name": "Warm Terracotta Coral", "hex": "#E07A5F"},
            {"name": "Soft Cashmere Cream", "hex": "#F4F1DE"},
            {"name": "Deep Plum Velvet", "hex": "#3D1635"}
        ]

    budget_items = []
    if is_kids:
        budget_items = [
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Entertainment & Games", "name": f"Interactive Performer / Science / Magic Show ({guests} kids)", "estimated": round(budget * 0.30), "actual": 0, "status": "pending", "notes": "60-75 minute interactive participatory show"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Food, Snacks & Cake", "name": "Custom Themed Tiered Birthday Cake & Cupcakes", "estimated": round(budget * 0.18), "actual": 0, "status": "pending", "notes": f"Nut-free safety certified ({dietary})"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Food, Snacks & Cake", "name": "Party Lunch & Refreshment Station (Pizza, fruit skewers, juices)", "estimated": round(budget * 0.14), "actual": 0, "status": "pending", "notes": "Kid-friendly snacks and adult beverage bar"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Decor, Balloons & Lights", "name": "Giant Themed Balloon Garland, Photo Wall & Backdrop", "estimated": round(budget * 0.18), "actual": 0, "status": "pending", "notes": "Custom color palette balloon arch with foil character balloons"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Favors & Activity Packs", "name": "Personalized Goodie Bags & Custom Take-Home Craft", "estimated": round(budget * 0.12), "actual": 0, "status": "pending", "notes": f"{guests} bags with themed toys, stickers, and activity books"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Contingency", "name": "Backup Activities & Extra Disposables", "estimated": round(budget * 0.08), "actual": 0, "status": "pending", "notes": "Reserved for weather shifts or extra guests"}
        ]
    else:
        budget_items = [
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Venue & Lounge", "name": f"Private Event Space / Lounge Rental ({guests} guests)", "estimated": round(budget * 0.35), "actual": 0, "status": "pending", "notes": "4 hours access, lounge seating, sound system setup"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Catering & Craft Bar", "name": "Artisanal Grazing Table & Passed Gourmet Sliders", "estimated": round(budget * 0.23), "actual": 0, "status": "pending", "notes": f"Abundant charcuterie, hot appetizers ({dietary})"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Catering & Craft Bar", "name": "Craft Mixologist & Signature Birthday Cocktails", "estimated": round(budget * 0.12), "actual": 0, "status": "pending", "notes": "2 bespoke craft cocktail recipes + beer/wine bar"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Music & Entertainment", "name": "Live DJ or Acoustic Duo & Party Lighting", "estimated": round(budget * 0.15), "actual": 0, "status": "pending", "notes": "Custom playlist curation honoring the celebrant's milestone"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Decor & Ambience", "name": "Custom Neon Light, Floral Accents & Photo Moment", "estimated": round(budget * 0.10), "actual": 0, "status": "pending", "notes": "Rentable milestone neon sign with lush greenery wall"},
            {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Contingency", "name": "Tips, Ice & Extra Supplies", "estimated": round(budget * 0.05), "actual": 0, "status": "pending", "notes": "Incidentals fund"}
        ]

    due_dates = _calculate_due_dates(target_date, [42, 28, 14, 7, 2, 0])
    timeline = [
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "6 Weeks Out", "task": "Lock in venue/location and book headline entertainment/DJ", "completed": False, "dueDate": due_dates[0]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "4 Weeks Out", "task": "Send digital animated invitations and confirm theme details", "completed": False, "dueDate": due_dates[1]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "2 Weeks Out", "task": "Order custom birthday cake and purchase balloon decor supplies", "completed": False, "dueDate": due_dates[2]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "1 Week Out", "task": "Assemble party favors and lock in final RSVP guest numbers", "completed": False, "dueDate": due_dates[3]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "2 Days Before", "task": "Pick up dry goods, test playlists, prepare game props", "completed": False, "dueDate": due_dates[4]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "Party Day", "task": "Inflate balloon decor, welcome guests, execute run of show, have a blast!", "completed": False, "dueDate": due_dates[5]}
    ]

    if is_kids:
        run_of_show = [
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "01:30 PM", "activity": "Host arrives: Balloon arch installation & treat table staging", "responsible": "Hosts", "location": "Party Zone"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "02:00 PM", "activity": "Guests arrive: Welcome station, themed name tags & tattoo/face paint", "responsible": "Welcome Coordinator", "location": "Entry Foyer"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "02:30 PM", "activity": "Headline Interactive Entertainment / Workshop begins", "responsible": "Performer / Entertainer", "location": "Main Play Area"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "03:15 PM", "activity": "High-Energy Movement Games & Relay Challenges", "responsible": "Game Master / Hosts", "location": "Lawn / Main Area"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "03:45 PM", "activity": "Snack Time: Pizza slices, fruit rockets & juice boxes", "responsible": "Kitchen Leads", "location": "Dining Tables"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "04:15 PM", "activity": "Happy Birthday Song, Candle Blowing & Cake Distribution", "responsible": "All Guests", "location": "Cake Table"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "04:45 PM", "activity": "Pinata smash / favor distribution & farewell hugs", "responsible": "Hosts", "location": "Exit Plaza"}
        ]
    else:
        run_of_show = [
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "06:00 PM", "activity": "Venue doors open: Mixologist ready & chill lounge playlist spinning", "responsible": "Mixologist & DJ", "location": "Lounge Terrace"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "06:30 PM", "activity": "Guests arrive: Signature cocktails served & grazing table opens", "responsible": "Host & Servers", "location": "Main Lounge"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "07:30 PM", "activity": "Golden hour photo ops & interactive milestone trivia game", "responsible": "MC / Best Friend", "location": "Photo Backdrop"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "08:15 PM", "activity": "Heartfelt toast to the celebrant & champagne pour", "responsible": "Close Friends / Family", "location": "Main Stage"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "08:30 PM", "activity": "Gourmet cake cutting & late-night warm bites served", "responsible": "Catering Lead", "location": "Dessert Bar"},
            {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "08:45 PM", "activity": "Dance floor heats up with favorite anthems through midnight", "responsible": "DJ & Guests", "location": "Dance Floor"}
        ]

    vendors = [
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Entertainment", "name": "Premier Event Talent Agency", "contact": "talent@eventperformer.com", "phone": "(555) 332-1144", "status": "to_research", "quoted": round(budget * 0.25), "notes": "Checking act availability and insurance certification"},
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Bakery", "name": "Sugar & Canvas Custom Cakes", "contact": "cakes@sugarcanvas.com", "phone": "(555) 776-9900", "status": "to_research", "quoted": round(budget * 0.15), "notes": "Requesting themed flavor portfolio"}
    ]

    creative_ideas = [
        {
            "title": "Celebrant Trivia & Roast/Toast Lightning Round",
            "category": "Interactive Entertainment",
            "description": "A rapid-fire digital smartphone trivia game (or card game) testing guests on hilarious little-known facts about the birthday VIP, with custom prizes for the top scorer."
        },
        {
            "title": "Interactive DIY Themed Station",
            "category": "Guest Activity",
            "description": "An interactive maker bar where guests create their own personalized souvenir (e.g. customized hot-sauce blending, mini terrarium planting, or custom ice cream sundae lab)."
        },
        {
            "title": "Milestone Memory Wall & Photo Mosaic",
            "category": "Decor & Nostalgia",
            "description": "A curated grid of framed photos celebrating funny and touching moments across every chapter of the celebrant's life, with cards for guests to write 'My favorite memory with you was...'."
        },
        {
            "title": "Custom Birthday Signature Elixir",
            "category": "Drink Concept",
            "description": "A vibrant signature beverage served with edible glitter and rosemary smoke bubble toppers that pop with aroma as guests take their first sip."
        }
    ]

    return {
        "id": event_id,
        "title": title,
        "eventType": "birthday",
        "subType": sub_type,
        "date": target_date,
        "location": location,
        "guestCount": guests,
        "totalBudget": budget,
        "currency": currency,
        "theme": theme,
        "priorities": priorities,
        "dietaryNotes": dietary,
        "colorPalette": palette,
        "creativeIdeas": creative_ideas,
        "budgetItems": budget_items,
        "timelineMilestones": timeline,
        "runOfShow": run_of_show,
        "vendors": vendors
    }


def _build_community_plan(event_id, title, sub_type, target_date, location, guests, budget, currency, theme, priorities, dietary):
    if not sub_type:
        sub_type = "Community Festival & Gathering"

    alloc = {
        "Permits & Safety": 0.14,
        "Stage, AV & Sound": 0.26,
        "Rentals, Tents & Sanitation": 0.22,
        "Marketing & Signage": 0.12,
        "Hospitality & Volunteer Support": 0.10,
        "Kids & Community Activities": 0.10,
        "Contingency": 0.06
    }

    budget_items = [
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Permits & Safety", "name": f"City Park Use Permit, Sound Variance & Fire Safety Review", "estimated": round(budget * alloc["Permits & Safety"] * 0.60), "actual": 0, "status": "pending", "notes": "Mandatory city parks & recreation department filing"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Permits & Safety", "name": "Event Liability Insurance Rider & First Aid Team", "estimated": round(budget * alloc["Permits & Safety"] * 0.40), "actual": 0, "status": "pending", "notes": "General commercial liability certificate naming city as additional insured"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Stage, AV & Sound", "name": "Covered Modular Stage, PA System & Microphones", "estimated": round(budget * alloc["Stage, AV & Sound"] * 0.75), "actual": 0, "status": "pending", "notes": "Includes on-site live sound engineer for musical performances"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Stage, AV & Sound", "name": "Quiet Mobile Generator & Power Distribution Drops", "estimated": round(budget * alloc["Stage, AV & Sound"] * 0.25), "actual": 0, "status": "pending", "notes": "Supplies power to main stage, sound rig, and volunteer booth"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Rentals, Tents & Sanitation", "name": "Canopy Tents, Folding Tables & Waste Sorting Bins", "estimated": round(budget * alloc["Rentals, Tents & Sanitation"] * 0.65), "actual": 0, "status": "pending", "notes": "Compost, recycling, and landfill marked stations"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Rentals, Tents & Sanitation", "name": "Portable Restroom Units (Standard + ADA Accessible)", "estimated": round(budget * alloc["Rentals, Tents & Sanitation"] * 0.35), "actual": 0, "status": "pending", "notes": "Delivered morning of event with hand-washing stations"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Marketing & Signage", "name": "Street Banners, Lawn Yard Signs & Directional Signage", "estimated": round(budget * alloc["Marketing & Signage"]), "actual": 0, "status": "pending", "notes": "High visibility weather-resistant vinyl signs"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Hospitality & Volunteer Support", "name": "Volunteer Hospitality Tent, T-Shirts & Meal Vouchers", "estimated": round(budget * alloc["Hospitality & Volunteer Support"]), "actual": 0, "status": "pending", "notes": f"Meals for volunteer crew ({dietary})"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Kids & Community Activities", "name": "Inflatable Bouncer / Family Lawn Games / Craft Supplies", "estimated": round(budget * alloc["Kids & Community Activities"]), "actual": 0, "status": "pending", "notes": "Includes safety operators and activity attendants"},
        {"id": f"b_{uuid.uuid4().hex[:6]}", "category": "Contingency", "name": "Incidentals & Emergency Fund", "estimated": round(budget * alloc["Contingency"]), "actual": 0, "status": "pending", "notes": "Reserved for unexpected city requirements or surge supplies"}
    ]

    due_dates = _calculate_due_dates(target_date, [90, 60, 30, 14, 3, 0])
    timeline = [
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "12-16 Weeks Out", "task": "Submit city park event permit applications, sound variance, and safety layout", "completed": False, "dueDate": due_dates[0]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "8-10 Weeks Out", "task": "Recruit local food truck partners, sponsor booths, and reserve stage/sound gear", "completed": False, "dueDate": due_dates[1]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "4-6 Weeks Out", "task": "Launch volunteer recruitment drive and order promotional print banners", "completed": False, "dueDate": due_dates[2]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "2 Weeks Out", "task": "Finalize performance schedules, assign volunteer shifts, and confirm equipment deliveries", "completed": False, "dueDate": due_dates[3]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "3 Days Before", "task": "Conduct site walk-through with park ranger/facilities lead, pack emergency safety kits", "completed": False, "dueDate": due_dates[4]},
        {"id": f"m_{uuid.uuid4().hex[:6]}", "phase": "Event Day", "task": "Morning vendor load-in, run festival smoothly, complete zero-waste teardown sweep", "completed": False, "dueDate": due_dates[5]}
    ]

    run_of_show = [
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "07:00 AM", "activity": "Logistics crew arrives: Park gates open, stage setup & restrooms delivery", "responsible": "Operations Lead", "location": "Park Grounds"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "08:30 AM", "activity": "Food trucks & community organization booths load in and park", "responsible": "Vendor Coordinator", "location": "Vendor Row"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "09:30 AM", "activity": "Volunteer shift 1 all-hands safety & assignment briefing", "responsible": "Volunteer Director", "location": "Info Pavilion"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "10:00 AM", "activity": "Event officially opens to public! Music on main stage begins", "responsible": "MC / Stage Team", "location": "Entire Park"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "11:30 AM", "activity": "Local youth performers & cultural dance showcases", "responsible": "Stage Manager", "location": "Main Stage"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "01:00 PM", "activity": "Keynote community leaders recognition & sponsor appreciation", "responsible": "Event Chair", "location": "Main Stage"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "02:30 PM", "activity": "Interactive community games, raffle draws & family competitions", "responsible": "Activity Hosts", "location": "Center Field"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "04:30 PM", "activity": "Headline community band performance & closing ceremony", "responsible": "Stage Team", "location": "Main Stage"},
        {"id": f"r_{uuid.uuid4().hex[:6]}", "time": "05:00 PM", "activity": "Festival concludes: Vendor load-out and zero-waste cleanup sweep", "responsible": "All Volunteers", "location": "Park Grounds"}
    ]

    vendors = [
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "AV & Stage", "name": "City Sound & Staging Solutions", "contact": "info@citystaging.com", "phone": "(555) 678-1234", "status": "to_research", "quoted": round(budget * 0.26), "notes": "Requires municipal electrical connection check"},
        {"id": f"v_{uuid.uuid4().hex[:6]}", "category": "Sanitation & Rentals", "name": "EcoEvent Sanitation & Tent Hire", "contact": "rentals@ecoeventrentals.com", "phone": "(555) 901-2345", "status": "to_research", "quoted": round(budget * 0.22), "notes": "Includes waste sorting containers"}
    ]

    palette = [
        {"name": "Community Evergreen", "hex": "#1B4931"},
        {"name": "Sunshine Gold", "hex": "#F4A261"},
        {"name": "Clean Sky Blue", "hex": "#2A9D8F"},
        {"name": "Heritage Brick Red", "hex": "#E76F51"},
        {"name": "Granite Charcoal", "hex": "#264653"}
    ]

    creative_ideas = [
        {
            "title": "Collaborative 'Voices of Our Town' Mural Wall",
            "category": "Interactive Art",
            "description": "Erect a giant canvas or wooden partition where attendees of all ages paint what community means to them. Later displayed in the public library or city hall."
        },
        {
            "title": "Community Passport Stamp Challenge",
            "category": "Attendee Engagement",
            "description": "Each attendee receives a printed mini-passport. Visiting 6 different community nonprofit and local maker booths earns a stamp, entering them into a grand prize local gift basket raffle."
        },
        {
            "title": "Local Hero / Youth Changemaker Spotlight",
            "category": "Programming Highlight",
            "description": "Dedicate a 20-minute stage segment to honor 3 unsung neighborhood volunteers or high school student leaders with custom framed certificates and public recognition."
        },
        {
            "title": "Zero-Waste 'Clean Green' Station with Seedling Favors",
            "category": "Sustainability & Favors",
            "description": "A staffed eco-station teaching fast composting and handing out native pollinator flower seedlings or tree saplings for families to plant in their gardens."
        }
    ]

    return {
        "id": event_id,
        "title": title,
        "eventType": "community",
        "subType": sub_type,
        "date": target_date,
        "location": location,
        "guestCount": guests,
        "totalBudget": budget,
        "currency": currency,
        "theme": theme,
        "priorities": priorities,
        "dietaryNotes": dietary,
        "colorPalette": palette,
        "creativeIdeas": creative_ideas,
        "budgetItems": budget_items,
        "timelineMilestones": timeline,
        "runOfShow": run_of_show,
        "vendors": vendors
    }


def generate_event_plan(params, provider="groq", api_key=None, model=None):
    """
    Main entrypoint for generating an event plan.
    Supports Groq API, Gemini API, and graceful local engine fallback.
    """
    active_key = (api_key or DEFAULT_GROQ_API_KEY).strip()
    active_provider = provider or "groq"
    active_model = model or DEFAULT_GROQ_MODEL

    if not provider or provider == "auto" or (active_provider == "gemini" and not api_key):
        if active_key and (active_key.startswith("gsk_") or "qwen" in str(active_model).lower() or "llama" in str(active_model).lower()):
            active_provider = "groq"
        elif active_key:
            active_provider = "gemini"
        else:
            active_provider = "groq"

    if active_key and active_provider in ("gemini", "groq"):
        try:
            sys_prompt = """You are PlanGenius AI, an elite event planner specializing in Weddings, Birthdays, and Community Events.
Return ONLY valid raw JSON matching the exact schema requested with realistic numbers, specific timelines, and creative ideas. Do not wrap in markdown quotes if possible."""

            user_prompt = f"""Generate a comprehensive master event plan for:
Event Type: {params.get('eventType')}
Title: {params.get('title')}
Subtype/Vibe: {params.get('subType')}
Target Date: {params.get('date')}
Location: {params.get('location')}
Guest Count: {params.get('guestCount')}
Total Budget: {params.get('currency', '$')}{params.get('totalBudget')}
Theme/Style: {params.get('theme')}
Priorities: {params.get('priorities')}
Dietary/Special Notes: {params.get('dietaryNotes')}

Return a single JSON object with these EXACT keys:
- "title": string
- "eventType": "wedding" | "birthday" | "community"
- "subType": string
- "date": YYYY-MM-DD
- "location": string
- "guestCount": integer
- "totalBudget": number
- "currency": string (e.g. "$", "€", "£")
- "theme": string
- "priorities": string
- "dietaryNotes": string
- "colorPalette": array of 5 objects: [{{"name": string, "hex": "#HEX"}}]
- "creativeIdeas": array of 4-5 objects: [{{"title": string, "category": string, "description": string}}]
- "budgetItems": array of 7-12 objects: [{{"id": string, "category": string, "name": string, "estimated": number, "actual": 0, "status": "pending", "notes": string}}]
- "timelineMilestones": array of 6-7 objects: [{{"id": string, "phase": string, "task": string, "completed": false, "dueDate": "YYYY-MM-DD"}}]
- "runOfShow": array of 6-12 objects: [{{"id": string, "time": string, "activity": string, "responsible": string, "location": string}}]
- "vendors": array of 4-6 objects: [{{"id": string, "category": string, "name": string, "contact": string, "phone": string, "status": "to_research", "quoted": number, "notes": string}}]
"""
            if active_provider == "groq":
                raw_text = call_groq_api(user_prompt, system_instruction=sys_prompt, api_key=active_key, model=active_model, json_mode=True)
            else:
                raw_text = call_gemini_api(user_prompt, system_instruction=sys_prompt, api_key=active_key, model=active_model or "gemini-2.5-flash", json_mode=True)

            cleaned = raw_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
            if not data.get("id"):
                data["id"] = f"evt-{uuid.uuid4().hex[:8]}"
            return data
        except Exception as e:
            print(f"{active_provider.capitalize()} API generation error: {e}. Falling back to local engine.")

    # Fallback to local intelligent planning engine
    return generate_local_event_plan(params)


def generate_copilot_response(messages, current_event=None, provider="groq", api_key=None, model=None):
    """
    Handle chat interactions with context of the current event.
    Always uses live Groq API by default with qwen/qwen3.8-27b.
    """
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    active_key = (api_key or DEFAULT_GROQ_API_KEY).strip()
    active_provider = provider or "groq"
    active_model = model or DEFAULT_GROQ_MODEL

    if not provider or provider == "auto" or (active_provider == "gemini" and not api_key):
        if active_key and (active_key.startswith("gsk_") or "qwen" in str(active_model).lower() or "llama" in str(active_model).lower()):
            active_provider = "groq"
        elif active_key:
            active_provider = "gemini"
        else:
            active_provider = "groq"

    if active_provider == "groq" and active_key:
        event_ctx = ""
        if current_event:
            event_ctx = f"""
Current Active Event Context:
- Title: {current_event.get('title')}
- Type: {current_event.get('eventType')} ({current_event.get('subType')})
- Date: {current_event.get('date')} | Location: {current_event.get('location')}
- Guests: {current_event.get('guestCount')}
- Total Budget: {current_event.get('currency', '$')}{current_event.get('totalBudget')}
- Spent so far: {current_event.get('currency', '$')}{sum(b.get('actual', 0) for b in current_event.get('budgetItems', []))}
- Theme: {current_event.get('theme')}
- Priorities: {current_event.get('priorities')}
- Vendors count: {len(current_event.get('vendors', []))}
- Milestones count: {len(current_event.get('timelineMilestones', []))}
"""
        sys_instruction = f"""You are PlanGenius AI Co-pilot, a friendly, ultra-knowledgeable event planning strategist.
You provide clear, actionable, structured advice (bullet points, concrete numbers, template drafts).
Always tailor your answers directly to the user's active event details. Respond naturally and helpfully to the user's input.
{event_ctx}
"""
        groq_messages = [{"role": "system", "content": sys_instruction}]
        for m in messages[-8:]:
            raw_role = m.get("role", "user")
            clean_role = "assistant" if raw_role in ["ai", "assistant", "model"] else ("system" if raw_role == "system" else "user")
            content = (m.get("content") or "").strip()
            if content:
                groq_messages.append({"role": clean_role, "content": content})

        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": active_model,
            "messages": groq_messages,
            "temperature": 0.7,
            "max_tokens": 750
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {active_key}",
                "User-Agent": "PlanGenius/1.0 (compatible; Mozilla/5.0)"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                choices = resp_data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"].get("content", "")
                return "No response received from Groq."
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            for alt_model in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]:
                if alt_model != active_model and (e.code == 429 or "rate_limit" in error_body or "model_not_found" in error_body):
                    print(f"Groq chat {active_model} issue ({e.code}). Auto-failing over to {alt_model}...")
                    return generate_copilot_response(messages, current_event=current_event, provider="groq", api_key=active_key, model=alt_model)
            return f"⚠️ Groq API Error ({e.code}): {error_body}"
        except Exception as e:
            return f"⚠️ Groq Connection Error: {str(e)}"

    elif active_provider == "gemini" and active_key:
        try:
            event_ctx = ""
            if current_event:
                event_ctx = f"""
Current Active Event Context:
- Title: {current_event.get('title')}
- Type: {current_event.get('eventType')} ({current_event.get('subType')})
- Date: {current_event.get('date')} | Location: {current_event.get('location')}
- Guests: {current_event.get('guestCount')}
- Total Budget: {current_event.get('currency', '$')}{current_event.get('totalBudget')}
- Spent so far: {current_event.get('currency', '$')}{sum(b.get('actual', 0) for b in current_event.get('budgetItems', []))}
- Theme: {current_event.get('theme')}
- Priorities: {current_event.get('priorities')}
- Vendors count: {len(current_event.get('vendors', []))}
- Milestones count: {len(current_event.get('timelineMilestones', []))}
"""
            sys_instruction = f"""You are PlanGenius AI Co-pilot, a friendly, ultra-knowledgeable event planning strategist.
You provide clear, actionable, structured advice.
Always tailor your answers directly to the user's active event details.
{event_ctx}
"""
            return call_gemini_api(last_user_msg, system_instruction=sys_instruction, api_key=active_key, model=active_model or "gemini-2.5-flash")
        except Exception as e:
            return f"⚠️ Gemini API Error: {str(e)}"

    # Local intelligent rule-based / contextual assistant
    q = last_user_msg.lower()
    event_title = current_event.get("title", "your event") if current_event else "your event"
    event_type = current_event.get("eventType", "event") if current_event else "event"
    curr = current_event.get("currency", "$") if current_event else "$"
    budget = current_event.get("totalBudget", 10000) if current_event else 10000
    guests = current_event.get("guestCount", 100) if current_event else 100

    if "budget" in q or "cost" in q or "cut" in q or "save" in q or "reduce" in q:
        ten_pct = round(budget * 0.10)
        fifteen_pct = round(budget * 0.15)
        return f"""### 💡 Strategic Budget Reduction for **{event_title}**

To trim **{curr}{ten_pct:,} to {curr}{fifteen_pct:,}** without sacrificing guest satisfaction:

1. **Strategic Beverage Reallocation**:
   - Rather than an unrestricted premium open bar, offer local craft beer, selected regional wines, and two signature craft cocktails during cocktail hour. This typically saves 20-30% on bar charges.
2. **Floral & Decor High-Impact Repurposing**:
   - Repurpose ceremony floral installations or backdrop arches to the reception sweetheart table or photo backdrop.
   - Mix high and low centerpieces: substitute half the floral arrangements with elevated glass hurricane candles and greenery sprigs.
3. **Plating & Course Optimization**:
   - Family-style or high-end stations often cut staffing fees compared to strict 4-course synchronized plated dinners.
   - Opt for seasonal in-market proteins and produce.
4. **Digital & Sustainable Stationery**:
   - Send digital Save-the-Dates and digital RSVP tracking, reserving print paper suites only for invitation keepsakes and day-of signage. Saves {curr}400–{curr}900 on postage and calligraphy.
5. **Vendor Timing Windows**:
   - Contract photography for 8 hours rather than 12 hours. Coverage from end-of-prep through 45 minutes of open dancing captures 95% of memorable moments without overtime rates.
"""

    elif "email" in q or "inquiry" in q or "vendor" in q or "contact" in q or "quote" in q:
        return f"""### ✉️ Professional Vendor Inquiry Template for **{event_title}**

Here is a tested, high-response outreach script you can copy and send:

```text
Subject: Availability & Pricing Inquiry: {event_title} on {current_event.get('date', 'Upcoming Date')}

Dear [Vendor Name / Team],

I hope this message finds you well! I admire your work and would love to check your availability for our upcoming {event_type}.

Here are the key event details:
• Event: {event_title}
• Date: {current_event.get('date', 'Upcoming Date')}
• Location: {current_event.get('location', 'Local Venue')}
• Estimated Guest Count: {guests} guests
• Style / Aesthetic: {current_event.get('theme', 'Modern Elegance')}
• Target Budget for this Service: approximately {curr}{round(budget * 0.15):,}

Could you please share your service packages, pricing brochures, and whether you are available on this date? 

If you are available, we would love to schedule a brief 15-minute introductory call to explore how we can collaborate.

Warm regards,
[Your Name]
[Your Phone Number]
[Your Email]
```
"""

    elif "timeline" in q or "schedule" in q or "day of" in q or "run of show" in q:
        return f"""### ⏱️ Day-Of Timeline Best Practices for **{event_title}**

Key timeline safeguards to guarantee a calm, seamless event:

1. **The 30-Minute 'Ghost Buffer'**:
   - Always schedule hair, makeup, or initial setup to conclude 30–45 minutes *before* first photos or guest arrivals. This absorbs inevitable traffic delays or dress steaming emergencies.
2. **Ceremony to Cocktail Transition**:
   - Account for 15 minutes of guest dispersal and hugging immediately following the ceremony before cocktail hour officially begins.
3. **Keep Speeches Punchy & Timed**:
   - Cap each toast at 3 to 4 minutes. Space them between courses rather than doing all speeches back-to-back, keeping guest energy elevated.
4. **Designate a Point Person**:
   - Never serve as the direct contact on the day. Assign a day-of coordinator, trusted family member, or bridal party lead to handle vendor arrivals and questions.
"""

    elif "speech" in q or "toast" in q or "vow" in q:
        return f"""### 🥂 Master Speech & Toast Framework for **{event_title}**

Use this proven 4-part structure (aim for 3 minutes total):

1. **The Engaging Hook (30 sec)**:
   - Introduce your relationship to the guest(s) of honor with warmth and a light, relatable opening line.
2. **The Signature Story (90 sec)**:
   - Share one specific, vivid anecdote demonstrating their authentic character, generosity, humor, or partnership. Avoid generic praise; show, don't tell!
3. **The Ripple Effect (30 sec)**:
   - Reflect on how the host/celebrant brings people together and has touched the lives of everyone in the room.
4. **The Toast (30 sec)**:
   - Raise your glass with a heartfelt, memorable closing blessing: *"To love, laughter, and an unforgettable journey ahead!"*
"""

    elif "emergency" in q or "kit" in q or "checklist" in q:
        return f"""### 🧰 Day-Of Emergency Kit Essentials

Must-pack items to keep in a designated organizer bag on site:

- **Attire & Wardrobe**: Mini sewing kit, pre-threaded needles, safety pins, lint roller, hem tape, stain remover wipes (Shout / Tide to Go), clear nail polish.
- **Health & Comfort**: Pain relievers (ibuprofen/acetaminophen), blister cushions/band-aids, antacids, eye drops, tissues, mints (avoid colored candy).
- **Tech & Tools**: Portable phone power banks with multi-cables, scissors, gaffer/fashion tape, Sharpies, lighters for candles.
- **Beauty Touch-ups**: Blotting papers, setting spray, compact mirror, hairpins, travel hairspray, deodorant wipes.
"""

    else:
        return f"""### 🌟 Planning Insights for **{event_title}**

Here are three personalized recommendations tailored to your {event_type} ({current_event.get('theme', 'celebration')}):

1. **Signature Highlight Moment**:
   - Create a focal memory anchor mid-event—whether it's a surprise musical performance, a coordinated sunset toast, or an interactive activity that gets all {guests} guests smiling together.
2. **Guest Flow & Comfort**:
   - Ensure hydration and seating options are immediately apparent upon entry. Clear directional signage prevents crowding.
3. **Action Next Step**:
   - Review your **Timeline** tab to verify that vendors have completed contracts for your top 3 milestone dates.

*Have a specific question about negotiating rates, writing speeches, or tweaking your schedule? Ask me anything!*
"""


def generate_vendor_email(vendor, event, provider="groq", api_key=None, model=None):
    """
    Draft a personalized, high-converting vendor inquiry email using live Groq AI when available.
    """
    active_key = (api_key or DEFAULT_GROQ_API_KEY).strip()
    active_provider = provider or "groq"
    active_model = model or DEFAULT_GROQ_MODEL

    category = vendor.get("category", "Service")
    vendor_name = vendor.get("name", "Vendor Team")
    event_title = event.get("title", "Our Upcoming Event")
    event_date = event.get("date", "Upcoming Date")
    location = event.get("location", "Venue TBD")
    guests = event.get("guestCount", 100)
    budget = vendor.get("quoted", 0)
    curr = event.get("currency", "$")
    budget_line = f"Target Budget Range: around {curr}{budget:,}" if budget else "We would appreciate your current standard package rates"

    if active_provider == "groq" and active_key:
        prompt = f"""Draft a professional, warm, and highly effective inquiry email to a vendor for an event.
Vendor Category: {category}
Vendor Name: {vendor_name}
Event Title: {event_title}
Event Date: {event_date}
Venue / Location: {location}
Estimated Guest Count: {guests}
{budget_line}

Requirements:
- Begin with 'Subject: Inquiry for {category} Services: {event_title} ({event_date})'
- Warm greeting to {vendor_name}
- Specific praise for their work in {category}
- Concise list of event requirements
- Call to action asking for availability, package brochure, and a discovery call
- Professional signoff with placeholders for [Your Name], [Your Phone Number], [Your Email]
Output ONLY the email text."""
        try:
            res = call_groq_api(prompt, system_instruction="You are an expert luxury event planner drafting correspondence. Output only the finished email.", api_key=active_key, model=active_model)
            if res and len(res.strip()) > 50:
                return res.strip()
        except Exception as e:
            print(f"Groq vendor email error: {e}")

    return f"""Subject: Inquiry for {category} Services: {event_title} ({event_date})

Hello {vendor_name},

I hope you're having a wonderful week!

We are currently planning {event_title} and are very impressed by your work in {category}. We would love to see if you are available for our date and explore working together.

Key Event Details:
• Event: {event_title}
• Date: {event_date}
• Venue / Location: {location}
• Estimated Guest Count: {guests}
• {budget_line}

Could you please confirm if your team is available on {event_date}? If so, please share your standard packages, typical deliverables, and booking terms.

We look forward to hearing from you and hope to connect soon!

Best regards,

[Your Name]
[Your Phone Number]
[Your Email]
"""


def generate_extra_ideas(category, event, provider="groq", api_key=None, model=None):
    """
    Generate additional creative ideas on demand using live Groq AI when available.
    """
    active_key = (api_key or DEFAULT_GROQ_API_KEY).strip()
    active_provider = provider or "groq"
    active_model = model or DEFAULT_GROQ_MODEL
    event_type = event.get("eventType", "wedding")
    theme = event.get("theme", "Celebration")
    guests = event.get("guestCount", 100)

    if active_provider == "groq" and active_key:
        prompt = f"""Generate 2 fresh, unexpected, highly creative ideas for a {event_type} in the category '{category}'.
Event Title: {event.get('title', 'Celebration')}
Theme: {theme}
Guest Count: {guests}
Location: {event.get('location', 'Scenic Venue')}

Return a JSON array containing EXACTLY 2 objects with keys:
- "title": string (catchy, creative title)
- "category": "{category.capitalize()}"
- "description": string (2-3 engaging sentences explaining the experience, aesthetic, and how guests interact with it)
Return ONLY raw JSON array."""
        try:
            raw = call_groq_api(prompt, system_instruction="You are a world-class creative director for bespoke events. Return ONLY a valid JSON array.", api_key=active_key, model=active_model, json_mode=True)
            cleaned = raw.strip()
            if cleaned.startswith("```json"): cleaned = cleaned[7:]
            if cleaned.startswith("```"): cleaned = cleaned[3:]
            if cleaned.endswith("```"): cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            if isinstance(parsed, dict):
                for val in parsed.values():
                    if isinstance(val, list) and len(val) > 0:
                        parsed = val
                        break
            if isinstance(parsed, list) and len(parsed) > 0:
                return parsed
        except Exception as e:
            print(f"Groq extra ideas error: {e}")

    if category == "drinks":
        return [
            {
                "title": f"Botanical Infusion Soda & Spritz Bar",
                "category": "Drinks",
                "description": "Craft soda fountain with house-made syrups (hibiscus lavender, ginger lemongrass, blood orange) with prosecco or club soda floats."
            },
            {
                "title": "Smoked Glass Bourbon / Mocktail Experience",
                "category": "Drinks",
                "description": "Bartender uses a handheld oak wood smoker cloche over coupe glasses before pouring, infusing the beverage with aroma."
            }
        ]
    elif category == "entertainment":
        return [
            {
                "title": "Retro Audio Record-Your-Own Vinyl Booth",
                "category": "Entertainment",
                "description": "A mini soundproof booth where guests cut a 60-second audio track onto a 7-inch vinyl record keepsake."
            },
            {
                "title": "Surprise Flash Flash-Mob / Brass Band Pop-up",
                "category": "Entertainment",
                "description": "A 5-piece brass band bursts onto the dance floor at 9:30 PM playing high-energy pop anthems."
            }
        ]
    else:
        return [
            {
                "title": "Custom Scent Blending Favor Bar",
                "category": "Favors",
                "description": "Guests select base oils and botanical botanicals into personalized 10ml rollerball perfumes or room mists."
            },
            {
                "title": "Polaroid Hanging Chandelier",
                "category": "Decor",
                "description": "An illuminated brass hoop where guests clip their candid snapshot instant photos throughout the evening."
            }
        ]
