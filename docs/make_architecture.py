
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# --- tokens -----------------------------------------------------------------
SURFACE = "#fcfcfb"
CARD = "#ffffff"
BORDER = "#e1e0d9"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"

SOURCES = "#52514e"  # neutral — sources are outside the warehouse
RAW = "#86b6ef"  # blue 250
STAGING = "#3987e5"  # blue 400
MARTS = "#184f95"  # blue 600
EXPLORER = "#1baf7a"  # aqua — terminal serving layer

plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans", "sans-serif"]

W, H = 1000, 896
fig = plt.figure(figsize=(W / 100, H / 100), dpi=200)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W)
ax.set_ylim(H, 0)  # invert: y grows downward
ax.axis("off")
fig.patch.set_facecolor(SURFACE)

M = 40
RIGHT = W - M


def tracked(s):
    """matplotlib Text has no letter-spacing; emulate tracking with thin spaces."""
    return " ".join(s.upper())


def card(x, y, w, h, accent, header, title, subtitle=None, bullets=None,
         rule_only=False):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h,
            boxstyle="round,pad=0,rounding_size=10",
            facecolor=CARD, edgecolor=BORDER, linewidth=1.2,
            mutation_aspect=1,
        )
    )
    pad = 18
    cy = y + pad + 2
    if header:
        ax.text(x + pad, cy, tracked(header), color=accent, fontsize=10,
                fontweight="bold", va="top", ha="left")
        cy += 17
        ax.add_patch(Rectangle((x + pad, cy), 34, 3.2, facecolor=accent,
                               edgecolor="none"))
        cy += 18
    elif rule_only:
        ax.add_patch(Rectangle((x + pad, cy + 1), 34, 3.2, facecolor=accent,
                               edgecolor="none"))
        cy += 20
    ax.text(x + pad, cy, title, color=INK, fontsize=15, fontweight="bold",
            va="top", ha="left")
    cy += 25
    if subtitle:
        ax.text(x + pad, cy, subtitle, color=INK_2, fontsize=12, va="top",
                ha="left")
        cy += 21
    for b in bullets or []:
        ax.text(x + pad, cy, b, color=INK_2, fontsize=12, va="top", ha="left")
        cy += 20


def arrow(x, y0, y1, label=None):
    ax.add_patch(
        FancyArrowPatch(
            (x, y0), (x, y1),
            arrowstyle="-|>", mutation_scale=15,
            color=MUTED, linewidth=1.8, shrinkA=0, shrinkB=0,
        )
    )
    if label:
        ax.text(x, (y0 + y1) / 2, label, color=INK_2, fontsize=11.5,
                va="center", ha="center",
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=3.5))


# --- row A: sources ---------------------------------------------------------
ax.text(M, 30, tracked("Heterogeneous sources"), color=MUTED, fontsize=10,
        fontweight="bold", va="top", ha="left")

gap = 22
sw = (RIGHT - M - 2 * gap) / 3
src_y, src_h = 52, 92
sources = [
    ("Clinical notes", "flat CSV", "Matillion / COPY"),
    ("Lab results", "streaming CSV", "Snowpipe auto-ingest"),
    ("Pathology report", "JSON", "COPY into VARIANT"),
]
centers = []
for i, (title, sub, _) in enumerate(sources):
    x = M + i * (sw + gap)
    card(x, src_y, sw, src_h, SOURCES, None, title, subtitle=sub,
         rule_only=True)
    centers.append(x + sw / 2)

# --- row B: RAW -------------------------------------------------------------
raw_y, raw_h = 226, 100
for cx, (_, _, edge) in zip(centers, sources):
    arrow(cx, src_y + src_h, raw_y, edge)
card(M, raw_y, RIGHT - M, raw_h, RAW, "raw schema",
     "Landing tables — as-ingested", subtitle="no typing, no cleaning · replayable")

# --- row C: STAGING ---------------------------------------------------------
stg_y, stg_h = 394, 116
arrow(W / 2, raw_y + raw_h, stg_y, "dbt + LLM")
card(M, stg_y, RIGHT - M, stg_h, STAGING, "staging schema  —  HRI platform analog",
     "Cleaned + typed",
     bullets=["LLM extractions  ·  data-quality gate"])

# --- row D: MARTS -----------------------------------------------------------
mrt_y, mrt_h = 584, 116
arrow(W / 2, stg_y + stg_h, mrt_y, "dbt marts")
card(M, mrt_y, RIGHT - M, mrt_h, MARTS, "marts schema  —  cohort data mart",
     "dim_patient (SCD Type 2)",
     bullets=["fct_diagnoses  ·  COHORT_DATA_MART"])

# --- row E: explorer --------------------------------------------------------
exp_y, exp_h = 762, 96
arrow(W / 2, mrt_y + mrt_h, exp_y)
card(M, exp_y, RIGHT - M, exp_h, EXPLORER, "serving layer",
     "Streamlit cohort explorer",
     subtitle="runs natively in Snowflake  ·  cBioPortal analog")

out = Path(__file__).resolve().parent / "architecture.png"
fig.savefig(out, dpi=200, facecolor=SURFACE)
print("wrote", out)
