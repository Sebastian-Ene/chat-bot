---
title: Aurora Home — Versionshinweise 4.1
subtitle: Hub H2, Thermostat T3, Sensor S1 · veröffentlicht am 6. Oktober 2025
lang: de
format: pdf
layout: brief
---

# Überblick

Version 4.1 bringt die Modulation über OpenTherm sowie mehrere Korrekturen an der
Zeitplanlogik. Die Verteilung erfolgt gestaffelt über die nächtliche Prüfung des
Hubs.

# Neu

- Modulierender Betrieb über OpenTherm für Kombi- und Brennwertgeräte.
- Korrekturwert für die Temperaturmessung je Thermostat in der App hinterlegbar.
- Exportierbare Verbrauchsübersicht im CSV-Format.

# Geändert

- Die Zeitplanansicht zeigt bis zu sechs Schaltpunkte je Tag; zuvor waren es vier.
- Der Frostschutz greift jetzt bei 7 °C statt bei 5 °C.
- Die Reaktionszeit des Fensterkontakts wurde von zwei Sekunden auf unter eine Sekunde verkürzt.

# Behoben

- Ein Zeitplan mit zwei Schaltpunkten zur selben Uhrzeit führte dazu, dass beide ignoriert wurden.
- Der Urlaubsmodus liess sich nicht beenden, solange eine Automatisierung aktiv war.
- Die App zeigte nach einem Hub-Neustart gelegentlich veraltete Messwerte an.

# Hinweise zur Aktualisierung

Ein Zurücksetzen auf 4.0 ist nicht möglich. Installationen mit
Schnittstellenmodul AH-IM1 sollten nach der Aktualisierung einen Zonentest
durchführen, da die Ansteuerung der Ventile neu kalibriert wird.
