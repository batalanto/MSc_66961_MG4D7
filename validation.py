"""
Validation of the clause classification and construct-space mapping.
"""

import csv
import math

import matplotlib
matplotlib.use("Agg")
import matplotlib.lines as mlines
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import matplotlib.transforms as transforms
from matplotlib.patches import Ellipse
import numpy as np
import pandas as pd

from reference_model import (
    ART_9_SETUP,
    ART_9_CORE,
    ART_9_TESTING,
    ART_9_PARALLEL,
    ART_12_ACTIVITIES,
)
from conformance import Checker, ALPHA_9, ALPHA_12, _project, fitness_against


# clause --> (representative activity, violation type)
# violation types:
# structural, dual, open, permissive
CLAUSE_MAP = {
    "Art. 9(1)":        ("Establish RMS", "structural"),
    "Art. 9(2) intro":  (None, "open"),
    "Art. 9(2)(a)":     ("Identify risks", "dual"),
    "Art. 9(2)(b)":     ("Estimate risks", "dual"),
    "Art. 9(2)(c)":     ("Evaluate post-market data", "structural"),
    "Art. 9(2)(d)":     ("Adopt measures", "dual"),
    "Art. 9(3)":        (None, "open"),
    "Art. 9(4)":        (None, "open"),
    "Art. 9(5) intro":  ("Judge residual risk", "open"),
    "Art. 9(5)(a)":     ("Reduce via design", "dual"),
    "Art. 9(5)(b)":     ("Implement mitigation", "dual"),
    "Art. 9(5)(c)":     ("Provide info", "structural"),
    "Art. 9(5) out":    (None, "open"),
    "Art. 9(6)":        ("Test AI system", "dual"),
    "Art. 9(7)":        (None, "permissive"),
    "Art. 9(8)":        ("Define metrics", "structural"),
    "Art. 9(9)":        (None, "open"),
    "Art. 9(10)":       (None, "permissive"),
    "Art. 12(1)":       ("enable logging", "structural"),
    "Art. 12(2) intro": (None, "open"),
    "Art. 12(2)(a)":    ("record risk-relevant events", "dual"),
    "Art. 12(2)(b)":    ("record post-market events", "structural"),
    "Art. 12(2)(c)":    ("record operational events", "structural"),
    "Art. 12(3) intro": (None, "permissive"),
    "Art. 12(3)(a)":    ("record use period", "structural"),
    "Art. 12(3)(b)":    ("record reference DB", "structural"),
    "Art. 12(3)(c)":    ("record matching input", "structural"),
    "Art. 12(3)(d)":    ("record verifier identity", "structural"),
}

KIND_COLOUR = {
    "structural": "#1D6F5C",
    "dual": "#C8922A",
    "open": "#C0473F",
    "permissive": "#AEB6C0",
}

KIND_LABEL = {
    "structural": "structural (checkable breach)",
    "dual": "dual (activity checkable, adequacy open)",
    "open": "open (no structural handle)",
    "permissive": "permissive (no obligation)",
}

ANGLE_MAP = {
    (1.0, 5.0): [15, 50, 85, 120],
    (1.0, 4.5): [145, 175],
    (1.0, 4.0): [165, 195],
    (1.0, 3.5): [180],
    (1.0, 3.0): [20, 200],
    (1.0, 2.5): [220, 320],
    (2.5, 3.5): [135],
    (2.5, 4.5): [45],
    (3.0, 1.0): [30],
    (3.0, 2.5): [210],
    (4.0, 4.0): [45],
    (4.5, 2.0): [220],
    (4.5, 2.5): [45],
    (4.5, 3.5): [135],
    (5.0, 1.0): [45],
    (5.0, 2.0): [315, 220],
    (5.0, 2.5): [140, 35],
    (5.0, 3.5): [135, 45],
}

# compliant baseline trace
BASE = (
    list(ART_9_SETUP)
    + list(ART_9_CORE)
    + list(ART_9_TESTING)
    + list(ART_9_PARALLEL)
    + list(ART_12_ACTIVITIES)
)


def probe_fitness(checker, activity, kind):
    """Tests whether a clause violation affects alignment fitness."""
    if kind == "permissive":
        return None

    if kind in ("structural", "dual") and activity is not None:
        broken = [a for a in BASE if a != activity]
        f9 = fitness_against(
            _project(broken, ALPHA_9),
            checker.net9,
            checker.im9,
            checker.fm9,
        )
        f12 = fitness_against(
            _project(broken, ALPHA_12),
            checker.net12,
            checker.im12,
            checker.fm12,
        )
        return min(f9, f12)

    # Open clauses leave the trace unchanged.
    return 1.0


def read_grid(path="clause_grid_coordinates.csv"):
    """Loads the clause coordinates."""
    rows = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            rows[row["reference"].strip()] = (
                float(row["dn_mean"]),
                float(row["ag_mean"]),
            )
    return rows


def run(
    grid_path="clause_grid_coordinates.csv",
    out_png="validation_grid.png",
    out_csv="validation_results.csv",
):
    """Runs the validation and saves the results."""
    checker = Checker()
    coords = read_grid(grid_path)
    results = []

    for ref, (activity, kind) in CLAUSE_MAP.items():
        if ref not in coords:
            continue

        dn, ag = coords[ref]
        fit = probe_fitness(checker, activity, kind)
        detected = fit is not None and fit < 0.999

        results.append(
            {
                "reference": ref,
                "dn": dn,
                "ag": ag,
                "activity": activity or "",
                "kind": kind,
                "probe_fitness": "" if fit is None else round(fit, 3),
                "detected": detected,
                "colour": KIND_COLOUR[kind],
            }
        )

    with open(out_csv, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "reference",
                "dn",
                "ag",
                "activity",
                "kind",
                "probe_fitness",
                "detected",
                "colour",
            ],
        )
        writer.writeheader()
        writer.writerows(results)

    _plot(results, out_png)
    return results


def _confidence_ellipse(x, y, ax, n_std=1.0, **kwargs):
    """Adds a covariance ellipse to an axis."""
    if len(x) < 3:
        return None

    cov = np.cov(x, y)
    if not np.all(np.isfinite(cov)):
        return None

    denom = np.sqrt(cov[0, 0] * cov[1, 1])
    if denom == 0:
        return None

    pearson = np.clip(cov[0, 1] / denom, -1.0, 1.0)
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)

    ellipse = Ellipse(
        (0, 0),
        width=ell_radius_x * 2,
        height=ell_radius_y * 2,
        **kwargs,
    )

    scale_x = np.sqrt(cov[0, 0]) * n_std
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    transform = (
        transforms.Affine2D()
        .rotate_deg(45)
        .scale(scale_x, scale_y)
        .translate(mean_x, mean_y)
    )
    ellipse.set_transform(transform + ax.transData)
    return ax.add_patch(ellipse)


def _article_for_reference(reference):
    """Returns the article group used for marker styling."""
    return "Article 12" if reference.startswith("Art. 12") else "Article 9"


def _plot(results, out_png):
    """Plots the redesigned validation grid."""
    df = pd.DataFrame(results)
    if df.empty:
        raise ValueError("No validation results available for plotting.")

    df["article"] = df["reference"].map(_article_for_reference)
    df["short_ref"] = df["reference"].str.replace("Art. ", "", regex=False)

    plt.rcParams["font.family"] = "serif"
    plt.rcParams["mathtext.fontset"] = "cm"
    plt.rcParams["axes.formatter.use_mathtext"] = True
    plt.rcParams["xtick.direction"] = "in"
    plt.rcParams["ytick.direction"] = "in"

    fig = plt.figure(figsize=(12, 12), dpi=300)
    gs = fig.add_gridspec(5, 5, wspace=0.08, hspace=0.08)

    ax_main = fig.add_subplot(gs[1:5, 0:4])
    ax_top = fig.add_subplot(gs[0, 0:4], sharex=ax_main)
    ax_right = fig.add_subplot(gs[1:5, 4], sharey=ax_main)

    ax_top.tick_params(
        labelbottom=False,
        bottom=False,
        left=True,
        labelleft=True,
        direction="in",
        labelsize=12,
    )
    ax_right.tick_params(
        labelleft=False,
        left=False,
        bottom=True,
        labelbottom=True,
        direction="in",
        labelsize=12,
    )
    ax_main.tick_params(
        top=True,
        right=True,
        direction="in",
        length=6,
        width=1,
        labelsize=13.5,
    )

    for spine in ["top", "right"]:
        ax_top.spines[spine].set_visible(False)
        ax_right.spines[spine].set_visible(False)

    ax_top.spines["bottom"].set_visible(False)
    ax_right.spines["left"].set_visible(False)
    ax_top.spines["left"].set_color("#333333")
    ax_right.spines["bottom"].set_color("#333333")

    # Slight horizontal separation between Article 9 and Article 12.
    jitter = 0.04
    df["plot_x"] = np.where(
        df["article"] == "Article 9",
        df["dn"] - jitter,
        df["dn"] + jitter,
    )

    # Main scatter plot.
    for _, row in df.iterrows():
        marker = "o" if row["article"] == "Article 9" else "s"
        ax_main.scatter(
            row["plot_x"],
            row["ag"],
            c=KIND_COLOUR[row["kind"]],
            marker=marker,
            s=70,
            zorder=4,
            edgecolor="white",
            linewidth=0.6,
        )

    # One-sigma confidence ellipses.
    for kind, linestyle in [
        ("structural", "--"),
        ("dual", "-."),
        ("open", ":"),
    ]:
        subset = df[df["kind"] == kind]
        if len(subset) >= 3:
            _confidence_ellipse(
                subset["dn"].to_numpy(),
                subset["ag"].to_numpy(),
                ax_main,
                n_std=1.0,
                edgecolor=KIND_COLOUR[kind],
                facecolor="none",
                linestyle=linestyle,
                alpha=0.7,
                lw=1.5,
                zorder=2,
            )

    # Stacked marginal histograms.
    values = np.arange(1.0, 5.5, 0.5)
    width = 0.22

    bottom_x = np.zeros(len(values))
    for kind in ["structural", "dual", "open", "permissive"]:
        counts = (
            df[df["kind"] == kind]["dn"]
            .value_counts()
            .reindex(values, fill_value=0)
            .to_numpy()
        )
        ax_top.bar(
            values,
            counts,
            width=width,
            bottom=bottom_x,
            color=KIND_COLOUR[kind],
            edgecolor="white",
            linewidth=0.5,
        )
        bottom_x += counts

    bottom_y = np.zeros(len(values))
    for kind in ["structural", "dual", "open", "permissive"]:
        counts = (
            df[df["kind"] == kind]["ag"]
            .value_counts()
            .reindex(values, fill_value=0)
            .to_numpy()
        )
        ax_right.barh(
            values,
            counts,
            height=width,
            left=bottom_y,
            color=KIND_COLOUR[kind],
            edgecolor="white",
            linewidth=0.5,
        )
        bottom_y += counts

    ax_top.set_ylabel("Count", fontsize=13, color="#333333")
    ax_right.set_xlabel("Count", fontsize=13, color="#333333")

    # Hatched danger zone.
    danger_rect = patches.Rectangle(
        (3, 1),
        2,
        2,
        linewidth=1,
        edgecolor="#AAAAAA",
        facecolor="none",
        hatch="///",
        alpha=0.3,
        zorder=1,
    )
    ax_main.add_patch(danger_rect)

    ax_main.text(
        4.0,
        0.72,
        r"$Zone_{danger}$" + "  " + r"$(Normative \wedge Abstract)$",
        color="#333333",
        ha="center",
        va="center",
        fontsize=13.5,
        zorder=2,
        bbox={
            "facecolor": "white",
            "edgecolor": "#CCCCCC",
            "lw": 0.6,
            "alpha": 0.95,
            "pad": 3.5,
        },
    )

    # Deterministic annotations for all clauses.
    for (dn, ag), group in df.groupby(["dn", "ag"], sort=False):
        angles = ANGLE_MAP.get(
            (float(dn), float(ag)),
            np.linspace(0, 360, len(group), endpoint=False),
        )

        for index, (_, row) in enumerate(group.iterrows()):
            x = row["plot_x"]
            y = row["ag"]
            degrees = angles[index % len(angles)]
            radians = np.radians(degrees)
            radius = 0.32

            label_x = x + radius * np.cos(radians)
            label_y = y + radius * np.sin(radians)

            cos_value = np.cos(radians)
            sin_value = np.sin(radians)
            ha = (
                "left"
                if cos_value > 0.15
                else "right"
                if cos_value < -0.15
                else "center"
            )
            va = (
                "bottom"
                if sin_value > 0.15
                else "top"
                if sin_value < -0.15
                else "center"
            )

            ax_main.annotate(
                rf"${row['short_ref']}$",
                xy=(x, y),
                xytext=(label_x, label_y),
                fontsize=11.5,
                color="#111111",
                ha=ha,
                va=va,
                arrowprops={
                    "arrowstyle": "-",
                    "color": "#777777",
                    "lw": 0.55,
                    "shrinkA": 5,
                    "shrinkB": 5,
                },
                zorder=5,
            )

    # Main axis formatting.
    ax_main.set_xlim(0.3, 5.7)
    ax_main.set_ylim(0.3, 5.7)
    ax_main.set_xticks([1, 2, 3, 4, 5])
    ax_main.set_yticks([1, 2, 3, 4, 5])

    ax_main.set_xlabel(
        r"$\longleftarrow Descriptive \quad|\quad Normative \longrightarrow$",
        fontsize=17,
    )
    ax_main.set_ylabel(
        r"$\longleftarrow Abstract \quad|\quad Granular \longrightarrow$",
        fontsize=17,
    )
    ax_main.set_title(
        "Clause Validation in Construct Space",
        fontsize=17,
        fontfamily="serif",
        pad=15,
    )

    ax_main.grid(
        True,
        linestyle=":",
        color="#DDDDDD",
        linewidth=1,
        zorder=0,
    )
    ax_main.spines["top"].set_visible(True)
    ax_main.spines["right"].set_visible(True)

    stats_text = (
        r"$\mathbf{Summary}$"
        + "\n"
        + rf"$N = {len(df)}$"
        + "\n"
        + rf"$\mathrm{{Structural}} = {(df['kind'] == 'structural').sum()}$"
        + "\n"
        + rf"$\mathrm{{Dual}} = {(df['kind'] == 'dual').sum()}$"
        + "\n"
        + rf"$\mathrm{{Open}} = {(df['kind'] == 'open').sum()}$"
        + "\n"
        + rf"$\mathrm{{Permissive}} = {(df['kind'] == 'permissive').sum()}$"
        + "\n"
        + r"Ellipses: $1\sigma$"
    )

    ax_main.text(
        0.98,
        0.98,
        stats_text,
        transform=ax_main.transAxes,
        fontsize=12.5,
        verticalalignment="top",
        horizontalalignment="right",
        bbox={
            "boxstyle": "round,pad=0.5",
            "facecolor": "white",
            "edgecolor": "#999999",
            "alpha": 0.8,
        },
        zorder=6,
    )

    # Category and article marker legend.
    handles = []
    for kind in ["structural", "dual", "open", "permissive"]:
        handles.append(
            mlines.Line2D(
                [],
                [],
                color=KIND_COLOUR[kind],
                marker="o",
                linestyle="None",
                markersize=8,
                label=KIND_LABEL[kind],
            )
        )

    handles.append(
        mlines.Line2D(
            [],
            [],
            color="#555555",
            marker="o",
            linestyle="None",
            markersize=8,
            label="Article 9 (Circle)",
        )
    )
    handles.append(
        mlines.Line2D(
            [],
            [],
            color="#555555",
            marker="s",
            linestyle="None",
            markersize=8,
            label="Article 12 (Square)",
        )
    )

    ax_main.legend(
        handles=handles,
        loc="lower left",
        frameon=True,
        edgecolor="#999999",
        fontsize=9.5,
        ncol=1,
    )

    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    for result in run():
        print(
            f"{result['reference']:20s} "
            f"{result['kind']:11s} "
            f"probe={str(result['probe_fitness']):>5s} "
            f"detected={result['detected']}"
        )