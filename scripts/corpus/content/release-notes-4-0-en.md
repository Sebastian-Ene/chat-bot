---
title: Aurora Home — Release Notes 4.0
subtitle: Hub H2, Thermostat T3, Sensor S1 · released 3 June 2025
lang: en
format: docx
layout: manual
---

# Overview

Release 4.0 replaced the pairing stack and raised the supported device count per
hub. It is the oldest release still receiving security fixes; hubs on 3.x should
update before the end of the current heating season.

# New

- Device capacity per hub raised from 32 to 64, counting thermostats, sensors and accessories together.
- Second hub supported in a single property, presented in the app as one system.
- Automations may span hubs within a property.
- Installer handover flow, transferring ownership without sharing a login.

# Changed

- Pairing now completes in around 30 seconds; the previous stack needed up to two minutes.
- The mesh prefers mains-powered devices as repeaters rather than choosing by signal strength alone.
- Sensors report temperature every 10 minutes; the previous interval was 15.

# Fixed

- Devices removed physically but left paired no longer count towards the capacity limit after a forced removal.
- Schedules created in one property could appear in another property on the same account.

# Migration from 3.x

Hubs upgrade in place and keep their pairings. Properties that had reached the old
32-device limit and were split across two hubs may now be consolidated onto one,
but consolidation is manual: unpair each device from the second hub and pair it
again with the first.

# Support window

Security fixes for 4.0 continue until twelve months after the release of 4.2.
Feature work has moved to the current release.
