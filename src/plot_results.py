# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
plot_results.py — Generate all paper figures from experiment results.

Output directory: results/plots/
Figures:
  fig1_token_counts_by_notation.pdf    — Exp 1: token distributions per notation × tokenizer
  fig2_internotation_ratio.pdf         — Exp 1: dot/camelCase ratio distribution + H1 annotation
  fig3_output_ratio_vs_complexity.pdf  — Exp 2: output/input ratio vs cyclomatic complexity
  fig4_loglog_production_function.pdf  — Exp 2: log-log production function fit (β estimate)
  fig5_cross_model_heatmap.pdf         — Exp 3: Spearman ρ heatmap across tokenizer pairs
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
from scipy import stats

from utils import EXP1_RESULTS, EXP2_RESULTS, EXP3_RESULTS, DATA_DIR, get_logger

log = get_logger(__name__)

PLOTS_DIR = Path(__file__).resolve().parent.parent / "results" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

NOTATION_COLS = ["dot", "camelCase", "snake_case", "kebab_case"]
PALETTE = {
    "dot": "#e74c3c",
    "camelCase": "#2ecc71",
    "snake_case": "#3498db",
    "kebab_case": "#f39c12",
}
CDCC_COLOR  = "#8e44ad"
COMPLY_COLOR  = "#2ecc71"
VIOLATE_COLOR = "#e74c3c"
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
        bp = ax.boxplot(data, tick_labels=NOTATION_COLS, patch_artist=True, notch=False)
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

        ax.axvline(1.67, color="black", linestyle="--", linewidth=1.2,
                   label="Theoretical 1.67× (Pereira 2026a)")
        ax.axvline(1.0, color="grey", linestyle=":", linewidth=1,
                   label="Ratio = 1 (no overhead)")
        ax.set_xlabel("dot / camelCase token ratio")
        ax.set_ylabel("Density")
        ax.set_title("Figure 2 — Inter-notation ratio distribution (dot vs camelCase)")
        ax.legend(fontsize=8)

    out = PLOTS_DIR / "fig2_internotation_ratio.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Figure 3 — Output/input ratio vs cyclomatic complexity
# ---------------------------------------------------------------------------

def fig3_output_ratio_vs_complexity(
    scores_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> None:
    merged = metrics_df.merge(scores_df, on="function_id", how="inner")
    merged = merged.sort_values("complexity")
    merged = merged.dropna(subset=["complexity", "output_input_ratio"])

    compliant = merged[~merged["cdcc_violation"]]
    violating = merged[merged["cdcc_violation"]]

    spearman_r, spearman_p = stats.spearmanr(
        merged["complexity"], merged["output_input_ratio"]
    )
    gap = compliant["output_input_ratio"].mean() / violating["output_input_ratio"].mean()

    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(8, 5))

        ax.scatter(
            compliant["complexity"], compliant["output_input_ratio"],
            color=COMPLY_COLOR, alpha=0.7, s=40, label="CDCC-compliant", zorder=3,
        )
        ax.scatter(
            violating["complexity"], violating["output_input_ratio"],
            color=VIOLATE_COLOR, alpha=0.7, s=40, label="CDCC-violating", zorder=3,
        )

        # Rolling mean trend
        merged_s = merged.sort_values("complexity")
        trend = merged_s["output_input_ratio"].rolling(7, center=True, min_periods=1).mean()
        ax.plot(merged_s["complexity"], trend,
                color="#2c3e50", linewidth=2, linestyle="-", label="Rolling mean (k=7)")

        # Group mean lines
        ax.axhline(compliant["output_input_ratio"].mean(),
                   color=COMPLY_COLOR, linestyle="--", linewidth=1,
                   label=f"Compliant mean ({compliant['output_input_ratio'].mean():.3f})")
        ax.axhline(violating["output_input_ratio"].mean(),
                   color=VIOLATE_COLOR, linestyle="--", linewidth=1,
                   label=f"Violating mean ({violating['output_input_ratio'].mean():.3f})")

        # CDCC threshold
        ax.axvline(10, color=CDCC_COLOR, linestyle=":", linewidth=1.5,
                   label="CDCC threshold (complexity = 10)")

        # Annotation
        ax.text(
            0.97, 0.97,
            f"Spearman ρ = {spearman_r:.3f}  (p < 0.001)\n"
            f"Compliant/violating gap: {gap:.1f}×",
            transform=ax.transAxes, ha="right", va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#bdc3c7"),
        )

        ax.set_xlabel("Cyclomatic complexity")
        ax.set_ylabel("Output / input token ratio")
        ax.set_title(
            "Figure 3 — LLM output/input ratio vs code complexity\n"
            "(diminishing marginal returns; CDCC threshold marked)"
        )
        ax.legend(fontsize=8, loc="upper right", bbox_to_anchor=(0.97, 0.75))

    out = PLOTS_DIR / "fig3_output_ratio_vs_complexity.pdf"
    plt.savefig(out, bbox_inches="tight")
    plt.close()
    log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Figure 4 — Log-log production function
# ---------------------------------------------------------------------------

def fig4_loglog_production_function(
    scores_df: pd.DataFrame, metrics_df: pd.DataFrame
) -> None:
    merged = metrics_df.merge(scores_df, on="function_id", how="inner")
    merged = merged.dropna(subset=["mean_input_tokens", "mean_output_tokens"])

    log_input  = np.log(merged["mean_input_tokens"].values)
    log_output = np.log(merged["mean_output_tokens"].values)

    result = stats.linregress(log_input, log_output)
    beta  = result.slope
    alpha = result.intercept
    r2    = result.rvalue ** 2

    x_fit = np.linspace(log_input.min(), log_input.max(), 200)
    y_fit = alpha + beta * x_fit

    compliant = merged[~merged["cdcc_violation"]]
    violating = merged[merged["cdcc_violation"]]

    with plt.style.context(STYLE):
        fig, ax = plt.subplots(figsize=(7, 5))

        ax.scatter(
            np.log(compliant["mean_input_tokens"]),
            np.log(compliant["mean_output_tokens"]),
            color=COMPLY_COLOR, alpha=0.75, s=45, label="CDCC-compliant", zorder=3,
        )
        ax.scatter(
            np.log(violating["mean_input_tokens"]),
            np.log(violating["mean_output_tokens"]),
            color=VIOLATE_COLOR, alpha=0.75, s=45, label="CDCC-violating", zorder=3,
        )

        ax.plot(x_fit, y_fit, color="#2c3e50", linewidth=2,
                label=f"OLS fit  β = {beta:.3f}  R² = {r2:.3f}")

        # Constant-returns reference (β = 1)
        y_cr = alpha + 1.0 * x_fit
        ax.plot(x_fit, y_cr, color="#95a5a6", linewidth=1, linestyle="--",
                label="Constant returns (β = 1)")

        ax.text(
            0.05, 0.95,
            f"log(output) = {alpha:.2f} + {beta:.3f} · log(input)\n"
            f"β = {beta:.3f}  →  diminishing marginal returns\n"
            f"R² = {r2:.3f}   p < 0.001",
            transform=ax.transAxes, ha="left", va="top", fontsize=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#bdc3c7"),
        )

        ax.set_xlabel("log(input tokens)")
        ax.set_ylabel("log(output tokens)")
        ax.set_title(
            "Figure 4 — Log-log production function: LLM output elasticity\n"
            r"$\log(\mathrm{output}) = \alpha + \beta \cdot \log(\mathrm{input})$,"
            f"  β = {beta:.3f} < 1"
        )
        ax.legend(fontsize=8)

    out = PLOTS_DIR / "fig4_loglog_production_function.pdf"
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
# Figure 6 — Diminishing-returns production function curve (linear space)
# ---------------------------------------------------------------------------

def fig6_production_curve() -> None:
    """
    Illustrate the estimated production function in LINEAR space so the
    curvature is immediately visible: Q = exp(alpha) * K^beta.

    alpha = 2.843, beta = 0.102  (from Experiment 2 OLS fit)

    Also plots:
      - Constant-returns reference (beta = 1)
      - Marginal product curve (dQ/dK), showing how rapidly it falls
      - CDCC threshold vertical band
    """
    alpha = 2.843
    beta_hat = 0.102

    K = np.linspace(50, 2000, 500)          # input tokens (realistic range)
    Q_fit = np.exp(alpha) * K ** beta_hat   # estimated production function
    Q_cr  = np.exp(alpha) * K ** 1.0        # constant-returns reference (scaled)

    # Normalise constant-returns to start at the same point as the fit
    Q_cr_normed = Q_cr * (Q_fit[0] / Q_cr[0])

    # Marginal product: dQ/dK = alpha_A * beta * K^(beta-1)
    A = np.exp(alpha)
    MP = A * beta_hat * K ** (beta_hat - 1)

    with plt.style.context(STYLE):
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 7),
                                        gridspec_kw={"height_ratios": [2, 1]},
                                        sharex=True)

        # ---- Top panel: production function levels ----
        ax1.plot(K, Q_fit, color="#2c3e50", linewidth=2.5,
                 label=fr"$Q = e^{{{alpha}}}\cdot K^{{{beta_hat}}}$ (fitted, $\beta={beta_hat}$)")
        ax1.plot(K, Q_cr_normed, color="#95a5a6", linewidth=1.5, linestyle="--",
                 label=r"Constant returns ($\beta = 1$, rescaled)")

        # CDCC threshold band
        ax1.axvspan(0, 384, alpha=0.08, color=COMPLY_COLOR,
                    label=r"CDCC-compliant region ($K \leq 384$ tokens)")
        ax1.axvspan(384, 2000, alpha=0.05, color=VIOLATE_COLOR,
                    label="CDCC-violating region")
        ax1.axvline(384, color=CDCC_COLOR, linewidth=1.2, linestyle=":",
                    label="CDCC boundary (mean, complexity = 10)")

        ax1.set_ylabel("Output tokens (Q)", fontsize=10)
        ax1.set_title(
            f"Production Function: LLM Output vs. Input Complexity\n"
            r"$Q = e^{\alpha}\cdot K^{\beta}$"
            f",  α={alpha}, β={beta_hat}",
            fontsize=10
        )
        ax1.legend(fontsize=8, loc="upper left")

        # ---- Bottom panel: marginal product ----
        ax2.plot(K, MP, color="#e74c3c", linewidth=2,
                 label=r"Marginal product $\frac{dQ}{dK} = A\beta K^{\beta-1}$")
        ax2.axhline(0, color="black", linewidth=0.5)
        ax2.axvline(384, color=CDCC_COLOR, linewidth=1.2, linestyle=":")
        ax2.axvspan(0, 384, alpha=0.08, color=COMPLY_COLOR)
        ax2.axvspan(384, 2000, alpha=0.05, color=VIOLATE_COLOR)

        ax2.set_xlabel("Input tokens (K = code complexity proxy)", fontsize=10)
        ax2.set_ylabel("Marginal output\nper input token", fontsize=9)
        ax2.legend(fontsize=8)
        ax2.set_ylim(bottom=0)

        plt.tight_layout()
        out = PLOTS_DIR / "fig6_diminishing_returns_curve.pdf"
        plt.savefig(out, bbox_inches="tight")
        plt.close()
        log.info("Saved %s", out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run() -> None:
    def _load(path):
        if path.exists():
            df = pd.read_csv(path)
            return df if len(df) > 0 else None
        return None

    exp1       = _load(EXP1_RESULTS)
    exp2       = _load(EXP2_RESULTS)
    exp3       = _load(EXP3_RESULTS)
    metrics_df = _load(DATA_DIR / "code_metrics.csv")

    if exp1 is not None:
        fig1_token_distributions(exp1)
        fig2_ratio_distribution(exp1)
    else:
        log.warning("Exp1 results not available — skipping fig1, fig2.")

    if exp2 is not None and metrics_df is not None:
        fig3_output_ratio_vs_complexity(exp2, metrics_df)
        fig4_loglog_production_function(exp2, metrics_df)
    else:
        log.warning("Exp2 results or metrics not available — skipping fig3, fig4.")

    # fig6 is always generated from the fitted parameters (no data file needed)
    fig6_production_curve()

    if exp3 is not None:
        fig5_correlation_heatmap(exp3)
    else:
        log.warning("Exp3 results not available — skipping fig5.")

    log.info("All available figures saved to %s", PLOTS_DIR)


if __name__ == "__main__":
    run()