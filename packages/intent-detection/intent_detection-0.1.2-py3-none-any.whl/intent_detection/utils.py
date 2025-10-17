import regex as re
import unicodedata
from wordfreq import zipf_frequency

WS_RE = re.compile(r"\s+")
LETTER_RE = re.compile(r"\p{L}+")
WORDLIKE_RE = re.compile(r"^\p{L}[\p{L}\p{M}'’-]*$")

def normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", text or "")
    text = text.replace("\u200b", "")
    return WS_RE.sub(" ", text).strip()

def non_letter_ratio(text: str) -> float:
    if not text:
        return 1.0
    letters = len("".join(LETTER_RE.findall(text)))
    return 1.0 - (letters / max(1, len(text)))

def tokenise_simple(text: str):
    return [t for t in re.findall(r"[\p{L}\p{M}'’-]+|\d+|[^\s\p{L}\p{M}\d]", text)]

def wordlike_ratio(tokens):
    if not tokens:
        return 0.0
    return sum(1 for t in tokens if WORDLIKE_RE.match(t)) / len(tokens)

def mean_zipf(tokens, lang="en"):
    wl = [t for t in tokens if WORDLIKE_RE.match(t)]
    if not wl:
        return 0.0
    vals = [zipf_frequency(t.lower(), lang) for t in wl]
    return sum(vals) / len(vals)

def lexical_coverage(tokens, lang="en", min_zipf: float = 3.0) -> float:
    """Proportion of tokens whose Zipf frequency >= min_zipf (≈ common words)."""
    wl = [t for t in tokens if WORDLIKE_RE.match(t)]
    if not wl:
        return 0.0
    hits = sum(1 for t in wl if zipf_frequency(t.lower(), lang) >= min_zipf)
    return hits / len(wl)
