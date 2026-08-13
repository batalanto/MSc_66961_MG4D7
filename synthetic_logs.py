"""
Generates the three synthetic event logs used for evaluation.

Log A contains compliant traces, Log B contains structural violations and
Log C contains substantive violations that cannot be detected from the log.
"""

import random
from reference_model import (ART_9_SETUP, ART_9_CORE, ART_9_TESTING,
                             ART_9_PARALLEL, ART_12_ACTIVITIES)
from vocabulary import SYNONYMS, NOVEL

_JOINERS = [" ", "_", "-"]
_PREFIXES = ["", "", "", "evt ", "log ", "sys "]


def _roughen(canonical, rng, novel_rate=0.0):
    """Converts a canonical activity into a noisy log label."""
    if novel_rate and canonical in NOVEL and rng.random() < novel_rate:
        text = NOVEL[canonical]
        words = text.split()
        text = rng.choice(_JOINERS).join(words)
        text = text.lower() if rng.random() < 0.5 else text.title()
        return rng.choice(_PREFIXES) + text
    base = rng.choice(SYNONYMS.get(canonical, [canonical]) + [canonical])
    words = base.split()
    joiner = rng.choice(_JOINERS)
    text = joiner.join(words)
    style = rng.random()
    if style < 0.33:
        text = text.lower()
    elif style < 0.66:
        text = text.title()
    if rng.random() < 0.12 and len(text) > 4:  # occasional typo
        i = rng.randrange(len(text) - 1)
        text = text[:i] + text[i + 1] + text[i] + text[i + 2:]
    return rng.choice(_PREFIXES) + text


def _compliant_canon(rng):
    """Generates compliant canonical trac."""
    passes = rng.choice([1, 2, 2])  # usually iterated, sometimes a single pass
    seq = list(ART_9_SETUP)
    for _ in range(passes):
        seq += list(ART_9_CORE)
    seq += list(ART_9_TESTING)
    parallel_tasks = list(ART_9_PARALLEL)
    rng.shuffle(parallel_tasks)
    seq += parallel_tasks
    # mix logging events into the trace
    logs = list(ART_12_ACTIVITIES)
    rng.shuffle(logs)
    for act in logs:
        seq.insert(rng.randint(0, len(seq)), act)
    return seq


def _structural_fault(canon, rng):
    """Introduces a single structural fault."""
    kind = rng.choice(["swap_core", "drop_core", "drop_field"])
    seq = list(canon)
    if kind == "swap_core":
        idx = [i for i, a in enumerate(seq) if a in ART_9_CORE]
        # swap two neighbouring core events
        i = rng.choice(idx[:-1])
        j = next(k for k in idx if k > i)
        seq[i], seq[j] = seq[j], seq[i]
    elif kind == "drop_core":
        idx = [i for i, a in enumerate(seq) if a in ART_9_CORE]
        seq.pop(rng.choice(idx))
    else:
        idx = [i for i, a in enumerate(seq) if a in ART_12_ACTIVITIES]
        seq.pop(rng.choice(idx))
    return seq, kind


def _to_trace(case_id, canon_seq, truth, rng, fault=None, novel_rate=0.0):
    """Creates a trace dictionary"""
    return {"case_id": case_id,
            "raw_events": [_roughen(a, rng, novel_rate) for a in canon_seq],
            "truth": truth,
            "fault": fault}


def generate_logs(n_per=50, seed=7, novel_rate=0.0):
    """Generates the 3 synthetic logs"""
    rng = random.Random(seed)
    # build all 3 log variants
    A, B, C = [], [], []
    # compliant traces
    for k in range(n_per):
        A.append(_to_trace(f"A{k:03d}", _compliant_canon(rng), "compliant", rng, novel_rate=novel_rate))
    # structural violations
    for k in range(n_per):
        canon, fault = _structural_fault(_compliant_canon(rng), rng)
        B.append(_to_trace(f"B{k:03d}", canon, "structural_violation", rng, fault, novel_rate))
    # substantive violations
    for k in range(n_per):
        C.append(_to_trace(f"C{k:03d}", _compliant_canon(rng), "substantive_violation", rng, novel_rate=novel_rate))
    return {"A": A, "B": B, "C": C}


if __name__ == "__main__":
    logs = generate_logs(n_per=3, seed=1)
    for name, traces in logs.items():
        print(f"\nLog {name}")
        for t in traces[:1]:
            print(" ", t["case_id"], t["truth"], t["fault"])
            for e in t["raw_events"][:6]:
                print("     ", e)