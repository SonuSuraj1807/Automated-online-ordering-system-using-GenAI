import os
import asyncio
import shutil
from google import genai
from playwright.async_api import async_playwright
from jarvis_core import speak, listen

# ==============================================================================
# 1. SYSTEM INITIALIZATION & API CONFIGURATION
# ==============================================================================
# Ensure you have run: export GEMINI_API_KEY='your_key'
API_KEY = os.getenv("GEMINI_API_KEY") 
client = genai.Client(api_key=API_KEY)

async def jarvis_brain(command):
    """
    Intelligent intent classifier with built-in quota protection.
    """
    cmd_lower = command.lower()
    
    # LOCAL SHORTCUTS: Skip API for basic commands to avoid 429 quota errors
    if any(word in cmd_lower for word in ["shutdown", "exit", "logout", "cart", "checkout", "scroll"]):
        return "COMMAND"
        
    try:
        prompt = (
            f"You are the brain of Jarvis. The user said: '{command}'. "
            "If they want to search for something, return ONLY the product name. "
            "Otherwise, return 'COMMAND'."
        )
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return response.text.strip().replace("'", "").replace('"', "")
    except Exception as e:
        print(f"!!! LLM Quota Limit: Switching to Local Logic. {e}")
        # Manual fallbacks if API is exhausted
        if "macbook" in cmd_lower: return "macbook"
        if "watch" in cmd_lower: return "watch"
        return "None"

# ==============================================================================
# 2. MAIN EXECUTION ENGINE
# ==============================================================================
async def run_jarvis():
    speak("Automated online ordering system is online. Persistent systems active. How can I help you, sir?")
    
    playwright_instance = None
    context = None
    page = None

    while True:
        user_input = listen().lower()
        if user_input == "none" or len(user_input) < 2:
            continue
            
        print(f"Recognized: {user_input}")

        # --- GLOBAL COMMAND: SYSTEM SHUTDOWN ---
        if any(word in user_input for word in ["exit", "shutdown", "stop", "power off", "shut"]):
            speak("Understood, sir. Terminating sessions and powering down. Goodbye.")
            if context: await context.close()
            if playwright_instance: await playwright_instance.stop()
            break

        # --- GLOBAL COMMAND: CLEAR SESSION (LOGOUT) ---
        elif "logout" in user_input or "clear session" in user_input:
            speak("Initiating session wipe. Deleting saved login data.")
            if context:
                await context.close()
                context = None
            if playwright_instance:
                await playwright_instance.stop()
                playwright_instance = None
            
            if os.path.exists('user_data'):
                shutil.rmtree('user_data') #
                speak("The session vault has been cleared.")
            continue

        # --- BROWSER INITIALIZATION ---
        if not context and any(word in user_input for word in ["search", "find", "amazon", "open", "log in", "macbook", "watch"]):
            speak("Accessing your Chrome session. Please stand by.")
            playwright_instance = await async_playwright().start()
            
            # Loads existing 'user_data' folder for auto-login
            context = await playwright_instance.chromium.launch_persistent_context(
                user_data_dir='user_data', 
                channel="chrome", 
                headless=False
            )
            
            page = context.pages[0] if context.pages else await context.new_page()
            
            if page.url == "about:blank" or "amazon.in" not in page.url:
                await page.goto("https://www.amazon.in", wait_until="domcontentloaded")

        # --- COMMAND: SEARCH ---
        if any(word in user_input for word in ["search", "find", "look for"]):
            product = await jarvis_brain(user_input)
            if product not in ["None", "COMMAND"]:
                speak(f"Searching Amazon for {product}.")
                if "amazon.in" not in page.url:
                    await page.goto("https://www.amazon.in")
                
                await page.wait_for_selector("#twotabsearchtextbox", timeout=10000)
                await page.fill("#twotabsearchtextbox", product)
                await page.press("#twotabsearchtextbox", "Enter")
                speak(f"I have results for {product}. Shall I scroll or select one?")

        # --- COMMAND: SCROLLING ---
        elif "scroll down" in user_input:
            if page:
                speak("Scrolling down for you, sir.")
                await page.mouse.wheel(0, 800) #
        elif "scroll up" in user_input:
            if page:
                speak("Scrolling back up.")
                await page.mouse.wheel(0, -800)

        # --- COMMAND: SELECT PRODUCT (TAB TRACKING) ---
        elif "select" in user_input or "click" in user_input:
            if page:
                speak("Selecting the top result. Switching to the product tab.")
                # Handles Amazon opening products in new tabs
                async with context.expect_page() as new_page_info:
                    await page.click(".s-image")
                page = await new_page_info.value 
                await page.bring_to_front()
                await page.wait_for_load_state("domcontentloaded")
                speak("Product page is loaded. Shall I add it to the cart?")

        # --- COMMAND: ADD TO CART (REFINED) ---
        elif "add to cart" in user_input:
            if page:
                speak("Searching for the cart button, sir.")
                await asyncio.sleep(2) # Give the page time to be interactive
                try:
                    cart_selectors = [
                        "#add-to-cart-button", 
                        "#add-to-cart-button-ubb", 
                        "input[name='submit.add-to-cart']"
                    ]
                    
                    button_found = False
                    for selector in cart_selectors:
                        if await page.query_selector(selector):
                            await page.click(selector)
                            button_found = True
                            break
                    
                    if button_found:
                        speak("Success. The item is in your cart.")
                        try:
                            await page.wait_for_selector(".a-size-medium-plus, #upsell-messaging-id", timeout=3000)
                            delivery = await page.inner_text(".a-size-medium-plus, #upsell-messaging-id")
                            speak(f"Estimated arrival is {delivery}.")
                        except:
                            pass
                    else:
                        # Fallback: Reload and scroll
                        await page.reload()
                        await page.mouse.wheel(0, 400)
                        speak("I've refreshed the page and scrolled. Please try the add to cart command again.")
                except Exception:
                    speak("I encountered a technical error with the cart system.")

        # --- COMMAND: CHECKOUT ---
        elif any(word in user_input for word in ["checkout", "proceed", "buy now"]):
            if page:
                speak("Navigating to the checkout terminal.")
                await page.goto("https://www.amazon.in/gp/cart/view.html")
                try:
                    # Direct click on the checkout button
                    await page.wait_for_selector("input[name='proceedToRetailCheckout']")
                    await page.click("input[name='proceedToRetailCheckout']")
                    speak("Final checkout screen reached. Please verify details, sir.")
                except:
                    speak("Navigation failed. Please ensure you are logged in.")

        # --- FALLBACK: CONVERSATION ---
        else:
            try:
                chat = client.models.generate_content(model="gemini-2.5-flash", contents=f"Reply as Jarvis: {user_input}")
                speak(chat.text)
            except:
                speak("I am standing by.")

if __name__ == "__main__":
    asyncio.run(run_jarvis())