import os
import json
from google import genai
from openai import OpenAI
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# Gemini Config
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_KEY)

# OpenAI Config
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_KEY) if OPENAI_KEY else None

# Groq Config (3rd Fallback)
GROQ_KEY = os.getenv("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_KEY) if GROQ_KEY else None

SYSTEM_PROMPT = """
You are the brain of 'Jarvis', a voice shopping assistant. 
Your job is to classify the USER's voice command into an INTENT and extracted PARAMETERS.

INTENTS:
1. SEARCH: User wants to find a product.
2. SELECT: User wants to click/choose a specific product or option (by name, number, or price).
3. SCROLL_DOWN: User wants to see more items below.
4. SCROLL_UP: User wants to go up.
5. ADD_TO_CART: User wants to buy/add the current item.
6. CHECKOUT: User wants to proceed to buying.
7. PAYMENT_METHOD: User is selecting a payment method (COD, Card, etc.).
8. PLACE_ORDER: User explicitly confirms to place the order.
9. GENERAL: General conversation, greeting, or unclear.
10. NAVIGATE: User wants to open a specific website or platform (e.g. Amazon, Flipkart).
11. CONFIRM: User says "Yes", "Proceed", "Do it", "Sure".
12. DENY: User says "No", "Cancel", "Stop", "Don't".
13. REFRESH: User says "Refresh page", "Reload".
14. GO_BACK: User says "Go back", "Previous page".
15. CANCEL_ORDER: User wants to cancel the order they just placed or their last order.

OUTPUT FORMAT:
Return ONLY a JSON object. No markdown.
{
  "intent": "INTENT_NAME",
  "data": "Extracted value (product name, payment method arg, specific select keywords, or chat response for general)"
}

EXAMPLES:
User: "Find iphone 15 pro" -> {"intent": "SEARCH", "data": "iphone 15 pro"}
User: "Search for red shoes" -> {"intent": "SEARCH", "data": "red shoes"}
User: "Select the second one" -> {"intent": "SELECT", "data": "2"}
User: "Choose the blue one" -> {"intent": "SELECT", "data": "blue"}
User: "Select the option with 500 rupees" -> {"intent": "SELECT", "data": "500"}
User: "Move down" -> {"intent": "SCROLL_DOWN", "data": null}
User: "Buy this now" -> {"intent": "ADD_TO_CART", "data": null}
User: "Go to checkout" -> {"intent": "CHECKOUT", "data": null}
User: "Pay with cash" -> {"intent": "PAYMENT_METHOD", "data": "cod"}
User: "Use card" -> {"intent": "PAYMENT_METHOD", "data": "card"}
User: "Place the order" -> {"intent": "PLACE_ORDER", "data": null}
User: "Start over" -> {"intent": "GENERAL", "data": "Resetting context."}
User: "Hello" -> {"intent": "GENERAL", "data": "Hello sir, I am online."}
User: "Open Amazon" -> {"intent": "NAVIGATE", "data": "amazon"}
User: "Go to Flipkart" -> {"intent": "NAVIGATE", "data": "flipkart"}
User: "Yes" -> {"intent": "CONFIRM", "data": null}
User: "No" -> {"intent": "DENY", "data": null}
User: "Refresh" -> {"intent": "REFRESH", "data": null}
User: "Go back" -> {"intent": "GO_BACK", "data": null}
"""

def parse_local_intent(text):
    """
    Fast, offline intent recognition for common commands to save API quota.
    Returns {"intent": ..., "data": ...} or None if uncertain.
    """
    text = text.lower().strip()
    print(f"DEBUG: Local Brain checking: '{text}'")
    
    # ADD_TO_CART
    if any(w in text for w in ["add to cart", "buy this", "autocar", "add item", "put in cart", "add to car"]):
        return {"intent": "ADD_TO_CART", "data": None}

    # COMPOUND: NAVIGATE + SEARCH
    if ("open amazon" in text or "go to amazon" in text) and ("search" in text or "find" in text):
        # Extract query: everything after 'search for' or 'find'
        query = ""
        if "search for " in text: query = text.split("search for ")[-1].strip()
        elif "search " in text: query = text.split("search ")[-1].strip()
        elif "find " in text: query = text.split("find ")[-1].strip()
        
        if query:
            return {"intent": "NAVIGATE_SEARCH", "data": {"site": "amazon", "query": query}}

    # SEARCH (Local fallback)
    if text.startswith("search for ") or text.startswith("find ") or text.startswith("buy ") or text.startswith("show me "):
        query = text.replace("search for ", "").replace("find ", "").replace("buy ", "").replace("show me ", "").strip()
        if query:
             return {"intent": "SEARCH", "data": query}

    # NAVIGATE
    if any(w in text for w in ["open amazon", "go to amazon", "home page"]):
        return {"intent": "NAVIGATE", "data": "amazon"}
    if any(w in text for w in ["open flipkart", "go to flipkart"]):
        return {"intent": "NAVIGATE", "data": "flipkart"}
    if any(w in text for w in ["orders", "order history", "returns", "my purchases"]):
        return {"intent": "NAVIGATE", "data": "orders"}
    
    # NAVIGATION
    if "refresh" in text or "reload" in text:
        return {"intent": "REFRESH", "data": None}
    if "go back" in text or "previous page" in text:
        return {"intent": "GO_BACK", "data": None}
        
    # SCROLL
    if "scroll down" in text:
        return {"intent": "SCROLL_DOWN", "data": None}
    if "scroll up" in text:
        return {"intent": "SCROLL_UP", "data": None}
        
    # CANCEL_ORDER (Higher priority than general DENY)
    if any(w in text for w in ["cancel order", "cancel my order", "cancel recent", "cancel last", "cancel my last", "abort purchase", "stop order"]):
        return {"intent": "CANCEL_ORDER", "data": None}

    # CONFIRM / YES
    confirm_words = ["yes", "sure", "ok", "okay", "proceed", "do it", "open", "confirm", "go ahead", "continue", "yep", "yup"]
    if any(w == text for w in confirm_words) or any(w in text for w in ["confirm", "proceed", "continue"]):
        return {"intent": "CONFIRM", "data": None}

    # DENY / NO
    deny_words = ["no", "cancel", "stop", "don't", "wait", "deny", "negative", "nope"]
    if any(w == text for w in deny_words) or (len(text.split()) == 1 and "cancel" in text):
        return {"intent": "DENY", "data": None}
        
    # CHECKOUT
    if any(w in text for w in ["checkout", "go to checkout", "proceed to buy", "buy now"]):
        return {"intent": "CHECKOUT", "data": None}
        
    # PAYMENT
    if any(w in text for w in ["cash on delivery", "cod", "pay cash"]):
        return {"intent": "PAYMENT_METHOD", "data": "cod"}
    if any(w in text for w in ["card", "credit card", "debit card"]):
        return {"intent": "PAYMENT_METHOD", "data": "card"}
        
    # PLACE_ORDER
    if any(w in text for w in ["place order", "place the order", "confirm order", "final order"]):
        return {"intent": "PLACE_ORDER", "data": None}

    # SELECT
    if any(w in text for w in ["select", "choose", "open ", "click", "option"]):
        # Extract potential data (numbers or product names)
        # remove the command word and filler
        clean = text.replace("select", "").replace("choose", "").replace("open", "").replace("click", "").replace("option", "")
        clean = clean.replace("the product with name", "").replace("with name", "").replace("the product", "").replace("the one", "")
        
        # Simple word-to-number for options 1-5
        mapping = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "first": "1", "second": "2", "third": "3"}
        val = clean.strip()
        if val in mapping:
            val = mapping[val]
            
        return {"intent": "SELECT", "data": val}
    
    # NUMERIC ONLY (often a price or option selection)
    if text.replace(" ", "").isdigit():
        return {"intent": "SELECT", "data": text}

    return None

def parse_intent(user_text):
    if not user_text or user_text == "none":
        return {"intent": "NONE", "data": None}

    # 1. Try local match first (Fast & Free)
    local_result = parse_local_intent(user_text)
    if local_result:
        # Log for debug
        # print(f"DEBUG: Local Intent Match: {local_result}")
        return local_result

    # 2. Try Gemini (Primary)
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=f"{SYSTEM_PROMPT}\nUser: {user_text}"
        )
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text)
        
    except Exception as e:
        print(f"DEBUG: Gemini Failure ({e}). Attempting OpenAI failover...")
        
        # 3. Try OpenAI (Fallback)
        if openai_client:
            try:
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ],
                    response_format={ "type": "json_object" }
                )
                text = response.choices[0].message.content
                return json.loads(text)
            except Exception as oe:
                print(f"DEBUG: OpenAI Failure ({oe})")
        
        # 4. Try Groq (Tertiary Fallback) - Ultra fast & Generous free tier
        if groq_client:
            try:
                print("DEBUG: Attempting Groq failover...")
                response = groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_text}
                    ],
                    response_format={ "type": "json_object" }
                )
                text = response.choices[0].message.content
                return json.loads(text)
            except Exception as ge:
                print(f"DEBUG: Groq Failure ({ge})")

        # 5. Final Fallback
        return {"intent": "GENERAL", "data": "I'm having trouble connecting to my brain, sir. Please try again or use simple commands."}



