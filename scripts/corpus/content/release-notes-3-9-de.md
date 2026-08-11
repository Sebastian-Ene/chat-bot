---
title: Aurora Home — Versionshinweise 3.9
subtitle: Hub H2, Thermostat T3, Sensor S1 · veröffentlicht am 11. Februar 2025
lang: de
format: html
layout: manual
---

# Überblick

Version 3.9 ist eine Wartungsversion. Sie enthält keine neuen Funktionen, sondern
Korrekturen an der Funkanbindung und an der Batterieanzeige.

# Behoben

- Sensoren meldeten nach einem Batteriewechsel gelegentlich weiterhin einen niedrigen Ladestand, bis der Hub neu gestartet wurde.
- Der Fensterkontakt löste bei starker Zugluft fälschlich aus.
- Die Restlaufzeitschätzung der Batterie berücksichtigte die Umgebungstemperatur nicht und war in kalten Räumen deutlich zu optimistisch.
- Zeitzonenwechsel wurden erst nach einem Neustart des Hubs übernommen.

# Bekannte Einschränkungen

- Die Gerätekapazität je Hub liegt in dieser Version bei 32 Geräten.
- Ein zweiter Hub je Objekt wird nicht unterstützt.
- Temperaturkorrekturwerte lassen sich nur über den Support hinterlegen.

# Empfehlung

Diese Version wird nicht mehr gepflegt. Aktualisieren Sie auf die aktuelle
Version; ein direkter Sprung von 3.9 auf 4.2 ist möglich und wird vom Hub
automatisch in zwei Schritten ausgeführt.
