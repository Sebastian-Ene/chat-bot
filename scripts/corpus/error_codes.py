"""Generates the error-code reference as Markdown.

Combinatorial rather than hand-authored: a reference of ~190 codes is exactly the
kind of bulk that should be templated. It is also the corpus's long document,
which is what stresses chunking and section context at the upper page range.

Deterministic — no randomness, so the output is stable across runs.
"""
from pathlib import Path

STEM = "fehlercode-referenz-de"

FAMILIES = [
    (
        "1xx — Netzwerk und Anbindung",
        "N",
        100,
        "Der Hub konnte die Verbindung zum Dienst nicht herstellen oder verlor sie.",
        [
            ("Kein Link am Netzwerkanschluss", "Kabel oder Switch-Port defekt", "Kabel an beiden Enden neu stecken"),
            ("Keine IP-Adresse erhalten", "DHCP im Netz nicht erreichbar", "Router prüfen, Hub neu starten"),
            ("DNS-Auflösung fehlgeschlagen", "DNS-Server blockiert oder falsch", "DNS des Routers prüfen"),
            ("Zeitabgleich fehlgeschlagen", "NTP ausgehend gesperrt", "NTP freigeben"),
            ("TLS-Handschlag abgebrochen", "Uhrzeit des Hubs weicht zu stark ab", "Zeitabgleich zulassen"),
            ("Verbindung zum Dienst abgelehnt", "Ausgehender Port 443 gesperrt", "Firewallregel ergänzen"),
            ("Verbindung wiederholt getrennt", "Instabile Uplink-Strecke", "Verkabelung und Switch prüfen"),
            ("Gastnetz erkannt", "Client-Isolierung aktiv", "Hub in das reguläre Netz umhängen"),
            ("Doppelte IP-Adresse erkannt", "Statische Adresse kollidiert", "Adressvergabe bereinigen"),
            ("Proxy-Antwort unerwartet", "Aufbrechendes TLS im Netz", "Hub von der Aufbrechung ausnehmen"),
        ],
    ),
    (
        "2xx — Funk und Mesh",
        "F",
        200,
        "Fehler der Funkstrecke zwischen Hub, Repeatern und Endgeräten.",
        [
            ("Gerät antwortet nicht", "Funkstrecke zu lang", "Netzbetriebenes Gerät dazwischen setzen"),
            ("Kopplung abgebrochen", "Zeitfenster überschritten", "Kopplung erneut starten"),
            ("Gerät bereits gekoppelt", "Kopplung an anderem Hub aktiv", "Gerät zuerst entkoppeln"),
            ("Signalqualität unzureichend", "Dämpfung durch Baustoffe", "Standort ändern oder Repeater ergänzen"),
            ("Mesh konvergiert nicht", "Zu wenige Repeater", "Netzbetriebene Geräte ergänzen"),
            ("Kanalwechsel erforderlich", "Störquelle auf dem Kanal", "Automatischen Kanalwechsel abwarten"),
            ("Paketverlust erhöht", "Störung durch Fremdanlage", "Abstand zu Fremdgeräten vergrößern"),
            ("Kapazitätsgrenze erreicht", "64 Geräte je Hub überschritten", "Zweiten Hub einsetzen"),
            ("Endknoten meldet verspätet", "Batteriespannung niedrig", "Batterie wechseln"),
            ("Firmware des Geräts zu alt", "Aktualisierung ausstehend", "Aktualisierung abwarten"),
        ],
    ),
    (
        "3xx — Heizungsansteuerung",
        "H",
        300,
        "Fehler bei der Ansteuerung des Wärmeerzeugers oder der Ventile.",
        [
            ("Kein Heizbedarf trotz Sollwert", "Mindestzykluszeit aktiv", "Zykluszeit prüfen"),
            ("Relais schaltet nicht", "Kontakt verschlissen", "Gerät tauschen"),
            ("OpenTherm-Antwort ungültig", "Gerät unterstützt Modulation nicht", "Auf Ein-Aus-Betrieb umstellen"),
            ("Ventil meldet keine Rückmeldung", "Aktor nicht verbunden", "Verdrahtung des Aktors prüfen"),
            ("Schnittstellenmodul nicht erkannt", "AH-IM1 nicht versorgt", "Versorgung des Moduls prüfen"),
            ("Sicherheitsverriegelung offen", "Interlock des Kessels aktiv", "Kesselstörung beheben"),
            ("Vorlauftemperatur nicht plausibel", "Fühler falsch platziert", "Fühlerposition korrigieren"),
            ("0–10 V ausserhalb des Bereichs", "Stellbereich falsch konfiguriert", "Stellbereich in der App setzen"),
            ("Pumpe läuft nach", "Nachlauf des Kessels", "Kein Eingriff erforderlich"),
            ("Zone reagiert nicht auf Zonentest", "Ventil sitzt fest", "Ventil mechanisch gängig machen"),
        ],
    ),
    (
        "4xx — Sensorik",
        "S",
        400,
        "Fehler der Messwerterfassung an Thermostat und Sensor.",
        [
            ("Messwert unplausibel", "Fremdwärme am Montageort", "Montageort ändern"),
            ("Kein Messwert empfangen", "Sensor offline", "Batterie und Funkstrecke prüfen"),
            ("Kontakt meldet dauerhaft offen", "Magnetabstand zu groß", "Magnet näher setzen"),
            ("Temperaturabweichung dauerhaft", "Kalibrierung erforderlich", "Korrekturwert hinterlegen"),
            ("Batteriespannung unter Schwelle", "Zelle erschöpft", "CR2450 ersetzen"),
            ("Batterieanzeige springt", "Kälteeinfluss auf die Zelle", "Nach Erwärmung erneut prüfen"),
            ("Meldeintervall überschritten", "Funkstrecke ausgelastet", "Repeater ergänzen"),
            ("Sensor nach Batteriewechsel unbekannt", "Kopplung verloren", "Sensor neu koppeln"),
            ("Feuchtewert nicht verfügbar", "Gerätevariante ohne Feuchtefühler", "Kein Eingriff möglich"),
            ("Zwei Sensoren melden widersprüchlich", "Mittelung über die Zone aktiv", "Leitsensor festlegen"),
        ],
    ),
    (
        "5xx — System und Konto",
        "K",
        500,
        "Fehler der Kontoverwaltung, der Zeitpläne und der Aktualisierung.",
        [
            ("Zeitplan nicht ausgeführt", "Urlaubsmodus überschreibt den Plan", "Urlaubsmodus beenden"),
            ("Automatisierung ohne Wirkung", "Gerät nach Anlage umbenannt", "Automatisierung neu anlegen"),
            ("Aktualisierung abgebrochen", "Uplink während der Verteilung verloren", "Aktualisierung erneut anstoßen"),
            ("Zurücksetzen nicht möglich", "Gerät noch gekoppelt", "Zuerst entkoppeln"),
            ("Freigabe fehlgeschlagen", "Empfängerkonto nicht bestätigt", "Einladung erneut senden"),
            ("Objekt nicht auffindbar", "Konto ohne Zuordnung", "Objekt in der App wählen"),
            ("Export unvollständig", "Zeitraum ohne Daten", "Zeitraum anpassen"),
            ("Anmeldung abgelehnt", "Zugangsdaten abgelaufen", "Neu anmelden"),
            ("Übergabe nicht abgeschlossen", "Installateurkonto weiterhin verknüpft", "Übergabe im Portal abschliessen"),
            ("Konto gelöscht, Daten vorhanden", "Löschfrist von 30 Tagen läuft", "Frist abwarten"),
        ],
    ),
]

SEVERITIES = ["Hinweis", "Warnung", "Störung", "Kritisch"]


def _markdown() -> str:
    lines = [
        "---",
        "title: Aurora Home — Fehlercode-Referenz",
        "subtitle: Vollständige Liste der Status- und Fehlercodes · Firmware 4.2.1",
        "lang: de",
        "format: pdf",
        "layout: brief",
        "---",
        "",
        "# Aufbau der Codes",
        "",
        "Jeder Code besteht aus einem Buchstaben für die Baugruppe und einer dreistelligen "
        "Nummer. Der Buchstabe entspricht der Familie, die Nummer der laufenden Meldung "
        "innerhalb der Familie. Codes werden in der App unter dem betroffenen Gerät "
        "angezeigt und im Ereignisprotokoll des Hubs mit Zeitstempel geführt.",
        "",
        "Der Schweregrad steuert lediglich die Darstellung in der App. Auch ein Hinweis "
        "kann auf eine Ursache zeigen, die längerfristig behoben werden sollte.",
        "",
    ]

    for family, letter, base, description, entries in FAMILIES:
        lines += [f"# {family}", "", description, ""]
        # Four variants per entry keep the reference long without inventing
        # symptoms that would not occur.
        variants = [
            ("", ""),
            (" beim Start", "unmittelbar nach dem Einschalten"),
            (" im Betrieb", "während des laufenden Betriebs"),
            (" nach Aktualisierung", "erstmals nach einer Firmwareaktualisierung"),
            (" nach Stromausfall", "nach einer Unterbrechung der Versorgung"),
            (" wiederholt", "mehrfach innerhalb einer Stunde"),
            (" sporadisch", "unregelmäßig und ohne erkennbaren Auslöser"),
        ]
        lines += ["| Code | Meldung | Ursache | Massnahme | Schweregrad |", "| --- | --- | --- | --- | --- |"]
        number = base
        for index, (symptom, cause, action) in enumerate(entries):
            for variant_index, (suffix, qualifier) in enumerate(variants):
                number += 1
                detail = f"{cause}, {qualifier}" if qualifier else cause
                severity = SEVERITIES[(index + variant_index) % len(SEVERITIES)]
                lines.append(
                    f"| {letter}{number} | {symptom}{suffix} | {detail} | {action} | {severity} |"
                )
        lines.append("")

    lines += [
        "# Umgang mit unbekannten Codes",
        "",
        "Codes, die hier nicht aufgeführt sind, stammen aus einer neueren Firmware als "
        "dieser Dokumentstand. Melden Sie den Code zusammen mit der Kennung des Hubs an "
        "den Support; erfinden Sie keine Massnahme auf Verdacht, insbesondere nicht bei "
        "Codes der Familie 3xx, die die Heizungsansteuerung betreffen.",
        "",
    ]
    return "\n".join(lines) + "\n"


def write(content_dir: Path) -> Path:
    path = content_dir / f"{STEM}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_markdown(), encoding="utf-8")
    return path
