"""
Checks abstracted traces against the reference Petri-nets.

The trace is projected onto the activities of article 9 & article 12 &
aligned with the corresponding reference model.

Supports alignment fitness & a simple activity presence check.
"""

import warnings, logging
warnings.filterwarnings("ignore")
logging.getLogger("pm4py").setLevel(logging.ERROR)

import pm4py
from pm4py.objects.log.obj import EventLog, Trace, Event
from reference_model import (build_art9_net, build_art12_net, ART_9_SETUP,
                             ART_9_CORE, ART_9_TESTING, ART_9_PARALLEL, ART_12_ACTIVITIES)

ALPHA_9 = set(ART_9_SETUP) | set(ART_9_CORE) | set(ART_9_TESTING) | set(ART_9_PARALLEL)
ALPHA_12 = set(ART_12_ACTIVITIES)
_ALIGNMENT_THRESHOLD = 0.999


def _one_trace_log(events):
    """Creates PM4Py log containing a single trace"""
    log = EventLog()
    tr = Trace()
    for i, a in enumerate(events):
        tr.append(Event({"concept:name": a, "time:timestamp": i}))
    log.append(tr)
    return log


def _project(events, alphabet):
    """Returns only events that belong to given alphabet"""
    return [e for e in events if e in alphabet]


def fitness_against(events, net, im, fm):
    """Computes the alignment fitness."""
    if not events:
        return 0.0
    res = pm4py.conformance_diagnostics_alignments(_one_trace_log(events), net, im, fm)
    return res[0]["fitness"]


def presence_ok(events, required):
    """Checks if all required activities are present"""
    return required.issubset(set(events))


class Checker:
    """Loads reference nets once & reuses them"""

    def __init__(self):
        self.net9, self.im9, self.fm9 = build_art9_net()
        self.net12, self.im12, self.fm12 = build_art12_net()

    def diagnose(self, canon_events):
        # split trace by reference model
        e9 = _project(canon_events, ALPHA_9)
        e12 = _project(canon_events, ALPHA_12)
        fit9 = fitness_against(e9, self.net9, self.im9, self.fm9)
        fit12 = fitness_against(e12, self.net12, self.im12, self.fm12)
        # alignment based result
        conforms = fit9 > _ALIGNMENT_THRESHOLD and fit12 > _ALIGNMENT_THRESHOLD
        # simple baseline
        presence = presence_ok(e9, ALPHA_9) and presence_ok(e12, ALPHA_12)
        return {"fit9": fit9, "fit12": fit12,
                "conforms": conforms, "presence_ok": presence}
