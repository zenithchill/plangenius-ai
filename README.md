# PlanGenius AI 🌟
### GenAI-Powered Event Planning Assistant for Weddings, Birthdays & Community Events

[![Live Demo](https://img.shields.io/badge/Live_Demo-GitHub_Pages-6366F1?style=for-the-badge&logo=github)](https://zenithchill.github.io/plangenius-ai/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq_Cloud-Ultra_Fast_Inference-F97316?style=for-the-badge&logo=fastapi)](https://console.groq.com)

🔗 **Live Interactive App**: [https://zenithchill.github.io/plangenius-ai/](https://zenithchill.github.io/plangenius-ai/)

PlanGenius AI is a comprehensive planning assistant engineered to help users organize memorable **Weddings**, **Birthdays**, and **Community Events** with intelligent budgets, phased milestone timelines, day-of run-of-shows, vendor checklists with AI negotiation/inquiry email drafters, and personalized creative concepts.

---

## ✨ Key Capabilities

### 1. Multi-Event Specialization
- **Weddings**: Rehearsals, ceremonies, cocktail hours, receptions, send-offs. Culturally nuanced themes (Rustic Garden, Modern Black Tie, Desi/South Asian, Boho Beach, Minimalist City Hall).
- **Birthdays**: Milestones (18th, 21st, 30th Rooftop, 50th Gala, 80th Legacy), Kids Themed Parties (Space Odyssey, Dinosaurs, Safari, Superheroes, Fairies), Surprise Soirées.
- **Community Events**: Charity Galas & Fundraisers, Neighborhood Block Parties, Cultural Festivals, Hackathons, 5K Fun Runs, and Farmers/Artisan Markets.

### 2. Multi-Provider AI Planning Engine
- **Groq Cloud API (⚡ Ultra-Fast Inference)**: Direct integration with Groq's high-speed API supporting `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`, and `gemma2-9b-it`. Delivers lightning-fast plan generation and instant co-pilot conversational responses.
- **Google Gemini Live Integration**: Direct REST API integration for `gemini-2.5-flash`, `gemini-1.5-flash`, and `gemini-1.5-pro` with structured JSON schema output and deep conversational reasoning.
- **Built-in Local Generator (Zero Setup / Offline)**: Operates 100% offline without requiring any API keys or billing setup. Accurately synthesizes scaled budgets, phased timelines, hour-by-hour run-of-shows, vendor allocations, and personalized ideas.

### 3. Smart Wizard & Master Plan Generator
- Step 1: Event Type, Name, Style/Vibe presets, Target Date, Location.
- Step 2: Total Budget, Currency ($, €, £, ₹, C$, A$), Target Guest Count, Venue Type.
- Step 3: Aesthetic Theme, Top Priorities, Dietary Restrictions.
- One-click instant generation producing a complete, synchronized master plan in seconds.

### 4. Categorized Budget Tracker
- Real-time spending analytics: Total Budget, Allocated Estimates, Actual Deposits Paid, Remaining Balance, and Over/Under warnings.
- Category allocation progress bars.
- Itemized expense table with status toggling (`Pending`, `Deposit Paid`, `Paid in Full`), inline editing, and deletion.

### 5. Timeline & Day-Of Run-of-Show
- **Milestone Roadmap**: Grouped by phase (9-12 Months, 6 Months, 3 Months, 1 Month, 1 Week, Day Of) with completion checkboxes.
- **Day-Of Run-of-Show**: Hour-by-hour chronological schedule detailing times, activity names, responsible leads, and location zones.
- **One-Click iCalendar (.ics) Sync**: Exports RFC 5545 `.ics` files that import directly into Apple Calendar, Google Calendar, and Microsoft Outlook.

### 6. Vendor Hub & Checklist with AI Email Drafter
- Filter by category (Venue, Catering, Photography, Music, Decor, Permits, etc.) and booking status (`To Research`, `Contacted`, `Quoted`, `Booked`, `Deposit Paid`, `Completed`).
- **AI Inquiry Email Drafter**: Select any vendor and click "Draft AI Email" to generate a tailored, professional outreach email pre-filled with date, location, guest count, style vibe, and target budget.

### 7. Personalized Creative Ideas & Mood Palette
- Hex-coded color palettes with one-click click-to-copy hex codes.
- Curated signature concepts: custom cocktail/mocktail recipes, interactive guest experiences, playlist vibes, late-night food surprises, and memorable favors.
- Planning Dilemma Solver bar for instant advice on rain contingencies or seating issues.

### 8. Interactive PlanAI Co-pilot Drawer
- Always-accessible slide-over conversational assistant with active event context.
- Instant prompt pills:
  - *"How can I cut 15% from my budget without hurting the experience?"*
  - *"Draft a vendor negotiation inquiry script"*
  - *"What are common mistakes on day-of event schedules?"*
  - *"Give me a 3-minute toast outline"*
  - *"Day-of emergency kit packing checklist"*

### 9. Export, Print & Sharing
- **Print / PDF Master Sheet**: Beautiful print-optimized CSS for clean physical binder sheets or PDF exports.
- **JSON Backup & Import**: Export event plans as JSON to save or share with co-planners; import previously saved JSON plans anytime.
- **Pre-Loaded Sample Events**: Includes 4 realistic, diverse pre-populated events ready for immediate testing:
  1. *Elena & Marcus's Tuscan Garden Wedding*
  2. *Leo's Space Explorer 7th Birthday Odyssey*
  3. *Oakwood Annual Charity Gala & Block Festival*
  4. *Maya's 30th Sunset Rooftop Soirée*

---

## 🚀 Quickstart Guide

### 1. Start the Server
```bash
python3 app.py
```
The application will launch at **`http://localhost:5000`**.

### 2. Run Tests
```bash
# Run backend unit tests
python3 test_backend.py

# Run full end-to-end integration tests
python3 test_integration.py
```

---

## 📁 Project Architecture

```
├── app.py                      # Flask REST API server & static asset routes
├── ai_engine.py                # Dual AI planning engine (Gemini API & local smart generator)
├── sample_data.py              # 4 rich pre-configured sample events
├── storage.py                  # Thread-safe persistent JSON store (data/events.json)
├── test_backend.py             # Unit tests for storage, AI engine & API routes
├── test_integration.py         # End-to-end integration test suite
├── static/
│   ├── index.html              # Main Single Page Application interface
│   ├── css/
│   │   └── styles.css          # Modern dark-theme design system & print styles
│   └── js/
│       ├── app.js              # Application controller & state machine
│       ├── api.js              # REST client & localStorage configuration
│       ├── icons.js            # SVG icons catalog
│       └── components/
│           ├── wizard.js       # Multi-step event creation wizard
│           ├── budget.js       # Budget manager & category progress tracker
│           ├── timeline.js     # Milestone roadmap & Day-of run-of-show scheduler
│           ├── vendors.js      # Vendor checklist & AI email drafter
│           ├── ideas.js        # Creative concepts, color palette & dilemma solver
│           ├── guests.js       # RSVP models, table layout & volunteer shift allocator
│           └── copilot.js      # Slide-over AI Co-pilot assistant drawer
```
