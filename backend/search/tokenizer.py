import re # for working with RegEx

def tokenize(text: str):
    text = text.lower()
    words = re.findall(r"\b[\w]+\b", text) # use the unicode standard to identify query tokens
    return words # returns an array of tokens