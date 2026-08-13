"""
Inter-coder reliability for the two construct-space axes, for two coders.
"""

import csv
import sys

K = 5  # the scale runs from 1 to 5


def read_coder(path):
    """Read exported coding sheet"""
    with open(path, newline="") as f:
        rows = list(csv.reader(f))
    header_idx = None
    for i, r in enumerate(rows):
        if any(c.strip().lower() == "reference" for c in r):
            header_idx = i
            break
    if header_idx is None:
        return {}
    header = [c.strip().lower() for c in rows[header_idx]]

    def find(match):
        for j, c in enumerate(header):
            if match(c):
                return j
        return None

    ref_j = find(lambda c: c == "reference")
    dn_j = find(lambda c: c == "dn" or "descriptive" in c)
    ag_j = find(lambda c: c == "ag" or "abstract" in c)
    if None in (ref_j, dn_j, ag_j):
        return {}

    scores = {}
    for r in rows[header_idx + 1:]:
        if len(r) <= max(ref_j, dn_j, ag_j):
            continue
        ref = r[ref_j].strip()
        if not ref or "EXAMPLE" in ref.upper():
            continue
        try:
            scores[ref] = (int(float(r[dn_j])), int(float(r[ag_j])))
        except (ValueError, TypeError):
            continue
    return scores


def cohen_kappa(a, b, weighted):
    """Cohen kappa for 2 score lists -> Quadratic weights if weighted is true"""
    n = len(a)
    O = [[0.0] * (K + 1) for _ in range(K + 1)]
    for x, y in zip(a, b):
        O[x][y] += 1
    if weighted:
        w = lambda i, j: 1 - ((i - j) ** 2) / ((K - 1) ** 2)
    else:
        w = lambda i, j: 1.0 if i == j else 0.0
    row = [sum(O[i][j] for j in range(1, K + 1)) for i in range(K + 1)]
    col = [sum(O[i][j] for i in range(1, K + 1)) for j in range(K + 1)]
    po = sum(w(i, j) * O[i][j] for i in range(1, K + 1) for j in range(1, K + 1)) / n
    pe = sum(w(i, j) * row[i] * col[j] / n for i in range(1, K + 1) for j in range(1, K + 1)) / n
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def report_axis(name, refs, a, b, which):
    n = len(a)
    exact = sum(1 for i in range(n) if a[i] == b[i]) / n
    within1 = sum(1 for i in range(n) if abs(a[i] - b[i]) <= 1) / n
    print(f"  {name}")
    print(f"    raw exact agreement     {exact * 100:5.1f} percent")
    print(f"    within one agreement    {within1 * 100:5.1f} percent")
    print(f"    Cohen kappa unweighted  {cohen_kappa(a, b, False):0.2f}")
    print(f"    Cohen kappa weighted    {cohen_kappa(a, b, True):0.2f}")
    big = [(refs[i], a[i], b[i]) for i in range(n) if abs(a[i] - b[i]) >= 2]
    if big:
        print(f"    reconcile these ({which} differs by two or more)")
        for ref, x, y in big:
            print(f"      {ref:20s} coder 1 = {x}   coder 2 = {y}")
    else:
        print(f"    no clause differs by two or more, nothing to reconcile")


def main():
    paths = sys.argv[1:] or ["coder_1.csv", "coder_2.csv"]
    if len(paths) != 2:
        print("This version expects exactly two coder files.")
        return
    c1, c2 = read_coder(paths[0]), read_coder(paths[1])
    common = sorted(set(c1) & set(c2))
    if not common:
        print("No clauses were scored by both coders. Check that the reference labels match.")
        return
    print(f"\nTwo coders, clauses scored by both {len(common)}\n")
    dn1, dn2 = [c1[r][0] for r in common], [c2[r][0] for r in common]
    ag1, ag2 = [c1[r][1] for r in common], [c2[r][1] for r in common]
    report_axis("Axis Descriptive to Normative", common, dn1, dn2, "dn")
    print()
    report_axis("Axis Abstract to Granular", common, ag1, ag2, "ag")
    print("\nGuide. Under about 0.4 is weak, 0.4 to 0.6 moderate, 0.6 to 0.8 substantial, "
          "above 0.8 almost perfect. Report the weighted kappa with the raw agreement, "
          "and describe how you reconciled the flagged clauses.\n")


if __name__ == "__main__":
    main()
