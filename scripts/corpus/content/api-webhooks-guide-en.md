---
title: Aurora Home — Webhooks and Integration
subtitle: Developer guide · covers release 4.3
lang: en
format: pdf
layout: report
batch: later
---

# What webhooks give you

From release 4.3 the hub can post state changes to an endpoint you control.
Webhooks are outbound only: there is no inbound API, and nothing you send to the
hub will change its state. Integrations that need to set a temperature do so
through the app's account-linking flow, not through this interface.

![Figure 1: A state change travels from device to hub to your endpoint; the hub retries on failure.](images/webhook-delivery.png)

# Registering an endpoint

Register an HTTPS endpoint in the app under Settings. Plain HTTP is rejected.
The hub sends a verification request containing a nonce, which your endpoint must
echo back within ten seconds before deliveries begin.

# Event types

| Event | Fires when | Payload includes |
| --- | --- | --- |
| `zone.setpoint_changed` | A setpoint changes, whether by schedule, automation or by hand | zone, old and new setpoint, source |
| `zone.temperature_reported` | A zone's averaged temperature changes by at least 0.5 K | zone, temperature, contributing sensors |
| `device.battery_low` | A device crosses the low-battery threshold | device, measured voltage |
| `device.unreachable` | A device misses three consecutive reports | device, last seen timestamp |
| `hub.updated` | Firmware finishes applying | previous and current version |

# Delivery and retries

Deliveries are at-least-once. A non-2xx response or a timeout over five seconds
is retried four times with exponential backoff, after which the event is dropped.
Your endpoint must therefore be idempotent: the same event identifier can arrive
more than once, and ordering is not guaranteed under retry.

| Attempt | Delay after the previous |
| --- | --- |
| 1 | immediate |
| 2 | 10 seconds |
| 3 | 60 seconds |
| 4 | 5 minutes |
| 5 | 30 minutes |

# Rate limits

A hub sends at most 60 events per minute. Beyond that, events of the same type
for the same zone are coalesced, and only the most recent is delivered. A busy
commercial property routinely reaches this limit during morning warm-up, so treat
coalescing as normal rather than as a fault.

# Signing

Every request carries an HMAC-SHA256 signature over the raw body, using the
secret shown once when the endpoint is registered. Verify it against the raw
bytes, before any JSON parsing: a re-serialised body will not match.

# Limits worth knowing

One endpoint per property. Payloads are capped at 64 KB. The event log the hub
keeps for its own retries holds 24 hours, so an endpoint offline for longer than
that loses the events in between with no backfill.
