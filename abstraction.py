"""
Map raw event labels to the canonical activity vocabulary.

import re
import difflib
from vocabulary import ALL_CANON, SYNONYMS, SIGNATURES


def normalise(text):
    """Normalise a label before matching."""
    text = text.lower()
    text = re.sub(r"[_\-/.:;,()\[\]]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def tokens(text):
    return set(normalise(text).split())


# lookup table
_SURFACE_TO_CANON = {}
for _c in ALL_CANON:
    _SURFACE_TO_CANON[normalise(_c)] = _c
for _c, _forms in SYNONYMS.items():
    for _f in _forms:
        _SURFACE_TO_CANON[normalise(_f)] = _c

_CANON_NORM = {normalise(c): c for c in ALL_CANON}


def map_dictionary(raw):
    """Returns the canonical activity if the label matches exactly."""
    return _CANON_NORM.get(normalise(raw))


def _match_by_tokens(raw):
    """Fallback token matching based on signature sets."""
    tks = tokens(raw)
    best, best_size = None, 0
    for canon, sigsets in SIGNATURES.items():
        for sig in sigsets:
            if sig.issubset(tks) and len(sig) > best_size:
                best, best_size = canon, len(sig)
    return best


def map_retrieval(raw, cutoff=0.72):
    """Returns the closest matching activity using fuzzy matching
    --> retrieval based mapper"""
    key = normalise(raw)
    hit = difflib.get_close_matches(key, list(_SURFACE_TO_CANON.keys()), n=1, cutoff=cutoff)
    if hit:
        return _SURFACE_TO_CANON[hit[0]]
    return _match_by_tokens(raw)


# cache already mapped labels
_LLM_CACHE = {}
_LLM_CLIENT = None
_LLM_CALLS = 0

# short descriptions used in the prompt
_GLOSS = {
    "Establish RMS": "set up or create the risk management system",
    "Implement RMS": "put the risk management system into operation",
    "Document RMS": "write down or document the risk management system",
    "Maintain RMS": "keep the risk management system up to date",
    "Identify risks": "find or list the risks",
    "Analyse risks": "analyse the risks that were identified",
    "Estimate risks": "estimate, quantify or score the risks",
    "Evaluate risks": "evaluate or assess the estimated risks",
    "Adopt measures": "adopt or choose risk management measures",
    "Reduce via design": "reduce the risk through design choices",
    "Implement mitigation": "put mitigation or control measures in place",
    "Judge residual risk": "decide whether the residual risk is acceptable",
    "Define metrics": "define the test metrics and thresholds",
    "Test AI system": "test the AI system",
    "Evaluate post-market data": "review data gathered after the system is on the market",
    "Provide info": "provide information or instructions for users",
    "Provide training": "provide training to users or operators",
    "enable logging": "switch on automatic event logging",
    "record risk-relevant events": "write a log entry for a risk relevant event",
    "record post-market events": "write a log entry for post-market monitoring",
    "record operational events": "write a log entry for normal operation of the system",
    "record use period": "log the start and end time of a use period",
    "record reference DB": "log which reference database was checked",
    "record matching input": "log the input data that produced a match",
    "record verifier identity": "log who verified the result",
}

# example mappings for prompt
_FEWSHOT = [
    ("field data evaluation", "Evaluate post-market data"),
    ("review post market data", "Evaluate post-market data"),
    ("log post market event", "record post-market events"),
    ("session timestamp recorded", "record use period"),
    ("log who verified the result", "record verifier identity"),
    ("analyse risk sources", "Analyse risks"),
    ("assess residual likelihood", "Evaluate risks"),
    ("quantify risks", "Estimate risks"),
]

_LLM_MENU = "\n".join(f"- {c}   ({_GLOSS[c]})" for c in ALL_CANON)
_LLM_EXAMPLES = "\n".join(f"  raw {r!r}  answer  {a}" for r, a in _FEWSHOT)


def _get_client():
    """Creates the Anthropic client once."""
    global _LLM_CLIENT
    if _LLM_CLIENT is None:
        import os
        import anthropic
        _LLM_CLIENT = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _LLM_CLIENT


def _resolve(answer, raw):
    """Maps the model output back to a canonical activity."""
    a = answer.strip().strip('".').strip()
    if a.lower() == "none" or a.lower().startswith("none"):
        return None
    # exact match first
    if a in ALL_CANON:
        return a
    na = normalise(a)
    for c in ALL_CANON:
        if normalise(c) == na:
            return c
    return map_retrieval(a) or map_retrieval(raw)


def map_llm(raw, client=None, model="claude-opus-4-8"):
    """LLM based mapper"""
    global _LLM_CALLS
    key = normalise(raw)
    # cache hit
    if key in _LLM_CACHE:
        return _LLM_CACHE[key]
    client = client or _get_client()
    # create prompt
    prompt = (
        "You map one raw event-log label onto exactly one activity from the list "
        "below, choosing the closest in meaning. Copy the activity text exactly as "
        "written, including capitalisation. Use the single word none only when no "
        "activity fits at all. Do not explain, answer with the activity text or none.\n\n"
        f"Activities and what they mean\n{_LLM_MENU}\n\n"
        f"Examples\n{_LLM_EXAMPLES}\n\n"
        f"Raw label\n{raw}\n\nAnswer"
    )
    msg = client.messages.create(model=model, max_tokens=40,
                                 messages=[{"role": "user", "content": prompt}])
    _LLM_CALLS += 1
    result = _resolve(msg.content[0].text, raw)
    _LLM_CACHE[key] = result
    return result


def llm_call_count():
    """Returns number of LLM calls"""
    return _LLM_CALLS


def map_hybrid(raw, **kw):
    """try retrieval first & falls back to LLM"""
    r = map_retrieval(raw)
    if r is not None:
        return r
    return map_llm(raw, **kw)


MAPPERS = {"dictionary": map_dictionary, "retrieval": map_retrieval,
           "llm": map_llm, "hybrid": map_hybrid}


def abstract_trace(raw_events, mapper="retrieval"):
    """Maps all events of a trace to canonical activities"""
    fn = MAPPERS[mapper]
    mapped = [fn(e) for e in raw_events]
    return [m for m in mapped if m is not None]
