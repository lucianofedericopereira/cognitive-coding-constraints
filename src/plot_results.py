"""
plot_results.py — Generate all paper figures from experiment results.

Output directory: results/plots/
Figures:
  fig1_token_counts_by_notation.pdf    — Exp 1: token distributions per notation × tokenizer
  fig2_internotation_ratio.pdf         — Exp 1: dot/camelCase ratio distribution + H1 annotation
  fig3_scs_vs_complexity.pdf           — Exp 2: SCS and SAS as functions of cyclomatic complexity
  fig4_changepoint_overlay.pdf         — Exp 2: piecewise fit with CDCC threshold annotation
  fig5_cross_model_heatmap.pdf         — Exp 3: Spearman ρ heatmap across tokenizer pairs
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns

from utils import EXP1_RESULTS, EXP2_RESULTS, EXP3_RESULTS, DATA_DIR, get_logger

log = get_logger(__name__)

PLOTS_DIR = Path(__file__).resolve().parent.parent / "results" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

NOTATION_COLS = ["dot", "camelCase", "snake_case", "kebab_case"]
PALETTE = {"dot": "#e74c3c", "camelCase": "#2ecc71", "snake_case": "#3498db", "kebab_case": "#f39c12"}
CDCC_COLOR = "#8e44ad"
STYLE = "seaborn-v0_8-whitegrid"


# ---------------------------------------------------------------------------
# Figure 1 — Token count distributions by notation and tokenizer
# ---------------------------------------------------------------------------

def fig1_token_distributions(df: pd.DataFrame) -> None:
    tokenizers = df["tokenizer"].unique()
    fig, axes = plt.subplots(1, len(tokenizers), figsize=(4 * len(tokenizers), 5), sharey=False)
    if len(tokenizers) == 1:
        axes = [axes]

    for ax, tok in zip(axes, tokenizers):
        sub = df[df["tokenizer"] == tok]
        data = [sub[f"{n}_tokens"].values for n in NOTATION_COLS]
        bp = ax.boxplot(data, labels=NOTATION_COLS, patch_artist=True, notch=False)
        for patch, notation in zip(bp["boxes"], NOTATION_COLS):
            patch.set_facecolor(PALETTE[notation])
            patch.set_alpha(0.7)
        ax.set_title(tok, fontsize=10)
        ax.set_ylabel("Token count" if tok == tokenizers[0] else "")
        ax.tick_params(axis="x", rotation=30)

    fig.suptitle("Figure 1 — Token count distributions by notation × tokenizer", fontsize=11, y=1.02)
    plt.tight_layout()
    out = PLOTS_DIR / "fig1_token_counts_by_notation.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Figure 2 — Inter-notation ratio distribution
# ---------------------------------------------------------------------------

def fig2_ratio_distribution(df: pd.DataFrame) -> None:
    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(7, 4))
        for tok in df["tokenizer"].unique():
            sub = df[df["tokenizer"] == tok].copy()
            if "dot_vs_camelCase_ratio" not in sub.columns:
                sub["dot_vs_camelCase_ratio"] = sub["dot_tokens"] / sub["camelCase_tokens"]
            ratios = sub["dot_vs_camelCase_ratio"].dropna()
            ax.hist(ratios, bins=20, alpha=0.5, label=tok, density=True)

        ax.axvline(1.67, color="black", linestyle="--", linewidth=1.2, label="Theoretical 1.67× (Pereira 2026a)")
        ax.axvline(1.0, color="grey", linestyle=":", linewidth=1, label="Ratio = 1 (no overhead)")
        ax.set_xlabel("dot / camelCase token ratio")
        ax.set_ylabel("Density")
        ax.set_title("Figure 2 — Inter-notation ratio distribution (dot vs camelCase)")
        ax.legend(fontsize=8)

    out = PLOTS_DIR / "fig2_internotation_ratio.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Figure 3 — SCS and SAS vs cyclomatic complexity
# ---------------------------------------------------------------------------

def fig3_scs_sas_vs_complexity(scores_df: pd.DataFrame, metrics_df: pd.DataFrame) -> None:
    merged = metrics_df.merge(scores_df, on="function_id", how="inner")
    merged = merged.sort_values("complexity")

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, col, label in [
        (axes[0], "scs", "Self-Consistency Score (SCS)"),
        (axes[1], "mean_sas", "Semantic Accuracy Score (SAS)"),
    ]:
        if col not in merged.columns:
            ax.text(0.5, 0.5, f"{col} not available", ha="center", va="center", transform=ax.transAxes)
            ax.set_title(label)
            continue
        sub = merged[["complexity", col]].dropna()
        ax.scatter(sub["complexity"], sub[col], alpha=0.5, s=20, color="#2c3e50")
        # Smooth trend via rolling mean
        sub_sorted = sub.sort_values("complexity")
        ax.plot(
            sub_sorted["complexity"],
            sub_sorted[col].rolling(5, center=True, min_periods=1).mean(),
            color="#e74c3c", linewidth=1.5, label="Rolling mean",
        )
        ax.axvline(10, color=CDCC_COLOR, linestyle="--", linewidth=1.2, label="CDCC threshold (10)")
        ax.set_xlabel("Cyclomatic complexity")
        ax.set_ylabel(label)
        ax.set_title(f"Figure 3 — {label} vs complexity")
        ax.legend(fontsize=8)

    plt.tight_layout()
    out = PLOTS_DIR / "fig3_scs_vs_complexity.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Figure 4 — Piecewise fit with CDCC threshold annotation
# ---------------------------------------------------------------------------

def fig4_changepoint_overlay(scores_df: pd.DataFrame, metrics_df: pd.DataFrame) -> None:
    merged = metrics_df.merge(scores_df, on="function_id", how="inner")
    merged = merged.sort_values("complexity")

    col = "scs" if "scs" in merged.columns else None
    if col is None:
        log.warning("SCS not available; skipping fig4.")
        return

    sub = merged[["complexity", col]].dropna()
    x = sub["complexity"].values
    y = sub[col].values

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(x, y, alpha=0.4, s=18, color="#7f8c8d", label="Observations")

    # Piecewise fit at CDCC threshold
    from scipy.stats import linregress
    for mask, color, seg_label in [
        (x <= 10, "#2ecc71", "Fit: complexity ≤ 10"),
        (x > 10, "#e74c3c", "Fit: complexity > 10"),
    ]:
        if mask.sum() >= 2:
            slope, intercept, *_ = linregress(x[mask], y[mask])
            xf = np.linspace(x[mask].min(), x[mask].max(), 100)
            ax.plot(xf, slope * xf + intercept, color=color, linewidth=2, label=seg_label)

    ax.axvline(10, color=CDCC_COLOR, linestyle="--", linewidth=1.5, label="CDCC threshold (complexity=10)")
    ax.set_xlabel("Cyclomatic complexity")
    ax.set_ylabel("Self-Consistency Score (SCS)")
    ax.set_title("Figure 4 — Piecewise linear fit with CDCC change-point overlay")
    ax.legend(fontsize=8)

    out = PLOTS_DIR / "fig4_changepoint_overlay.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Figure 5 — Cross-model Spearman ρ heatmap
# ---------------------------------------------------------------------------

def fig5_correlation_heatmap(corr_df: pd.DataFrame) -> None:
    tokenizers = sorted(set(corr_df["tokenizer_a"].tolist() + corr_df["tokenizer_b"].tolist()))
    n = len(tokenizers)
    matrix = np.ones((n, n))
    idx = {t: i for i, t in enumerate(tokenizers)}

    for _, row in corr_df.iterrows():
        i, j = idx[row["tokenizer_a"]], idx[row["tokenizer_b"]]
        matrix[i, j] = row["spearman_rho"]
        matrix[j, i] = row["spearman_rho"]

    fig, ax = plt.subplots(figsize=(max(5, n), max(4, n - 1)))
    sns.heatmap(
        matrix, annot=True, fmt=".2f",
        xticklabels=tokenizers, yticklabels=tokenizers,
        vmin=0, vmax=1, cmap="YlGnBu",
        ax=ax, linewidths=0.5,
    )
    ax.set_title("Figure 5 — Cross-model Spearman ρ (notation efficiency ranking)")
    plt.tight_layout()
    out = PLOTS_DIR / "fig5_cross_model_heatmap.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    exp1 = pd.read_csv(EXP1_RESULTS) if EXP1_RESULTS.exists() and EXP1_RESULTS.stat().st_size > 50 else None
    exp2 = pd.read_csv(EXP2_RESULTS) if EXP2_RESULTS.exists() and EXP2_RESULTS.stat().st_size > 50 else None
    exp3 = pd.read_csv(EXP3_RESULTS) if EXP3_RESULTS.exists() and EXP3_RESULTS.stat().st_size > 50 else None
    metrics = DATA_DIR / "code_metrics.csv"
    metrics_df = pd.read_csv(metrics) if metrics.exists() and metrics.stat().st_size > 50 else None

    if exp1 is not None:
        fig1_token_distributions(exp1)
        fig2_ratio_distribution(exp1)
    else:
        log.warning("Exp1 results not available — skipping fig1, fig2.")

    if exp2 is not None and metrics_df is not None:
        fig3_scs_sas_vs_complexity(exp2, metrics_df)
        fig4_changepoint_overlay(exp2, metrics_df)
    else:
        log.warning("Exp2 results or metrics not available — skipping fig3, fig4.")

    if exp3 is not None and not exp3.empty:
        fig5_correlation_heatmap(exp3)
    else:
        log.warning("Exp3 results not available — skipping fig5.")

    log.info("All available figures saved to %s", PLOTS_DIR)


if __name__ == "__main__":
    run()
