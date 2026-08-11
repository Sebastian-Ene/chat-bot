---
title: Aurora Home — Automations and Scenes
subtitle: App guide · covers release 4.2
lang: en
format: pdf
layout: report
---

# What an automation is

An automation is a trigger, an optional set of conditions, and one or more
actions. It belongs to a property, may span hubs within that property, and runs
on the hub rather than in the app — so it continues to work while your phone is
elsewhere.

![Figure 1: The four parts of an automation, evaluated left to right.](images/automation-flow.png)

# Triggers

::: two-column
## Time

A time trigger fires at a fixed clock time on selected days, or at a fixed offset
from sunrise or sunset for the property's location. Offsets may be negative.

## Sensor

A sensor trigger fires when a contact opens or closes, or when a measured
temperature crosses a threshold. Threshold triggers fire on the crossing, not
continuously while the condition holds.

## Presence

A presence trigger fires when the first person arrives or the last person leaves,
based on the phones associated with the account. Presence is deliberately coarse:
it does not distinguish who arrived.

## Manual

A manual trigger does nothing on its own and is fired from the app. This is how
scenes are built — a named set of actions with no automatic trigger at all.
:::

# Conditions

Conditions are evaluated once, at the moment the trigger fires. An automation
whose condition becomes true a minute later does not run: the trigger has already
passed. This catches people out when combining a presence trigger with a
temperature condition, and is the single most common misunderstanding in support
tickets about automations.

# Actions

Actions set a temperature in a zone, activate or clear holiday mode, or send a
notification. An action that sets a temperature behaves like a manual setpoint:
it holds until the next scheduled setpoint, not indefinitely.

# Ordering and conflicts

Where two automations act on the same zone at the same moment, the one created
most recently wins. There is no priority setting. If ordering matters, combine
the logic into a single automation rather than relying on creation order, which
is invisible in the interface and easy to disturb.

# Limits

A property supports up to 50 automations. Each automation supports up to 10
actions. Notifications are rate-limited to one per automation per five minutes,
so an automation triggered repeatedly will not flood the phone.
