"""
Runs the complete evaluation pipeline.

Generates the synthetic logs, performs abstraction and conformance checking,
and prints a summary of the results.
"""

import argparse
import csv
from collections import Counter

from synthetic_logs import generate_logs
from abstraction import abstract_trace
from conformance import Checker
import validation


def score_logs(logs, checker, mapper):
    """Runs abstraction & conformance checking for all traces"""
    rows = []
    for name, traces in logs.items():
        for t in traces:
            abstracted = abstract_trace(t["raw_events"], mapper)
            d = checker.diagnose(abstracted)
            rows.append({"log": name, "case_id": t["case_id"], "truth": t["truth"],
                         "fault": t["fault"] or "", "fit9": round(d["fit9"], 3),
                         "fit12": round(d["fit12"], 3), "conforms": d["conforms"],
                         "presence_ok": d["presence_ok"]})
    return rows


def report(rows):
    """Prints a summary of the results for each log"""
    print("\n" + "=" * 74)
    print("Stage 2 & 3 results")
    print("=" * 74)
    by_log = {"A": [], "B": [], "C": []}
    for r in rows:
        by_log[r["log"]].append(r)

    headline = {"A": "should be true green", "B": "should be true red", "C": "should be false green"}
    for name in ["A", "B", "C"]:
        rs = by_log[name]
        conf = sum(1 for r in rs if r["conforms"])
        flag = len(rs) - conf
        print(f"\nLog {name}, {headline[name]}, {len(rs)} traces")
        print(f"  conforms {conf}    flagged {flag}")
        if name == "B":
            gap = sum(1 for r in rs if r["presence_ok"] and not r["conforms"])
            print(f"  of the flagged traces, {gap} passed the presence check but failed conformance")
        if name == "C":
            missed = sum(1 for r in rs if r["conforms"])
            print(f"  {missed} substantive violations returned as compliant, the false-green result")


def rag_vs_dictionary(checker, n, seed):
    """Compares retrieval mapping with exact dictionary matching"""
    print("\n" + "=" * 74)
    print("retrieval vs. dictionary mapping")
    print("=" * 74)
    clean = generate_logs(n_per=n, seed=seed, novel_rate=0.0)
    A = {"A": clean["A"]}
    for mapper in ["dictionary", "retrieval"]:
        # evaluate all traces
        rows = score_logs(A, checker, mapper)
        conf = sum(1 for r in rows if r["conforms"])
        print(f"  {mapper:11s} conforms {conf} of {len(rows)}   "
              f"wrongly flagged {len(rows) - conf}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50, help="traces per log")
    ap.add_argument("--mapper", default="retrieval", choices=["retrieval", "dictionary", "llm", "hybrid"])
    ap.add_argument("--novel", type=float, default=0.0,
                    help="fraction of order-free labels given a novel wording that only the model can place")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    logs = generate_logs(n_per=args.n, seed=args.seed, novel_rate=args.novel)
    checker = Checker()

    rows = score_logs(logs, checker, args.mapper)
    if args.mapper in ("llm", "hybrid"):
        import abstraction
        from abstraction import normalise
        distinct = len(set(normalise(e) for L in logs.values() for t in L for e in t["raw_events"]))
        calls = abstraction.llm_call_count()
        print(f"\nDivision of labour in the {args.mapper} mapper")
        print(f"  {distinct} distinct labels, {calls} sent to the model, "
              f"{distinct - calls} placed by retrieval")
        # save per-trace results
    with open("trace_results.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["log", "case_id", "truth", "fault",
                                          "fit9", "fit12", "conforms", "presence_ok"])
        w.writeheader()
        w.writerows(rows)

    report(rows)
    rag_vs_dictionary(checker, args.n, args.seed)

    # compare retrieval and hybrid on novel labels
    if args.novel > 0:
        print("\n" + "=" * 74)
        print("retrieval vs. hybrid mapping")
        print("=" * 74)
        retr = score_logs({"A": logs["A"]}, checker, "retrieval")
        retr_conf = sum(1 for r in retr if r["conforms"])
        hyb_conf = sum(1 for r in rows if r["log"] == "A" and r["conforms"])
        print(f"  retrieval alone conforms {retr_conf} of {len(logs['A'])}, "
              f"it cannot place the novel labels")
        print(f"  hybrid conforms {hyb_conf} of {len(logs['A'])}")

    print("\n" + "=" * 74)
    print("validation results")
    print("=" * 74)
    # run construct-space validation
    vres = validation.run()
    counts = Counter(r["kind"] for r in vres)
    print(f"  clauses coloured   checkable {counts['structural']}   dual {counts['dual']}   "
          f"open {counts['open']}   permissive {counts['permissive']}")
    print("  saved validation_grid.png and validation_results.csv")
    print("  saved trace_results.csv")
    print("\nFinished.")


if __name__ == "__main__":
    main()