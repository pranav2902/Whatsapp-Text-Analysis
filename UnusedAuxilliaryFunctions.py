import re

def RemoveHyperlink(inputString):
    return re.sub(r'http\S+', '', stringliteral)