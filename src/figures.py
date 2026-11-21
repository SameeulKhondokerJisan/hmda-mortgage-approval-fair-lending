"""Static figures for the README, memo and notebook (reports/figures/*.png)."""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import config  # noqa: E402

BLUE, ORANGE, GREY, GREEN, RED = "#1f5aa6", "#e07b39", "#9aa5b1", "#2e8b57", "#c0392b"
GROUP_COLORS = {"White": GREY, "Black": BLUE, "Hispanic": ORANGE, "Asian": GREEN, "Other minority": "#7b5ea7",
                "Joint": "#b8c2cc", "Not reported": "#d5dbe1"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlesize": 11, "axes.titleweight": "bold", "figure.dpi": 110})


def _save(fig, name: str) -> str:
    path = config.FIGURES / name
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return f"reports/figures/{name}"


def denial_by_group(gr: pd.DataFrame) -> str:
    d = gr.iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.barh(d.applicant_group, d.denial_rate * 100, color=[GROUP_COLORS[g] for g in d.applicant_group])
    ax.errorbar(d.denial_rate * 100, d.applicant_group, xerr=[(d.denial_rate - d.denial_ci_low) * 100,
                                                              (d.denial_ci_high - d.denial_rate) * 100],
                fmt="none", ecolor="black", capsize=3, lw=1)
    for y, (rate, n) in enumerate(zip(d.denial_rate, d.applications)):
        ax.text(rate * 100 + 0.4, y, f"{rate * 100:.1f}%  (n={n:,.0f})", va="center", fontsize=9)
    ax.set_xlabel("Denial rate, % of decided applications (95% Wilson interval)")
    ax.set_title("Home-purchase mortgage denial rate by applicant group, 2025")
    ax.set_xlim(0, d.denial_rate.max() * 100 * 1.45)
    return _save(fig, "01_denial_rate_by_group.png")


def gap_ladder(ladder: pd.DataFrame) -> str:
    specs = list(dict.fromkeys(ladder.spec))
    groups = [g for g in ("Black", "Hispanic", "Asian", "Other minority") if g in set(ladder.group)]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    width = 0.8 / len(groups)
    for i, g in enumerate(groups):
        d = ladder[ladder.group == g].set_index("spec").reindex(specs)
        x = np.arange(len(specs)) + (i - (len(groups) - 1) / 2) * width
        ax.bar(x, d.coef * 100, width, color=GROUP_COLORS[g], label=g)
        ax.errorbar(x, d.coef * 100, yerr=[(d.coef - d.ci_low) * 100, (d.ci_high - d.coef) * 100], fmt="none",
                    ecolor="black", capsize=2, lw=0.8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(np.arange(len(specs)), [s[2:] for s in specs])
    ax.set_ylabel("Denial gap vs White applicants (percentage points)")
    ax.set_title("Denial gaps shrink with underwriting controls but do not close")
    ax.legend(frameon=False, ncol=4, loc="upper right")
    return _save(fig, "02_denial_gap_ladder.png")


def dti_profile(dti: pd.DataFrame) -> str:
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    for lt, color in (("Conventional", BLUE), ("FHA", ORANGE), ("VA", GREEN)):
        d = dti[dti.loan_type == lt].sort_values("dti_value")
        exact = d[d.dti_value.between(36, 49)]
        ax.plot(d.dti_value, d.denial_rate * 100, color=color, lw=1, alpha=0.4)
        ax.plot(exact.dti_value, exact.denial_rate * 100, color=color, marker="o", ms=3, lw=1.6, label=lt)
        for v in (15, 25, 33, 55, 65):
            b = d[d.dti_value == v]
            if len(b):
                ax.plot(v, b.denial_rate.iloc[0] * 100, marker="s", color=color, ms=5)
    ax.axvline(49.5, color="black", ls="--", lw=0.8)
    ax.text(50, ax.get_ylim()[1] * 0.92, "50%: Fannie Mae automated\nunderwriting maximum", fontsize=8, va="top")
    ax.set_xticks([15, 25, 33, 36, 40, 44, 49, 55, 65], ["<20", "20-29", "30-35", "36", "40", "44", "49", "50-60", ">60"])
    ax.set_xlabel("Debt-to-income ratio reported (%), squares = published bands")
    ax.set_ylabel("Denial rate (%)")
    ax.set_title("Denial rates jump once debt-to-income passes 49%")
    ax.legend(frameon=False)
    return _save(fig, "03_denial_by_dti.png")


def denial_reasons(reasons: pd.DataFrame) -> str:
    keep = ["White", "Black", "Hispanic", "Asian"]
    top = (reasons[reasons.applicant_group.isin(keep)].groupby("reason").share_of_denials.mean()
           .sort_values(ascending=False).head(6).index)
    d = reasons[reasons.applicant_group.isin(keep) & reasons.reason.isin(top)]
    piv = d.pivot(index="reason", columns="applicant_group", values="share_of_denials").reindex(top[::-1])[keep]
    fig, ax = plt.subplots(figsize=(8.5, 4.4))
    y = np.arange(len(piv))
    h = 0.8 / len(keep)
    for i, g in enumerate(keep):
        ax.barh(y + (i - 1.5) * h, piv[g] * 100, h, color=GROUP_COLORS[g], label=g)
    ax.set_yticks(y, piv.index)
    ax.set_xlabel("% of denied applications citing the reason (up to four per application)")
    ax.set_title("Why applications were denied")
    ax.legend(frameon=False, loc="lower right")
    return _save(fig, "04_denial_reasons.png")


def decomposition(oax: list[dict]) -> str:
    fig, ax = plt.subplots(figsize=(8.5, 3.9))
    labels = [o["group"] for o in oax]
    for i, o in enumerate(oax):
        ax.barh(i, o["explained"] * 100, color=BLUE, label="Explained by underwriting factors" if i == 0 else None)
        ax.barh(i, o["unexplained"] * 100, left=o["explained"] * 100, color=ORANGE,
                label="Not explained" if i == 0 else None)
        top = max(o["blocks"].items(), key=lambda kv: kv[1])
        ax.text(o["raw_gap"] * 100 + 0.2, i, f"gap {o['raw_gap'] * 100:.1f} pp; "
                f"{o['unexplained'] / o['raw_gap'] * 100:.0f}% not explained; largest explained part: "
                f"{top[0].lower()} ({top[1] * 100:.1f} pp)", va="center", fontsize=8)
    ax.set_yticks(range(len(labels)), [f"{g} vs White" for g in labels])
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Denial-rate gap (percentage points), Oaxaca-Blinder decomposition")
    ax.set_title("How much of each gap underwriting factors explain")
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.2))
    ax.set_xlim(min(0, min(o["explained"] for o in oax) * 100) - 0.3, max(o["raw_gap"] for o in oax) * 100 * 2.4)
    return _save(fig, "05_gap_decomposition.png")


def tract_heatmap(tracts: pd.DataFrame) -> str:
    piv = tracts.pivot(index="tract_minority_band", columns="tract_income_band", values="denial_rate") * 100
    fig, ax = plt.subplots(figsize=(7.5, 4))
    im = ax.imshow(piv.to_numpy(), cmap="Oranges", aspect="auto")
    ax.set_xticks(range(piv.shape[1]), [c[2:] for c in piv.columns], fontsize=8)
    ax.set_yticks(range(piv.shape[0]), [r[2:] for r in piv.index])
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.iat[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.1f}%", ha="center", va="center", fontsize=8)
    ax.set_xlabel("Census tract median income, % of area median")
    ax.set_ylabel("Minority share of tract population")
    ax.set_title("Raw denial rate by neighbourhood")
    fig.colorbar(im, ax=ax, label="Denial rate (%)")
    return _save(fig, "06_denial_by_neighbourhood.png")


def pricing_gaps(price: pd.DataFrame) -> str:
    specs = list(dict.fromkeys(price.spec))
    groups = [g for g in ("Black", "Hispanic", "Asian") if g in set(price.group)]
    fig, ax = plt.subplots(figsize=(8, 3.8))
    width = 0.8 / len(groups)
    for i, g in enumerate(groups):
        d = price[price.group == g].set_index("spec").reindex(specs)
        x = np.arange(len(specs)) + (i - (len(groups) - 1) / 2) * width
        ax.bar(x, d.coef, width, color=GROUP_COLORS[g], label=g)
        ax.errorbar(x, d.coef, yerr=[d.coef - d.ci_low, d.ci_high - d.coef], fmt="none", ecolor="black", capsize=2,
                    lw=0.8)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(np.arange(len(specs)), [s[2:] for s in specs])
    ax.set_ylabel("Rate spread vs White borrowers (basis points)")
    ax.set_title("Pricing gaps on originated conventional 30-year fixed loans")
    ax.legend(frameon=False, ncol=3)
    return _save(fig, "07_pricing_gaps.png")


def lender_screen(screen: pd.DataFrame) -> str:
    d = screen.sort_values("adj_gap_black")
    fig, ax = plt.subplots(figsize=(8.5, max(4, 0.28 * len(d) + 1)))
    y = np.arange(len(d))
    ax.errorbar(d.adj_gap_black * 100, y, xerr=[(d.adj_gap_black - d.ci_low_black) * 100,
                                               (d.ci_high_black - d.adj_gap_black) * 100],
                fmt="o", color=BLUE, ecolor=BLUE, ms=4, capsize=2, label="Adjusted (controls + county)")
    ax.plot(d.raw_gap_black * 100, y, "x", color=GREY, label="Raw gap")
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y, [n[:34] for n in d.lender_name], fontsize=7)
    ax.set_xlabel("Black-White denial gap within the lender (percentage points, 95% CI)")
    ax.set_title(f"Lender screen: {len(d)} largest lenders")
    ax.legend(frameon=False, fontsize=8, loc="lower right")
    return _save(fig, "08_lender_screen.png")
