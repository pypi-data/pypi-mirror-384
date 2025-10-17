# src/intent_prefilter/__init__.py
"""
intent_prefilter: local, CPU-friendly pre-filter for user inputs.

Public API:
- run_prefilter(text) -> Verdict
- Verdict dataclass with fields: language, lang_conf, pppl, nonsense_score,
  toxicity, action, debug
"""

from .pipeline import run_prefilter, Verdict  # re-export the main API
