import asyncio
import os
import sys
from jarvis_core import speak, listen
from brain import parse_intent
from browser_manager import BrowserManager
from commerce_agents.amazon_agent import AmazonAgent
from dotenv import load_dotenv

load_dotenv()

# SHOPPING STATES
class States:
    IDLE = "IDLE"
    BROWSING = "BROWSING"           # On a page, generic
    SEARCH_RESULTS = "SEARCH_RESULTS" # Just searched, asking to scroll
    PRODUCT_PAGE = "PRODUCT_PAGE"     # Viewing product, asking to add to cart
    CART_ADDED = "CART_ADDED"         # Added, asking to checkout
    CHECKOUT_FLOW = "CHECKOUT_FLOW"   # In checkout, handling payment
    CONFIRM_ORDER = "CONFIRM_ORDER"   # Final 5s wait
    AWAITING_CANCELLATION_CONFIRM = "AWAITING_CANCELLATION_CONFIRM"

# Global state
shopping_state = {
    "current_state": States.IDLE,
    "current_agent": None, 
    "browser_mgr": None,
    "page": None,
    "last_search_query": None,
    "payment_method": "cod", # Default
    "last_candidates": []
}

async def init_browser():
    shopping_state["browser_mgr"] = BrowserManager(user_data_dir="user_data", headless=False)
    try:
        shopping_state["page"] = await shopping_state["browser_mgr"].start()
        shopping_state["current_agent"] = AmazonAgent(shopping_state["page"], speak)
        return True
    except Exception as e:
        speak("Failed to launch browser.")
        print(f"Error: {e}")
        return False

async def main():
    print("--- JARVIS VOICE SHOPPING SYSTEM ONLINE ---")
    speak("Automated online ordering system is online. I am Jarvis. How may I assist you, sir?")
    
    try:
        while True:
            # 1. LISTEN
            user_text = listen()
            if user_text == "none":
                await asyncio.sleep(0.1)
                continue
            
            print(f"User said: {user_text}")
            # Give the audio hardware a moment to switch from Mic to Speaker
            if sys.platform == "win32":
                await asyncio.sleep(0.2)

            # 2. CHECK GLOBAL EXIT
            if any(w in user_text.lower() for w in ["exit", "shutdown", "terminate"]):
                speak("Shutting down. Goodbye.")
                break

            # 3. CONTEXTUAL HANDLING BEFORE AI PARSING
            # Handle YES/NO based on state
            state = shopping_state["current_state"]
            
            # 4. PARSE INTENT
            analysis = parse_intent(user_text)
            intent = analysis.get("intent")
            data = analysis.get("data")
            print(f"DEBUG: State={state}, Intent={intent}, Data={data}")
            
            # Special check for CONFIRM_ORDER to prevent accidental searches
            if state == States.CONFIRM_ORDER:
                if intent == "CONFIRM" or (intent == "GENERAL" and any(w in user_text.lower() for w in ["yes", "confirm", "proceed"])):
                    await shopping_state["current_agent"].place_order()
                    shopping_state["current_state"] = States.IDLE
                    continue
                elif intent == "DENY" or (intent == "GENERAL" and any(w in user_text.lower() for w in ["no", "cancel"])):
                    speak("Order cancelled.")
                    shopping_state["current_state"] = States.CHECKOUT_FLOW
                    continue
                else:
                    speak("Sir, I am waiting for your confirmation to place the order. Say 'Yes' to proceed or 'No' to cancel.")
                    continue

            # 5. STATE MACHINE & EXECUTIONS
            agent = shopping_state["current_agent"]

            # GLOBAL NAVIGATION COMMANDS (Refresh/Back/Navigate)
            if intent == "REFRESH" and shopping_state["page"]:
                speak("Refreshing page.")
                await shopping_state["browser_mgr"].reload_page()
                continue
            elif intent == "GO_BACK" and shopping_state["page"]:
                speak("Going back to previous page.")
                await shopping_state["browser_mgr"].go_back()
                # Reset state to safe default if back
                if state == States.PRODUCT_PAGE:
                    shopping_state["current_state"] = States.SEARCH_RESULTS
                continue
            
            elif intent == "SCROLL_DOWN" and shopping_state["page"]:
                speak("Scrolling down.")
                await shopping_state["page"].mouse.wheel(0, 600)
                await asyncio.sleep(1)
                continue
            
            elif intent == "SCROLL_UP" and shopping_state["page"]:
                speak("Scrolling up.")
                await shopping_state["page"].mouse.wheel(0, -600)
                await asyncio.sleep(1)
                continue
            
            elif intent == "CANCEL_ORDER" and shopping_state["page"]:
                speak("Sir, are you sure you want to cancel your last order? Say 'Yes' to confirm or 'No' to keep it.")
                shopping_state["current_state"] = States.AWAITING_CANCELLATION_CONFIRM
                continue

            elif intent == "NAVIGATE" or intent == "NAVIGATE_SEARCH":
                data_val = data.get("site") if isinstance(data, dict) else data
                if "amazon" in str(data_val).lower():
                    speak("Opening Amazon.")
                    # Init if needed
                    if not shopping_state["page"]:
                        if not await init_browser():
                             continue # Fail to init
                    
                    agent = shopping_state["current_agent"]
                    await shopping_state["page"].goto("https://www.amazon.in")
                    await agent.ensure_loggedin()
                    
                    if intent == "NAVIGATE_SEARCH":
                        query = data.get("query")
                        speak(f"Searching for {query}...")
                        await agent.search(query)
                        shopping_state["current_state"] = States.SEARCH_RESULTS
                        speak("The search results are here. Should I scroll down?")
                    else:
                        shopping_state["current_state"] = States.BROWSING
                        speak("Amazon is open. I am standing by.")
                elif "orders" in str(data_val).lower() or "returns" in str(data_val).lower():
                    speak("Opening your order history.")
                    if not shopping_state["page"]:
                         if not await init_browser(): continue
                    await shopping_state["page"].goto("https://www.amazon.in/gp/css/order-history")
                    shopping_state["current_state"] = States.BROWSING
                else:
                    speak("I can only open Amazon or your Orders right now.")
                continue

            # --- IDLE STATE ---
            if state == States.IDLE:
                if intent == "GENERAL":
                    speak(str(data) if data else "I am listening.")

            # --- BROWSING / SEARCH RESULTS ---
            elif state in [States.BROWSING, States.SEARCH_RESULTS, "AWAITING_PRICE", "CONFIRM_SELECTION"]:
                
                # Sub-state: AWAITING_PRICE
                if state == "AWAITING_PRICE":
                    # Treat input as price for identification
                    speak(f"Checking for product with price {user_text}")
                    result = await agent.identify_product(user_text) # Use text as identifier which falls back to price
                    # Process result below (merged logic)
                
                # Sub-state: CONFIRM_SELECTION
                elif state == "CONFIRM_SELECTION":
                    if intent == "CONFIRM" or (intent == "SELECT" and "open" in user_text):
                        item = shopping_state.get("pending_selection")
                        if item:
                            speak("Opening product page.")
                            success = await agent.click_product(item)
                            if success:
                                shopping_state["current_state"] = States.PRODUCT_PAGE
                                speak("Product details page is loaded. Should I add the item to cart?")
                            else:
                                speak("I couldn't verify that the product page loaded correctly, sir. Please try selecting it again.")
                                shopping_state["current_state"] = States.SEARCH_RESULTS
                        else:
                            speak("Selection lost. Please select again.")
                            shopping_state["current_state"] = States.SEARCH_RESULTS
                    elif intent == "DENY":
                        speak("Okay, please select another product.")
                        shopping_state["current_state"] = States.SEARCH_RESULTS
                    
                    # Stop processing other intents here if we were in confirmation state
                    continue

                # Normal Search/Select Handling
                if intent == "SEARCH":
                    speak(f"Searching for {data}...")
                    await agent.search(data)
                    shopping_state["current_state"] = States.SEARCH_RESULTS
                    speak("The search results are here. Should I scroll down?")
                

                elif intent == "SELECT" or state == "AWAITING_PRICE":
                    target = data if data else user_text
                    
                    # 1. Handle "Option X" from previous list
                    if str(target).isdigit() and len(shopping_state.get("last_candidates", [])) > 0:
                        idx = int(target) - 1
                        if 0 <= idx < len(shopping_state["last_candidates"]):
                            candidate = shopping_state["last_candidates"][idx]
                            shopping_state["pending_selection"] = candidate
                            shopping_state["last_candidates"] = [] # Clear
                            shopping_state["current_state"] = "CONFIRM_SELECTION"
                            speak(f"I found {candidate['title'][:50]}... for {candidate['price']}. Should I open this?")
                            continue

                    # 2. Regular identification
                    result = await agent.identify_product(target)
                    status = result['status']
                    
                    if status == "match":
                        candidate = result['candidates'][0]
                        title = candidate['title']
                        price = candidate['price']
                        shopping_state["pending_selection"] = candidate
                        shopping_state["last_candidates"] = [] # Clear
                        shopping_state["current_state"] = "CONFIRM_SELECTION"
                        speak(f"I found {title[:50]}... for {price}. Should I open this?")
                        
                    elif status == "multiple":
                        cands = result['candidates']
                        shopping_state["last_candidates"] = cands # STORE THEM
                        speak(f"I found {len(cands)} options.")
                        for i, c in enumerate(cands):
                            speak(f"Option {i+1}: {c['title'][:50]}... Price: {c['price']}")
                        
                        if len(cands) == 1:
                            speak("Please select Option 1.")
                        else:
                            speak(f"Please select Option 1 to {len(cands)}.")
                        shopping_state["current_state"] = States.SEARCH_RESULTS
                        
                    else:
                        if state == "AWAITING_PRICE":
                            speak("Still no match found. Please try searching again.")
                            shopping_state["current_state"] = States.SEARCH_RESULTS
                        else:
                            speak("I could not find that product by name. Please tell me the price.")
                            shopping_state["current_state"] = "AWAITING_PRICE"
                
                elif state == States.SEARCH_RESULTS and intent == "CONFIRM":
                    # User said "Yes" to "Should I scroll down?"
                    speak("Scrolling down.")
                    await shopping_state["page"].mouse.wheel(0, 600)
                
                elif state == States.SEARCH_RESULTS and intent == "DENY":
                    speak("Okay, waiting for your command.")

            # --- PRODUCT PAGE ---
            elif state == States.PRODUCT_PAGE:
                if intent == "ADD_TO_CART" or intent == "CONFIRM":
                    # "Yes" (to 'add to cart?') or "Add to cart"
                    speak("Attempting to add to cart.")
                    if await agent.add_to_cart():
                        shopping_state["current_state"] = States.CART_ADDED
                        speak("Item added to cart successfully. Should I proceed to checkout?")
                    else:
                        speak("I couldn't find the add to cart button. You might need to select a variant manually.")
                
                elif intent == "DENY":
                    speak("Okay. Staying on product page.")
                
                elif intent == "SEARCH":
                    speak(f"Searching for {data}...")
                    await agent.search(data)
                    shopping_state["current_state"] = States.SEARCH_RESULTS
                    speak("The search results are here. Should I scroll down?")

            # --- CART ADDED ---
            elif state == States.CART_ADDED:
                if intent == "CHECKOUT" or intent == "CONFIRM":
                    # "Yes" (to 'proceed to checkout?') or "Checkout"
                    speak("Navigating to checkout info page. Please monitor the process.")
                    if await agent.checkout():
                         shopping_state["current_state"] = States.CHECKOUT_FLOW
                         # Verify Payment Options
                         speak("I am checking for COD availability.")
                         # Logic to check COD would go here, assuming available for now or basic 'handle_payment'
                         # We'll ask the user.
                         speak("Would you like to continue with Cash on Delivery?")
                elif intent == "DENY":
                    speak("Okay, staying in cart.")

            # --- CHECKOUT FLOW ---
            elif state == States.CHECKOUT_FLOW:
                if intent == "CONFIRM": # "Yes" to COD
                    if await agent.handle_payment("cod"):
                        shopping_state["current_state"] = States.CONFIRM_ORDER
                        speak("Selected Cash on Delivery. Waiting 5 seconds before placing order. Say 'Yes' to confirm.")
                    else:
                        speak("I couldn't select Cash on Delivery automatically. Please select it manually on your screen, then say 'place order'.")
                        # Transition to a state where we just wait for final 'place order'
                        shopping_state["current_state"] = States.CONFIRM_ORDER 
                    await asyncio.sleep(1) # Small pause
                
                elif intent == "DENY" or intent == "PAYMENT_METHOD":
                    # "No" or "Use Card"
                    method = data if data else "card" # Default fallback if just 'No' 
                    if intent == "DENY":
                        speak("Which payment option would you like to choose?")
                        # We wait for next loop usually, but let's just prompt
                        continue 
                    
                    await agent.handle_payment(method)
                    shopping_state["current_state"] = States.CONFIRM_ORDER
                    speak(f"Selected {method}. Waiting 5 seconds before placing order. Say 'Yes' to confirm.")

            # --- CONFIRM ORDER ---
            elif state == States.CONFIRM_ORDER:
                 # Logic handled in step 3 mainly, but if intent parses:
                 if intent == "CONFIRM" or intent == "PLACE_ORDER":
                     await agent.place_order()
                     speak("Order placed successfully.")
                     shopping_state["current_state"] = States.IDLE
            
            # --- AWAITING CANCELLATION CONFIRM ---
            elif state == States.AWAITING_CANCELLATION_CONFIRM:
                if intent == "CONFIRM" or (intent == "GENERAL" and any(w in user_text.lower() for w in ["yes", "proceed", "cancel it", "confirm"])):
                    success = await agent.cancel_order()
                    if success:
                        speak("Order cancellation confirmed.")
                    else:
                        # Error message already spoken by agent
                        pass
                    shopping_state["current_state"] = States.IDLE
                elif intent == "DENY" or (intent == "GENERAL" and any(w in user_text.lower() for w in ["no", "keep", "don't"])):
                    speak("Okay, order remains active.")
                    shopping_state["current_state"] = States.IDLE
                else:
                    speak("I am waiting for your confirmation to cancel the order. Say 'Yes' to cancel or 'No' to keep it.")
                    continue

            # Fallback for unexpected intents
            pass

    except Exception as e:
        print(f"Critical Error: {e}")
        speak("Critical error encountered.")
    finally:
        if shopping_state["browser_mgr"]:
            await shopping_state["browser_mgr"].close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
