# src/intent_detection/cli.py

import sys
import json
from .pipeline import run_prefilter

def main():
    """
    Usage:
      prefilter-cli "Your text here"
      echo "Your text here" | prefilter-cli
    """
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = sys.stdin.read().strip()

    v = run_prefilter(text)

    out = {
        "language": v.language,
        "lang_conf": round(v.lang_conf, 3),
        "pppl": round(v.pppl, 1),
        "nonsense_score": round(v.nonsense_score, 3),
        "toxicity": round(v.toxicity, 3),
        "action": v.action,
        "debug": v.debug,
    }
    print(json.dumps(out, ensure_ascii=False))
