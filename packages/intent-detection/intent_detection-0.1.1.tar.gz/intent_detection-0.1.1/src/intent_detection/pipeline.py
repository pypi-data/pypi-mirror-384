from dataclasses import dataclass
from typing import Dict, Any, Literal

from .config import DEFAULT_THRESHOLDS as TH
from .utils import normalise, non_letter_ratio, tokenise_simple, wordlike_ratio, mean_zipf
from .lang_detect import detect_language
from .pseudoppl import pseudo_perplexity
from .toxicity import toxicity_overall

Action = Literal["ALLOW", "WARN", "BLOCK", "CLARIFY"]

@dataclass
class Verdict:
    language: str
    lang_conf: float
    pppl: float
    nonsense_score: float  # 0..1 (higher => more nonsense)
    toxicity: float        # 0..1
    action: Action
    debug: Dict[str, Any]

def nonsense_composite(pppl: float, wl_ratio: float, mean_zipf_val: float) -> float:
    # Map each raw signal to 0..1 badness, then average (no labels)
    # pPPL mapping: <=good -> 0.0, >=bad -> 1.0
    if pppl <= TH.good_ppl:
        ppl_bad = 0.0
    elif pppl >= TH.bad_ppl:
        ppl_bad = 1.0
    else:
        ppl_bad = (pppl - TH.good_ppl) / (TH.bad_ppl - TH.good_ppl)

    wl_bad = 1.0 - wl_ratio  # fewer wordlike tokens => worse

    # Zipf ~ 0..7; <2 poor, >5 good
    if mean_zipf_val <= 2.0:
        zipf_bad = 1.0
    elif mean_zipf_val >= 5.0:
        zipf_bad = 0.0
    else:
        zipf_bad = 1.0 - (mean_zipf_val - 2.0) / 3.0

    return max(0.0, min(1.0, (ppl_bad + wl_bad + zipf_bad) / 3.0))

def decide_action(nonsense_score: float, toxicity: float) -> Action:
    if toxicity >= TH.block_toxicity:
        return "BLOCK"
    if toxicity >= TH.warn_toxicity:
        return "WARN"
    if nonsense_score >= TH.max_nonsense_score:
        return "CLARIFY"
    return "ALLOW"

def run_prefilter(user_text: str) -> Verdict:
    norm = normalise(user_text)

    # early shape checks (still model-free)
    if len(norm) < TH.min_len_chars:
        return Verdict("und", 0.0, 1e9, 1.0, 0.0, "CLARIFY", {"reason": "too_short"})
    nlr = non_letter_ratio(norm)
    if nlr > TH.max_non_letter_ratio:
        return Verdict("und", 0.0, 1e9, 1.0, 0.0, "CLARIFY", {"reason": "non_letter_ratio", "ratio": nlr})

    # language (no labels needed)
    lang, lang_conf = detect_language(norm)

    # word stats
    toks = tokenise_simple(norm)
    wl = wordlike_ratio(toks)
    mz = mean_zipf(toks, lang=lang)

    # model-based linguisticity
    pppl = pseudo_perplexity(norm)

    # combine
    ns = nonsense_composite(pppl=pppl, wl_ratio=wl, mean_zipf_val=mz)

    # toxicity
    tox = toxicity_overall(norm)

    action = decide_action(ns, tox)

    return Verdict(
        language=lang,
        lang_conf=lang_conf,
        pppl=pppl,
        nonsense_score=ns,
        toxicity=tox,
        action=action,
        debug={"non_letter_ratio": nlr, "wordlike_ratio": wl, "mean_zipf": mz}
    )
