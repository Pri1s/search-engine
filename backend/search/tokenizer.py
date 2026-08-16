import re # for working with RegEx

def tokenizer(text: str):
    text = text.lower()
    words = re.findall(r"\b[a-z]+\b", text) # find complete words made of only lowercase letter
    return words # returns an array of words