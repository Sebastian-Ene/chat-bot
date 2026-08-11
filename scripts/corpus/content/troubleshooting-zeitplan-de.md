---
title: Aurora Home — Zeitplan schaltet nicht wie erwartet
subtitle: Fehlerbehebungsartikel TS-021 · zuletzt geprüft im Januar 2026
lang: de
format: docx
layout: brief
---

# Symptom

Ein Zeitplan ist hinterlegt, die Heizung schaltet aber nicht zur erwarteten
Uhrzeit oder hält eine andere Temperatur als eingestellt.

# Häufigste Ursachen

- Der Urlaubsmodus ist aktiv und überschreibt jeden Zeitplan im gesamten Objekt.
- Ein manueller Sollwert wurde gesetzt und gilt bis zum nächsten Schaltpunkt.
- Der Zeitplan gehört zu einer anderen Zone als dem Raum, in dem gemessen wird.
- Die Mindestzykluszeit verhindert ein sofortiges Wiedereinschalten.

# Zeitpläne haben keine Aus-Zeiten

Ein Schaltpunkt gilt bis zum nächsten. Wer eine Absenkung über Nacht wünscht,
muss einen Schaltpunkt mit niedriger Temperatur setzen; das Löschen des
Abendeintrags verlängert stattdessen den vorherigen Wert bis zum Morgen. Dieses
Verhalten ist die mit Abstand häufigste Meldung zu diesem Symptom.

# Nach einem Stromausfall

Der Hub verbindet sich selbstständig wieder. Während des Ausfalls laufen keine
Zeitpläne, und verpasste Schaltpunkte werden nicht nachgeholt. Nach der
Wiederverbindung gilt wieder der jeweils aktuelle Schaltpunkt, nicht der
verpasste.

# Umbenannte Geräte

Automatisierungen verweisen auf den Gerätenamen zum Zeitpunkt der Erstellung.
Wurde ein Gerät später umbenannt, läuft die Automatisierung ins Leere, ohne eine
Fehlermeldung anzuzeigen. Legen Sie die betroffene Automatisierung in diesem Fall
neu an.

# Prüfliste vor der Supportanfrage

- Urlaubsmodus deaktiviert?
- Sollwert liegt über dem Istwert?
- Zone enthält das erwartete Thermostat?
- Zonentest ausgeführt und Reaktion beobachtet?
