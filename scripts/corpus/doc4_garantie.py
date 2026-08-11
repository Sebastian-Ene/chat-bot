"""Doc 4 — Garantie, Rückgabe und Versand (DE, DOCX).

The German counterpart of doc 3. Most of the substance is expressed in both
languages, which is what makes cross-lingual retrieval testable: a German
question must find the English document and vice versa (requirements.md §4).

Deliberately **not** a literal translation — one section (Reparatur vor Ort) is
German-only, so the overlap is partial rather than total, as it would be in a
real bilingual knowledge base.
"""
from pathlib import Path

from scripts.corpus import docx_kit

TITLE = "Aurora Home — Garantie, Rückgabe und Versand"
SUBTITLE = "Privat- und Geschäftskunden · gültig ab 1. Februar 2026 · Version 3"


def build(out_dir: Path) -> Path:
    document = docx_kit.new_document(TITLE, SUBTITLE)

    document.add_heading("1. Geltungsbereich", level=1)
    document.add_paragraph(
        "Diese Richtlinie gilt für Aurora-Home-Hardware, die direkt bei Aurora Home oder bei "
        "einem autorisierten Fachhändler in der Europäischen Union, im Vereinigten Königreich "
        "und in der Schweiz gekauft wurde. Für Hardware aus anderen Märkten gilt die dortige "
        "Richtlinie. Software und Cloud-Dienste unterliegen den gesonderten Nutzungsbedingungen."
    )
    document.add_paragraph(
        "Ihre gesetzlichen Rechte bleiben unberührt. Sieht das nationale Recht eine längere "
        "Frist oder einen weitergehenden Anspruch vor, gilt das nationale Recht."
    )

    document.add_heading("2. Garantie", level=1)
    document.add_paragraph(
        "Für jedes Aurora-Home-Gerät gilt eine Herstellergarantie auf Material- und "
        "Verarbeitungsfehler ab dem Datum des Kaufbelegs. Wer sein Gerät registriert, erhält "
        "die verlängerte Garantie kostenlos — sofern die Registrierung innerhalb der unten "
        "genannten Frist erfolgt."
    )
    docx_kit.add_table(
        document,
        ["Gerät", "Standardgarantie", "Verlängerte Garantie", "Registrierungsfrist"],
        [
            ["Thermostat T3", "24 Monate", "36 Monate", "60 Tage ab Kauf"],
            ["Sensor S1", "24 Monate", "36 Monate", "60 Tage ab Kauf"],
            ["Hub H2", "24 Monate", "36 Monate", "60 Tage ab Kauf"],
            ["Schnittstellenmodul AH-IM1", "12 Monate", "nicht verfügbar", "—"],
            ["Netzteil, Kabel", "12 Monate", "nicht verfügbar", "—"],
        ],
    )
    docx_kit.add_caption(document, "Tabelle 1: Garantiebedingungen nach Gerät.")

    document.add_paragraph(
        "Die Garantie umfasst nach Wahl von Aurora Home die Reparatur oder den Austausch. Nicht "
        "abgedeckt sind Unfallschäden, Schäden durch eine Installation entgegen dem "
        "Installationshandbuch, optischer Verschleiß sowie Verbrauchsteile. Batterien gelten "
        "als Verbrauchsteil."
    )

    document.add_heading("2.1 Garantiefall melden", level=2)
    document.add_paragraph(
        "Wenden Sie sich mit der Gerätekennung und dem Kaufbeleg an den Support. Wird der "
        "Garantiefall anerkannt, stellt Aurora Home ein vorfrankiertes Rücksendeetikett bereit. "
        "Für Austauschgeräte gelten dieselben Lieferbedingungen wie für Neubestellungen; die "
        "Restlaufzeit der ursprünglichen Garantie geht auf das Austauschgerät über, es beginnt "
        "keine neue Frist."
    )

    # German-only section: the overlap between doc 3 and doc 4 is deliberately partial.
    document.add_heading("2.2 Reparatur vor Ort", level=2)
    document.add_paragraph(
        "In Deutschland und Österreich bietet Aurora Home für gewerbliche Installationen ab "
        "zwanzig Geräten eine Vor-Ort-Reparatur an. Der Einsatz erfolgt innerhalb von fünf "
        "Werktagen nach Anerkennung des Garantiefalls und ist auf Objekte mit einem gültigen "
        "Wartungsvertrag beschränkt. Für Privatkundinnen und Privatkunden ist die "
        "Vor-Ort-Reparatur nicht verfügbar."
    )

    document.add_heading("3. Rückgabe", level=1)
    document.add_paragraph(
        "Rückgabe und Garantiefall sind zu unterscheiden: Eine Rückgabe betrifft Hardware, die "
        "Sie nicht behalten möchten, ein Garantiefall betrifft defekte Hardware. Für Rückgaben "
        "gelten die folgenden Fristen und Gebühren."
    )
    docx_kit.add_table(
        document,
        ["Kundengruppe", "Rückgabefrist", "Zustand", "Wiedereinlagerungsgebühr", "Erstattung"],
        [
            ["Privatkunden", "30 Tage", "ungeöffnet", "keine", "ursprüngliches Zahlungsmittel"],
            ["Privatkunden", "30 Tage", "geöffnet, vollständig", "keine", "ursprüngliches Zahlungsmittel"],
            ["Privatkunden", "30 Tage", "geöffnet, unvollständig", "25 %", "ursprüngliches Zahlungsmittel"],
            ["Geschäftskunden", "14 Tage", "ungeöffnet", "keine", "Gutschrift"],
            ["Geschäftskunden", "14 Tage", "geöffnet, vollständig", "15 %", "Gutschrift"],
            ["Geschäftskunden", "14 Tage", "geöffnet, unvollständig", "30 %", "Gutschrift"],
            ["Installationspartner", "45 Tage", "beliebig", "keine", "Kontoguthaben"],
        ],
    )
    docx_kit.add_caption(document, "Tabelle 2: Rückgabefristen und Wiedereinlagerungsgebühren.")

    document.add_paragraph(
        "Die Rücksendekosten tragen Sie selbst, sofern die Rücksendung nicht auf einen "
        "anerkannten Garantiefall oder einen Lieferfehler unsererseits zurückgeht. Die "
        "Erstattung erfolgt innerhalb von zehn Werktagen nach Eingang der Ware in unserem Lager."
    )

    document.add_heading("4. Versand", level=1)
    document.add_paragraph(
        "Bestellungen, die an einem Werktag vor 14:00 Uhr MEZ eingehen, werden am selben Tag "
        "versandt. Spätere Bestellungen sowie Bestellungen am Wochenende gehen am nächsten "
        "Werktag raus."
    )
    docx_kit.add_table(
        document,
        ["Zielgebiet", "Standardversand", "Expressversand", "Versandfrei ab"],
        [
            ["Deutschland", "2–3 Werktage", "nächster Werktag", "49 €"],
            ["Österreich, Niederlande, Belgien", "3–4 Werktage", "2 Werktage", "59 €"],
            ["Übrige Europäische Union", "4–6 Werktage", "3 Werktage", "79 €"],
            ["Schweiz", "5–7 Werktage", "3 Werktage", "nicht verfügbar"],
            ["Vereinigtes Königreich", "5–7 Werktage", "3 Werktage", "nicht verfügbar"],
        ],
    )
    docx_kit.add_caption(document, "Tabelle 3: Lieferzeiten und Versandkostengrenzen.")

    document.add_paragraph(
        "Bei Lieferungen außerhalb der Europäischen Union können Zoll und Einfuhrumsatzsteuer "
        "anfallen. Diese trägt die empfangende Person; sie sind in den angezeigten Preisen "
        "nicht enthalten."
    )

    document.add_heading("5. Kontakt", level=1)
    document.add_paragraph(
        "Schriftliche Anfragen zu dieser Richtlinie richten Sie bitte an die in der App "
        "hinterlegte Support-Adresse. Geben Sie dabei Ihre Bestellnummer an: Ohne sie lässt "
        "sich ein Kauf nicht zuordnen und ein Garantiefall nicht eröffnen."
    )

    return docx_kit.save(document, out_dir / "aurora-garantie-ruckgabe-versand-de.docx")
