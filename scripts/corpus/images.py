"""Figures for the corpus.

Every figure here is deliberately the **only** source of at least one fact: the
surrounding prose never repeats the numbers. That is what makes the
image-description and OCR paths (requirements.md §6.1) testable rather than
incidentally redundant.
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # no display, and deterministic output

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

INK = "#1b1b1b"
ACCENT = "#b5651d"


def _save(fig: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def battery_retention_chart(path: Path) -> Path:
    """Doc 2, uncaptioned. Only source of the cold-weather retention figures —
    the prose says only that temperature matters, never by how much."""
    months = list(range(0, 25, 3))
    warm = [100, 96, 92, 88, 84, 79, 74, 68, 62]
    mild = [100, 94, 88, 81, 74, 66, 58, 49, 40]
    cold = [100, 88, 76, 63, 51, 40, 30, 21, 14]

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(months, warm, marker="o", color=ACCENT, label="+20 °C")
    ax.plot(months, mild, marker="s", color=INK, label="+5 °C")
    ax.plot(months, cold, marker="^", color="#4a6fa5", label="−10 °C")

    ax.set_xlabel("Betriebsdauer (Monate)")
    ax.set_ylabel("Restkapazität (%)")
    ax.set_xticks(months)
    ax.set_yticks(range(0, 101, 20))
    ax.grid(True, linestyle=":", alpha=0.5)
    ax.legend(title="Umgebungstemperatur")

    # The value the golden set asks for: 40 % at −10 °C after 15 months.
    ax.annotate(
        "40 % nach 15 Monaten",
        xy=(15, 40),
        xytext=(16.5, 62),
        arrowprops={"arrowstyle": "->", "color": INK},
        fontsize=9,
    )
    return _save(fig, path)


def wiring_diagram(path: Path) -> Path:
    """Doc 1, captioned. The C-wire requirement appears only in this drawing."""
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    # Boxes are narrow and the wires run between them, so annotations sit in the
    # clear gap rather than colliding with the box edges.
    ax.add_patch(Rectangle((0.4, 1.5), 1.8, 3, fill=False, linewidth=1.6, edgecolor=INK))
    ax.text(1.3, 4.7, "Boiler terminal block", ha="center", fontsize=10, color=INK)

    ax.add_patch(Rectangle((7.8, 1.5), 1.8, 3, fill=False, linewidth=1.6, edgecolor=ACCENT))
    ax.text(8.7, 4.7, "Aurora Thermostat T3", ha="center", fontsize=10, color=ACCENT)

    terminals = [
        ("R", 4.0, "24 V AC power"),
        ("C", 3.3, "common — REQUIRED"),
        ("W", 2.6, "heat call"),
        ("Y", 1.9, "cooling call"),
    ]
    for label, y, note in terminals:
        ax.text(0.9, y, label, fontsize=11, color=INK, va="center")
        ax.text(8.3, y, label, fontsize=11, color=ACCENT, va="center")
        ax.add_patch(
            FancyArrowPatch((2.3, y), (7.7, y), arrowstyle="-", color=INK, linewidth=1.1)
        )
        ax.text(5.0, y + 0.18, note, ha="center", fontsize=8.5, color="#333333")

    ax.text(
        5.0,
        0.9,
        "The T3 draws continuous power: the C terminal must be connected.",
        ha="center",
        fontsize=9,
        color=INK,
    )
    return _save(fig, path)


def support_volume_chart(path: Path) -> Path:
    """Doc 5 (HTML), uncaptioned. Only source of the busiest-day figure."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    contacts = [420, 380, 355, 340, 505, 190, 120]

    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    bars = ax.bar(days, contacts, color=[ACCENT if v == max(contacts) else "#9aa5b1" for v in contacts])
    ax.set_ylabel("Support contacts")
    ax.set_title("Average weekly contact volume")
    ax.bar_label(bars, fontsize=8)
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, path)


def energy_savings_chart(path: Path) -> Path:
    """Captioned, used by the German energy-report explainer."""
    months = ["Okt", "Nov", "Dez", "Jan", "Feb", "Mär"]
    before = [310, 480, 610, 640, 560, 420]
    after = [268, 402, 503, 528, 470, 350]

    fig, ax = plt.subplots(figsize=(6.2, 3.3))
    width = 0.38
    positions = range(len(months))
    ax.bar([p - width / 2 for p in positions], before, width, label="Vorjahr", color="#9aa5b1")
    ax.bar([p + width / 2 for p in positions], after, width, label="mit Zeitplan", color=ACCENT)
    ax.set_xticks(list(positions))
    ax.set_xticklabels(months)
    ax.set_ylabel("Verbrauch (kWh)")
    ax.legend()
    ax.spines[["top", "right"]].set_visible(False)
    return _save(fig, path)


def automation_flow_diagram(path: Path) -> Path:
    """Captioned, used by the English automations guide."""
    fig, ax = plt.subplots(figsize=(6.6, 2.4))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")

    steps = [("Trigger", 0.6), ("Condition", 3.6), ("Action", 6.6), ("Notification", 9.6)]
    for label, x in steps:
        ax.add_patch(Rectangle((x, 1.0), 2.2, 1.0, fill=False, linewidth=1.4, edgecolor=INK))
        ax.text(x + 1.1, 1.5, label, ha="center", va="center", fontsize=10, color=INK)
    for x in (2.8, 5.8, 8.8):
        ax.add_patch(FancyArrowPatch((x, 1.5), (x + 0.8, 1.5), arrowstyle="->", color=ACCENT, linewidth=1.4))
    ax.text(6.0, 0.5, "Conditions are evaluated once, when the trigger fires.", ha="center", fontsize=9, color="#555555")
    return _save(fig, path)


def webhook_delivery_diagram(path: Path) -> Path:
    """Captioned, used by the webhooks guide."""
    fig, ax = plt.subplots(figsize=(6.6, 2.6))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")

    steps = [("Device", 0.5), ("Hub", 4.3), ("Your endpoint", 8.1)]
    for label, x in steps:
        ax.add_patch(Rectangle((x, 1.3), 2.6, 1.0, fill=False, linewidth=1.4, edgecolor=INK))
        ax.text(x + 1.3, 1.8, label, ha="center", va="center", fontsize=10, color=INK)

    # Arrows stop short of the box edge so the head is visible.
    for start, label in ((3.2, "state change"), (7.0, "HTTPS POST, signed")):
        ax.add_patch(
            FancyArrowPatch(
                (start, 1.8),
                (start + 1.0, 1.8),
                arrowstyle="-|>",
                mutation_scale=14,
                color=ACCENT,
                linewidth=1.4,
            )
        )
        ax.text(start + 0.5, 2.45, label, ha="center", fontsize=8.5, color="#555555")

    # Retry path: endpoint back to hub, bowed below the boxes.
    ax.add_patch(
        FancyArrowPatch(
            (9.4, 1.25),
            (5.6, 1.25),
            arrowstyle="-|>",
            mutation_scale=14,
            color="#4a6fa5",
            linewidth=1.2,
            connectionstyle="arc3,rad=-0.45",
        )
    )
    ax.text(
        7.5, 0.42, "non-2xx or timeout → 4 retries, then dropped",
        ha="center", fontsize=8.5, color="#4a6fa5",
    )
    return _save(fig, path)


def build_all(images_dir: Path) -> dict[str, Path]:
    """Figures are build inputs: PDFs and DOCX embed them, HTML gets a copy."""
    return {
        "battery": battery_retention_chart(images_dir / "battery-retention.png"),
        "wiring": wiring_diagram(images_dir / "t3-wiring.png"),
        "support_volume": support_volume_chart(images_dir / "support-volume.png"),
        "energy": energy_savings_chart(images_dir / "energie-vergleich.png"),
        "automation": automation_flow_diagram(images_dir / "automation-flow.png"),
        "webhook": webhook_delivery_diagram(images_dir / "webhook-delivery.png"),
    }
