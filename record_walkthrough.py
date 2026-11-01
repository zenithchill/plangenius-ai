#!/usr/bin/env python3
"""
PlanGenius AI - Automated High-Definition Walkthrough Video Recorder
Navigates the full PlanGenius AI application and records a comprehensive demo video.
"""

import os
import time
import glob
import subprocess
from playwright.sync_api import sync_playwright

RECORD_DIR = "/home/deepak/Downloads/c/recordings"
FINAL_VIDEO_MP4 = "/home/deepak/Downloads/c/plangenius_ai_submission_demo.mp4"

os.makedirs(RECORD_DIR, exist_ok=True)
for f in glob.glob(f"{RECORD_DIR}/*.webm"):
    try:
        os.remove(f)
    except Exception:
        pass

def smooth_scroll(page, start_y, end_y, steps=15, delay=0.03):
    delta = (end_y - start_y) / steps
    for i in range(steps):
        page.evaluate(f"window.scrollTo(0, {start_y + delta * (i + 1)})")
        time.sleep(delay)

def run():
    print("🎬 Starting PlanGenius AI Walkthrough Recording...")
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/usr/bin/chromium",
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--hide-scrollbars",
                "--mute-audio"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=1,
            record_video_dir=RECORD_DIR,
            record_video_size={"width": 1440, "height": 900}
        )
        page = context.new_page()
        page.set_default_timeout(8000)

        # Step 1: Open Application
        print("1. Opening PlanGenius AI dashboard...")
        page.goto("http://127.0.0.1:5000", wait_until="networkidle")
        time.sleep(2.5)

        # Overview of Hero & Metric Cards
        smooth_scroll(page, 0, 320, steps=12, delay=0.03)
        time.sleep(1.5)
        smooth_scroll(page, 320, 0, steps=12, delay=0.03)
        time.sleep(1.0)

        # Step 2: Demonstrate Multi-Event Switcher
        print("2. Demonstrating Event Switcher...")
        page.select_option("#event-switcher", "evt-birthday-space")
        time.sleep(2.0)

        page.select_option("#event-switcher", "evt-community-gala")
        time.sleep(2.0)

        page.select_option("#event-switcher", "evt-wedding-tuscan")
        time.sleep(2.0)

        # Step 3: Tab 1 - Budget Tracker
        print("3. Exploring Budget & Expense Tracker...")
        page.click("button.tab-btn[data-tab='budget']")
        time.sleep(2.0)
        smooth_scroll(page, 0, 420, steps=15, delay=0.03)
        time.sleep(2.0)
        smooth_scroll(page, 420, 0, steps=15, delay=0.03)
        time.sleep(1.0)

        # Step 4: Tab 2 - Timeline & Run of Show
        print("4. Exploring Phased Timeline & Day-Of Run of Show...")
        page.click("button.tab-btn[data-tab='timeline']")
        time.sleep(2.0)

        # Toggle a milestone completion checkbox
        try:
            checkbox = page.locator(".milestone-checkbox").first
            if checkbox.count() > 0:
                checkbox.click()
                time.sleep(1.5)
        except Exception as e:
            print("   Milestone checkbox:", e)

        # Switch to Day-Of Run of Show
        print("   Switching to Day-Of Run of Show...")
        try:
            page.click("button:has-text('Day-Of Run of Show')")
            time.sleep(2.0)
        except Exception as e:
            print("   Run of show button:", e)

        smooth_scroll(page, 0, 350, steps=12, delay=0.03)
        time.sleep(1.5)
        smooth_scroll(page, 350, 0, steps=12, delay=0.03)
        time.sleep(1.0)

        # Step 5: Tab 3 - Vendor Hub & AI Negotiation Email
        print("5. Demonstrating Vendor Hub & AI Email Drafter...")
        page.click("button.tab-btn[data-tab='vendors']")
        time.sleep(2.0)

        # Click Draft AI Email on the first vendor
        try:
            draft_btn = page.locator("button:has-text('Draft AI Email')").first
            if draft_btn.count() > 0:
                draft_btn.click()
                time.sleep(3.5)  # Wait for modal and AI generation
                # Click Copy to Clipboard
                copy_btn = page.locator("button:has-text('Copy to Clipboard')").first
                if copy_btn.count() > 0:
                    copy_btn.click()
                    time.sleep(1.5)
                # Close vendor email modal cleanly
                page.evaluate("VendorsComponent.closeEmailModal()")
                time.sleep(1.0)
        except Exception as e:
            print("   Vendor email drafter:", e)
            page.evaluate("document.querySelectorAll('.modal-overlay.active').forEach(m => m.classList.remove('active'))")

        # Step 6: Tab 4 - Creative Ideas & Mood Board
        print("6. Exploring Creative Ideas & Mood Palettes...")
        page.click("button.tab-btn[data-tab='ideas']")
        time.sleep(2.0)
        smooth_scroll(page, 0, 320, steps=12, delay=0.03)
        time.sleep(2.0)
        smooth_scroll(page, 320, 0, steps=12, delay=0.03)
        time.sleep(1.0)

        # Step 7: Tab 5 - Guest Management
        print("7. Exploring Guest Management...")
        page.click("button.tab-btn[data-tab='guests']")
        time.sleep(2.0)

        # Step 8: AI Co-pilot Drawer Interaction
        print("8. Opening AI Co-pilot Drawer...")
        try:
            page.click("button:has-text('AI Co-pilot')")
            time.sleep(2.0)

            # Send prompt: Budget reduction advice
            print("   Asking Co-pilot for strategic budget optimization...")
            prompt_pill = page.locator(".prompt-pill >> text='Cut 15% Budget'").first
            if prompt_pill.count() > 0:
                prompt_pill.click()
            else:
                page.fill("#copilot-input", "How can I cut 15% from my budget without hurting the guest experience?")
                page.click(".copilot-input-bar button")

            # Wait for live AI response
            time.sleep(4.5)

            # Ask maid of honor toast outline
            print("   Asking Co-pilot for custom speech outline...")
            page.fill("#copilot-input", "Draft a 3-minute toast outline for the maid of honor tailored to our Tuscan theme.")
            time.sleep(0.8)
            page.click(".copilot-input-bar button")
            time.sleep(5.5)

            # Scroll through Co-pilot messages
            page.evaluate("document.getElementById('copilot-messages').scrollTop = document.getElementById('copilot-messages').scrollHeight")
            time.sleep(2.5)

            # Close drawer cleanly
            page.evaluate("Copilot.close()")
            time.sleep(1.5)
        except Exception as e:
            print("   Copilot drawer:", e)
            page.evaluate("Copilot.close()")

        # Step 9: Smart Wizard Demonstration
        print("9. Launching Smart Event Wizard...")
        try:
            page.click("button:has-text('New Event')")
            time.sleep(1.5)

            # Step 1: Basic info
            page.click("button.wizard-type-btn[data-type='birthday']")
            time.sleep(0.5)
            page.fill("#wiz-title", "Aria's 30th Parisian Sunset Soiree")
            time.sleep(0.5)
            page.fill("#wiz-location", "Le Rooftop Cafe, Paris")
            time.sleep(0.5)
            page.click("button:has-text('Next: Scale & Budget')")
            time.sleep(1.0)

            # Step 2: Budget & Guests
            page.fill("#wiz-budget", "18000")
            time.sleep(0.5)
            page.fill("#wiz-guests", "65")
            time.sleep(0.5)
            page.click("button:has-text('Next: Style & Priorities')")
            time.sleep(1.0)

            # Step 3: Style & Theme
            page.fill("#wiz-theme", "French Chic with Golden Hour Jazz")
            time.sleep(0.5)
            page.fill("#wiz-priorities", "Artisanal cocktails, live jazz trio, rooftop photography")
            time.sleep(1.0)

            # Generate Master Plan
            print("   Generating Master Event Plan...")
            page.click("#wiz-submit-btn")
            time.sleep(5.0)  # Wait for generation and transition to dashboard

            # Final showcase of the newly generated event
            print("10. Showcasing newly generated event...")
            smooth_scroll(page, 0, 420, steps=15, delay=0.03)
            time.sleep(2.0)
            smooth_scroll(page, 420, 0, steps=12, delay=0.03)
            time.sleep(2.5)
        except Exception as e:
            print("   Wizard error:", e)

        print("🏁 Walkthrough scenario completed! Closing context to finalize recording...")
        page.close()
        context.close()
        browser.close()

    # Find the recorded webm file
    webm_files = glob.glob(f"{RECORD_DIR}/*.webm")
    if not webm_files:
        print("❌ No video file recorded.")
        return

    latest_webm = max(webm_files, key=os.path.getctime)
    raw_size = os.path.getsize(latest_webm)
    print(f"📹 Raw video recorded: {latest_webm} ({raw_size / (1024*1024):.2f} MB)")

    # Convert to High-Quality MP4 with faststart for universal web compatibility
    print(f"🔄 Converting to MP4: {FINAL_VIDEO_MP4}...")
    cmd = [
        "ffmpeg", "-y",
        "-i", latest_webm,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        "-crf", "22",
        "-preset", "fast",
        "-movflags", "+faststart",
        FINAL_VIDEO_MP4
    ]
    subprocess.run(cmd, check=True)
    mp4_size = os.path.getsize(FINAL_VIDEO_MP4)
    print(f"✅ Finished MP4 video: {FINAL_VIDEO_MP4} ({mp4_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    run()
