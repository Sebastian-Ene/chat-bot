---
title: Aurora Home — Release Notes 4.2
subtitle: Hub H2, Thermostat T3, Sensor S1 · released 14 January 2026
lang: en
format: html
layout: report
---

# Highlights

Release 4.2 concentrates on mesh stability in large properties and on making
schedules easier to reason about. It is a staged rollout: hubs check nightly and
update themselves, and connected devices follow over the following days.

# New

- Zone test now runs every zone in sequence from the app and reports which zones responded.
- Holiday mode accepts a return date and clears itself automatically on that date.
- Schedules can be copied between zones, including across properties on the same account.
- The device list can be sorted by floor when a floor prefix is present in the name.

# Changed

- The minimum cycle time for heat-pump installations is now configurable between 5 and 30 minutes; the previous fixed value was 10 minutes.
- Low-battery warnings fire at 2.6 V, raised from 2.5 V, to give more notice in cold rooms.
- Pairing mode times out after 90 seconds instead of 60.

# Fixed

- A hub that lost its uplink during a firmware staging window could leave a device reporting an in-progress update indefinitely.
- Renaming a zone no longer detaches its schedule.
- Temperature offsets entered in Fahrenheit were stored without conversion on accounts created before 3.9.

# Known issues

- Sensors that have been offline for more than 30 days occasionally need to be re-paired rather than rejoining on their own.
- The energy report understates consumption for the first partial month after installation.

# Upgrade notes

There is no rollback. Properties with more than forty devices should expect the
mesh to re-converge over several hours after the hub restarts; this is normal and
needs no intervention.
