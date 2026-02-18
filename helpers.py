import re
from word2number import w2n

def parse_price(text):
    """Converts 'four hundred', '₹499', '499.00' to integer 499."""
    # Clean string: remove ₹, commas, .00
    text = text.lower().replace("rupees", "").replace("rupee", "").strip()
    text = text.replace("₹", "").replace(",", "")
    if "." in text:
        text = text.split(".")[0]
    
    # Custom handling for "seven nine nine" -> 799
    digit_match = re.search(r'\d+', text)
    if digit_match:
        return int(digit_match.group())
    # Handle word-to-number conversion
    # Custom handling for "seven nine nine" -> 799
    text_digits = text.replace(" ", "")
    if text_digits.isdigit():
        return int(text_digits)
    
    # Try word2number
    try:
        val = w2n.word_to_num(text)
        return val
    except:
        # Fallback: manually map simple digits if spoken as words sequence
        # e.g. "seven nine nine"
        word_map = {
            "one": "1", "two": "2", "three": "3", "four": "4", "five": "5",
            "six": "6", "seven": "7", "eight": "8", "nine": "9", "zero": "0"
        }
        words = text.split()
        digits = []
        for w in words:
            if w in word_map:
                digits.append(word_map[w])
        
        if digits:
            return int("".join(digits))
            
    return None
