"""Doc 2 — Technische Daten und Fehlerbehebung (DE, PDF).

Carries: an **unruled** specification table (alignment is the only structural
cue), and a battery-retention chart with **no caption** whose figures appear
nowhere in the prose — so both the generated-caption path and OCR of in-image
numbers are exercised.
"""
from pathlib import Path

from reportlab.platypus import Paragraph, Spacer

from scripts.corpus import paths, pdf_kit

TITLE = "Aurora Home — Technische Daten und Fehlerbehebung"


def _p(text: str, style) -> Paragraph:
    return Paragraph(text, style)


def _story(s: dict, usable: float) -> list:
    story: list = [
        _p(TITLE, s["title"]),
        _p("Thermostat T3 · Sensor S1 · Hub H2 — Firmware 4.2.1 · Dokumentstand 4", s["subtitle"]),
        _p("1. Geltungsbereich", s["h1"]),
        _p(
            "Dieses Dokument fasst die technischen Daten der Aurora-Home-Geräte zusammen und "
            "beschreibt die Fehlerbilder, die der Support am häufigsten sieht. Es richtet sich "
            "an Installateure und an technisch versierte Endkundinnen und Endkunden. Angaben "
            "zur Montage finden Sie im Installationshandbuch, nicht hier.",
            s["body"],
        ),
        _p("2. Technische Daten", s["h1"]),
        _p(
            "Die folgenden Werte gelten für Firmware 4.2.1. Abweichungen zwischen "
            "Produktionschargen liegen innerhalb der angegebenen Toleranzen.",
            s["body"],
        ),
        _p("2.1 Thermostat T3", s["h2"]),
    ]

    specs_t3 = [
        ["Merkmal", "Wert", "Toleranz"],
        ["Abmessungen (B × H × T)", "86 × 86 × 24 mm", "± 0,5 mm"],
        ["Displaydiagonale", "2,4 Zoll", "—"],
        ["Betriebstemperatur", "0 °C bis 45 °C", "—"],
        ["Messgenauigkeit Temperatur", "± 0,3 K", "bei 20 °C"],
        ["Versorgungsspannung", "24 V AC", "± 10 %"],
        ["Leistungsaufnahme", "1,4 W", "typisch"],
        ["Schaltleistung Relais", "230 V AC / 3 A", "ohmsche Last"],
        ["Funkstandard", "868 MHz, proprietäres Mesh", "—"],
        ["Schutzart", "IP20", "—"],
    ]
    story.append(pdf_kit.unruled_table(specs_t3, [usable * w for w in (0.42, 0.34, 0.24)]))
    story.append(Spacer(1, 12))

    story += [
        _p("2.2 Sensor S1", s["h2"]),
        _p(
            "Der S1 ist ein Tür- und Fensterkontakt mit integrierter Temperaturmessung. Er "
            "arbeitet als Endknoten im Mesh und leitet keinen Datenverkehr für andere Geräte "
            "weiter.",
            s["body"],
        ),
    ]

    specs_s1 = [
        ["Merkmal", "Wert", "Toleranz"],
        ["Abmessungen (B × H × T)", "52 × 26 × 12 mm", "± 0,5 mm"],
        ["Batterietyp", "CR2450, 3 V Lithium", "—"],
        ["Betriebstemperatur", "−15 °C bis 50 °C", "—"],
        ["Meldeintervall Temperatur", "10 Minuten", "± 30 s"],
        ["Reaktionszeit Kontakt", "unter 1 Sekunde", "—"],
        ["Schutzart", "IP20", "—"],
    ]
    story.append(pdf_kit.unruled_table(specs_s1, [usable * w for w in (0.42, 0.34, 0.24)]))
    story.append(Spacer(1, 14))

    story += [
        _p("3. Batterielaufzeit", s["h1"]),
        _p(
            "Die Batterielaufzeit des S1 hängt vor allem von der Umgebungstemperatur ab. In "
            "beheizten Innenräumen erreichen die Geräte regelmäßig mehrere Jahre; in "
            "unbeheizten Nebenräumen, Garagen und Wintergärten fällt die Kapazität deutlich "
            "schneller ab. Die Chemie der Lithium-Knopfzelle ist dafür verantwortlich, nicht "
            "eine erhöhte Sendeleistung des Sensors.",
            s["body"],
        ),
        _p(
            "Der folgende Verlauf zeigt die gemessene Restkapazität über die Betriebsdauer bei "
            "drei Umgebungstemperaturen.",
            s["body"],
        ),
    ]

    # Deliberately no caption: Docling finds none, so a description must be generated.
    story += pdf_kit.figure(
        paths.image_source("battery-retention.png"), usable * 0.78, None, s["caption"]
    )

    story += [
        _p(
            "Planen Sie den Batteriewechsel bei kalt montierten Sensoren entsprechend früher "
            "ein. Die App meldet einen niedrigen Ladestand, sobald die Zellenspannung unter "
            "2,6 V fällt.",
            s["body"],
        ),
        _p("4. Fehlerbehebung", s["h1"]),
        _p("4.1 Gerät wird als nicht erreichbar angezeigt", s["h2"]),
        _p(
            "Prüfen Sie zuerst, ob das Gerät physisch vorhanden und die Batterie eingelegt ist. "
            "Bleibt der Status bestehen, bewegen Sie ein netzbetriebenes Gerät näher an den "
            "Sensor: In den meisten Fällen ist die Funkstrecke und nicht das Gerät die "
            "Ursache. Ein Neustart des Hubs behebt das Problem nur dann dauerhaft, wenn "
            "tatsächlich der Hub die Verbindung verloren hat.",
            s["body"],
        ),
        _p("4.2 Thermostat heizt nicht trotz Sollwert", s["h2"]),
        _p(
            "Kontrollieren Sie die Mindestlaufzeit: Ist eine Mindestzykluszeit von 15 Minuten "
            "gesetzt, schaltet der T3 nach einem Ausschaltvorgang nicht sofort wieder ein. "
            "Prüfen Sie anschließend, ob der Sollwert tatsächlich über dem Istwert liegt und "
            "ob der Urlaubsmodus aktiv ist. Der Urlaubsmodus überschreibt jeden Zeitplan.",
            s["body"],
        ),
        _p("4.3 Temperaturwert weicht vom Referenzthermometer ab", s["h2"]),
        _p(
            "Eine Abweichung von bis zu 0,5 K ist normal, insbesondere in den ersten zwei "
            "Stunden nach der Montage, solange sich das Gehäuse thermisch noch nicht "
            "eingependelt hat. Ist die Abweichung dauerhaft größer, hinterlegen Sie in der App "
            "einen Korrekturwert. Montieren Sie den T3 nicht über einem Heizkörper und nicht an "
            "einer Außenwand.",
            s["body"],
        ),
        _p("4.4 Zeitplan wird nicht ausgeführt", s["h2"]),
        _p(
            "Zeitpläne gelten je Zone. Wurde ein Gerät umbenannt, nachdem eine Automatisierung "
            "angelegt wurde, verweist die Automatisierung weiterhin auf den alten Namen und "
            "läuft ins Leere. Legen Sie die betroffene Automatisierung in diesem Fall neu an.",
            s["body"],
        ),
        _p(
            "Hinweis: Nach einem Stromausfall stellt der Hub die Verbindung selbstständig wieder "
            "her. Zeitpläne laufen währenddessen nicht; verpasste Schaltpunkte werden nicht "
            "nachgeholt.",
            s["note"],
        ),
        _p("5. Support kontaktieren", s["h1"]),
        _p(
            "Halten Sie die zwölfstellige Kennung des Hubs und die Firmwareversion bereit. Beide "
            "finden Sie in der App unter Einstellungen. Ohne diese Angaben kann der Support ein "
            "Gerät nicht eindeutig zuordnen.",
            s["body"],
        ),
    ]
    return story


def build(out_dir: Path) -> Path:
    return pdf_kit.build_pdf(
        out_dir / "aurora-technische-daten-de.pdf", TITLE, "Aurora Home", _story
    )
