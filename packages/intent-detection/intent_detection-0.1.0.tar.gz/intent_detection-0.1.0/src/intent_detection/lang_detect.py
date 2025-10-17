import langid

def detect_language(text: str):
    # returns (lang, confidence in 0..1)
    lang, conf = langid.classify(text)
    conf = max(0.0, min(1.0, (conf + 12) / 14))  # squash to 0..1 for readability
    return lang, conf
