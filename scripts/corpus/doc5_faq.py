"""Doc 5 — Support FAQ (EN + DE, HTML).

Carries: the HTML format, a CSS **multi-column** section, an **uncaptioned**
chart, and the multi-hop hook — the second-hub statement here only answers a
capacity question when combined with the 64-device limit in doc 1.

Both languages live in one page, as a real FAQ often does.
"""
from pathlib import Path

from scripts.corpus import paths

TITLE = "Aurora Home — Support FAQ"

_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Aurora Home — Support FAQ</title>
    <style>
      body { font-family: Georgia, serif; max-width: 52rem; margin: 2rem auto; color: #1b1b1b; }
      h1 { font-size: 1.9rem; }
      h2 { font-size: 1.3rem; margin-top: 2rem; border-bottom: 1px solid #ddd; }
      h3 { font-size: 1.05rem; margin-bottom: .2rem; }
      .lede { color: #555; font-style: italic; }
      .two-column { column-count: 2; column-gap: 2.5rem; }
      .two-column h3 { break-after: avoid; }
      figure { margin: 1.5rem 0; }
      figure img { width: 100%; max-width: 34rem; }
      table { border-collapse: collapse; margin: 1rem 0; }
      th, td { border: 1px solid #999; padding: .35rem .6rem; text-align: left; }
      th { background: #e8e3d8; }
    </style>
  </head>
  <body>
    <h1>Aurora Home — Support FAQ</h1>
    <p class="lede">Frequently asked questions · Häufige Fragen · updated February 2026</p>

    <h2>Getting help</h2>
    <p>
      Support is staffed Monday to Friday, 08:00 to 18:00 CET, excluding public holidays in
      Berlin. Messages sent outside those hours are answered on the next working day. There is
      no telephone line: every enquiry goes through the app so that the device history travels
      with the ticket.
    </p>

    <figure>
      <img src="images/support-volume.png" alt="" />
    </figure>

    <p>
      Response times vary through the week. If your question is not urgent, the middle of the
      week is usually quieter than either end of it.
    </p>

    <h2>Accounts and property setup</h2>
    <div class="two-column">
      <h3>Can I have more than one property on one account?</h3>
      <p>
        Yes. An account can hold any number of properties, each with its own hubs, zones and
        schedules. Switching property in the app switches the whole context, so a schedule
        edited in one property never affects another.
      </p>

      <h3>What happens if I need more capacity?</h3>
      <p>
        Add a second hub. Each additional hub adds its own full device capacity to the
        property, and the app continues to present the property as a single system. Devices
        belong to exactly one hub and can be moved between hubs by unpairing and re-pairing.
      </p>

      <h3>Can I share access with someone else?</h3>
      <p>
        Yes, per property. A shared user can adjust temperatures and run automations, but
        cannot add or remove hubs, and cannot see billing information.
      </p>

      <h3>Wie viele Zonen kann ich anlegen?</h3>
      <p>
        Die Anzahl der Zonen ist nicht begrenzt. Praktisch begrenzt wird sie durch die Zahl der
        Thermostate: Jede Zone benötigt genau ein Thermostat, Sensoren können beliebig viele
        hinzukommen.
      </p>

      <h3>Kann ich die App ohne Hub nutzen?</h3>
      <p>
        Nein. Ohne Hub lassen sich Geräte weder einbinden noch fernsteuern. Ein Thermostat
        funktioniert dann nur als eigenständiger Regler direkt an der Wand.
      </p>

      <h3>Was passiert bei einem Internetausfall?</h3>
      <p>
        Zeitpläne laufen lokal auf dem Hub weiter. Fernzugriff und Sprachassistenten sind
        während des Ausfalls nicht verfügbar, die Heizung wird aber weiter geregelt.
      </p>
    </div>

    <h2>Orders and deliveries</h2>
    <p>
      Delivery times, return windows and warranty terms are set out in the warranty, returns
      and shipping policy, which is the authoritative document for all three. This FAQ does not
      repeat those figures, because a policy that exists in two places eventually disagrees
      with itself.
    </p>

    <h3>Where do replacement units ship from?</h3>
    <p>
      Replacements ship from the same warehouse as new orders and under the same delivery
      terms, so the delivery time for your destination applies unchanged.
    </p>

    <h2>Datenschutz</h2>
    <p>
      Temperatur- und Sensordaten werden dem Konto zugeordnet gespeichert, solange das Konto
      besteht. Beim Löschen des Kontos werden alle Messwerte innerhalb von 30 Tagen entfernt.
      Anonymisierte Auswertungen zur Produktverbesserung bleiben davon unberührt und lassen
      keinen Rückschluss auf einzelne Haushalte zu.
    </p>

    <h2>Feature requests</h2>
    <p>
      Suggestions go through the app's feedback form rather than support tickets. Aurora Home
      does not commit to timelines for individual requests, and does not maintain a public
      roadmap.
    </p>
  </body>
</html>
"""


FIGURES = ["images/support-volume.png"]


def build(out_dir: Path) -> Path:
    path = out_dir / "aurora-support-faq.html"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_HTML, encoding="utf-8")
    # HTML references its figure by relative path, so the file has to sit beside
    # the document rather than only in the sources.
    paths.copy_images(FIGURES, out_dir)
    return path
