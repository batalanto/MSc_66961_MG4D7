"""
Sensitivity analysis for the two thresholds in the pipeline.
Sweeps the conformance threshold (stage three) and the retrieval cutoff (stage two)
and shows how stable the true-red and false-green result is in Times New Roman style.
"""
import warnings, logging
warnings.filterwarnings("ignore"); logging.getLogger("pm4py").setLevel(logging.ERROR)
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import random

from synthetic_logs import generate_logs, _roughen
from abstraction import map_retrieval
from conformance import Checker, ALPHA_9, ALPHA_12, _project, fitness_against
from reference_model import (ART_9_SETUP, ART_9_CORE, ART_9_TESTING,
                             ART_9_PARALLEL, ART_12_ACTIVITIES)

INK, TEAL, AMBER, RED = "#15233B", "#1D6F5C", "#C8922A", "#C0473F"

def _abstract(raw_events, cutoff):
    return [m for m in (map_retrieval(e, cutoff=cutoff) for e in raw_events) if m is not None]

def conformance_sweep(chk, n=50, seed=7):
    logs = generate_logs(n_per=n, seed=seed)
    mins = {"A": [], "B": [], "C": []}
    for name, traces in logs.items():
        for t in traces:
            ab = _abstract(t["raw_events"], 0.72)
            f9 = fitness_against(_project(ab, ALPHA_9), chk.net9, chk.im9, chk.fm9)
            f12 = fitness_against(_project(ab, ALPHA_12), chk.net12, chk.im12, chk.fm12)
            mins[name].append(min(f9, f12))
    thresholds = [0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.99, 0.999]
    print("\nConformance threshold sweep, traces conforming out of", n)
    print(f"  {'threshold':>10s}{'A true-green':>14s}{'B flagged':>12s}{'C false-green':>15s}")
    rows = []
    for th in thresholds:
        a = sum(1 for m in mins["A"] if m > th)
        b = sum(1 for m in mins["B"] if m <= th)
        c = sum(1 for m in mins["C"] if m > th)
        rows.append((th, a, b, c))
        print(f"  {th:>10.3f}{a:>14d}{b:>12d}{c:>15d}")
    maxB = max(mins["B"])
    print(f"\n  highest structural-fault fitness in B is {maxB:.3f}")
    print(f"  A and C sit at fitness {min(mins['A']+mins['C']):.3f}")
    print(f"  any threshold between {maxB:.3f} and 1.000 separates them perfectly")
    print("  the false-green result is threshold-free, C conforms for every threshold below one")
    return rows, maxB

def cutoff_sweep(chk, n=50, seed=7):
    rng = random.Random(3)
    canon = ART_9_SETUP + ART_9_CORE + ART_9_TESTING + ART_9_PARALLEL + list(ART_12_ACTIVITIES)
    labelled = []
    for _ in range(1200):
        c = rng.choice(canon); labelled.append((_roughen(c, rng), c))
    logs = generate_logs(n_per=n, seed=seed)
    cutoffs = [0.60, 0.65, 0.70, 0.72, 0.75, 0.80, 0.85, 0.90]
    print("\nRetrieval cutoff sweep")
    print(f"  {'cutoff':>8s}{'mapping accuracy':>18s}{'A conforms of '+str(n):>18s}")
    rows = []
    for cut in cutoffs:
        acc = sum(1 for raw, true in labelled if map_retrieval(raw, cutoff=cut) == true) / len(labelled)
        conf = 0
        for t in logs["A"]:
            ab = _abstract(t["raw_events"], cut)
            f9 = fitness_against(_project(ab, ALPHA_9), chk.net9, chk.im9, chk.fm9)
            f12 = fitness_against(_project(ab, ALPHA_12), chk.net12, chk.im12, chk.fm12)
            conf += 1 if (f9 > 0.999 and f12 > 0.999) else 0
        rows.append((cut, acc, conf))
        print(f"  {cut:>8.2f}{acc*100:>17.1f}%{conf:>18d}")
    return rows

def plots(csweep, maxB, ksweep, n=50, out_png="sensitivity.png"):
    # --- EXACT TIMES NEW ROMAN & STIX TYPOGRAPHY ---
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman", "Nimbus Roman", "Liberation Serif"] + plt.rcParams["font.serif"]
    plt.rcParams["mathtext.fontset"] = "stix"
    plt.rcParams["axes.formatter.use_mathtext"] = True
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["ytick.direction"] = "in"

    fig, ax = plt.subplots(1, 2, figsize=(13.5, 5.8), dpi=300)

    th = [r[0] for r in csweep]
    cut = [r[0] for r in ksweep]

    # --- PANEL (a): STAGE THREE ---
    ax[0].plot(th, [r[1] for r in csweep], "-o", color=TEAL, linewidth=2.2,
               markersize=8, markeredgecolor="white", markeredgewidth=1.2,
               label="A (True-green)", zorder=4)
    ax[0].plot(th, [r[2] for r in csweep], "-s", color=RED, linewidth=2.2,
               markersize=8, markeredgecolor="white", markeredgewidth=1.2,
               label="B (Flagged)", zorder=4)
    ax[0].plot(th, [r[3] for r in csweep], "-^", color=AMBER, linewidth=2.2,
               markersize=8, markeredgecolor="white", markeredgewidth=1.2,
               label="C (False-green)", zorder=3)

    # Shaded & Hatched Stable Band
    ax[0].axvspan(maxB, 1.0, color=TEAL, alpha=0.08, zorder=1)
    ax[0].axvspan(maxB, 1.0, facecolor="none", edgecolor=TEAL, hatch="///",
                  alpha=0.18, linewidth=0.0, zorder=2)
    ax[0].axvline(maxB, color=TEAL, linestyle="--", linewidth=1.2, alpha=0.7, zorder=3)

    mid_band = (maxB + 1.000) / 2.0
    ax[0].text(mid_band, n * 0.45,
               r"$\mathbf{Stable\ Band}$" + "\n" + rf"($[{maxB:.3f}, 1.000]$)",
               ha="center", va="center", fontsize=12.5, color=INK, zorder=5,
               bbox=dict(facecolor="white", edgecolor="#CCCCCC", lw=0.6, alpha=0.95, pad=4.0))

    ax[0].set_xlabel(r"$\longleftarrow\ \mathrm{Conformance\ Threshold}\ (\tau)\ \longrightarrow$", fontsize=15)
    ax[0].set_ylabel(rf"$\mathrm{{Traces\ Conforming\ (out\ of\ N={n})}}$", fontsize=15)
    ax[0].set_title(r"$\mathbf{(a)}$ Stage Three: Threshold Sensitivity", fontsize=16.5, pad=14, color=INK)
    ax[0].set_ylim(-2.5, n + 4.5)
    ax[0].set_xlim(min(th) - 0.004, 1.004)

    # --- PANEL (b): STAGE TWO ---
    ax[1].plot(cut, [r[1] * 100 for r in ksweep], "-o", color=TEAL, linewidth=2.2,
               markersize=8, markeredgecolor="white", markeredgewidth=1.2,
               label="Mapping Accuracy (%)", zorder=4)
    ax[1].plot(cut, [r[2] / n * 100 for r in ksweep], "-s", color=AMBER, linewidth=2.2,
               markersize=8, markeredgecolor="white", markeredgewidth=1.2,
               label="A: Conforming Traces (%)", zorder=4)

    ax[1].axvline(0.72, color="#777777", linestyle="--", linewidth=1.2, alpha=0.7, zorder=2)
    ax[1].text(0.72, 18, r"$\mathrm{Cutoff} = 0.72$", ha="center", va="center",
               fontsize=12, color="#333333", zorder=5,
               bbox=dict(facecolor="white", edgecolor="#CCCCCC", lw=0.6, alpha=0.95, pad=3.5))

    ax[1].set_xlabel(r"$\longleftarrow\ \mathrm{Retrieval\ Similarity\ Cutoff}\ (\theta)\ \longrightarrow$", fontsize=15)
    ax[1].set_ylabel(r"$\mathrm{Percentage\ (\%)}$", fontsize=15)
    ax[1].set_title(r"$\mathbf{(b)}$ Stage Two: Cutoff Sensitivity", fontsize=16.5, pad=14, color=INK)
    ax[1].set_ylim(0, 108)
    ax[1].set_xlim(min(cut) - 0.01, max(cut) + 0.01)

    # --- SHARED STYLING ---
    for a in ax:
        a.grid(True, linestyle=":", color="#DDDDDD", linewidth=1, zorder=0)
        a.tick_params(top=True, right=True, direction="in", length=6, width=1, labelsize=13)
        a.spines["top"].set_visible(True)
        a.spines["right"].set_visible(True)
        a.legend(loc="lower left" if a == ax[0] else "lower center",
                 frameon=True, edgecolor="#CCCCCC", fontsize=12.5,
                 facecolor="white", framealpha=0.95)

    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    print("\nsaved", out_png)

if __name__ == "__main__":
    chk = Checker()
    csweep, maxB = conformance_sweep(chk)
    ksweep = cutoff_sweep(chk)
    plots(csweep, maxB, ksweep)