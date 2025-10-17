"""Gemini Browser Agent - Browser automation powered by Gemini Computer Use API."""

import os
import json
import time
import logging
import uuid
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from google import genai
from google.genai import types
from google.genai.types import Content, Part
from playwright.sync_api import sync_playwright, Page
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-computer-use-preview-10-2025")
SCREEN_WIDTH = int(os.environ.get("SCREEN_WIDTH", "1440"))
SCREEN_HEIGHT = int(os.environ.get("SCREEN_HEIGHT", "900"))
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
SCREENSHOT_OUTPUT_DIR = os.environ.get("SCREENSHOT_OUTPUT_DIR", "output_screenshots")


class GeminiBrowserAgent:
    """
    Browser automation agent powered by Gemini Computer Use API.

    Handles web browsing, navigation, and interaction tasks using
    Gemini's vision and action planning capabilities with Playwright.
    """

    def __init__(self, logger=None):
        """Initialize browser agent."""
        self.logger = logger or logging.getLogger("GeminiBrowserAgent")

        # Validate Gemini API key
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)

        # Browser automation state
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

        # Screenshot session setup - persistent for entire browser session
        self.session_id = (
            datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]
        )
        self.screenshot_dir = Path(SCREENSHOT_OUTPUT_DIR) / self.session_id
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.screenshot_counter = 0

        # Progress tracking
        self.progress_updates = []

        self.logger.info(f"Browser session ID: {self.session_id}")
        self.logger.info(f"Screenshots will be saved to: {self.screenshot_dir}")
        self.logger.info("Initialized GeminiBrowserAgent")

    # ------------------------------------------------------------------ #
    # Browser automation
    # ------------------------------------------------------------------ #

    def setup_browser(self):
        """Initialize Playwright browser."""
        try:
            mode = "headless" if HEADLESS else "headed"
            self.logger.info(f"Initializing browser ({mode} mode)...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=HEADLESS)
            self.context = self.browser.new_context(
                viewport={"width": SCREEN_WIDTH, "height": SCREEN_HEIGHT}
            )
            self.page = self.context.new_page()
            self.logger.info("Browser ready!")
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            raise

    def cleanup_browser(self):
        """Clean up Playwright browser resources."""
        try:
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            self.logger.info("Browser cleaned up successfully")
        except Exception as e:
            self.logger.error(f"Browser cleanup error: {e}")

    def execute_task(
        self, task: str, url: Optional[str] = "https://www.google.com"
    ) -> Dict[str, Any]:
        """
        Execute a browser automation task.

        Args:
            task: Description of the browsing task to perform
            url: Optional starting URL (defaults to Google)

        Returns:
            Dictionary with ok status and either data or error
        """
        try:
            self.logger.info(f"Task: {task}")
            self.logger.info(f"Starting URL: {url}")
            self.logger.info(f"Session ID: {self.session_id}")

            # Setup browser if not already done
            if not self.page:
                self.setup_browser()

            # Navigate to starting URL if provided
            if url:
                self.page.goto(url, wait_until="domcontentloaded", timeout=10000)
                self.logger.info(f"Navigated to: {url}")
            else:
                # Start with a search engine
                self.page.goto(
                    "https://www.google.com", wait_until="domcontentloaded", timeout=10000
                )
                self.logger.info("Starting from Google")

            # Run the browser automation loop
            result = self._run_browser_automation_loop(task)

            self.logger.info(
                f"Task completed! Screenshots saved to: {self.screenshot_dir}"
            )

            return {
                "ok": True,
                "data": result,
                "screenshot_dir": str(self.screenshot_dir),
                "session_id": self.session_id,
                "progress": self.progress_updates,
            }

        except Exception as exc:
            self.logger.exception("Browser automation failed")
            return {"ok": False, "error": str(exc)}

    def _run_browser_automation_loop(self, task: str, max_turns: int = 30) -> str:
        """
        Run the Gemini Computer Use agent loop to complete the task.

        Args:
            task: The browsing task to complete
            max_turns: Maximum number of agent turns

        Returns:
            The final result as a string
        """
        # Configure Gemini with Computer Use
        config = types.GenerateContentConfig(
            tools=[
                types.Tool(
                    computer_use=types.ComputerUse(
                        environment=types.Environment.ENVIRONMENT_BROWSER
                    )
                )
            ],
        )

        # Initial screenshot - take once and save
        initial_screenshot = self.page.screenshot(type="png")
        timestamp = datetime.now().strftime("%H%M%S")
        screenshot_path = (
            self.screenshot_dir
            / f"step_{self.screenshot_counter:02d}_initial_{timestamp}.png"
        )
        with open(screenshot_path, "wb") as f:
            f.write(initial_screenshot)
        self.logger.info(f"Saved initial screenshot: {screenshot_path}")
        self.screenshot_counter += 1

        # Build initial contents
        contents = [
            Content(
                role="user",
                parts=[
                    Part(text=task),
                    Part.from_bytes(data=initial_screenshot, mime_type="image/png"),
                ],
            )
        ]

        self.logger.info(f"Starting browser automation loop for task: {task}")
        self._add_progress("Started browser automation", "info")

        # Agent loop
        for turn in range(max_turns):
            self.logger.info(f"Turn {turn + 1}/{max_turns}")
            self._add_progress(f"Turn {turn + 1}/{max_turns}", "turn")

            try:
                # Get response from Gemini
                response = self.gemini_client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=contents,
                    config=config,
                )

                candidate = response.candidates[0]
                contents.append(candidate.content)

                # Check if there are function calls
                has_function_calls = any(
                    part.function_call for part in candidate.content.parts
                )

                if not has_function_calls:
                    # No more actions - extract final text response
                    text_response = " ".join(
                        [part.text for part in candidate.content.parts if part.text]
                    )
                    self.logger.info(f"Agent finished: {text_response}")

                    # Save final screenshot
                    timestamp = datetime.now().strftime("%H%M%S")
                    screenshot_path = (
                        self.screenshot_dir
                        / f"step_{self.screenshot_counter:02d}_final_{timestamp}.png"
                    )
                    self.page.screenshot(path=str(screenshot_path))
                    self.logger.info(f"Saved final screenshot: {screenshot_path}")
                    self.screenshot_counter += 1

                    return text_response

                # Execute function calls
                self.logger.info("Executing browser actions...")
                self._add_progress("Executing browser actions", "action")
                results = self._execute_gemini_function_calls(candidate)

                # Get function responses with new screenshot
                function_responses = self._get_gemini_function_responses(results)

                # Save screenshot after actions
                timestamp = datetime.now().strftime("%H%M%S")
                screenshot_path = (
                    self.screenshot_dir
                    / f"step_{self.screenshot_counter:02d}_{timestamp}.png"
                )
                self.page.screenshot(path=str(screenshot_path))
                self.logger.info(f"Saved screenshot: {screenshot_path}")
                self.screenshot_counter += 1

                # Add function responses to contents
                contents.append(
                    Content(
                        role="user",
                        parts=[Part(function_response=fr) for fr in function_responses],
                    )
                )

            except Exception as e:
                self.logger.error(f"Error in browser automation loop: {e}")
                raise

        # If we hit max turns, return what we have
        return f"Task reached maximum turns ({max_turns}). Please check browser state."

    def _execute_gemini_function_calls(self, candidate) -> list:
        """Execute Gemini Computer Use function calls using Playwright."""
        results = []
        function_calls = [
            part.function_call for part in candidate.content.parts if part.function_call
        ]

        for function_call in function_calls:
            fname = function_call.name
            args = function_call.args
            self.logger.info(f"Executing Gemini action: {fname}")
            self._add_progress(f"Action: {fname}", "function_call")

            action_result = {}

            try:
                if fname == "open_web_browser":
                    pass  # Already open
                elif fname == "wait_5_seconds":
                    time.sleep(5)
                elif fname == "go_back":
                    self.page.go_back()
                elif fname == "go_forward":
                    self.page.go_forward()
                elif fname == "search":
                    self.page.goto("https://www.google.com")
                elif fname == "navigate":
                    self.page.goto(args["url"], wait_until="domcontentloaded", timeout=10000)
                elif fname == "click_at":
                    actual_x = self._denormalize_x(args["x"])
                    actual_y = self._denormalize_y(args["y"])
                    self.page.mouse.click(actual_x, actual_y)
                elif fname == "hover_at":
                    actual_x = self._denormalize_x(args["x"])
                    actual_y = self._denormalize_y(args["y"])
                    self.page.mouse.move(actual_x, actual_y)
                elif fname == "type_text_at":
                    actual_x = self._denormalize_x(args["x"])
                    actual_y = self._denormalize_y(args["y"])
                    text = args["text"]
                    press_enter = args.get("press_enter", True)
                    clear_before = args.get("clear_before_typing", True)

                    self.page.mouse.click(actual_x, actual_y)
                    if clear_before:
                        self.page.keyboard.press("Meta+A")
                        self.page.keyboard.press("Backspace")
                    self.page.keyboard.type(text)
                    if press_enter:
                        self.page.keyboard.press("Enter")
                elif fname == "key_combination":
                    keys = args["keys"]
                    self.page.keyboard.press(keys)
                elif fname == "scroll_document":
                    direction = args["direction"]
                    if direction == "down":
                        self.page.keyboard.press("PageDown")
                    elif direction == "up":
                        self.page.keyboard.press("PageUp")
                    elif direction == "left":
                        self.page.keyboard.press("ArrowLeft")
                    elif direction == "right":
                        self.page.keyboard.press("ArrowRight")
                elif fname == "scroll_at":
                    actual_x = self._denormalize_x(args["x"])
                    actual_y = self._denormalize_y(args["y"])
                    direction = args["direction"]
                    magnitude = args.get("magnitude", 800)

                    # Scroll by moving to position and using wheel
                    self.page.mouse.move(actual_x, actual_y)
                    scroll_amount = int(magnitude * SCREEN_HEIGHT / 1000)
                    if direction == "down":
                        self.page.mouse.wheel(0, scroll_amount)
                    elif direction == "up":
                        self.page.mouse.wheel(0, -scroll_amount)
                    elif direction == "left":
                        self.page.mouse.wheel(-scroll_amount, 0)
                    elif direction == "right":
                        self.page.mouse.wheel(scroll_amount, 0)
                elif fname == "drag_and_drop":
                    x = self._denormalize_x(args["x"])
                    y = self._denormalize_y(args["y"])
                    dest_x = self._denormalize_x(args["destination_x"])
                    dest_y = self._denormalize_y(args["destination_y"])

                    self.page.mouse.move(x, y)
                    self.page.mouse.down()
                    self.page.mouse.move(dest_x, dest_y)
                    self.page.mouse.up()
                else:
                    self.logger.warning(f"Unimplemented action: {fname}")

                # Quick stability check - only wait if navigation occurred
                if fname in ["navigate", "go_back", "go_forward", "search"]:
                    self.page.wait_for_load_state("domcontentloaded", timeout=3000)
                else:
                    time.sleep(0.3)  # Brief pause for UI updates

            except Exception as e:
                self.logger.error(f"Error executing {fname}: {e}")
                action_result = {"error": str(e)}

            # Get safety decision from the function call if present
            safety_decision = None
            if hasattr(function_call, 'safety_decision'):
                safety_decision = function_call.safety_decision
                self.logger.info(f"Safety decision present for {fname}: {safety_decision}")

            results.append((fname, action_result, safety_decision))

        return results

    def _get_gemini_function_responses(self, results: list):
        """Generate function responses with current screenshot."""
        screenshot_bytes = self.page.screenshot(type="png")
        current_url = self.page.url
        function_responses = []

        for name, result, safety_decision in results:
            response_data = {"url": current_url}
            response_data.update(result)

            # Build function response with safety acknowledgment if present
            func_response = types.FunctionResponse(
                name=name,
                response=response_data,
                parts=[
                    types.FunctionResponsePart(
                        inline_data=types.FunctionResponseBlob(
                            mime_type="image/png", data=screenshot_bytes
                        )
                    )
                ],
            )

            # Acknowledge safety decision if present
            if safety_decision is not None:
                func_response.safety_decision_acknowledgment = safety_decision

            function_responses.append(func_response)

        return function_responses

    def _add_progress(self, message: str, event_type: str):
        """Add a progress update with timestamp."""
        self.progress_updates.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
            "message": message
        })

    def _denormalize_x(self, x: int) -> int:
        """Convert normalized x coordinate (0-999) to actual pixel coordinate."""
        return int(x / 1000 * SCREEN_WIDTH)

    def _denormalize_y(self, y: int) -> int:
        """Convert normalized y coordinate (0-999) to actual pixel coordinate."""
        return int(y / 1000 * SCREEN_HEIGHT)
