from __future__ import annotations
from pathlib import Path
from typing import Any

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib import patheffects as pe

from matplotlib.colors import to_rgba


from .utils import Hit


def plot_domain_map(seq_len: int, hits: list[Hit], conserved_idx: list[int], out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 1.8))
    ax.plot([1, seq_len], [0.5, 0.5], color="#444", linewidth=1.2, zorder=1)

    for h in hits:
        x0 = min(int(h.ali_start), int(h.ali_end))
        width = abs(int(h.ali_end) - int(h.ali_start)) + 1
        ax.add_patch(
            Rectangle(
                (x0, 0.25),
                width,
                0.5,
                facecolor="#7fb3d5",
                alpha=0.8,
                linewidth=0,
                zorder=0,
                label=h.family,
            )
        )

    if conserved_idx:
        ax.scatter(
            conserved_idx,
            [0.5] * len(conserved_idx),
            s=30,
            facecolors="none",
            edgecolors="#d62728",
            linewidths=1.5,
            zorder=2,
        )

    ax.set_xlim(1, seq_len)
    ax.set_ylim(0, 1)
    ax.set_yticks([])
    ax.set_xlabel("Sequence position")
    ax.set_title("Domain map with conserved sites")
    fig.tight_layout()
    fig.savefig(str(out_png), dpi=200)
    plt.close(fig)


def plot_conservation_track(scores: dict, out_png: Path, title: str = "Conservation (JSD)") -> None:
    jsd = scores["jsd"]
    fig, ax = plt.subplots(figsize=(10, 2.2))
    ax.plot(np.arange(1, len(jsd) + 1), jsd, linewidth=1.5)
    ax.set_xlim(1, len(jsd))
    ax.set_ylim(0, 1)
    ax.set_xlabel("Sequence position (aligned)")
    ax.set_ylabel("JSD (norm)")
    ax.set_title(title)
    fig.tight_layout()
    fig.savefig(str(out_png), dpi=200)
    plt.close(fig)


def plot_alignment_panel(
    seq: str,
    hit: Hit,
    conserved: set[int],
    out_png: Path,
    cons_values: list[float] | np.ndarray | None = None,
    *,
    cons_clip: tuple[float, float] = (5.0, 95.0),   # percentile clip range
    cons_gamma: float = 0.75,                       # <1 brightens mids; >1 darkens
    cons_smooth: int = 0,                           # 0=off, else odd window (e.g., 3)
    cons_show_scale: bool = True,                   # draw a tiny grayscale legend
    cons_min_brightness: float = 0.18,              # floor for background brightness
) -> None:
    """
    ...
    NEW controls:
      - cons_clip: percentile clip (low, high) before normalization (forces contrast)
      - cons_gamma: gamma applied after 0-1 normalization (shapes midtones)
      - cons_smooth: optional moving-average window over the span
      - cons_show_scale: draw a mini grayscale bar with numeric endpoints
    """
    start, end = int(hit.ali_start), int(hit.ali_end)
    if end < start:
        start, end = end, start

    xs = np.arange(start, end + 1)
    subseq = seq[start - 1 : end]

    fig_w = max(10.0, 0.12 * len(xs))
    fig, ax = plt.subplots(figsize=(fig_w, 1.8), constrained_layout=True)
    ax.set_facecolor("white")

    # translucent domain band behind text
    ax.axvspan(start - 0.5, end + 0.5, color="#77b3d5", alpha=0.25, zorder=0)

    # ---------- GRADIENT BACKGROUND (improved) ----------
    if cons_values is not None and len(xs) > 0:
        vec = np.asarray(cons_values, dtype=float)

        # Prefer slicing by absolute positions if vector covers full sequence;
        # otherwise accept a vector already matching the hit span.
        if vec.size >= len(seq):
            span_vals = vec[start - 1 : end]
        elif vec.size == len(xs):
            span_vals = vec
        else:
            span_vals = None  # length mismatch -> skip gracefully

        if span_vals is not None and span_vals.size == len(xs):
            v = np.array(span_vals, dtype=float)
            v[~np.isfinite(v)] = 0.0

            # Percentile clip to force usable contrast
            lo_p, hi_p = cons_clip
            lo = float(np.percentile(v, lo_p)) if hi_p > lo_p else float(np.min(v))
            hi = float(np.percentile(v, hi_p)) if hi_p > lo_p else float(np.max(v))
            if hi <= lo:
                lo, hi = float(np.min(v)), float(np.max(v))
            if hi > lo:
                v = (v - lo) / (hi - lo)
            else:
                v = np.zeros_like(v)

            # Optional smoothing (simple moving average)
            if cons_smooth and cons_smooth > 1 and cons_smooth % 2 == 1:
                k = cons_smooth
                pad = k // 2
                v_pad = np.pad(v, (pad, pad), mode="edge")
                kernel = np.ones(k, dtype=float) / k
                v = np.convolve(v_pad, kernel, mode="valid")

            # Gamma shaping for midtone richness
            v = np.clip(v, 0.0, 1.0) ** cons_gamma

            # grayscale color (dark=high)
            def _gray(val: float) -> tuple[float, float, float]:
                # g in [min_g, 1], where lower = darker
                g = max(cons_min_brightness, 1.0 - float(val))
                return (g, g, g)

            # Paint before letters/outlines, above the blue band
            for x, score in zip(xs, v):
                ax.add_patch(
                    Rectangle(
                        (x - 0.5, -0.35),
                        1.0,
                        0.7,
                        facecolor=_gray(score),
                        edgecolor="none",
                        linewidth=0.0,
                        zorder=0.6,
                    )
                )

            # Optional mini scale bar that "says the values" without overlapping
            if cons_show_scale:
                # inset in axes-fraction coords: x, y, w, h
                ax2 = ax.inset_axes([0.012, 0.80, 0.20, 0.12], zorder=5)
                ax2.set_facecolor("white")  # white background (no alpha, avoids tuple error)
                ax2.set_alpha(0.85)  # optional: slight transparency
                for spine in ("top", "right", "left", "bottom"):
                    ax2.spines[spine].set_visible(True)

                # draw a horizontal grayscale bar leaving room for labels below
                grad = np.linspace(0, 1, 256).reshape(1, -1)
                ax2.imshow(grad, aspect="auto", cmap="gray_r", extent=[0, 1, 0.45, 0.95], clip_on=False)

                # no ticks—avoid layout bleed into the main axes
                ax2.set_xticks([]); ax2.set_yticks([])
                ax2.set_xlim(0, 1); ax2.set_ylim(0, 1)

                # label the clipped endpoints and midpoint inside the inset
                ticks_vals = [lo, (lo + hi) / 2.0, hi]
                ax2.text(0.0, 0.20, f"{ticks_vals[0]:.2f}", ha="left",  va="center", fontsize=7, clip_on=False)
                ax2.text(0.5, 0.20, f"{ticks_vals[1]:.2f}", ha="center", va="center", fontsize=7, clip_on=False)
                ax2.text(1.0, 0.20, f"{ticks_vals[2]:.2f}", ha="right", va="center", fontsize=7, clip_on=False)

                # compact title inside the inset
                ax2.text(0.01, 0.98, "bg=JSD", ha="left", va="top", fontsize=7, clip_on=False)

    # ---------- END GRADIENT BACKGROUND ----------

    # letters
    text_effect = [pe.withStroke(linewidth=1.0, foreground="black", alpha=0.6)]
    for x, aa in zip(xs, subseq):
        ax.text(
            x,
            0.0,
            aa,
            ha="center",
            va="center",
            fontsize=12,
            family="DejaVu Sans Mono",
            color="white",
            path_effects=text_effect,
            zorder=3,
        )

    # light cell outlines
    for x in xs:
        ax.add_patch(
            Rectangle(
                (x - 0.5, -0.35),
                1.0,
                0.7,
                facecolor="none",
                edgecolor="#cccccc",
                linewidth=0.6,
                zorder=1,
            )
        )

    # conserved markers (hollow red)
    cons_mask = [p in conserved for p in xs]
    if any(cons_mask):
        xs_cons = xs[cons_mask]
        y_cons = np.full_like(xs_cons, 0.18, dtype=float)
        ms: Any = "o"
        ax.scatter(
            xs_cons,
            y_cons,
            s=36,
            marker=ms,
            facecolors="none",
            edgecolors="#d62728",
            linewidths=1.5,
            zorder=4,
        )

    # cosmetics
    ax.set_xlim(start - 0.5, end + 0.5)
    ax.set_ylim(-0.6, 0.6)
    ax.set_xticks([]); ax.set_yticks([])
    for spine in ("top", "right", "left", "bottom"):
        ax.spines[spine].set_visible(False)
    ax.set_title(f"{hit.family}  {start}-{end}", fontsize=13, pad=6)

    fig.savefig(str(out_png), dpi=200)
    plt.close(fig)


def plot_msa_with_gradient(
    msa: np.ndarray,
    names: list[str],
    out_png: Path,
    *,
    title: str,
    metric_values: np.ndarray,        # length L, in [0,1], higher = more conserved
    clip: tuple[float, float] = (5, 95),
    gamma: float = 0.8,
    min_brightness: float = 0.25,     # floor for background brightness
    gap_glyph: str = "dash",          # <-- new
    gap_cell_brightness: float = 0.9, # <-- new
) -> None:
    """Draw an MSA with a columnwise grayscale gradient + letters on top."""
    N, L = msa.shape
    v = metric_values.astype(float).copy()
    v[~np.isfinite(v)] = 0.0

    lo_p, hi_p = clip
    lo = float(np.percentile(v, lo_p)) if hi_p > lo_p else float(np.min(v))
    hi = float(np.percentile(v, hi_p)) if hi_p > lo_p else float(np.max(v))
    if hi > lo:
        v = (v - lo) / (hi - lo)
    else:
        v[:] = 0.0
    v = np.clip(v, 0.0, 1.0) ** gamma       # shape midtones

    # Handle NaN values (low coverage columns) by setting them to white
    v = np.nan_to_num(v, nan=0.0)

    # Build a background image: same column shade for all rows.
    # Enforce a minimum brightness so letters never vanish
    bg_full = np.tile(1.0 - v[None, :], (N, 1))         # old approach
    gap_mask = (msa == "-")
    bg_full = np.where(gap_mask, gap_cell_brightness, bg_full)  # configurable brightness for gaps
    bg = min_brightness + (1.0 - min_brightness) * bg_full  # dark = conserved

    # Figure sizing tuned for readability
    fig_w = max(10.0, 0.12 * L)
    fig_h = max(2.0, 0.35 * N + 0.8)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.imshow(bg, aspect="auto", cmap="gray", interpolation="nearest",
              extent=[0, L, 0, N])  # data coords: x in [0,L], y in [0,N]

    # Letters (overlay)
    ax.set_xlim(0, L); ax.set_ylim(0, N)
    ax.invert_yaxis()  # row 0 at top
    ax.axis("off")

    # Left margin for names
    name_ax = ax.inset_axes([-0.22, 0, 0.22, 1], transform=ax.transAxes)
    name_ax.set_xlim(0, 1); name_ax.set_ylim(0, N); name_ax.invert_yaxis()
    name_ax.axis("off")
    for i, nm in enumerate(names):
        name_ax.text(1.0, i + 0.5, nm, ha="right", va="center", fontsize=10)

    # Characters
    text_effect = [pe.withStroke(linewidth=0.9, foreground="black", alpha=0.6)]
    for i in range(N):
        row = msa[i]
        for j in range(L):
            ch = row[j]
            if ch == "-":
                # draw a configurable glyph for gaps if not "none"
                if gap_glyph == "dash":
                    gap_char = "–"  # en dash looks nicer than "-"
                elif gap_glyph == "dot":
                    gap_char = "·"  # middle dot
                else:  # gap_glyph == "none"
                    continue

                ax.text(j + 0.5, i + 0.5, gap_char,
                        ha="center", va="center",
                        fontsize=9, color="#C0C0C0",
                        family="DejaVu Sans Mono")
                continue
            ax.text(j + 0.5, i + 0.5, ch,
                    ha="center", va="center",
                    fontsize=10, color="white",
                    family="DejaVu Sans Mono",
                    path_effects=text_effect)

    ax.set_title(title, pad=10, fontsize=14)
    fig.tight_layout()
    fig.savefig(str(out_png), dpi=200)
    plt.close(fig)


def plot_similarity_matrix(msa: np.ndarray, names: list[str], out_png: Path) -> np.ndarray:
    """
    Compute and plot pairwise % identity for sequences in MSA.

    Args:
        msa: MSA array (already RF/coverage-trimmed and matches the panel)
        names: Row labels matching the MSA
        out_png: Output PNG path

    Returns:
        N×N similarity matrix (% identity)
    """
    N, L = msa.shape
    M = np.zeros((N, N), dtype=float)

    # Pairwise % identity ignoring gaps
    for a in range(N):
        for b in range(N):
            both = (msa[a] != "-") & (msa[b] != "-")
            denom = np.count_nonzero(both)
            num = np.count_nonzero((msa[a] == msa[b]) & both)
            M[a, b] = 100.0 * num / denom if denom > 0 else np.nan

    # Plot
    fig, ax = plt.subplots(figsize=(max(4, 0.35 * N), max(3.5, 0.35 * N)))
    im = ax.imshow(M, aspect="equal")
    ax.set_xticks(range(N))
    ax.set_yticks(range(N))
    ax.set_xticklabels(names, rotation=90, fontsize=8)
    ax.set_yticklabels(names, fontsize=8)
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("% identity")
    fig.tight_layout()
    fig.savefig(str(out_png), dpi=200)
    plt.close(fig)

    return M
