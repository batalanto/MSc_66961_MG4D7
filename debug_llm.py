"""
Simple debug script for the LLM mapper.
"""

from synthetic_logs import generate_logs
from abstraction import map_llm, map_retrieval

if __name__ == "__main__":
    logs = generate_logs(n_per=2, seed=7)
    # avoid repeated LLM calls
    seen = set()
    disagreements = 0
    print(f"{'raw label':42s}{'model':26s}{'retrieval':26s}")
    print("-" * 94)
    for name in ["A", "B", "C"]:
        for t in logs[name]:
            for raw in t["raw_events"]:
                if raw in seen:
                    continue
                seen.add(raw)
                m = map_llm(raw)
                r = map_retrieval(raw)
                # highlight mismatches
                mark = "" if m == r else "   <-- differ"
                if m != r:
                    disagreements += 1
                print(f"{raw[:40]:42s}{str(m)[:24]:26s}{str(r)[:24]:26s}{mark}")
    print("-" * 94)
    print(f"{len(seen)} distinct labels, {disagreements} disagreements between model and retrieval")
    print("A few mismatches are expected.")
