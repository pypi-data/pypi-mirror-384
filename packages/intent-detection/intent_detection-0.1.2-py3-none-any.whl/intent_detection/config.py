from dataclasses import dataclass

@dataclass(frozen=True)
class Thresholds:
    # Early reject
    min_len_chars: int = 2
    max_non_letter_ratio: float = 0.75

    # Composite nonsense (0..1): higher => more nonsense
    max_nonsense_score: float = 0.60

    # pPPL ranges (heuristic defaults)
    # English-like short inputs: <70 good, 70-150 borderline, >150 likely junk
    good_ppl: float = 70.0
    bad_ppl: float = 150.0

    # Toxicity
    warn_toxicity: float = 0.50
    block_toxicity: float = 0.85

    short_text_token_cutoff: int = 6
    min_dict_coverage: float = 0.25  # below this looks like keyboard-mash
    dict_coverage_zipf: float = 3.0  # "known word" threshold

DEFAULT_THRESHOLDS = Thresholds()
