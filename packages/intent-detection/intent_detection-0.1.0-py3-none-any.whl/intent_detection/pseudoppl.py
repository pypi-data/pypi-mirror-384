import torch
from transformers import AutoTokenizer, AutoModelForMaskedLM

# Small, fast masked-LM
_MODEL_ID = "distilroberta-base"
_tok = AutoTokenizer.from_pretrained(_MODEL_ID)
_mlm = AutoModelForMaskedLM.from_pretrained(_MODEL_ID)
_mlm.eval()

@torch.no_grad()
def pseudo_perplexity(text: str, max_len: int = 256) -> float:
    """
    Pseudo-perplexity (pPPL) via token-by-token masking (Wang & Cho 2019).
    Lower is better (more fluent).
    """
    enc = _tok(text, return_tensors="pt", truncation=True, max_length=max_len)
    input_ids = enc["input_ids"][0]
    if input_ids.numel() <= 2:
        return 1e9  # effectively garbage for empty/too short

    losses = []
    for i in range(1, input_ids.numel() - 1):  # skip special tokens
        masked = input_ids.clone()
        masked[i] = _tok.mask_token_id
        out = _mlm(masked.unsqueeze(0)).logits[0, i]
        # negative log-likelihood of the true token
        nll = -torch.log_softmax(out, dim=-1)[input_ids[i]].item()
        losses.append(nll)

    # standard definition uses exp(mean NLL)
    return float(torch.exp(torch.tensor(losses).mean()).item())
