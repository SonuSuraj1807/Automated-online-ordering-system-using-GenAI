import google.genai as genai

# HARDCODE YOUR KEY HERE FOR THE DEMO
genai.configure(api_key="AIzaSyB26qDDZGGL1ZqiqNYvyFBnsk8mO5nGeUM")
model = genai.GenerativeModel('gemini-1.5-flash')

def understand(text):
    prompt = f"Extract 'Item' and 'Platform' from this: {text}. Format as Item: [item], Platform: [platform]"
    response = model.generate_content(prompt)
    return response.text