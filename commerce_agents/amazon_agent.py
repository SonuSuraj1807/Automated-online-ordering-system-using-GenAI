import asyncio
import os
import datetime
from .base_agent import CommerceAgent
from helpers import parse_price

class AmazonAgent(CommerceAgent):
    def __init__(self, page, speaker):
        super().__init__(page)
        self.speaker = speaker # To talk back during actions

    async def ensure_loggedin(self):
        """Checks if logged in, if not, prompts user (voice flow usually requires pre-login or manual intervention first time)."""
        # Amazon specific login check could be finding "Hello, Sign in" vs "Hello, [Name]"
        try:
            # If "Hello, sign in" is visible, we are likely not logged in.
            if await self.page.query_selector("text='Hello, sign in'"):
                 self.speaker("It seems you are not logged in. Please log in manually once, and I will remember it next time.")
                 # potentially wait here or just return
        except:
            pass

    async def search(self, query):
        if "amazon.in" not in self.page.url:
            await self.page.goto("https://www.amazon.in")
        
        await self.page.wait_for_selector("#twotabsearchtextbox", timeout=10000)
        await self.page.fill("#twotabsearchtextbox", query)
        await self.page.press("#twotabsearchtextbox", "Enter")
        await self.page.wait_for_load_state("domcontentloaded")
        # Speech handled by main.py

    async def click_product(self, product_data):
        """
        product_data: {'element': JSHandle, 'asin': str, 'title': str}
        """
        element = product_data.get('element')
        asin = product_data.get('asin')
        
        # 1. Try to find the element again if it might be stale
        if asin:
            new_el = await self.page.query_selector(f"div[data-asin='{asin}']")
            if new_el: 
                element = new_el
                print(f"DEBUG: Re-located element by ASIN: {asin}")

        if not element:
            print("DEBUG: Could not locate product element.")
            return False

        # 2. Find the link within this element
        # We try the title first as it's the most standard link
        link = await element.query_selector("h2 a") or \
               await element.query_selector("a.a-link-normal") or \
               await element.query_selector("img.s-image")
               
        if link:
            context = self.page.context
            print("DEBUG: Clicking product link...")
            
            try:
                # Prepare to catch a popup (new tab)
                async with context.expect_page(timeout=5000) as popup_info:
                    # evaluate click is often more robust than .click() for Amazon's JS-heavy links
                    await link.evaluate("el => el.click()")
                
                # If we get here, a new tab opened
                self.page = await popup_info.value
                print("DEBUG: Switched to new tab via popup event.")
            except Exception as e:
                # No popup, might have navigated in same tab or just a slow click
                print(f"DEBUG: No new tab detected ({e}). Checking current tab...")
            
            # Wait for load 
            try:
                # Amazon can be slow, wait for network idle if possible or at least DOM
                await self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                # VITAL VERIFICATION
                await self.page.wait_for_selector("#productTitle, #add-to-cart-button, #buyNow, #buy-now-button", timeout=10000)
                print("DEBUG: Product page confirmed.")
                return True
            except Exception as e:
                print(f"DEBUG: Failed to confirm product page load: {e}")
                return False
        return False

    async def get_visible_products(self):
        """Returns list of visible products to speak out."""
        # Primary selector
        products = await self.page.query_selector_all(".s-result-item[data-component-type='s-search-result']")
        
        # Fallback selector if primary fails
        if not products:
            print("DEBUG: Primary selector found 0 items. Trying fallback div[data-asin]...")
            products = await self.page.query_selector_all("div[data-asin]:not([data-asin=''])")
            
        print(f"DEBUG: Found {len(products)} potential product elements.")
        
        visible = []
        for i, p in enumerate(products):
            # VISIBILITY CHECK
            if not await p.is_visible():
                # print(f"DEBUG: Item {i} skipped: Not visible.")
                continue

            # TITLE CHECK - Get FULL title
            # Strategy: Image Alt text often contains the full clean title.
            title = "Unknown"
            img_el = await p.query_selector("img.s-image")
            if img_el:
                title = await img_el.get_attribute("alt")
            
            # Fallback to text if image alt is missing or too short
            if not title or len(title) < 5:
                title_el = await p.query_selector("h2 a span.a-text-normal") or \
                           await p.query_selector("h2 a") or \
                           await p.query_selector("h2")
                if title_el:
                    title = await title_el.inner_text()

            if title and len(title) > 3:
                # Clean title
                title = title.replace("Sponsored", "").strip()
                
                # Robust Price Finding
                price_text = "Unknown"
                
                # 1. Try standard selectors
                price_el = await p.query_selector(".a-price .a-offscreen") or \
                           await p.query_selector(".a-price-whole")
                
                if price_el:
                    price_text = await price_el.inner_text()
                else:
                    # 2. Fallback: Search in full text
                    all_text = await p.inner_text()
                    import re
                    # Look for price pattern like ₹2,299 or 2,299
                    match = re.search(r"[₹Rs\.]\s?([\d,]+\.?\d{0,2})", all_text)
                    if match:
                         price_text = match.group(1)
                
                # Normalize for debug
                asin = await p.get_attribute("data-asin")
                print(f"DEBUG: Scraped Item - ASIN: {asin}, Title: '{title[:30]}...', Raw Price: '{price_text}'")
                visible.append({"element": p, "asin": asin, "title": title, "price": price_text})
            else:
                print(f"DEBUG: Item {i} skipped: No title found.")
        
        print(f"DEBUG: Returning {len(visible)} visible items.")
        return visible

    async def identify_product(self, identifier, price_hint=None):
        """
        Identifies product candidates.
        """
        visible = await self.get_visible_products()
        if not visible:
            return {"status": "none", "candidates": []}

        candidates = []

        # 1. OPTION NUMBER
        try:
            if str(identifier).isdigit():
                idx = int(identifier) - 1
                if 0 <= idx < len(visible):
                    return {"status": "match", "candidates": [visible[idx]]}
        except:
            pass

        # 2. NAME MATCH (Improved)
        if isinstance(identifier, str):
            # Normalize identifier
            import re
            cleaned_id = identifier.lower().replace("plus", "+").replace(" pro", "pro")
            # Remove special chars but keep alphanums
            keywords = re.findall(r"\w+|[+]", cleaned_id)
            
            for item in visible:
                # Normalize title
                text = item['title'].lower()
                
                # Logic 1: Exact consecutive subsequence match (very strong)
                # If user says "boat rockerz 255", check if that phrase exists
                if cleaned_id in text:
                    # Give this high priority
                    candidates.insert(0, item)
                    continue

                # Logic 2: Keyword overlap
                match_count = 0
                for k in keywords:
                    if k in text:
                        match_count += 1
                
                # If good overlap (>70%)
                if len(keywords) > 0 and (match_count / len(keywords) >= 0.7):
                    if item not in candidates:
                        candidates.append(item)
        
        # 3. PRICE MATCH (if no name match or specific price hint)
        if not candidates and (price_hint or (str(identifier).replace(" ", "").isdigit())):
             # Treat identifier as price if it looks like one
             p_val = price_hint if price_hint else identifier
             parsed_target = parse_price(str(p_val))
             
             if parsed_target:
                 for item in visible:
                    item_price = parse_price(item['price'])
                    if item_price and abs(item_price - parsed_target) < 5: # Tolerance
                        candidates.append(item)

        if len(candidates) == 1:
            return {"status": "match", "candidates": candidates}
        elif len(candidates) > 1:
            # If we have exact matches at the front, prioritize them
            return {"status": "multiple", "candidates": candidates[:3]} # Return top 3
        
        return {"status": "none", "candidates": []}

    async def add_to_cart(self):
        # Try common selectors
        selectors = ["#add-to-cart-button", "#add-to-cart-button-ubb", "input[name='submit.add-to-cart']"]
        for sel in selectors:
            if await self.page.query_selector(sel):
                await self.page.click(sel)
                # Speech handled by main.py
                # Handle "No thanks"
                try:
                    await self.page.wait_for_selector("#attach-close_sideSheet-link", timeout=2000)
                    await self.page.click("#attach-close_sideSheet-link")
                except:
                    pass
                return True
        self.speaker("I could not find the add to cart button.")
        return False

    async def proceed_to_checkout(self):
        # 1. Check if already on a checkout-related page
        if any(k in self.page.url for k in ["checkout", "buy", "address", "pay", "ship"]):
            print(f"DEBUG: Already in checkout flow URL: {self.page.url}")
            return True
            
        # 2. Go to cart if not there
        if "/cart/" not in self.page.url:
            await self.page.goto("https://www.amazon.in/gp/cart/view.html")
        
        # 3. Try multiple selectors for Proceed to Buy
        checkout_selectors = [
            "input[name='proceedToRetailCheckout']",
            "input[name='proceedToCheckout']",
            "#sc-buy-box-ptc-button",
            "a[data-action='proceed-to-checkout']",
            "text='Proceed to Buy'",
            "text='Proceed to checkout'"
        ]
        
        for sel in checkout_selectors:
            try:
                btn = await self.page.query_selector(sel)
                if btn and await btn.is_visible():
                    print(f"DEBUG: Clicking checkout button with selector: {sel}")
                    await btn.evaluate("el => el.click()")
                    # Wait for URL change or load
                    try:
                        await self.page.wait_for_load_state("networkidle", timeout=5000)
                    except: pass
                    
                    if any(k in self.page.url for k in ["checkout", "buy", "address", "pay"]):
                        print("DEBUG: Navigation successful via URL check.")
                        return True
            except Exception as e:
                print(f"DEBUG: Error trying {sel}: {e}")
                continue

        # 4. Final Fallback: URL check again
        if any(k in self.page.url for k in ["checkout", "buy", "address", "pay"]):
             return True

        self.speaker("Could not find checkout button in cart.")
        return False

    async def handle_payment(self, method_text):
        """
        Selects payment method.
        method_text: 'cod', 'card', 'upi', 'netbanking'
        """
        self.speaker(f"Selecting {method_text} payment method.")
        method = method_text.lower()
        
        try:
            candidates = []
            if "cod" in method or "cash" in method:
                # Amazon uses "Cash on Delivery" or "Pay on Delivery"
                texts = ["Cash on Delivery", "Pay on Delivery", "COD"]
                for t in texts:
                    els = await self.page.get_by_text(t, exact=False).all()
                    candidates.extend(els)
            elif "card" in method:
                candidates = await self.page.get_by_text("Credit or debit card", exact=False).all()
            
            if candidates:
                # Sort by visibility but try the first one regardless if none are visible
                for el in candidates:
                    try:
                        if await el.is_visible():
                            print(f"DEBUG: Found visible {method} option. Clicking...")
                            await el.scroll_into_view_if_needed()
                            await el.evaluate("el => el.click()")
                            await asyncio.sleep(2)
                            return True
                    except: continue
                
                # If none were 'visible' to Playwright, try clicking the first one anyway
                print(f"DEBUG: No visible {method} option found among {len(candidates)} matches. Forced click on first match.")
                await candidates[0].evaluate("el => el.click()")
                await asyncio.sleep(2)
                return True
                
        except Exception as e:
            print(f"Payment selection error: {e}")
            
        self.speaker("I have tried to select the payment method. Please verify it is selected on screen.")
        return False

    async def place_order(self):
        """
        Final step.
        """
        # Step 1: Intermediate buttons (Use this payment method, Continue)
        try:
             continue_selectors = [
                 "input[aria-labelledby='orderSummaryPrimaryActionBtn-announce']",
                 "input[aria-labelledby='pp-confirm-button-announce']",
                 "span#orderSummaryPrimaryActionBtn-announce",
                 "input[name='ppw-widgetState']",
                 "input.a-button-input[type='submit']",
                 "input[aria-label='Use this payment method']",
                 "text='Use this payment method'",
                 "text='Use this method'",
                 "text='Continue'"
             ]
             for sel in continue_selectors:
                 btn = await self.page.query_selector(sel)
                 if btn and await btn.is_visible():
                     print(f"DEBUG: Clicking intermediate button: {sel}")
                     await btn.scroll_into_view_if_needed()
                     await btn.evaluate("el => el.click()")
                     await self.page.wait_for_load_state("networkidle", timeout=5000)
                     await asyncio.sleep(2)
                     break
        except Exception as e:
            print(f"Intermediate button error: {e}")

        # Step 2: Final Place Order Button
        try:
            place_btn_selectors = [
                "#placeYourOrder",
                "input[name='placeYourOrder1']",
                "#submitOrderButtonId",
                "input[aria-labelledby='submitOrderButtonId-announce']",
                "input[value='Place your order']",
                "button:has-text('Place your order')",
                "text='Place your order'"
            ]
            
            button = None
            for sel in place_btn_selectors:
                try:
                    button = await self.page.wait_for_selector(sel, timeout=3000)
                    if button: 
                        print(f"DEBUG: Found place order button: {sel}")
                        break
                except: continue

            if button:
                self.speaker("Placing the order now...")
                await button.scroll_into_view_if_needed()
                await button.evaluate("el => el.click()")
                
                await asyncio.sleep(5) 
                self.speaker("Order placed. Capturing receipt.")
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                final_dir = os.path.join(os.getcwd(), "Jarvis", "final")
                os.makedirs(final_dir, exist_ok=True)
                path = os.path.join(final_dir, f"order_receipt_{timestamp}.png")
                
                await self.page.screenshot(path=path)
                self.speaker(f"Receipt saved to {path}. Process complete.")
                return True
            else:
                 self.speaker("I could not find the place order button. Sir, please click it manually if you see it.")
                 return False
            
        except Exception as e:
            self.speaker(f"I encountered an error placing the order: {e}")
            return False

    async def checkout(self):
        return await self.proceed_to_checkout()

    async def cancel_order(self):
        """
        Navigates to order history and cancels the most recent order.
        """
        self.speaker("Navigating to your order history to cancel the last order.")
        try:
            # 1. Go to Order History
            await self.page.goto("https://www.amazon.in/gp/css/order-history")
            await self.page.wait_for_load_state("networkidle")
            
            # 2. Find "Cancel items" button for the first order
            # Step 2: Look for the Cancel Button
            cancel_btn_selectors = [
                "a:has-text('Cancel items')",
                "a:has-text('Cancel order')",
                "text='Cancel items'",
                "text='Cancel order'",
                "a[data-action='cancel-items']",
                "input[value='Cancel items']"
            ]
            
            cancel_btn = None
            for sel in cancel_btn_selectors:
                try:
                    cancel_btn = await self.page.wait_for_selector(sel, timeout=3000)
                    if cancel_btn and await cancel_btn.is_visible():
                        print(f"DEBUG: Found cancel button with selector: {sel}")
                        break
                except: continue
            
            if not cancel_btn:
                # Fallback: If we are on the main Order History, we might need to click "Order Details" first
                # But the user's screenshot shows we are ALREADY on Order Details.
                # Let's check for any link containing 'cancel'
                links = await self.page.query_selector_all("a")
                for link in links:
                    txt = await link.inner_text()
                    if "cancel" in txt.lower():
                        print(f"DEBUG: Found 'cancel' link by text: {txt}")
                        cancel_btn = link
                        break
            
            if not cancel_btn:
                # Still no button? Check if we need to click "Order Details" (redundant if already there)
                view_btn = await self.page.query_selector("a:has-text('View or edit order')") or \
                           await self.page.query_selector("a:has-text('Order Details')")
                if view_btn:
                    print("DEBUG: Clicking Order Details fallback.")
                    await view_btn.click()
                    await self.page.wait_for_load_state("networkidle")
                    # Try selectors again
                    for sel in cancel_btn_selectors:
                        try:
                            cancel_btn = await self.page.wait_for_selector(sel, timeout=3000)
                            if cancel_btn: break
                        except: continue

            if cancel_btn:
                await cancel_btn.click()
                await self.page.wait_for_load_state("networkidle")
                
                # 3. SELECT ITEMS (Ticking the checkboxes)
                # Usually name starts with 'cancel.item.' or just input[type="checkbox"]
                try:
                    checkboxes = await self.page.query_selector_all("input[type='checkbox']")
                    if checkboxes:
                        print(f"DEBUG: Found {len(checkboxes)} checkboxes. Ticking them all.")
                        for cb in checkboxes:
                            if not await cb.is_checked():
                                await cb.evaluate("el => el.click()")
                    else:
                        print("DEBUG: No checkboxes found, might be a single-item cancellation page.")
                except Exception as ce:
                    print(f"DEBUG: Error ticking checkboxes: {ce}")

                # 4. Select Cancellation Reason
                # Reason dropdown: name="cancel.reason"
                reason_selector = "select[name='cancel.reason']"
                try:
                    await self.page.wait_for_selector(reason_selector, timeout=5000)
                    # Select "Order Created by Mistake" - usually index 1 or 2
                    await self.page.select_option(reason_selector, label="Order Created by Mistake")
                    print("DEBUG: Selected cancellation reason.")
                except:
                    print("DEBUG: Could not find or select cancellation reason dropdown. Proceeding anyway.")

                # 4. Confirm Cancellation
                confirm_selectors = [
                    "input[name='cq.submit']",
                    "button:has-text('Request cancellation')",
                    "text='Request cancellation'",
                    "input[value='Request cancellation']",
                    "text='Cancel checked items'",
                    "input[value='Cancel checked items']",
                    "#cancel-items-button"
                ]
                
                final_btn = None
                for sel in confirm_selectors:
                    try:
                        final_btn = await self.page.wait_for_selector(sel, timeout=3000)
                        if final_btn:
                            print(f"DEBUG: Tying to click confirmation button: {sel}")
                            # Scroll into view just in case
                            await final_btn.scroll_into_view_if_needed()
                            await asyncio.sleep(0.5)
                            # Try a regular click first, fallback to evaluate
                            try:
                                await final_btn.click(timeout=3000)
                            except:
                                await final_btn.evaluate("el => el.click()")
                            
                            await self.page.wait_for_load_state("networkidle")
                            # Check for confirmation message
                            content = await self.page.content()
                            if "cancelled" in content.lower() or "cancellation" in content.lower():
                                self.speaker("Your request for cancellation has been submitted successfully, sir.")
                                return True
                    except: continue
            
            self.speaker("I could not find the cancel button for your recent order. You might need to do it manually.")
            return False

        except Exception as e:
            print(f"Cancellation error: {e}")
            self.speaker(f"I encountered an error while trying to cancel: {e}")
            return False
