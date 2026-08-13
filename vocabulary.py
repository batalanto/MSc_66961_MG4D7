"""
Vocabulary used by the event label abstraction step.
"""

from reference_model import (ART_9_SETUP, ART_9_CORE, ART_9_TESTING,
                             ART_9_PARALLEL, ART_12_ACTIVITIES)

CANON_9 = ART_9_SETUP + ART_9_CORE + ART_9_TESTING + ART_9_PARALLEL
CANON_12 = list(ART_12_ACTIVITIES)
ALL_CANON = CANON_9 + CANON_12

# possible event-log variants
SYNONYMS = {
    "Establish RMS": ["set up risk management system", "create risk mgmt framework", "rms establishment"],
    "Implement RMS": ["roll out risk management system", "deploy rms", "put risk mgmt into operation"],
    "Document RMS": ["document the risk management system", "write up rms records", "rms documentation"],
    "Maintain RMS": ["maintain risk management system", "update rms", "keep risk mgmt current"],
    "Identify risks": ["identify foreseeable risks", "list hazards", "spot risks"],
    "Analyse risks": ["analyse known risks", "analyze risk sources", "examine risks"],
    "Estimate risks": ["estimate risk levels", "quantify risks", "score the risks"],
    "Evaluate risks": ["evaluate risks", "assess residual likelihood", "weigh the risks"],
    "Adopt measures": ["adopt risk measures", "choose control measures", "select mitigations"],
    "Reduce via design": ["reduce risk through design", "design out the hazard", "safe by design step"],
    "Implement mitigation": ["implement mitigation controls", "apply mitigation measures", "put controls in place"],
    "Judge residual risk": ["judge residual risk acceptable", "accept residual risk", "residual risk decision"],
    "Define metrics": ["define test metrics", "set thresholds", "fix metrics and thresholds"],
    "Test AI system": ["test the ai system", "run system testing", "execute model tests"],
    "Evaluate post-market data": ["review post market data", "post-market monitoring review", "field data evaluation"],
    "Provide info": ["provide user information", "issue instructions for use", "give usage info"],
    "Provide training": ["provide user training", "train the operators", "deliver training"],
    "enable logging": ["enable automatic logging", "turn on event logging", "logging switched on"],
    "record risk-relevant events": ["log risk relevant event", "record risk event", "risk situation logged"],
    "record post-market events": ["log post market event", "record post-market entry", "pms event logged"],
    "record operational events": ["log operational event", "record operation event", "runtime event logged"],
    "record use period": ["record use period", "log start and end time", "session timestamp recorded"],
    "record reference DB": ["record reference database", "log reference db checked", "ref database recorded"],
    "record matching input": ["record matching input data", "log the matched input", "input match recorded"],
    "record verifier identity": ["record verifier identity", "log who verified the result", "verifier id recorded"],
}

# larger signatures have priority during matching process
SIGNATURES = {
    "Establish RMS": [{"establish", "risk"}, {"set", "up", "risk"}, {"create", "risk", "mgmt"}, {"rms", "establishment"}],
    "Implement RMS": [{"roll", "out", "risk"}, {"deploy", "rms"}, {"operation", "risk", "management"}],
    "Document RMS": [{"document", "risk", "management"}, {"rms", "documentation"}, {"write", "rms"}],
    "Maintain RMS": [{"maintain", "risk", "management"}, {"update", "rms"}, {"keep", "risk", "mgmt"}],
    "Identify risks": [{"identify", "risk"}, {"list", "hazard"}, {"spot", "risk"}],
    "Analyse risks": [{"analyse", "risk"}, {"analyze", "risk"}, {"examine", "risk"}],
    "Estimate risks": [{"estimate", "risk"}, {"quantify", "risk"}, {"score", "risk"}],
    "Evaluate risks": [{"evaluate", "risk"}, {"assess", "likelihood"}, {"weigh", "risk"}],
    "Adopt measures": [{"adopt", "measure"}, {"choose", "control", "measure"}, {"select", "mitigation"}],
    "Reduce via design": [{"reduce", "design"}, {"design", "out"}, {"safe", "design"}],
    "Implement mitigation": [{"implement", "mitigation"}, {"apply", "mitigation"}, {"controls", "place"}],
    "Judge residual risk": [{"residual", "acceptable"}, {"accept", "residual"}, {"residual", "decision"}, {"judge", "residual"}],
    "Define metrics": [{"define", "metric"}, {"set", "threshold"}, {"metric", "threshold"}],
    "Test AI system": [{"test", "system"}, {"run", "testing"}, {"model", "test"}],
    "Evaluate post-market data": [{"post", "market", "review"}, {"post-market", "monitoring"}, {"field", "data", "evaluation"}, {"review", "post", "market"}],
    "Provide info": [{"user", "information"}, {"instructions", "use"}, {"usage", "info"}],
    "Provide training": [{"training"}, {"train", "operators"}],
    "enable logging": [{"enable", "logging"}, {"turn", "on", "logging"}, {"logging", "on"}],
    "record risk-relevant events": [{"log", "risk", "event"}, {"record", "risk", "event"}, {"risk", "situation", "logged"}],
    "record post-market events": [{"log", "post", "market", "event"}, {"record", "post-market"}, {"pms", "event"}],
    "record operational events": [{"log", "operational", "event"}, {"record", "operation", "event"}, {"runtime", "event"}],
    "record use period": [{"use", "period"}, {"start", "end", "time"}, {"session", "timestamp"}],
    "record reference DB": [{"reference", "database"}, {"reference", "db"}, {"ref", "database"}],
    "record matching input": [{"matching", "input"}, {"matched", "input"}, {"input", "match"}],
    "record verifier identity": [{"verifier", "identity"}, {"who", "verified"}, {"verifier", "id"}],
}


# novel labels used to test LLM fallback
NOVEL = {
    "Provide training": "onboarding session for the operating staff",
    "Provide info": "hand the operators the usage booklet",
    "Document RMS": "file the paperwork for the risk framework",
    "Maintain RMS": "periodic upkeep of the risk framework",
    "Evaluate post-market data": "look over the feedback gathered after launch",
}