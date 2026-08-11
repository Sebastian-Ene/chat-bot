"""Doc 3 — Warranty, Returns and Shipping (EN, DOCX).

Carries: ruled tables with **merged cells**, a captioned figure, and several
values that exist **only in a table** — the returns window, the restocking fee
and the shipping times are never restated in prose.

Doc 4 is the German counterpart of this document: together they provide the
cross-lingual overlap required by requirements.md §4.
"""
from pathlib import Path

from scripts.corpus import docx_kit

TITLE = "Aurora Home — Warranty, Returns and Shipping"
SUBTITLE = "Consumer and business customers · valid from 1 February 2026 · version 3"


def build(out_dir: Path) -> Path:
    document = docx_kit.new_document(TITLE, SUBTITLE)

    document.add_heading("1. Scope", level=1)
    document.add_paragraph(
        "This policy applies to Aurora Home hardware bought directly from Aurora Home or from "
        "an authorised reseller in the European Union, the United Kingdom and Switzerland. "
        "Hardware bought elsewhere is covered by the policy of the market it was sold in. "
        "Software and cloud services are covered by the separate terms of service."
    )
    document.add_paragraph(
        "Nothing in this policy limits your statutory rights. Where national law grants you a "
        "longer period or a stronger remedy than the terms below, national law prevails."
    )

    document.add_heading("2. Warranty", level=1)
    document.add_paragraph(
        "Every Aurora Home device carries a manufacturer's warranty against defects in "
        "materials and workmanship, running from the date on your proof of purchase. "
        "Registering a device extends its warranty at no cost, provided registration happens "
        "within the window shown below."
    )
    docx_kit.add_table(
        document,
        ["Device", "Standard warranty", "Extended warranty", "Registration window"],
        [
            ["Thermostat T3", "24 months", "36 months", "60 days from purchase"],
            ["Sensor S1", "24 months", "36 months", "60 days from purchase"],
            ["Hub H2", "24 months", "36 months", "60 days from purchase"],
            ["Interface module AH-IM1", "12 months", "not available", "—"],
            ["Power adapter, cables", "12 months", "not available", "—"],
        ],
    )
    docx_kit.add_caption(document, "Table 1: Warranty terms by device.")

    document.add_paragraph(
        "The warranty covers repair or replacement at Aurora Home's discretion. It does not "
        "cover accidental damage, damage caused by installation contrary to the installation "
        "guide, cosmetic wear, or consumable parts. Batteries are consumables."
    )

    document.add_heading("2.1 Making a warranty claim", level=2)
    document.add_paragraph(
        "Contact support with the device identifier and your proof of purchase. Where a claim "
        "is accepted, Aurora Home issues a prepaid return label. Replacement units ship under "
        "the same delivery terms as new orders, and the replacement inherits the remaining "
        "warranty of the original device rather than starting a new term."
    )

    document.add_heading("3. Returns", level=1)
    document.add_paragraph(
        "Returns are handled separately from warranty claims: a return is for hardware you no "
        "longer want, a warranty claim is for hardware that has failed. The windows and fees "
        "below apply to returns."
    )
    docx_kit.add_table(
        document,
        ["Customer type", "Return window", "Condition", "Restocking fee", "Refund method"],
        [
            ["Consumer", "30 days", "Unopened", "None", "Original payment method"],
            ["Consumer", "30 days", "Opened, complete", "None", "Original payment method"],
            ["Consumer", "30 days", "Opened, incomplete", "25%", "Original payment method"],
            ["Business", "14 days", "Unopened", "None", "Credit note"],
            ["Business", "14 days", "Opened, complete", "15%", "Credit note"],
            ["Business", "14 days", "Opened, incomplete", "30%", "Credit note"],
            ["Installer partner", "45 days", "Any", "None", "Account credit"],
        ],
    )
    docx_kit.add_caption(document, "Table 2: Return windows and restocking fees.")

    document.add_paragraph(
        "Return shipping is at your own cost unless the return follows an accepted warranty "
        "claim or a delivery error on our side. Refunds are issued within ten working days of "
        "the returned hardware arriving at our warehouse."
    )

    document.add_heading("4. Shipping", level=1)
    document.add_paragraph(
        "Orders placed before 14:00 CET on a working day are dispatched the same day. Orders "
        "placed later, or at a weekend, are dispatched the next working day."
    )
    docx_kit.add_table(
        document,
        ["Destination", "Standard delivery", "Express delivery", "Free over"],
        [
            ["Germany", "2–3 working days", "next working day", "€49"],
            ["Austria, Netherlands, Belgium", "3–4 working days", "2 working days", "€59"],
            ["Rest of the European Union", "4–6 working days", "3 working days", "€79"],
            ["Switzerland", "5–7 working days", "3 working days", "not available"],
            ["United Kingdom", "5–7 working days", "3 working days", "not available"],
        ],
    )
    docx_kit.add_caption(document, "Table 3: Delivery times and free-shipping thresholds.")

    document.add_paragraph(
        "Deliveries outside the European Union may attract customs duty and import VAT, which "
        "are payable by the recipient and are not included in the prices shown at checkout."
    )

    document.add_heading("5. Contact", level=1)
    document.add_paragraph(
        "Written enquiries about this policy should go to the support address in the app. "
        "Please quote your order number: without it we cannot locate a purchase, and a warranty "
        "claim cannot be opened on a device we cannot tie to a sale."
    )

    return docx_kit.save(document, out_dir / "aurora-warranty-returns-shipping-en.docx")
