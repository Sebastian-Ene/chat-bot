---
title: Aurora Home — Release Notes 4.3
subtitle: Hub H2, Thermostat T3, Sensor S1 · released 24 March 2026
lang: en
format: html
layout: report
batch: later
---

# Highlights

Release 4.3 adds outbound webhooks, a maintenance window for staged updates, and
a rewritten zone-averaging model. It is the first release to require a hub with
at least 256 MB of memory; every H2 shipped since 2023 meets that.

# New

- Outbound webhooks for state changes, documented in the integration guide.
- A maintenance window setting: staged firmware updates only apply inside it.
- Zone averaging can now be weighted per sensor rather than treating every sensor equally.
- Schedules can be exported and re-imported as JSON, which finally makes a hub factory reset survivable.

# Changed

- The automation limit per property rises from 50 to 100.
- Notification rate limiting is now per automation per minute, rather than per five minutes.
- Holiday mode no longer clears a manual setpoint when it ends; the schedule resumes at the next setpoint instead.

# Fixed

- Weighted averaging previously ignored sensors reporting exactly at the setpoint.
- A schedule copied between properties kept the source property's holiday dates.
- The energy report double-counted the first day of a month for zones created mid-month.

# Deprecations

- CSV export of the energy report is deprecated in favour of the JSON export and will be removed in 4.5.
- Support for firmware 3.x hubs ends with this release; 3.x hubs no longer receive security fixes.

# Upgrade notes

Set a maintenance window before upgrading a commercial installation, otherwise
staged updates apply as soon as they arrive, which is the previous behaviour.
