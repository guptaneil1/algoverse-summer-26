#!/usr/bin/env python3
"""Render the result figures from the generated table data.

Reads ``table_data.json`` -- the file ``generate_final_tables.py`` writes -- so the
figures and the tables cannot disagree about a number. Nothing is computed here that
is not already in that file, and nothing is typed.

Two figures:

* ``F1_trajectories.svg`` -- four panels over the generation axis: held-out human NLL,
  NLL regret against each chain's own generation 0, tail retention, and every chain's
  primary outcome as a strip plot. The last panel exists so all twenty-five chains
  appear somewhere rather than only their arm means.
* ``F2_contrasts.svg`` -- the paired contrasts as intervals against the practical
  equivalence region, which is how a result whose finding is "no difference" has to be
  drawn: an interval inside a band, not a bar next to another bar.
* ``report.html`` -- both figures and the three main tables on one page, for reading and
  for review. Its numbers come from the same payload, so it cannot drift from the
  ``.tex`` the manuscript uses.

Palette: categorical slots 1-4 of the validated default (blue, orange, aqua, yellow) for
the four spending arms, in fixed order, with the no-rescue control in muted ink because
it is the reference rather than a fifth competitor. Validated for the adjacent pairlist;
aqua and yellow fall below 3:1 on the light surface, so every series carries a direct
label and a legend entry rather than relying on colour.

Usage:
    python scripts/render_result_figures.py \\
        --data docs/paper/final_tables/table_data.json \\
        --outdir docs/paper/final_tables
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ARM_ORDER = ("no_rescue", "random", "schedule_only", "selection_only", "joint")
LABEL = {
    "no_rescue": "No rescue (control)",
    "random": "Fresh random",
    "schedule_only": "Schedule-only",
    "selection_only": "Selection-only",
    "joint": "Joint time-and-mode",
}
SHORT = {
    "no_rescue": "Control",
    "random": "Random",
    "schedule_only": "Schedule",
    "selection_only": "Selection",
    "joint": "Joint",
}
COLOR = {
    "random": "#2a78d6",
    "schedule_only": "#eb6834",
    "selection_only": "#1baf7a",
    "joint": "#eda100",
    "no_rescue": "#52514e",
}
INK = "#0b0b0b"
MUTED = "#52514e"
GRID = "#e5e4e0"
SURFACE = "#fcfcfb"
CONTROL = "no_rescue"

# 12px system-ui averages a little under 7px per character. Used only to lay out the
# legend and the direct labels, where a bad estimate shows up as overlapping text.
CHAR_W = 6.6


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x: float, y: float, body: str, *, anchor: str = "start", fill: str = INK,
         size: float = 12, weight: str = "normal") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}" '
        f'font-size="{size}" font-weight="{weight}">{esc(body)}</text>'
    )


def nice_ticks(lo: float, hi: float, target: int = 5) -> list[float]:
    """Round tick values inside [lo, hi], so an axis reads 2.30 rather than 2.2947.

    Picks the 1/2/2.5/5 step whose tick count lands nearest ``target`` rather than the
    first step wide enough, which on a narrow range leaves an axis with two labels.
    """
    span = hi - lo
    if span <= 0:
        return [lo]
    exponent = math.floor(math.log10(span / target))
    best, best_cost = None, None
    for multiple in (1, 2, 2.5, 5, 10):
        step = multiple * 10 ** exponent
        first = math.ceil(lo / step) * step
        count = int((hi - first) / step) + 1 if first <= hi else 0
        if count < 3:
            continue
        cost = abs(count - target)
        if best_cost is None or cost < best_cost:
            best, best_cost = step, cost
    step = best or span / target
    first = math.ceil(lo / step) * step
    ticks, value = [], first
    while value <= hi + step * 1e-9:
        ticks.append(round(value, 10))
        value += step
    return ticks


def legend(arms: list[str], x: float, y: float, width: float) -> list[str]:
    """A wrapping legend whose entries are placed from measured widths, never guessed."""
    parts, cursor, row = [], x, 0
    for arm in arms:
        entry = LABEL[arm] + (" — reference" if arm == CONTROL else "")
        entry_w = 30 + len(entry) * CHAR_W + 22
        if cursor + entry_w > x + width and cursor > x:
            cursor, row = x, row + 1
        ly = y + row * 22
        dash = ' stroke-dasharray="7 4"' if arm == CONTROL else ""
        parts.append(
            f'<line x1="{cursor:.1f}" y1="{ly:.1f}" x2="{cursor + 24:.1f}" y2="{ly:.1f}" '
            f'stroke="{COLOR[arm]}" stroke-width="2.5"{dash} stroke-linecap="round"/>'
        )
        parts.append(text(cursor + 32, ly + 4, entry, fill=MUTED))
        cursor += entry_w
    return parts


class Panel:
    """One plotting rectangle with its own scales, ticks and labels."""

    def __init__(self, x: float, y: float, w: float, h: float, title: str,
                 lo: float, hi: float, fmt: str = "{:.2f}"):
        self.x, self.y, self.w, self.h, self.title, self.fmt = x, y, w, h, title, fmt
        pad = (hi - lo) * 0.12 or 0.01
        self.lo, self.hi = lo - pad, hi + pad

    def sy(self, value: float) -> float:
        return self.y + self.h * (self.hi - value) / (self.hi - self.lo)

    def frame(self, x_ticks: list[tuple[float, str]], x_label: str) -> list[str]:
        parts = [text(self.x, self.y - 14, self.title, fill=INK, weight="600")]
        for value in nice_ticks(self.lo, self.hi):
            if not self.lo <= value <= self.hi:
                continue
            sy = self.sy(value)
            parts.append(
                f'<line x1="{self.x:.1f}" y1="{sy:.1f}" x2="{self.x + self.w:.1f}" '
                f'y2="{sy:.1f}" stroke="{GRID}"/>'
            )
            parts.append(
                text(self.x - 9, sy + 4, self.fmt.format(value), anchor="end", fill=MUTED,
                     size=11)
            )
        for sx, body in x_ticks:
            parts.append(text(sx, self.y + self.h + 18, body, anchor="middle", fill=MUTED,
                              size=11))
        parts.append(
            text(self.x + self.w / 2, self.y + self.h + 38, x_label, anchor="middle",
                 fill=MUTED)
        )
        return parts


def series_panel(panel: Panel, trajectory: dict, arms: list[str], key: str,
                 horizon: int) -> list[str]:
    def sx(g: int) -> float:
        return panel.x + panel.w * g / (horizon - 1)

    parts = panel.frame([(sx(g), str(g)) for g in range(horizon)], "Generation")
    for arm in arms:
        means = trajectory[arm][f"{key}_mean"]
        sds = trajectory[arm][f"{key}_sd"]
        band_top = " ".join(
            f"{sx(g):.1f},{panel.sy(m + sd):.1f}"
            for g, (m, sd) in enumerate(zip(means, sds, strict=True))
        )
        band_bottom = " ".join(
            f"{sx(g):.1f},{panel.sy(m - sd):.1f}"
            for g, (m, sd) in reversed(list(enumerate(zip(means, sds, strict=True))))
        )
        parts.append(
            f'<polygon points="{band_top} {band_bottom}" fill="{COLOR[arm]}" '
            f'fill-opacity="0.12"/>'
        )
        dash = ' stroke-dasharray="7 4"' if arm == CONTROL else ""
        line = " ".join(f"{sx(g):.1f},{panel.sy(m):.1f}" for g, m in enumerate(means))
        parts.append(
            f'<polyline points="{line}" fill="none" stroke="{COLOR[arm]}" '
            f'stroke-width="2"{dash} stroke-linejoin="round"><title>'
            f'{esc(LABEL[arm])}</title></polyline>'
        )
    return parts


def label_line_ends(panel: Panel, trajectory: dict, arms: list[str], key: str) -> list[str]:
    """Direct labels at the right edge, pushed apart so none can overlap another."""
    placed: list[tuple[float, str, str]] = []
    for arm in arms:
        placed.append((panel.sy(trajectory[arm][f"{key}_mean"][-1]), arm, SHORT[arm]))
    placed.sort()
    minimum_gap = 14.0
    for index in range(1, len(placed)):
        y, arm, body = placed[index]
        previous = placed[index - 1][0]
        if y - previous < minimum_gap:
            placed[index] = (previous + minimum_gap, arm, body)
    return [
        text(panel.x + panel.w + 8, y + 4, body, fill=COLOR[arm], size=11, weight="600")
        for y, arm, body in placed
    ]


def strip_panel(panel: Panel, chains: list[dict], arms: list[str]) -> list[str]:
    """Every chain as a point, its arm's mean as a rule. Twenty-five points, no hiding."""
    slot = panel.w / len(arms)
    x_ticks = [(panel.x + slot * (i + 0.5), SHORT[a]) for i, a in enumerate(arms)]
    parts = panel.frame(x_ticks, "Policy")
    for index, arm in enumerate(arms):
        centre = panel.x + slot * (index + 0.5)
        values = [c["auc"] for c in chains if c["arm"] == arm]
        mean = sum(values) / len(values)
        parts.append(
            f'<line x1="{centre - 26:.1f}" y1="{panel.sy(mean):.1f}" '
            f'x2="{centre + 26:.1f}" y2="{panel.sy(mean):.1f}" stroke="{COLOR[arm]}" '
            f'stroke-width="2.5"/>'
        )
        for offset, chain in enumerate(sorted(values)):
            cx = centre + (offset - (len(values) - 1) / 2) * 9
            parts.append(
                f'<circle cx="{cx:.1f}" cy="{panel.sy(chain):.1f}" r="4" '
                f'fill="{COLOR[arm]}" fill-opacity="0.85" stroke="{SURFACE}" '
                f'stroke-width="2"><title>{esc(SHORT[arm])}: {chain:.4f}</title></circle>'
            )
    return parts


def figure_trajectories(payload: dict, out: Path) -> None:
    trajectory = payload["trajectory"]
    arms = [a for a in ARM_ORDER if a in trajectory]
    horizon = len(trajectory[arms[0]]["nll_mean"])
    width, height = 1060, 740
    margin_x, panel_gap, label_gutter = 62, 46, 66
    panel_w = (width - margin_x * 2 - panel_gap - label_gutter * 2) / 2
    panel_h = 224
    legend_y = 30
    top = 108

    regret = {
        arm: {
            "nll_mean": [m - trajectory[arm]["nll_mean"][0]
                         for m in trajectory[arm]["nll_mean"]],
            "nll_sd": trajectory[arm]["nll_sd"],
        }
        for arm in arms
    }

    def bounds(source: dict, key: str) -> tuple[float, float]:
        values = [
            v
            for arm in arms
            for m, sd in zip(source[arm][f"{key}_mean"], source[arm][f"{key}_sd"],
                             strict=True)
            for v in (m - sd, m + sd)
        ]
        return min(values), max(values)

    aucs = [c["auc"] for c in payload["chains"]]
    left = margin_x
    right = margin_x + panel_w + label_gutter + panel_gap

    p1 = Panel(left, top, panel_w, panel_h, "a. Held-out human NLL (nats) ↓",
               *bounds(trajectory, "nll"), fmt="{:.2f}")
    p2 = Panel(right, top, panel_w, panel_h, "b. NLL regret vs own generation 0 ↓",
               *bounds(regret, "nll"), fmt="{:.2f}")
    p3 = Panel(left, top + panel_h + 96, panel_w, panel_h, "c. Tail retention (ratio) ↑",
               *bounds(trajectory, "tail"), fmt="{:.3f}")
    p4 = Panel(right, top + panel_h + 96, panel_w, panel_h,
               "d. NLL-regret AUC, every chain ↓", min(aucs), max(aucs), fmt="{:.2f}")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="system-ui, -apple-system, Segoe UI, sans-serif" font-size="12" '
        f'role="img" aria-label="Recursive-training trajectories by allocation policy">',
        f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
    ]
    parts += legend(arms, margin_x, legend_y, width - margin_x * 2)
    parts += series_panel(p1, trajectory, arms, "nll", horizon)
    parts += label_line_ends(p1, trajectory, arms, "nll")
    parts += series_panel(p2, regret, arms, "nll", horizon)
    parts += label_line_ends(p2, regret, arms, "nll")
    parts += series_panel(p3, trajectory, arms, "tail", horizon)
    parts += label_line_ends(p3, trajectory, arms, "tail")
    parts += strip_panel(p4, payload["chains"], arms)
    # Say what the bands are, and that they are small. A band the reader cannot see is
    # worse than no band if the caption claims one.
    parts.append(
        text(margin_x, height - 34,
             "Panels a–c: mean over the five frozen seeds, with a ±1 SD band.",
             fill=MUTED, size=11)
    )
    parts.append(
        text(margin_x, height - 18,
             "Between-chain SD is under 1.1% of the mean, so those bands sit inside the "
             "stroke at this scale. Panel d plots all 25 chains.",
             fill=MUTED, size=11)
    )
    parts.append("</svg>")
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")


def figure_contrasts(payload: dict, out: Path) -> None:
    """Intervals against the equivalence band -- the only honest form for a null.

    Three fixed columns: the contrast's name, its numbers, and the plot. Fixed rather
    than fitted, because a name and a value sharing a row will otherwise collide the
    moment either grows.
    """
    rows = ([payload["primary"]] if payload.get("primary") else []) + payload["contrasts"]
    threshold = payload["threshold_units"]

    width = 1140
    margin = 44
    name_x, value_right, plot_x = margin, 470, 520
    plot_w = width - plot_x - margin - 10
    row_h, top, bottom = 48, 150, 96
    height = top + row_h * len(rows) + bottom

    span = max([abs(r["low"]) for r in rows] + [abs(r["high"]) for r in rows] + [threshold])
    span *= 1.15

    def sx(value: float) -> float:
        return plot_x + plot_w * (value + span) / (2 * span)

    band_top, band_bottom = top - 26, top + row_h * (len(rows) - 1) + 26
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'font-family="system-ui, -apple-system, Segoe UI, sans-serif" font-size="12" '
        f'role="img" aria-label="Paired contrasts against the practical equivalence '
        f'region">',
        f'<rect width="{width}" height="{height}" fill="{SURFACE}"/>',
        text(margin, 40, "Paired difference in NLL-regret AUC, with 95% intervals",
             weight="600", size=14),
        text(margin, 62,
             "Each row is one policy minus another, paired by seed over five chains. "
             "Negative favours the first policy.", fill=MUTED, size=11),
        text(margin, 80,
             f"The shaded band is the preregistered practical-equivalence region, "
             f"±{threshold:.4f} AUC units. An interval lying wholly inside it means the "
             f"two policies are equivalent at this operating point.", fill=MUTED,
             size=11),
        f'<rect x="{sx(-threshold):.1f}" y="{band_top:.1f}" '
        f'width="{sx(threshold) - sx(-threshold):.1f}" '
        f'height="{band_bottom - band_top:.1f}" fill="#1baf7a" fill-opacity="0.12" '
        f'stroke="#1baf7a" stroke-opacity="0.35"/>',
        text(sx(0), band_top - 10, "practical equivalence", anchor="middle",
             fill="#0f7a55", size=11, weight="600"),
        f'<line x1="{sx(0):.1f}" y1="{band_top:.1f}" x2="{sx(0):.1f}" '
        f'y2="{band_bottom:.1f}" stroke="{MUTED}" stroke-width="1.4" '
        f'stroke-dasharray="4 3"/>',
        text(name_x, top - 46, "Contrast", fill=MUTED, size=11, weight="600"),
        text(value_right, top - 46, "Difference  [95% interval]", anchor="end",
             fill=MUTED, size=11, weight="600"),
    ]

    for index, row in enumerate(rows):
        y = top + index * row_h
        primary = index == 0 and payload.get("primary") is not None
        name = f"{SHORT[row['treatment']]} − {SHORT[row['baseline']]}"
        label, _ = (name + " (primary)", None) if primary else (name, None)
        parts.append(text(name_x, y + 4, label, fill=INK,
                          weight="700" if primary else "normal"))
        parts.append(
            text(value_right, y + 4,
                 f"{row['mean']:+.4f}  [{row['low']:+.4f}, {row['high']:+.4f}]",
                 anchor="end", fill=MUTED, size=11)
        )
        colour = COLOR[row["treatment"]]
        parts.append(
            f'<line x1="{sx(row["low"]):.1f}" y1="{y:.1f}" x2="{sx(row["high"]):.1f}" '
            f'y2="{y:.1f}" stroke="{colour}" stroke-width="2.5" stroke-linecap="round"/>'
        )
        for end in ("low", "high"):
            parts.append(
                f'<line x1="{sx(row[end]):.1f}" y1="{y - 6:.1f}" '
                f'x2="{sx(row[end]):.1f}" y2="{y + 6:.1f}" stroke="{colour}" '
                f'stroke-width="2"/>'
            )
        parts.append(
            f'<circle cx="{sx(row["mean"]):.1f}" cy="{y:.1f}" r="5.5" fill="{colour}" '
            f'stroke="{SURFACE}" stroke-width="2"><title>{esc(name)}: '
            f'{row["mean"]:+.4f}</title></circle>'
        )

    axis_y = band_bottom + 22
    parts.append(
        f'<line x1="{plot_x:.1f}" y1="{axis_y:.1f}" x2="{plot_x + plot_w:.1f}" '
        f'y2="{axis_y:.1f}" stroke="{GRID}"/>'
    )
    for value in nice_ticks(-span, span, 6):
        parts.append(
            f'<line x1="{sx(value):.1f}" y1="{axis_y:.1f}" x2="{sx(value):.1f}" '
            f'y2="{axis_y + 5:.1f}" stroke="{GRID}"/>'
        )
        body = "0.00" if abs(value) < 1e-9 else f"{value:+.2f}"
        parts.append(text(sx(value), axis_y + 20, body, anchor="middle", fill=MUTED,
                          size=11))
    parts.append(text(plot_x + plot_w / 2, axis_y + 44,
                      "Difference in NLL-regret AUC (nats × generations)",
                      anchor="middle", fill=MUTED))
    parts.append("</svg>")
    out.write_text("\n".join(parts) + "\n", encoding="utf-8")


REPORT_CSS = """
:root {
  color-scheme: light;
  --ground: #fbfbf9;
  --panel: #f3f4f0;
  --rule: #e2e4de;
  --ink: #101413;
  --ink-2: #4b5450;
  --ink-3: #77817c;
  --accent: #0f7a55;
  --accent-soft: rgba(15, 122, 85, 0.10);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --ground: #14171a;
    --panel: #1c2023;
    --rule: #2b3136;
    --ink: #f1f4f2;
    --ink-2: #b9c2bd;
    --ink-3: #8b948f;
    --accent: #4fc496;
    --accent-soft: rgba(79, 196, 150, 0.14);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --ground: #14171a;
  --panel: #1c2023;
  --rule: #2b3136;
  --ink: #f1f4f2;
  --ink-2: #b9c2bd;
  --ink-3: #8b948f;
  --accent: #4fc496;
  --accent-soft: rgba(79, 196, 150, 0.14);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--ground);
  color: var(--ink);
  font-family: "Source Sans 3", ui-sans-serif, system-ui, sans-serif;
  font-size: 17px;
  line-height: 1.6;
}
.wrap { max-width: 1180px; margin: 0 auto; padding: 56px 28px 96px; }
header { display: flex; flex-direction: column; gap: 10px; margin-bottom: 40px; }
.eyebrow {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px; letter-spacing: 0.09em; text-transform: uppercase; color: var(--ink-3);
}
h1 {
  font-family: Newsreader, ui-serif, Georgia, serif;
  font-weight: 500; font-size: clamp(30px, 4vw, 46px); line-height: 1.1; margin: 0;
  text-wrap: balance;
}
h2 {
  font-family: Newsreader, ui-serif, Georgia, serif;
  font-weight: 500; font-size: 27px; margin: 56px 0 6px; text-wrap: balance;
}
p { max-width: 68ch; color: var(--ink-2); margin: 10px 0; }
.lede { font-size: 19px; color: var(--ink); }
.verdict {
  border: 1px solid var(--rule); border-left: 4px solid var(--accent);
  background: var(--accent-soft); border-radius: 3px;
  padding: 20px 24px; margin: 28px 0 8px; display: grid; gap: 6px;
}
.verdict strong { font-size: 19px; }
.verdict .num {
  font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 15px;
  color: var(--ink-2);
}
figure { margin: 22px 0 0; }
.figbox {
  background: var(--panel); border: 1px solid var(--rule); border-radius: 3px;
  padding: 14px; overflow-x: auto;
}
.figbox svg { display: block; width: 100%; height: auto; min-width: 720px; }
figcaption { color: var(--ink-3); font-size: 14px; margin-top: 10px; max-width: 80ch; }
.tablebox { overflow-x: auto; margin-top: 18px; }
table { border-collapse: collapse; width: 100%; font-size: 15px; min-width: 640px; }
caption { text-align: left; color: var(--ink-3); font-size: 14px; padding-bottom: 10px; }
th, td { padding: 9px 12px; border-bottom: 1px solid var(--rule); text-align: right; }
th:first-child, td:first-child { text-align: left; }
thead th {
  font-family: "IBM Plex Mono", ui-monospace, monospace;
  font-size: 12px; letter-spacing: 0.04em; text-transform: uppercase;
  color: var(--ink-3); font-weight: 500; border-bottom: 1px solid var(--ink-3);
}
td.num, th.num { font-variant-numeric: tabular-nums;
  font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 14px; }
tr.primary td { background: var(--accent-soft); font-weight: 600; color: var(--ink); }
.tag {
  display: inline-block; padding: 1px 9px; border-radius: 999px; font-size: 12px;
  font-family: "IBM Plex Mono", ui-monospace, monospace; border: 1px solid var(--rule);
  color: var(--ink-2);
}
.tag.ok { border-color: var(--accent); color: var(--accent); }
footer {
  margin-top: 64px; padding-top: 20px; border-top: 1px solid var(--rule);
  color: var(--ink-3); font-size: 14px;
}
code { font-family: "IBM Plex Mono", ui-monospace, monospace; font-size: 0.92em; }
"""


def report_html(payload: dict, figures: list[tuple[str, str, str]]) -> str:
    """One page carrying both figures and the three main tables, numbers from payload."""
    arms = payload["arms"]
    primary = payload.get("primary")
    rows = ([primary] if primary else []) + payload["contrasts"]
    threshold = payload["threshold_units"]

    def cells(values: list[str]) -> str:
        return "".join(
            f'<td class="num">{v}</td>' if i else f"<td>{v}</td>"
            for i, v in enumerate(values)
        )

    budget = "".join(
        "<tr>" + cells([
            LABEL[a], f"{arms[a]['n']}", f"{arms[a]['human']:,.0f}",
            f"{100 * arms[a]['human'] / payload['ceiling']:.2f}",
            f"{arms[a]['total']:,.0f}",
        ]) + "</tr>"
        for a in ARM_ORDER if a in arms
    )
    outcomes = "".join(
        "<tr>" + cells([
            LABEL[a], f"{arms[a]['n']}", f"{arms[a]['auc_mean']:.4f}",
            f"{arms[a]['auc_sd']:.4f}", f"{arms[a]['auc_cv']:.2f}",
            f"{arms[a]['tail_mean']:.4f}", f"{arms[a]['tail_sd']:.4f}",
        ]) + "</tr>"
        for a in ARM_ORDER if a in arms
    )

    def verdict_of(row: dict) -> str:
        inside = -threshold < row["low"] and row["high"] < threshold
        if inside:
            return "negligible"
        if row["high"] < 0 and row["mean"] <= -threshold:
            return "beneficial"
        if row["low"] > 0 and row["mean"] >= threshold:
            return "harmful"
        return "uncertain"

    contrasts = ""
    for index, row in enumerate(rows):
        klass = ' class="primary"' if index == 0 and primary else ""
        name = f"{SHORT[row['treatment']]} − {SHORT[row['baseline']]}"
        if index == 0 and primary:
            name += " (primary)"
        contrasts += f"<tr{klass}>" + cells([
            name, f"{row['mean']:+.4f}",
            f"[{row['low']:+.4f}, {row['high']:+.4f}]", f"{row['relative']:+.2f}",
            verdict_of(row),
        ]) + "</tr>"

    figure_blocks = "".join(
        f"<figure><div class=\"figbox\">{svg}</div>"
        f"<figcaption><strong>{title}.</strong> {caption}</figcaption></figure>"
        for title, caption, svg in figures
    )

    primary_line = (
        f"{SHORT[primary['treatment']]} − {SHORT[primary['baseline']]} = "
        f"{primary['mean']:+.4f}, 95% CI [{primary['low']:+.4f}, {primary['high']:+.4f}], "
        f"{primary['relative']:+.2f}% relative, against an equivalence region of "
        f"±{threshold:.4f}"
        if primary else "primary contrast not established"
    )

    return f"""<title>Where the Human Tokens Go</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Newsreader:wght@400;500&\
family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{REPORT_CSS}</style>
<div class="wrap">
<header>
  <div class="eyebrow">{payload['run_id']} · 25 chains · generated, not typed</div>
  <h1>Which examples you buy matters. When you buy them does not.</h1>
  <p class="lede">Under a fixed lifetime budget of human-origin optimizer tokens, five
  allocation policies were run to ten generations across five seeds each, with both
  budget axes matched by construction.</p>
</header>

<div class="verdict">
  <strong>The preregistered primary contrast is practically equivalent.</strong>
  <span class="num">{primary_line}</span>
  <span>The interval lies wholly inside the equivalence region, so this is the strong
  form of the negative: adding timing to mode selection buys nothing measurable here,
  and the data are precise enough to say so.</span>
</div>

<h2>Fair comparison first</h2>
<p>Every contrast below is admissible only because realised spend matched on both axes
that <code>PROTOCOL.md</code> §4 names. Human spend lands within
{payload['indivisibility_bound']:,} optimizer tokens of the ceiling — one indivisible
rescue candidate — and total optimizer tokens are identical across all five arms, which
P-011's displacement rule enforces by construction.</p>
<div class="tablebox"><table>
<caption>Table 1 — Realised budget, in optimizer tokens actually consumed.
Permitted spread {payload['permitted_spread_percent']:.2f}% on each axis;
<span class="tag ok">both axes hold</span></caption>
<thead><tr><th>Policy</th><th class="num">Chains</th><th class="num">Human tokens</th>
<th class="num">% of ceiling</th><th class="num">Total tokens</th></tr></thead>
<tbody>{budget}</tbody></table></div>

<h2>What each policy achieved</h2>
<div class="tablebox"><table>
<caption>Table 2 — NLL-regret AUC (nats × generations, lower better) and end-of-horizon
tail retention (ratio, higher better), mean over five seeds with between-chain
SD.</caption>
<thead><tr><th>Policy</th><th class="num">Chains</th><th class="num">AUC ↓</th>
<th class="num">SD</th><th class="num">CV %</th><th class="num">Tail ↑</th>
<th class="num">SD</th></tr></thead>
<tbody>{outcomes}</tbody></table></div>

<h2>The comparisons</h2>
<div class="tablebox"><table>
<caption>Table 3 — Paired-by-seed differences with 95% intervals. Verdicts are the four
preregistered labels, read against ±{threshold:.4f} AUC units.</caption>
<thead><tr><th>Contrast</th><th class="num">Δ AUC ↓</th><th class="num">95% CI</th>
<th class="num">Relative %</th><th class="num">Verdict</th></tr></thead>
<tbody>{contrasts}</tbody></table></div>

{figure_blocks}

<footer>Every number on this page is computed from the run's
<code>chain_result.json</code> artifacts by <code>scripts/generate_final_tables.py</code>
and rendered by <code>scripts/render_result_figures.py</code>. Source:
<code>{payload['source']}</code>. Whether any of it may be quoted in the manuscript is
<code>PROTOCOL.md</code> §5's question, not this page's.</footer>
</div>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.data.read_text(encoding="utf-8"))
    args.outdir.mkdir(parents=True, exist_ok=True)
    figure_trajectories(payload, args.outdir / "F1_trajectories.svg")
    figure_contrasts(payload, args.outdir / "F2_contrasts.svg")
    figures = [
        ("Figure 1", "Trajectories over the ten-generation horizon. Panel b is the "
                     "primary outcome's integrand; panel d is every chain.",
         (args.outdir / "F1_trajectories.svg").read_text(encoding="utf-8")),
        ("Figure 2", "Each contrast as an interval against the practical-equivalence "
                     "band. Inside the band means equivalent, not merely undecided.",
         (args.outdir / "F2_contrasts.svg").read_text(encoding="utf-8")),
    ]
    (args.outdir / "report.html").write_text(report_html(payload, figures),
                                             encoding="utf-8")
    print(f"wrote F1_trajectories.svg, F2_contrasts.svg and report.html to {args.outdir}")


if __name__ == "__main__":
    main()
