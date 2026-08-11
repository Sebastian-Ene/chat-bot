"""Doc 1 — Aurora Home Installation & Setup Guide (EN, PDF, long).

Carries: a two-column section, a ruled compatibility table that spans a page
break with its header repeated, and a captioned wiring diagram whose C-wire
requirement appears nowhere in the prose.
"""
from pathlib import Path

from reportlab.platypus import NextPageTemplate, PageBreak, Paragraph, Spacer

from scripts.corpus import paths, pdf_kit

TITLE = "Aurora Home — Installation and Setup Guide"


def _p(text: str, style) -> Paragraph:
    return Paragraph(text, style)


def _story(s: dict, usable: float) -> list:
    story: list = [
        _p(TITLE, s["title"]),
        _p(
            "Thermostat T3 · Sensor S1 · Hub H2 — firmware 4.2.1 · document revision 7",
            s["subtitle"],
        ),
        _p("1. About this guide", s["h1"]),
        _p(
            "This guide covers the physical installation and first-time setup of the Aurora "
            "Home range: the T3 thermostat, the S1 door and window sensor, and the H2 hub. "
            "It is written for homeowners doing their own installation and for installers "
            "commissioning several properties at once. Where a step requires an electrician, "
            "the text says so explicitly.",
            s["body"],
        ),
        _p(
            "Read section 2 before opening the packaging. The T3 connects to mains-derived "
            "low-voltage wiring, and the sequence in which you isolate the boiler matters.",
            s["body"],
        ),
        _p("2. Safety and prerequisites", s["h1"]),
        _p(
            "Isolate the heating system at the consumer unit before removing an existing "
            "thermostat. Confirm the circuit is dead with a voltage tester rather than relying "
            "on the boiler's own display, which can remain lit from a separate supply. Aurora "
            "Home devices are for indoor use only, in dry rooms, at ambient temperatures "
            "between 0 °C and 45 °C.",
            s["body"],
        ),
        _p(
            "You will need: a small flat screwdriver, a voltage tester, a drill with a 6 mm "
            "masonry bit if you are mounting on brick, and a smartphone running the Aurora "
            "Home app. Allow forty minutes for a single-thermostat installation and around "
            "two hours for a whole-property commissioning.",
            s["body"],
        ),
        _p(
            "Note: if your existing thermostat is battery-powered and has only two wires, your "
            "system almost certainly lacks the common conductor the T3 needs. Read section 3 "
            "before ordering.",
            s["note"],
        ),
        _p("3. Wiring the T3", s["h1"]),
        _p(
            "The T3 replaces an existing wall thermostat and reuses its backplate position in "
            "most installations. Remove the old faceplate, photograph the terminal block before "
            "disconnecting anything, and label each conductor as you release it. The terminal "
            "designations used by Aurora Home follow the common four-wire convention.",
            s["body"],
        ),
        _p(
            "The diagram below shows the mapping between a typical boiler terminal block and "
            "the T3 backplate. Match the labels rather than the colours: conductor colours vary "
            "by installer and by country, and are not a reliable guide.",
            s["body"],
        ),
    ]

    story += pdf_kit.figure(
        paths.image_source("t3-wiring.png"),
        usable * 0.82,
        "Figure 1: Terminal mapping between a four-wire boiler block and the T3 backplate.",
        s["caption"],
    )

    story += [
        _p(
            "Tighten each terminal to a firm stop, then tug each conductor gently to confirm it "
            "is captive. Refit the backplate, clip the T3 body on until it clicks, and restore "
            "power at the consumer unit. The display illuminates within ten seconds.",
            s["body"],
        ),
        _p("3.1 If the display stays dark", s["h2"]),
        _p(
            "A dark display after restoring power almost always means the backplate is not "
            "seated or a terminal has not made contact. Isolate the circuit again, remove the "
            "body, and inspect the four spring contacts on the rear for debris or bent leaves. "
            "Only after that should you suspect the unit itself.",
            s["body"],
        ),
        # Two-column section from here.
        NextPageTemplate("TwoCol"),
        PageBreak(),
        _p("4. Commissioning the H2 hub", s["h1"]),
        _p(
            "The H2 hub bridges the Aurora radio mesh to your home network. It must sit within "
            "radio range of at least one powered device, and within cable reach of your router. "
            "The hub has no battery: it is powered permanently from the supplied adapter, and a "
            "power cut interrupts automation until the hub rejoins the network.",
            s["body"],
        ),
        _p(
            "Connect the hub to the router with the supplied cable, wait for the status ring to "
            "settle to a steady white, then open the Aurora Home app and choose Add hub. The "
            "app discovers hubs on the same subnet automatically. If discovery fails, the hub "
            "can be added manually using the twelve-character identifier printed on its base.",
            s["body"],
        ),
        _p("4.1 Pairing devices", s["h2"]),
        _p(
            "Devices pair one at a time. Put the hub into pairing mode from the app, then hold "
            "the pairing button on the device for three seconds until its indicator pulses. "
            "Pairing completes within thirty seconds; the device then appears in the app under "
            "its default name, which you should change immediately to something that identifies "
            "the room. Automations refer to devices by name, and renaming a device later does "
            "not rewrite existing automations.",
            s["body"],
        ),
        _p(
            "Sensors join the mesh as leaf nodes and do not relay traffic for other devices. "
            "Thermostats and any mains-powered accessory act as repeaters, so in a large "
            "property the practical range depends far more on where the thermostats are than on "
            "where the hub is.",
            s["body"],
        ),
        _p("4.2 Placement and range", s["h2"]),
        _p(
            "Radio range in free air is generous, but real buildings are not free air. Foil-"
            "backed insulation, wet plaster and reinforced concrete all attenuate the signal "
            "sharply. As a rule of thumb, allow one internal wall between any sensor and its "
            "nearest repeater, and two at the absolute limit. Where a sensor sits at the far end "
            "of a long extension, adding a mains-powered accessory in between is more reliable "
            "than moving the hub.",
            s["body"],
        ),
        _p(
            "Avoid mounting the hub inside a metal cabinet or directly beside the router: the "
            "router's own radios raise the noise floor and reduce effective mesh range.",
            s["body"],
        ),
        _p("5. Zoning and schedules", s["h1"]),
        _p(
            "A zone groups one thermostat with any number of sensors. The thermostat holds the "
            "schedule; the sensors report temperature and occupancy into it. Where a zone "
            "contains several sensors, the thermostat averages their readings by default, and "
            "can be configured instead to follow whichever sensor reports occupancy.",
            s["body"],
        ),
        _p(
            "Schedules are per zone and per day, with up to six setpoints in each day. A "
            "setpoint applies until the next one begins; there is no explicit off period. To "
            "leave a room unheated overnight, set a low setpoint rather than deleting the "
            "evening entry, which would extend the previous setpoint until morning.",
            s["body"],
        ),
        _p(
            "Holiday mode overrides every schedule in the property with a single frost-"
            "protection setpoint, and ends automatically on the return date you set.",
            s["body"],
        ),
        # Back to a single column for the wide table.
        NextPageTemplate("OneCol"),
        PageBreak(),
        _p("6. Compatibility matrix", s["h1"]),
        _p(
            "The matrix below lists the heating system types verified by Aurora Home for the "
            "current firmware. Systems marked as requiring an interface module need the AH-IM1 "
            "accessory between the T3 and the boiler; systems marked as unsupported cannot be "
            "controlled by the T3 at all and are not made supportable by an accessory.",
            s["body"],
        ),
        _p(
            "Verified means Aurora Home has tested the combination in its own laboratory. "
            "Combinations not listed may still work, but are not covered by support.",
            s["body"],
        ),
    ]

    header = ["System type", "Control method", "T3", "Interface module", "Notes"]
    rows = [
        ["Combi boiler, on/off", "Volt-free contact", "Verified", "Not required", "Most common UK and DE installations"],
        ["Combi boiler, OpenTherm", "Modulating", "Verified", "Not required", "Modulation requires firmware 4.1 or later"],
        ["System boiler with cylinder", "Volt-free contact", "Verified", "Not required", "Hot water control via separate channel"],
        ["Heat-only boiler", "Volt-free contact", "Verified", "Not required", "Pump overrun handled by the boiler"],
        ["Underfloor heating, wet", "Zone valve", "Verified", "Required", "One valve actuator per zone"],
        ["Underfloor heating, electric", "Direct switching", "Not supported", "—", "Load exceeds the T3 relay rating"],
        ["District heating substation", "0–10 V", "Verified", "Required", "Set the actuator range in the app"],
        ["Air-source heat pump, on/off", "Volt-free contact", "Verified", "Not required", "Minimum cycle time must be set to 15 minutes"],
        ["Air-source heat pump, modulating", "Proprietary bus", "Not supported", "—", "No open control interface"],
        ["Ground-source heat pump", "Volt-free contact", "Verified", "Required", "Interface module isolates the control circuit"],
        ["Electric panel heaters", "Direct switching", "Not supported", "—", "Load exceeds the T3 relay rating"],
        ["Storage heaters", "Time-of-use relay", "Not supported", "—", "Charge control is outside the T3's remit"],
        ["Biomass boiler", "Volt-free contact", "Verified", "Required", "Interface module required for safety interlock"],
        ["Oil boiler, on/off", "Volt-free contact", "Verified", "Not required", "Same wiring as a heat-only boiler"],
        ["Warm-air unit", "Volt-free contact", "Verified", "Not required", "Fan delay configured on the unit itself"],
        ["Solar thermal, supplementary", "Monitoring only", "Verified", "Not required", "T3 reads, never controls, the solar circuit"],
        ["Radiator valves, third-party", "Radio", "Not supported", "—", "Only Aurora Home valves join the mesh"],
        ["Ventilation with heat recovery", "Volt-free contact", "Verified", "Required", "Boost function mapped to a schedule"],
        ["Gas absorption heat pump", "Volt-free contact", "Verified", "Required", "Interface module handles the interlock"],
        ["Hybrid boiler and heat pump", "OpenTherm", "Verified", "Not required", "The hybrid controller decides which source runs"],
        ["Wood pellet stove with back boiler", "Volt-free contact", "Verified", "Required", "Manual override on the stove takes precedence"],
        ["Electric boiler, wet system", "Volt-free contact", "Verified", "Not required", "Check the relay rating against the boiler contactor"],
        ["Two-pipe fan coil units", "0–10 V", "Verified", "Required", "One actuator per coil"],
        ["Four-pipe fan coil units", "0–10 V", "Not supported", "—", "Simultaneous heating and cooling is not modelled"],
        ["Radiant ceiling panels", "Zone valve", "Verified", "Required", "Slow response; widen the deadband"],
        ["Towel rail, electric", "Direct switching", "Not supported", "—", "Load exceeds the T3 relay rating"],
        ["Immersion heater", "Time-of-use relay", "Not supported", "—", "Hot water only; outside the T3's remit"],
        ["Thermal store with coil", "Volt-free contact", "Verified", "Not required", "Store temperature read by a separate sensor"],
        ["Air handling unit, commercial", "0–10 V", "Not supported", "—", "Commercial plant is out of scope"],
        ["Infrared panel heaters", "Direct switching", "Not supported", "—", "Load exceeds the T3 relay rating"],
        ["Condensing boiler, weather compensated", "OpenTherm", "Verified", "Not required", "Compensation curve stays on the boiler"],
        ["Multi-zone manifold, six zones", "Zone valve", "Verified", "Required", "One interface module per manifold"],
        ["Swimming pool heat exchanger", "Volt-free contact", "Not supported", "—", "Outside the tested temperature range"],
    ]
    widths = [usable * w for w in (0.24, 0.17, 0.12, 0.17, 0.30)]
    story.append(pdf_kit.ruled_table([header, *rows], widths))
    story.append(Spacer(1, 10))
    story.append(
        _p(
            "Table 1: Verified heating system types for firmware 4.2.1. The table continues "
            "across the page break; the header row repeats.",
            s["caption"],
        )
    )

    story += [
        _p("7. Capacity limits", s["h1"]),
        _p(
            "A single H2 hub supports a maximum of 64 paired devices, counting thermostats, "
            "sensors and accessories together. Properties needing more capacity add a second "
            "hub; the app presents multiple hubs as one property, and automations may span "
            "them. Each hub maintains its own mesh, and a device belongs to exactly one hub.",
            s["body"],
        ),
        _p(
            "In practice the radio mesh becomes the limiting factor before the device count "
            "does. Above roughly forty devices, Aurora Home recommends at least three "
            "mains-powered repeaters spread across the property.",
            s["body"],
        ),
        _p("8. Firmware updates", s["h1"]),
        _p(
            "The hub checks for firmware nightly and stages updates for connected devices. "
            "Thermostats update in place and are unavailable for roughly ninety seconds. "
            "Sensors update opportunistically when they next report, so a full property can "
            "take several days to converge — this is expected and needs no intervention.",
            s["body"],
        ),
        _p(
            "Updates cannot be rolled back. If an update introduces a problem in your specific "
            "installation, contact support rather than attempting to reflash a device.",
            s["body"],
        ),
        _p("9. Decommissioning", s["h1"]),
        _p(
            "Remove devices from the app before removing them from the wall. A device removed "
            "physically but left paired continues to occupy a slot against the 64-device limit "
            "and will be reported as unreachable. If you have already removed the hardware, the "
            "app offers a forced removal that clears the pairing from the hub's side.",
            s["body"],
        ),
        _p(
            "Factory-resetting the hub erases every pairing, all schedules and all automation "
            "history. There is no export, so record any complex schedule before resetting.",
            s["body"],
        ),
        _p("10. Commissioning several properties", s["h1"]),
        _p(
            "Installers commissioning a block of flats or a small estate should treat each "
            "dwelling as a separate property in the app rather than as zones of one large "
            "property. Zones within a property share holiday mode and share the device budget "
            "of their hub, neither of which is what you want across separate households. The "
            "extra work is a few minutes per dwelling at handover and saves an awkward "
            "migration later.",
            s["body"],
        ),
        _p(
            "Name devices for the room rather than the resident. Residents change; rooms do "
            "not, and a schedule that refers to a former tenant's name is confusing for whoever "
            "inherits it. Where a property has several identical rooms, add a floor prefix so "
            "that the sorted device list matches the order you would walk the building in.",
            s["body"],
        ),
        _p("10.1 Handover to the resident", s["h2"]),
        _p(
            "Hand over the hub identifier in writing and confirm the resident can sign in "
            "before you leave. An installer account that retains access after handover is a "
            "support liability: the resident cannot remove it themselves, and Aurora Home will "
            "not remove it on request without the installer's confirmation. Transfer ownership "
            "properly at handover rather than sharing a login.",
            s["body"],
        ),
        _p(
            "Leave the property with at least one schedule in place. A system with no schedule "
            "holds whatever setpoint was last entered, which after commissioning is usually a "
            "test value rather than something anyone wants to live with.",
            s["body"],
        ),
        _p("11. Maintenance", s["h1"]),
        _p(
            "Aurora Home devices need no scheduled servicing. Sensor batteries are the only "
            "consumable, and the app reports a low battery well before the device stops "
            "reporting. Replace with the specified cell type: rechargeable equivalents have a "
            "lower nominal voltage and the low-battery warning will fire almost immediately.",
            s["body"],
        ),
        _p(
            "Clean the thermostat with a dry cloth. Do not use solvents on the display bezel, "
            "and do not spray any cleaner directly at the unit — the vent slots on the underside "
            "feed the temperature sensor, and liquid drawn in there will skew readings long "
            "before it does any visible damage.",
            s["body"],
        ),
        _p("11.1 Seasonal checks", s["h2"]),
        _p(
            "Before the heating season, run each zone for ten minutes and confirm the expected "
            "radiators warm up. Zone valves that have sat unused all summer occasionally stick, "
            "and finding that in September is considerably better than finding it in December. "
            "The app's zone test does this in sequence and reports which zones responded.",
            s["body"],
        ),
        _p(
            "After the heating season, leave the system powered. Holiday mode and frost "
            "protection both depend on the hub being online, and a system switched off at the "
            "consumer unit protects nothing.",
            s["body"],
        ),
        _p("12. Glossary", s["h1"]),
        _p(
            "<b>Zone</b> — one thermostat and the sensors associated with it, sharing a single "
            "schedule. <b>Setpoint</b> — the target temperature from a given time until the next "
            "setpoint begins. <b>Repeater</b> — any mains-powered device that relays mesh "
            "traffic on behalf of others. <b>Leaf node</b> — a battery-powered device that does "
            "not relay. <b>Deadband</b> — the difference between the temperature at which "
            "heating starts and the temperature at which it stops, which prevents rapid "
            "cycling. <b>Interface module</b> — the AH-IM1 accessory, required where the boiler "
            "cannot be switched directly by the T3 relay.",
            s["body"],
        ),
    ]
    return story


def build(out_dir: Path) -> Path:
    return pdf_kit.build_pdf(
        out_dir / "aurora-installation-guide-en.pdf", TITLE, "Aurora Home", _story
    )
