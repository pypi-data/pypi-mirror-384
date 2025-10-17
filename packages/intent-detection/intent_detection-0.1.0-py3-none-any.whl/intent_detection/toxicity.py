import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

_MODEL_ID = "unitary/toxic-bert"
_tok = AutoTokenizer.from_pretrained(_MODEL_ID)
_clf = AutoModelForSequenceClassification.from_pretrained(_MODEL_ID)
_clf.eval()

@torch.no_grad()
def toxicity_overall(text: str) -> float:
    enc = _tok(text, truncation=True, max_length=256, return_tensors="pt")
    probs = torch.sigmoid(_clf(**enc).logits).cpu().numpy()[0]
    return float(probs.max())  # overall = max label prob
