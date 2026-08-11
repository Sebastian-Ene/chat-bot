---
title: Aurora Home — Hub Shows as Offline
subtitle: Troubleshooting article TS-014 · last reviewed January 2026
lang: en
format: pdf
layout: manual
---

# Symptom

The app reports the hub as offline. Devices continue to follow their schedules,
because schedules run locally on the hub, but remote control and voice assistants
stop working until the hub reconnects.

# Check the obvious first

- The status ring is unlit: the hub has no power. Check the adapter and the socket.
- The status ring pulses amber: the hub has power but no network link.
- The status ring is steady white: the hub believes it is online, and the problem is between your router and our service.

# If the ring pulses amber

Reseat the network cable at both ends and confirm the router port shows a link
light. Hubs are fixed at 100 Mbit/s full duplex; a switch port forced to a
different setting will not negotiate, and the symptom is exactly this. If the
cable runs through a wall plate, test with a short cable directly to the router
before suspecting the hub.

# If the ring is steady white

The hub has an address and a route but cannot reach the service. This is almost
always upstream filtering. The hub needs outbound access on TCP 443 to the Aurora
Home service and outbound NTP for time; blocking NTP is a common cause, because a
hub with a badly wrong clock cannot complete the TLS handshake and reports the
failure as an offline state rather than as a clock problem.

Guest networks and networks with client isolation enabled will not work: the app
discovers the hub on the local subnet during setup.

# Restarting

Restart the hub by unplugging it for ten seconds. A restart resolves a genuinely
stuck uplink and nothing else — if the hub returns to offline within minutes,
restarting it repeatedly will not help and the cause is upstream.

# When to contact support

Contact support with the twelve-character hub identifier if the ring is steady
white, the network is unfiltered, and the hub has been restarted once. Include
the time of the last successful connection, which the app shows on the hub detail
screen.
