# intent-detection

Local, CPU-friendly pre-filter for user text:
- **pseudo-perplexity (DistilRoBERTa)** → fluency / “is it human-like?”
- **nonsense score** → composite of pPPL + word statistics
- **toxicity** → compact English toxicity classifier
- **language detection** → `langid`

## Install

```
pip install intent-prefilter
```

## Quick start
```
from intent_prefilter import run_prefilter

v = run_prefilter("Use of dornes in nowray")
print(v.action, v.nonsense_score, v.pppl, v.toxicity)
```

## Notes
- Runs fully local, no hand-crafted intent labels. 
- Adjust thresholds in config.py if needed.

