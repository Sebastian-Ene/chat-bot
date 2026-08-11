"""Golden question/answer set, generated alongside the documents.

This is the ground truth for the eval harness: `source` names the document and
the element the answer lives in, which is what makes recall@k and MRR
computable without hand-labelling later.

Written here rather than derived from the documents on purpose — a set derived
from the same code that wrote the documents would only prove the code is
self-consistent.

`batch` makes incremental ingestion *testable* rather than merely demonstrated:
`later` questions must be declined as unanswerable before the second batch is
ingested, and answered afterwards.
"""
import json
from pathlib import Path

QA = [
    # ---- table-only: the answer exists in a table and nowhere in prose ----
    {
        "id": "qa-001",
        "type": "table_only",
        "language": "en",
        "question": "How long do business customers have to return an opened but complete Aurora Home order, and what fee applies?",
        "expected_answer": "14 days, with a 15% restocking fee.",
        "source": {"document": "aurora-warranty-returns-shipping-en.docx", "element": "Table 2"},
    },
    {
        "id": "qa-002",
        "type": "table_only",
        "language": "de",
        "question": "Wie lang ist die Standardgarantie für das Schnittstellenmodul AH-IM1?",
        "expected_answer": "12 Monate; eine verlängerte Garantie ist dafür nicht verfügbar.",
        "source": {"document": "aurora-garantie-ruckgabe-versand-de.docx", "element": "Tabelle 1"},
    },
    {
        "id": "qa-003",
        "type": "table_only",
        "language": "de",
        "question": "Welche Betriebstemperatur ist für den Sensor S1 angegeben?",
        "expected_answer": "−15 °C bis 50 °C.",
        "source": {
            "document": "aurora-technische-daten-de.pdf",
            "element": "unruled specification table, section 2.2",
        },
    },
    {
        "id": "qa-004",
        "type": "table_only",
        "language": "en",
        "question": "Does the T3 support electric underfloor heating?",
        "expected_answer": "No — it is listed as not supported because the load exceeds the T3 relay rating.",
        "source": {
            "document": "aurora-installation-guide-en.pdf",
            "element": "Table 1, compatibility matrix (spans a page break)",
        },
    },
    # ---- image-only: the answer is legible only inside a figure ----
    {
        "id": "qa-005",
        "type": "image_only",
        "language": "de",
        "question": "Wie viel Restkapazität hat die Batterie des S1 nach 15 Monaten bei −10 °C?",
        "expected_answer": "Etwa 40 %.",
        "source": {
            "document": "aurora-technische-daten-de.pdf",
            "element": "uncaptioned battery retention chart, section 3",
        },
        "notes": "Value appears only in the chart; the prose says temperature matters but gives no figures.",
    },
    {
        "id": "qa-006",
        "type": "image_only",
        "language": "en",
        "question": "Which terminal must be connected for the Aurora T3 to work, and why?",
        "expected_answer": "The C (common) terminal, because the T3 draws continuous power.",
        "source": {"document": "aurora-installation-guide-en.pdf", "element": "Figure 1, wiring diagram"},
        "notes": "The C-wire requirement is stated only inside the diagram.",
    },
    {
        "id": "qa-007",
        "type": "image_only",
        "language": "en",
        "question": "Which weekday does Aurora Home support receive the most contacts on?",
        "expected_answer": "Friday, with about 505 contacts.",
        "source": {"document": "aurora-support-faq.html", "element": "uncaptioned support volume chart"},
    },
    # ---- cross-lingual: question language differs from the document that answers best ----
    {
        "id": "qa-008",
        "type": "cross_lingual",
        "language": "de",
        "question": "What is the free-shipping threshold for orders delivered within Germany?",
        "expected_answer": "€49.",
        "source": {
            "document": "aurora-garantie-ruckgabe-versand-de.docx",
            "element": "Tabelle 3",
            "also_in": "aurora-warranty-returns-shipping-en.docx (Table 3)",
        },
        "notes": "English question, answer present in both the German and English policy.",
    },
    {
        "id": "qa-009",
        "type": "cross_lingual",
        "language": "de",
        "question": "Bietet Aurora Home eine Vor-Ort-Reparatur an, und für wen?",
        "expected_answer": (
            "Ja, in Deutschland und Österreich für gewerbliche Installationen ab zwanzig "
            "Geräten mit gültigem Wartungsvertrag; für Privatkunden nicht."
        ),
        "source": {"document": "aurora-garantie-ruckgabe-versand-de.docx", "element": "section 2.2"},
        "notes": "German-only section — the English policy has no counterpart, so the overlap is partial.",
    },
    # ---- multi-hop: needs two documents combined ----
    {
        "id": "qa-010",
        "type": "multi_hop",
        "language": "en",
        "question": "If I install two hubs in one property, how many devices can I connect in total?",
        "expected_answer": "128 — each hub supports 64 devices, and a second hub adds its own full capacity.",
        "source": {
            "documents": ["aurora-installation-guide-en.pdf", "aurora-support-faq.html"],
            "element": "section 7 capacity limit + FAQ 'What happens if I need more capacity?'",
        },
        "notes": "Neither document states 128; the total requires combining both.",
    },
    {
        "id": "qa-011",
        "type": "multi_hop",
        "language": "en",
        "question": "How long will a warranty replacement take to reach me in Austria?",
        "expected_answer": (
            "3–4 working days by standard delivery — replacements ship under the same delivery "
            "terms as new orders."
        ),
        "source": {
            "documents": ["aurora-support-faq.html", "aurora-warranty-returns-shipping-en.docx"],
            "element": "FAQ 'Where do replacement units ship from?' + Table 3",
        },
    },
    # ---- unanswerable: must be declined, not invented ----
    {
        "id": "qa-012",
        "type": "unanswerable",
        "language": "en",
        "question": "Does the Aurora T3 work with Matter over Thread?",
        "expected_answer": "Not covered by the documentation — the assistant should say so rather than guess.",
        "source": None,
    },
    {
        "id": "qa-013",
        "type": "unanswerable",
        "language": "de",
        "question": "Wie hoch ist der monatliche Preis für das Aurora-Home-Cloud-Abonnement?",
        "expected_answer": "In der Dokumentation nicht enthalten — es darf kein Preis erfunden werden.",
        "source": None,
    },
    {
        "id": "qa-014",
        "type": "unanswerable",
        "language": "en",
        "question": "What is the IP rating of the Aurora outdoor sensor?",
        "expected_answer": "Not covered — there is no outdoor sensor in the product range.",
        "source": None,
        "notes": "False premise: the assistant should not invent a product to answer about.",
    },
    # ---- near-miss: a distractor holds a plausible but wrong answer ----
    {
        "id": "qa-017",
        "type": "near_miss",
        "language": "de",
        "question": "Wie lang ist die Rückgabefrist für Privatkunden in der Schweiz?",
        "expected_answer": "14 Tage ab Erhalt — der Schweizer Serviceanhang weicht von den allgemeinen 30 Tagen ab.",
        "source": {"document": "service-addendum-ch-de.pdf", "element": "Rückgabe"},
        "notes": "The general policy says 30 days for consumers; retrieving that instead is the failure mode.",
    },
    {
        "id": "qa-018",
        "type": "near_miss",
        "language": "en",
        "question": "How many devices can a single hub support?",
        "expected_answer": "64 — the 32-device limit appears only in the notes for the withdrawn 3.9 release.",
        "source": {"document": "aurora-installation-guide-en.pdf", "element": "section 7"},
        "notes": "release-notes-3-9-de states 32 as a known limitation; that is the trap.",
    },
    {
        "id": "qa-019",
        "type": "near_miss",
        "language": "en",
        "question": "What warranty applies to the AH-IM1 interface module?",
        "expected_answer": "12 months, and it cannot be extended by registration.",
        "source": {
            "document": "aurora-warranty-returns-shipping-en.docx",
            "element": "Table 1",
            "also_in": "accessory-catalogue-en.docx",
        },
        "notes": "Two documents agree here — retrieval may return either, and both are correct.",
    },
    {
        "id": "qa-020",
        "type": "near_miss",
        "language": "en",
        "question": "Is free shipping available for orders to the United Kingdom?",
        "expected_answer": "No — the UK addendum states free shipping is not offered there.",
        "source": {"document": "service-addendum-uk-en.html", "element": "Shipping and duties"},
        "notes": "The general policy's free-shipping thresholds are the distractor.",
    },
    {
        "id": "qa-021",
        "type": "table_only",
        "language": "de",
        "question": "Was bedeutet der Fehlercode F250?",
        "expected_answer": "Kapazitätsgrenze erreicht — 64 Geräte je Hub überschritten; Abhilfe ist ein zweiter Hub.",
        "source": {"document": "fehlercode-referenz-de.pdf", "element": "Tabelle 2xx — Funk und Mesh"},
        "notes": "Deep inside a 25-page table: tests chunking and retrieval within a long document.",
    },
    # ---- plain single-hop prose, as a baseline ----
    {
        "id": "qa-015",
        "type": "prose",
        "language": "en",
        "question": "When is Aurora Home support available?",
        "expected_answer": "Monday to Friday, 08:00–18:00 CET, excluding Berlin public holidays.",
        "source": {"document": "aurora-support-faq.html", "element": "Getting help"},
    },
    {
        "id": "qa-016",
        "type": "prose",
        "language": "de",
        "question": "Was soll ich tun, wenn ein Gerät als nicht erreichbar angezeigt wird?",
        "expected_answer": (
            "Zuerst Gerät und Batterie prüfen, dann ein netzbetriebenes Gerät näher an den "
            "Sensor bringen — meist ist die Funkstrecke die Ursache, nicht das Gerät."
        ),
        "source": {"document": "aurora-technische-daten-de.pdf", "element": "section 4.1"},
    },
]


# Answerable only from the second batch. Before it is ingested these must be
# declined; afterwards they must be answered. That is the incremental-ingestion
# test, and it is why they are kept separate rather than mixed into QA above.
LATER_QA = [
    {
        "id": "qa-101",
        "type": "table_only",
        "language": "de",
        "question": "Wie lange werden die Messwerte von Aurora Home aufbewahrt?",
        "expected_answer": "24 Monate; nach Kontolöschung werden sie innerhalb von 30 Tagen entfernt.",
        "source": {"document": "datenschutzerklaerung-de.docx", "element": "Datenkategorien-Tabelle"},
    },
    {
        "id": "qa-102",
        "type": "table_only",
        "language": "en",
        "question": "Which firmware versions are affected by advisory AH-SA-2026-01, and what fixes it?",
        "expected_answer": "4.0.x, 4.1.x, 4.2.x and 3.9 or earlier are affected; firmware 4.3 fixes it.",
        "source": {"document": "security-advisory-2026-01-en.pdf", "element": "affected firmware table"},
    },
    {
        "id": "qa-103",
        "type": "table_only",
        "language": "de",
        "question": "Welche Reaktionszeit sichert die Wartungsvertragsstufe Premium zu?",
        "expected_answer": "4 Stunden an Werktagen zwischen 08:00 und 18:00 Uhr MEZ.",
        "source": {"document": "wartungsvertrag-de.pdf", "element": "Stufen-Tabelle"},
    },
    {
        "id": "qa-104",
        "type": "prose",
        "language": "en",
        "question": "How many times does the hub retry a failed webhook delivery, and over what period?",
        "expected_answer": "Four retries after the first attempt, spread over roughly 36 minutes.",
        "source": {"document": "api-webhooks-guide-en.pdf", "element": "Delivery and retries"},
    },
    {
        "id": "qa-105",
        "type": "near_miss",
        "language": "en",
        "question": "How many automations can one property have?",
        "expected_answer": "100 from release 4.3; the limit of 50 applies only before that release.",
        "source": {"document": "release-notes-4-3-en.html", "element": "Changed"},
        "notes": "automations-guide-en.pdf states 50 — correct for 4.2, stale after the second batch lands.",
    },
]


def write(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Everything defaults to the initial batch; `LATER_QA` entries carry their own.
    entries = [{"batch": "initial", **entry} for entry in QA] + [
        {"batch": "later", **entry} for entry in LATER_QA
    ]
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in QA + LATER_QA:
        counts[entry["type"]] = counts.get(entry["type"], 0) + 1
    return counts
