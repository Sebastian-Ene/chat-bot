---
title: Aurora Home — Energiebericht verstehen
subtitle: App-Leitfaden · Stand Januar 2026
lang: de
format: pdf
layout: report
---

# Was der Bericht zeigt

Der monatliche Energiebericht schätzt den Wärmeverbrauch je Zone anhand der
Laufzeit des Wärmeerzeugers und der gemessenen Raumtemperaturen. Es handelt sich
um eine Schätzung: Aurora Home misst keinen Gas- oder Stromverbrauch und ersetzt
keinen geeichten Zähler.

![Abbildung 1: Verbrauch der Heizperiode im Vergleich zum Vorjahr, Beispielobjekt mit sechs Zonen.](images/energie-vergleich.png)

# Wie die Schätzung entsteht

Grundlage ist die Einschaltdauer je Zone, gewichtet mit der Differenz zwischen
Soll- und Aussentemperatur. Für modulierende Anlagen über OpenTherm fliesst
zusätzlich der gemeldete Modulationsgrad ein, wodurch die Schätzung deutlich
genauer wird als bei einfacher Ein-Aus-Ansteuerung.

# Grenzen der Aussagekraft

- Der erste angebrochene Monat nach der Installation wird zu niedrig ausgewiesen.
- Warmwasser ist nicht enthalten, auch wenn es derselbe Erzeuger bereitstellt.
- Zusätzliche Wärmequellen wie Kaminöfen oder elektrische Zusatzheizungen bleiben unberücksichtigt und führen zu einer scheinbaren Einsparung.
- Ein Vergleich mit dem Vorjahr ist nur bei ähnlicher Witterung aussagekräftig; der Bericht normiert nicht auf Gradtagzahlen.

# Vergleichszeitraum

Der Bericht vergleicht standardmässig mit dem gleichen Monat des Vorjahres. Liegen
weniger als zwölf Monate Daten vor, entfällt der Vergleich und es wird nur der
laufende Monat dargestellt.

# Export

Die Daten lassen sich als CSV exportieren, eine Zeile je Zone und Tag. Der Export
enthält die Rohwerte für Laufzeit und Temperatur, sodass eigene Auswertungen
möglich sind.
