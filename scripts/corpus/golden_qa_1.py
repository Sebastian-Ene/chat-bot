"""Second golden set — question shapes the first one does not test.

`golden_qa_0` asks *where does this fact live*: table-only, image-only,
near-miss, cross-lingual. Every answer is a value that appears verbatim in one
document, so retrieving the right chunk is most of the work.

These ten ask something else — what must the model do *after* retrieving:

- **enumeration** — the answer is a set, and a partial answer is wrong. Tests
  whether every qualifying row is read out of a table, not just the first match.
- **derivation** — the answer appears nowhere in the corpus and has to be
  computed from values that do. Tests arithmetic over retrieved facts, and
  catches a model that pattern-matches a nearby number instead.
- **exclusion** — the documented fact is a negative. Tests whether a stated
  limitation survives, or gets answered as though it were the positive case.

Same documents as `golden_qa_0`, all in `corpus/docs-initial/`, so the two sets
are directly comparable — any score difference is the question shape, not the
corpus. Every expected answer is checked against the generator source that
produced the document (`accessory-catalogue-en.md`, `doc3_warranty.py`,
`doc4_garantie.py`); `scripts/check_corpus.py` guards the references.
"""
import json
from pathlib import Path

QA = [
    # ---- enumeration: the answer is a set; a partial answer is wrong ----
    {
        "id": "qb-001",
        "batch": "initial",
        "type": "enumeration",
        "language": "en",
        "question": "Which accessories in the Aurora Home range carry a 24-month warranty?",
        "expected_answer": (
            "Four: the AH-BP1 backplate adapter, the AH-RV1 radiator valve, the AH-RP1 mesh "
            "repeater and the AH-SM1 surface mounting box. The other three (AH-IM1, AH-PS2, "
            "AH-CB2) carry 12 months."
        ),
        "source": {"document": "accessory-catalogue-en.docx", "element": "Range table"},
    },
    {
        "id": "qb-002",
        "batch": "initial",
        "type": "enumeration",
        "language": "en",
        "question": "Which delivery destinations have no free-shipping threshold at all?",
        "expected_answer": "Switzerland and the United Kingdom — both are listed as not available.",
        "source": {
            "document": "aurora-warranty-returns-shipping-en.docx",
            "element": "Table 3",
            "also_in": "aurora-garantie-ruckgabe-versand-de.docx (Tabelle 3)",
        },
    },
    {
        "id": "qb-003",
        "batch": "initial",
        "type": "enumeration",
        "language": "de",
        "question": "Für welche Geräte ist eine verlängerte Garantie auf 36 Monate verfügbar?",
        "expected_answer": (
            "Für das Thermostat T3, den Sensor S1 und den Hub H2 — jeweils bei Registrierung "
            "innerhalb von 60 Tagen ab Kauf."
        ),
        "source": {
            "document": "aurora-garantie-ruckgabe-versand-de.docx",
            "element": "Tabelle 1",
            "also_in": "aurora-warranty-returns-shipping-en.docx (Table 1)",
        },
    },
    # ---- derivation: computed from documented values, stated nowhere ----
    {
        "id": "qb-004",
        "batch": "initial",
        "type": "derivation",
        "language": "en",
        "question": "What do a radiator valve and a mains-powered mesh repeater cost together, excluding VAT?",
        "expected_answer": "€98 — the AH-RV1 at €59 plus the AH-RP1 at €39.",
        "source": {"document": "accessory-catalogue-en.docx", "element": "Range table"},
    },
    {
        "id": "qb-005",
        "batch": "initial",
        "type": "derivation",
        "language": "en",
        "question": "A business customer returns an opened but complete order worth 400 euros. How much is deducted?",
        "expected_answer": "€60 — the business restocking fee for an opened, complete return is 15%.",
        "source": {"document": "aurora-warranty-returns-shipping-en.docx", "element": "Table 2"},
    },
    {
        "id": "qb-006",
        "batch": "initial",
        "type": "derivation",
        "language": "de",
        "question": "Wie viele Monate Garantie gewinnt man durch die Registrierung eines Thermostats T3?",
        "expected_answer": "Zwölf Monate — 24 Monate Standardgarantie gegenüber 36 Monaten nach Registrierung.",
        "source": {
            "document": "aurora-garantie-ruckgabe-versand-de.docx",
            "element": "Tabelle 1",
            "also_in": "aurora-warranty-returns-shipping-en.docx (Table 1)",
        },
    },
    {
        "id": "qb-007",
        "batch": "initial",
        "type": "derivation",
        "language": "en",
        "question": "Does an order of two radiator valves and one mesh repeater ship free to Germany?",
        "expected_answer": (
            "Yes — the order comes to €157 (two AH-RV1 at €59 plus an AH-RP1 at €39), which is "
            "above the €49 free-shipping threshold for Germany."
        ),
        "source": {
            "documents": [
                "accessory-catalogue-en.docx",
                "aurora-warranty-returns-shipping-en.docx",
            ],
            "element": "Range table prices + Table 3 threshold",
        },
    },
    # ---- exclusion: the documented fact is a negative ----
    {
        "id": "qb-008",
        "batch": "initial",
        "type": "exclusion",
        "language": "en",
        "question": "Can the warranty on an AH-IM1 interface module be extended by registering it?",
        "expected_answer": (
            "No — extended warranty is not available for the AH-IM1, and accessory warranties "
            "are not extended by registration at all."
        ),
        "source": {
            "document": "aurora-warranty-returns-shipping-en.docx",
            "element": "Table 1",
            "also_in": "accessory-catalogue-en.docx",
        },
    },
    {
        "id": "qb-009",
        "batch": "initial",
        "type": "exclusion",
        "language": "en",
        "question": "If a property is running out of device capacity, does adding a mesh repeater help?",
        "expected_answer": (
            "No — a repeater extends the mesh but adds no device capacity. A property short of "
            "capacity needs a second hub; a repeater only helps devices dropping out at range."
        ),
        "source": {
            "document": "accessory-catalogue-en.docx",
            "element": "Choosing between a repeater and a second hub",
        },
    },
    {
        "id": "qb-010",
        "batch": "initial",
        "type": "exclusion",
        "language": "en",
        "question": "Does fitting radiator valves throughout a property improve mesh coverage?",
        # Only what the question asks. An earlier version also required "and they
        # count against hub capacity", which the question never asks for — the
        # app answered correctly and was marked wrong for the omission.
        "expected_answer": "No — valves are battery-powered leaf nodes and do not relay traffic.",
        "source": {"document": "accessory-catalogue-en.docx", "element": "Radiator valves"},
    },
    # ---- precedence: a specific addendum overrides the general policy ----
    # The general policy and the regional addendum both match the question, and
    # both are retrievable. Answering from the general table is the failure.
    {
        "id": "qb-011",
        "batch": "initial",
        "type": "precedence",
        "language": "en",
        "question": "What is the free-shipping threshold for an order delivered to Luxembourg?",
        "expected_answer": (
            "€69, per the Benelux addendum. The general shipping table would put Luxembourg "
            "under 'rest of the European Union' at €79, but the addendum is specific to it."
        ),
        "source": {
            "document": "service-addendum-benelux-en.pdf",
            "element": "Shipping table",
            "also_in": "aurora-warranty-returns-shipping-en.docx (Table 3, general case)",
        },
    },
    {
        "id": "qb-012",
        "batch": "initial",
        "type": "precedence",
        "language": "de",
        "question": "Wie lange hat eine Privatkundin in der Schweiz Zeit, eine Bestellung zurückzugeben?",
        "expected_answer": (
            "14 Tage ab Erhalt der Ware — der Schweizer Serviceanhang weicht ausdrücklich von "
            "der allgemeinen Frist von 30 Tagen ab."
        ),
        "source": {
            "document": "service-addendum-ch-de.pdf",
            "element": "Rückgabe",
            "also_in": "aurora-garantie-ruckgabe-versand-de.docx (Tabelle 2, allgemeiner Fall)",
        },
    },
    {
        "id": "qb-013",
        "batch": "initial",
        "type": "precedence",
        "language": "en",
        "question": "How long does standard delivery to Luxembourg take?",
        "expected_answer": (
            "Four to five working days — one day longer than the Netherlands and Belgium, "
            "because of the onward leg from the Belgian hub."
        ),
        "source": {"document": "service-addendum-benelux-en.pdf", "element": "Shipping table"},
    },
    # ---- conditional: the answer branches, and naming one branch is wrong ----
    {
        "id": "qb-014",
        "batch": "initial",
        "type": "conditional",
        "language": "en",
        "question": "When does an order qualify for free shipping?",
        "expected_answer": (
            "It depends on the destination: over €49 to Germany, over €59 to Austria, the "
            "Netherlands and Belgium, over €69 to Luxembourg, and over €79 to the rest of the "
            "EU. Switzerland and the United Kingdom have no free shipping at all."
        ),
        "source": {
            "documents": [
                "aurora-warranty-returns-shipping-en.docx",
                "service-addendum-benelux-en.pdf",
            ],
            "element": "Table 3 + Benelux shipping table",
        },
    },
    {
        "id": "qb-015",
        "batch": "initial",
        "type": "conditional",
        "language": "en",
        "question": "As a consumer, how many days do I have to return an order?",
        "expected_answer": (
            "30 days under the general policy, but 14 days in Switzerland and 14 days from "
            "delivery in the United Kingdom — both regional addenda differ from the general rule."
        ),
        "source": {
            "documents": [
                "aurora-warranty-returns-shipping-en.docx",
                "service-addendum-ch-de.pdf",
                "service-addendum-uk-en.html",
            ],
            "element": "Table 2 + CH Rückgabe + UK Returns",
        },
    },
    {
        "id": "qb-016",
        "batch": "initial",
        "type": "conditional",
        "language": "de",
        "question": "Was kostet der Versand eines 12 kg schweren Zubehörpakets in die Schweiz?",
        "expected_answer": (
            "CHF 39.90 bei 7–9 Werktagen — ab 10 kg gilt der Sperrgut-Tarif, nicht der "
            "Standardtarif von CHF 14.90."
        ),
        "source": {"document": "service-addendum-ch-de.pdf", "element": "Versand und Zoll"},
    },
    # ---- procedural: the order of steps is the answer ----
    {
        "id": "qb-017",
        "batch": "initial",
        "type": "procedural",
        "language": "en",
        "question": "How do I pair a new device with the hub?",
        # The sequence and its timings only — "one device at a time" is a
        # constraint on pairing several, which this question does not ask about.
        "expected_answer": (
            "Put the hub into pairing mode from the app, then hold the device's pairing button "
            "for three seconds until its indicator pulses. Pairing completes within thirty "
            "seconds."
        ),
        "source": {"document": "aurora-installation-guide-en.pdf", "element": "4.1 Pairing devices"},
    },
    {
        "id": "qb-018",
        "batch": "initial",
        "type": "procedural",
        "language": "en",
        "question": "What has to happen before a paired device is taken off the wall?",
        "expected_answer": (
            "Remove it from the app first. A device removed physically but left paired keeps "
            "occupying a slot against the 64-device limit; the app offers a forced removal to "
            "clear the pairing from the hub's side."
        ),
        "source": {"document": "aurora-installation-guide-en.pdf", "element": "Removing devices"},
    },
    # ---- harder questions in the shapes both sets already cover ----
    {
        "id": "qb-019",
        "batch": "initial",
        "type": "derivation",
        "language": "en",
        "question": "What does a Gold-tier installer partner pay for ten radiator valves, excluding VAT and shipping?",
        "expected_answer": "€472 — ten AH-RV1 at €59 is €590, less the 20% Gold discount.",
        "source": {
            "documents": ["accessory-catalogue-en.docx", "installer-programme-en.html"],
            "element": "Range table price + tier discount table",
        },
    },
    {
        "id": "qb-020",
        "batch": "initial",
        "type": "derivation",
        "language": "en",
        # The question asks for the tier and the payment terms, so the discount
        # is now asked for rather than silently required.
        "question": "An installer partner fitted 180 devices last year. Which tier applies, and what discount and payment terms come with it?",
        "expected_answer": "Silver — 51 to 250 devices — which is a 15% discount on 14 days net.",
        "source": {"document": "installer-programme-en.html", "element": "Tier table"},
    },
    {
        "id": "qb-021",
        "batch": "initial",
        "type": "enumeration",
        "language": "de",
        "question": "Welche Einschränkungen waren für die Firmware 3.9 dokumentiert?",
        "expected_answer": (
            "Drei: die Gerätekapazität lag bei 32 Geräten je Hub, ein zweiter Hub je Objekt "
            "wurde nicht unterstützt, und Temperaturkorrekturwerte liessen sich nur über den "
            "Support hinterlegen."
        ),
        "source": {"document": "release-notes-3-9-de.html", "element": "Bekannte Einschränkungen"},
    },
    {
        "id": "qb-022",
        "batch": "initial",
        "type": "cross_lingual",
        "language": "en",
        "question": "What does standard shipping to Switzerland cost?",
        "expected_answer": "CHF 14.90, taking five to seven working days.",
        "source": {"document": "service-addendum-ch-de.pdf", "element": "Versand und Zoll"},
    },
    {
        "id": "qb-023",
        "batch": "initial",
        "type": "multi_hop",
        "language": "en",
        "question": "A Swiss consumer returns an order. How long do they have, and is the original shipping cost refunded?",
        "expected_answer": (
            "14 days from receipt, and no — the original shipping cost is not refunded, though "
            "the import duties paid at purchase are."
        ),
        "source": {"document": "service-addendum-ch-de.pdf", "element": "Rückgabe"},
    },
    {
        "id": "qb-024",
        "batch": "initial",
        "type": "exclusion",
        "language": "en",
        "question": "May an installer partner keep access to a client's property after handover?",
        "expected_answer": (
            "No — retaining access after handover is a breach of the programme terms. The "
            "client cannot remove the account themselves, and support will not remove it "
            "without the partner's confirmation."
        ),
        "source": {"document": "installer-programme-en.html", "element": "Ownership at handover"},
    },
    {
        "id": "qb-025",
        "batch": "initial",
        "type": "unanswerable",
        "language": "en",
        "question": "What is the express delivery surcharge for an order to Belgium?",
        "expected_answer": (
            "Not covered — the Benelux addendum gives express transit times but never a price "
            "for it, and no other document states one. Only Switzerland has priced shipping."
        ),
    },
]


def write(path: Path) -> Path:
    path.write_text(json.dumps(QA, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def summary() -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in QA:
        counts[entry["type"]] = counts.get(entry["type"], 0) + 1
    return counts
