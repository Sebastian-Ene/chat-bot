---
title: Aurora Home — Fehlercode-Referenz
subtitle: Vollständige Liste der Status- und Fehlercodes · Firmware 4.2.1
lang: de
format: pdf
layout: brief
---

# Aufbau der Codes

Jeder Code besteht aus einem Buchstaben für die Baugruppe und einer dreistelligen Nummer. Der Buchstabe entspricht der Familie, die Nummer der laufenden Meldung innerhalb der Familie. Codes werden in der App unter dem betroffenen Gerät angezeigt und im Ereignisprotokoll des Hubs mit Zeitstempel geführt.

Der Schweregrad steuert lediglich die Darstellung in der App. Auch ein Hinweis kann auf eine Ursache zeigen, die längerfristig behoben werden sollte.

# 1xx — Netzwerk und Anbindung

Der Hub konnte die Verbindung zum Dienst nicht herstellen oder verlor sie.

| Code | Meldung | Ursache | Massnahme | Schweregrad |
| --- | --- | --- | --- | --- |
| N101 | Kein Link am Netzwerkanschluss | Kabel oder Switch-Port defekt | Kabel an beiden Enden neu stecken | Hinweis |
| N102 | Kein Link am Netzwerkanschluss beim Start | Kabel oder Switch-Port defekt, unmittelbar nach dem Einschalten | Kabel an beiden Enden neu stecken | Warnung |
| N103 | Kein Link am Netzwerkanschluss im Betrieb | Kabel oder Switch-Port defekt, während des laufenden Betriebs | Kabel an beiden Enden neu stecken | Störung |
| N104 | Kein Link am Netzwerkanschluss nach Aktualisierung | Kabel oder Switch-Port defekt, erstmals nach einer Firmwareaktualisierung | Kabel an beiden Enden neu stecken | Kritisch |
| N105 | Kein Link am Netzwerkanschluss nach Stromausfall | Kabel oder Switch-Port defekt, nach einer Unterbrechung der Versorgung | Kabel an beiden Enden neu stecken | Hinweis |
| N106 | Kein Link am Netzwerkanschluss wiederholt | Kabel oder Switch-Port defekt, mehrfach innerhalb einer Stunde | Kabel an beiden Enden neu stecken | Warnung |
| N107 | Kein Link am Netzwerkanschluss sporadisch | Kabel oder Switch-Port defekt, unregelmäßig und ohne erkennbaren Auslöser | Kabel an beiden Enden neu stecken | Störung |
| N108 | Keine IP-Adresse erhalten | DHCP im Netz nicht erreichbar | Router prüfen, Hub neu starten | Warnung |
| N109 | Keine IP-Adresse erhalten beim Start | DHCP im Netz nicht erreichbar, unmittelbar nach dem Einschalten | Router prüfen, Hub neu starten | Störung |
| N110 | Keine IP-Adresse erhalten im Betrieb | DHCP im Netz nicht erreichbar, während des laufenden Betriebs | Router prüfen, Hub neu starten | Kritisch |
| N111 | Keine IP-Adresse erhalten nach Aktualisierung | DHCP im Netz nicht erreichbar, erstmals nach einer Firmwareaktualisierung | Router prüfen, Hub neu starten | Hinweis |
| N112 | Keine IP-Adresse erhalten nach Stromausfall | DHCP im Netz nicht erreichbar, nach einer Unterbrechung der Versorgung | Router prüfen, Hub neu starten | Warnung |
| N113 | Keine IP-Adresse erhalten wiederholt | DHCP im Netz nicht erreichbar, mehrfach innerhalb einer Stunde | Router prüfen, Hub neu starten | Störung |
| N114 | Keine IP-Adresse erhalten sporadisch | DHCP im Netz nicht erreichbar, unregelmäßig und ohne erkennbaren Auslöser | Router prüfen, Hub neu starten | Kritisch |
| N115 | DNS-Auflösung fehlgeschlagen | DNS-Server blockiert oder falsch | DNS des Routers prüfen | Störung |
| N116 | DNS-Auflösung fehlgeschlagen beim Start | DNS-Server blockiert oder falsch, unmittelbar nach dem Einschalten | DNS des Routers prüfen | Kritisch |
| N117 | DNS-Auflösung fehlgeschlagen im Betrieb | DNS-Server blockiert oder falsch, während des laufenden Betriebs | DNS des Routers prüfen | Hinweis |
| N118 | DNS-Auflösung fehlgeschlagen nach Aktualisierung | DNS-Server blockiert oder falsch, erstmals nach einer Firmwareaktualisierung | DNS des Routers prüfen | Warnung |
| N119 | DNS-Auflösung fehlgeschlagen nach Stromausfall | DNS-Server blockiert oder falsch, nach einer Unterbrechung der Versorgung | DNS des Routers prüfen | Störung |
| N120 | DNS-Auflösung fehlgeschlagen wiederholt | DNS-Server blockiert oder falsch, mehrfach innerhalb einer Stunde | DNS des Routers prüfen | Kritisch |
| N121 | DNS-Auflösung fehlgeschlagen sporadisch | DNS-Server blockiert oder falsch, unregelmäßig und ohne erkennbaren Auslöser | DNS des Routers prüfen | Hinweis |
| N122 | Zeitabgleich fehlgeschlagen | NTP ausgehend gesperrt | NTP freigeben | Kritisch |
| N123 | Zeitabgleich fehlgeschlagen beim Start | NTP ausgehend gesperrt, unmittelbar nach dem Einschalten | NTP freigeben | Hinweis |
| N124 | Zeitabgleich fehlgeschlagen im Betrieb | NTP ausgehend gesperrt, während des laufenden Betriebs | NTP freigeben | Warnung |
| N125 | Zeitabgleich fehlgeschlagen nach Aktualisierung | NTP ausgehend gesperrt, erstmals nach einer Firmwareaktualisierung | NTP freigeben | Störung |
| N126 | Zeitabgleich fehlgeschlagen nach Stromausfall | NTP ausgehend gesperrt, nach einer Unterbrechung der Versorgung | NTP freigeben | Kritisch |
| N127 | Zeitabgleich fehlgeschlagen wiederholt | NTP ausgehend gesperrt, mehrfach innerhalb einer Stunde | NTP freigeben | Hinweis |
| N128 | Zeitabgleich fehlgeschlagen sporadisch | NTP ausgehend gesperrt, unregelmäßig und ohne erkennbaren Auslöser | NTP freigeben | Warnung |
| N129 | TLS-Handschlag abgebrochen | Uhrzeit des Hubs weicht zu stark ab | Zeitabgleich zulassen | Hinweis |
| N130 | TLS-Handschlag abgebrochen beim Start | Uhrzeit des Hubs weicht zu stark ab, unmittelbar nach dem Einschalten | Zeitabgleich zulassen | Warnung |
| N131 | TLS-Handschlag abgebrochen im Betrieb | Uhrzeit des Hubs weicht zu stark ab, während des laufenden Betriebs | Zeitabgleich zulassen | Störung |
| N132 | TLS-Handschlag abgebrochen nach Aktualisierung | Uhrzeit des Hubs weicht zu stark ab, erstmals nach einer Firmwareaktualisierung | Zeitabgleich zulassen | Kritisch |
| N133 | TLS-Handschlag abgebrochen nach Stromausfall | Uhrzeit des Hubs weicht zu stark ab, nach einer Unterbrechung der Versorgung | Zeitabgleich zulassen | Hinweis |
| N134 | TLS-Handschlag abgebrochen wiederholt | Uhrzeit des Hubs weicht zu stark ab, mehrfach innerhalb einer Stunde | Zeitabgleich zulassen | Warnung |
| N135 | TLS-Handschlag abgebrochen sporadisch | Uhrzeit des Hubs weicht zu stark ab, unregelmäßig und ohne erkennbaren Auslöser | Zeitabgleich zulassen | Störung |
| N136 | Verbindung zum Dienst abgelehnt | Ausgehender Port 443 gesperrt | Firewallregel ergänzen | Warnung |
| N137 | Verbindung zum Dienst abgelehnt beim Start | Ausgehender Port 443 gesperrt, unmittelbar nach dem Einschalten | Firewallregel ergänzen | Störung |
| N138 | Verbindung zum Dienst abgelehnt im Betrieb | Ausgehender Port 443 gesperrt, während des laufenden Betriebs | Firewallregel ergänzen | Kritisch |
| N139 | Verbindung zum Dienst abgelehnt nach Aktualisierung | Ausgehender Port 443 gesperrt, erstmals nach einer Firmwareaktualisierung | Firewallregel ergänzen | Hinweis |
| N140 | Verbindung zum Dienst abgelehnt nach Stromausfall | Ausgehender Port 443 gesperrt, nach einer Unterbrechung der Versorgung | Firewallregel ergänzen | Warnung |
| N141 | Verbindung zum Dienst abgelehnt wiederholt | Ausgehender Port 443 gesperrt, mehrfach innerhalb einer Stunde | Firewallregel ergänzen | Störung |
| N142 | Verbindung zum Dienst abgelehnt sporadisch | Ausgehender Port 443 gesperrt, unregelmäßig und ohne erkennbaren Auslöser | Firewallregel ergänzen | Kritisch |
| N143 | Verbindung wiederholt getrennt | Instabile Uplink-Strecke | Verkabelung und Switch prüfen | Störung |
| N144 | Verbindung wiederholt getrennt beim Start | Instabile Uplink-Strecke, unmittelbar nach dem Einschalten | Verkabelung und Switch prüfen | Kritisch |
| N145 | Verbindung wiederholt getrennt im Betrieb | Instabile Uplink-Strecke, während des laufenden Betriebs | Verkabelung und Switch prüfen | Hinweis |
| N146 | Verbindung wiederholt getrennt nach Aktualisierung | Instabile Uplink-Strecke, erstmals nach einer Firmwareaktualisierung | Verkabelung und Switch prüfen | Warnung |
| N147 | Verbindung wiederholt getrennt nach Stromausfall | Instabile Uplink-Strecke, nach einer Unterbrechung der Versorgung | Verkabelung und Switch prüfen | Störung |
| N148 | Verbindung wiederholt getrennt wiederholt | Instabile Uplink-Strecke, mehrfach innerhalb einer Stunde | Verkabelung und Switch prüfen | Kritisch |
| N149 | Verbindung wiederholt getrennt sporadisch | Instabile Uplink-Strecke, unregelmäßig und ohne erkennbaren Auslöser | Verkabelung und Switch prüfen | Hinweis |
| N150 | Gastnetz erkannt | Client-Isolierung aktiv | Hub in das reguläre Netz umhängen | Kritisch |
| N151 | Gastnetz erkannt beim Start | Client-Isolierung aktiv, unmittelbar nach dem Einschalten | Hub in das reguläre Netz umhängen | Hinweis |
| N152 | Gastnetz erkannt im Betrieb | Client-Isolierung aktiv, während des laufenden Betriebs | Hub in das reguläre Netz umhängen | Warnung |
| N153 | Gastnetz erkannt nach Aktualisierung | Client-Isolierung aktiv, erstmals nach einer Firmwareaktualisierung | Hub in das reguläre Netz umhängen | Störung |
| N154 | Gastnetz erkannt nach Stromausfall | Client-Isolierung aktiv, nach einer Unterbrechung der Versorgung | Hub in das reguläre Netz umhängen | Kritisch |
| N155 | Gastnetz erkannt wiederholt | Client-Isolierung aktiv, mehrfach innerhalb einer Stunde | Hub in das reguläre Netz umhängen | Hinweis |
| N156 | Gastnetz erkannt sporadisch | Client-Isolierung aktiv, unregelmäßig und ohne erkennbaren Auslöser | Hub in das reguläre Netz umhängen | Warnung |
| N157 | Doppelte IP-Adresse erkannt | Statische Adresse kollidiert | Adressvergabe bereinigen | Hinweis |
| N158 | Doppelte IP-Adresse erkannt beim Start | Statische Adresse kollidiert, unmittelbar nach dem Einschalten | Adressvergabe bereinigen | Warnung |
| N159 | Doppelte IP-Adresse erkannt im Betrieb | Statische Adresse kollidiert, während des laufenden Betriebs | Adressvergabe bereinigen | Störung |
| N160 | Doppelte IP-Adresse erkannt nach Aktualisierung | Statische Adresse kollidiert, erstmals nach einer Firmwareaktualisierung | Adressvergabe bereinigen | Kritisch |
| N161 | Doppelte IP-Adresse erkannt nach Stromausfall | Statische Adresse kollidiert, nach einer Unterbrechung der Versorgung | Adressvergabe bereinigen | Hinweis |
| N162 | Doppelte IP-Adresse erkannt wiederholt | Statische Adresse kollidiert, mehrfach innerhalb einer Stunde | Adressvergabe bereinigen | Warnung |
| N163 | Doppelte IP-Adresse erkannt sporadisch | Statische Adresse kollidiert, unregelmäßig und ohne erkennbaren Auslöser | Adressvergabe bereinigen | Störung |
| N164 | Proxy-Antwort unerwartet | Aufbrechendes TLS im Netz | Hub von der Aufbrechung ausnehmen | Warnung |
| N165 | Proxy-Antwort unerwartet beim Start | Aufbrechendes TLS im Netz, unmittelbar nach dem Einschalten | Hub von der Aufbrechung ausnehmen | Störung |
| N166 | Proxy-Antwort unerwartet im Betrieb | Aufbrechendes TLS im Netz, während des laufenden Betriebs | Hub von der Aufbrechung ausnehmen | Kritisch |
| N167 | Proxy-Antwort unerwartet nach Aktualisierung | Aufbrechendes TLS im Netz, erstmals nach einer Firmwareaktualisierung | Hub von der Aufbrechung ausnehmen | Hinweis |
| N168 | Proxy-Antwort unerwartet nach Stromausfall | Aufbrechendes TLS im Netz, nach einer Unterbrechung der Versorgung | Hub von der Aufbrechung ausnehmen | Warnung |
| N169 | Proxy-Antwort unerwartet wiederholt | Aufbrechendes TLS im Netz, mehrfach innerhalb einer Stunde | Hub von der Aufbrechung ausnehmen | Störung |
| N170 | Proxy-Antwort unerwartet sporadisch | Aufbrechendes TLS im Netz, unregelmäßig und ohne erkennbaren Auslöser | Hub von der Aufbrechung ausnehmen | Kritisch |

# 2xx — Funk und Mesh

Fehler der Funkstrecke zwischen Hub, Repeatern und Endgeräten.

| Code | Meldung | Ursache | Massnahme | Schweregrad |
| --- | --- | --- | --- | --- |
| F201 | Gerät antwortet nicht | Funkstrecke zu lang | Netzbetriebenes Gerät dazwischen setzen | Hinweis |
| F202 | Gerät antwortet nicht beim Start | Funkstrecke zu lang, unmittelbar nach dem Einschalten | Netzbetriebenes Gerät dazwischen setzen | Warnung |
| F203 | Gerät antwortet nicht im Betrieb | Funkstrecke zu lang, während des laufenden Betriebs | Netzbetriebenes Gerät dazwischen setzen | Störung |
| F204 | Gerät antwortet nicht nach Aktualisierung | Funkstrecke zu lang, erstmals nach einer Firmwareaktualisierung | Netzbetriebenes Gerät dazwischen setzen | Kritisch |
| F205 | Gerät antwortet nicht nach Stromausfall | Funkstrecke zu lang, nach einer Unterbrechung der Versorgung | Netzbetriebenes Gerät dazwischen setzen | Hinweis |
| F206 | Gerät antwortet nicht wiederholt | Funkstrecke zu lang, mehrfach innerhalb einer Stunde | Netzbetriebenes Gerät dazwischen setzen | Warnung |
| F207 | Gerät antwortet nicht sporadisch | Funkstrecke zu lang, unregelmäßig und ohne erkennbaren Auslöser | Netzbetriebenes Gerät dazwischen setzen | Störung |
| F208 | Kopplung abgebrochen | Zeitfenster überschritten | Kopplung erneut starten | Warnung |
| F209 | Kopplung abgebrochen beim Start | Zeitfenster überschritten, unmittelbar nach dem Einschalten | Kopplung erneut starten | Störung |
| F210 | Kopplung abgebrochen im Betrieb | Zeitfenster überschritten, während des laufenden Betriebs | Kopplung erneut starten | Kritisch |
| F211 | Kopplung abgebrochen nach Aktualisierung | Zeitfenster überschritten, erstmals nach einer Firmwareaktualisierung | Kopplung erneut starten | Hinweis |
| F212 | Kopplung abgebrochen nach Stromausfall | Zeitfenster überschritten, nach einer Unterbrechung der Versorgung | Kopplung erneut starten | Warnung |
| F213 | Kopplung abgebrochen wiederholt | Zeitfenster überschritten, mehrfach innerhalb einer Stunde | Kopplung erneut starten | Störung |
| F214 | Kopplung abgebrochen sporadisch | Zeitfenster überschritten, unregelmäßig und ohne erkennbaren Auslöser | Kopplung erneut starten | Kritisch |
| F215 | Gerät bereits gekoppelt | Kopplung an anderem Hub aktiv | Gerät zuerst entkoppeln | Störung |
| F216 | Gerät bereits gekoppelt beim Start | Kopplung an anderem Hub aktiv, unmittelbar nach dem Einschalten | Gerät zuerst entkoppeln | Kritisch |
| F217 | Gerät bereits gekoppelt im Betrieb | Kopplung an anderem Hub aktiv, während des laufenden Betriebs | Gerät zuerst entkoppeln | Hinweis |
| F218 | Gerät bereits gekoppelt nach Aktualisierung | Kopplung an anderem Hub aktiv, erstmals nach einer Firmwareaktualisierung | Gerät zuerst entkoppeln | Warnung |
| F219 | Gerät bereits gekoppelt nach Stromausfall | Kopplung an anderem Hub aktiv, nach einer Unterbrechung der Versorgung | Gerät zuerst entkoppeln | Störung |
| F220 | Gerät bereits gekoppelt wiederholt | Kopplung an anderem Hub aktiv, mehrfach innerhalb einer Stunde | Gerät zuerst entkoppeln | Kritisch |
| F221 | Gerät bereits gekoppelt sporadisch | Kopplung an anderem Hub aktiv, unregelmäßig und ohne erkennbaren Auslöser | Gerät zuerst entkoppeln | Hinweis |
| F222 | Signalqualität unzureichend | Dämpfung durch Baustoffe | Standort ändern oder Repeater ergänzen | Kritisch |
| F223 | Signalqualität unzureichend beim Start | Dämpfung durch Baustoffe, unmittelbar nach dem Einschalten | Standort ändern oder Repeater ergänzen | Hinweis |
| F224 | Signalqualität unzureichend im Betrieb | Dämpfung durch Baustoffe, während des laufenden Betriebs | Standort ändern oder Repeater ergänzen | Warnung |
| F225 | Signalqualität unzureichend nach Aktualisierung | Dämpfung durch Baustoffe, erstmals nach einer Firmwareaktualisierung | Standort ändern oder Repeater ergänzen | Störung |
| F226 | Signalqualität unzureichend nach Stromausfall | Dämpfung durch Baustoffe, nach einer Unterbrechung der Versorgung | Standort ändern oder Repeater ergänzen | Kritisch |
| F227 | Signalqualität unzureichend wiederholt | Dämpfung durch Baustoffe, mehrfach innerhalb einer Stunde | Standort ändern oder Repeater ergänzen | Hinweis |
| F228 | Signalqualität unzureichend sporadisch | Dämpfung durch Baustoffe, unregelmäßig und ohne erkennbaren Auslöser | Standort ändern oder Repeater ergänzen | Warnung |
| F229 | Mesh konvergiert nicht | Zu wenige Repeater | Netzbetriebene Geräte ergänzen | Hinweis |
| F230 | Mesh konvergiert nicht beim Start | Zu wenige Repeater, unmittelbar nach dem Einschalten | Netzbetriebene Geräte ergänzen | Warnung |
| F231 | Mesh konvergiert nicht im Betrieb | Zu wenige Repeater, während des laufenden Betriebs | Netzbetriebene Geräte ergänzen | Störung |
| F232 | Mesh konvergiert nicht nach Aktualisierung | Zu wenige Repeater, erstmals nach einer Firmwareaktualisierung | Netzbetriebene Geräte ergänzen | Kritisch |
| F233 | Mesh konvergiert nicht nach Stromausfall | Zu wenige Repeater, nach einer Unterbrechung der Versorgung | Netzbetriebene Geräte ergänzen | Hinweis |
| F234 | Mesh konvergiert nicht wiederholt | Zu wenige Repeater, mehrfach innerhalb einer Stunde | Netzbetriebene Geräte ergänzen | Warnung |
| F235 | Mesh konvergiert nicht sporadisch | Zu wenige Repeater, unregelmäßig und ohne erkennbaren Auslöser | Netzbetriebene Geräte ergänzen | Störung |
| F236 | Kanalwechsel erforderlich | Störquelle auf dem Kanal | Automatischen Kanalwechsel abwarten | Warnung |
| F237 | Kanalwechsel erforderlich beim Start | Störquelle auf dem Kanal, unmittelbar nach dem Einschalten | Automatischen Kanalwechsel abwarten | Störung |
| F238 | Kanalwechsel erforderlich im Betrieb | Störquelle auf dem Kanal, während des laufenden Betriebs | Automatischen Kanalwechsel abwarten | Kritisch |
| F239 | Kanalwechsel erforderlich nach Aktualisierung | Störquelle auf dem Kanal, erstmals nach einer Firmwareaktualisierung | Automatischen Kanalwechsel abwarten | Hinweis |
| F240 | Kanalwechsel erforderlich nach Stromausfall | Störquelle auf dem Kanal, nach einer Unterbrechung der Versorgung | Automatischen Kanalwechsel abwarten | Warnung |
| F241 | Kanalwechsel erforderlich wiederholt | Störquelle auf dem Kanal, mehrfach innerhalb einer Stunde | Automatischen Kanalwechsel abwarten | Störung |
| F242 | Kanalwechsel erforderlich sporadisch | Störquelle auf dem Kanal, unregelmäßig und ohne erkennbaren Auslöser | Automatischen Kanalwechsel abwarten | Kritisch |
| F243 | Paketverlust erhöht | Störung durch Fremdanlage | Abstand zu Fremdgeräten vergrößern | Störung |
| F244 | Paketverlust erhöht beim Start | Störung durch Fremdanlage, unmittelbar nach dem Einschalten | Abstand zu Fremdgeräten vergrößern | Kritisch |
| F245 | Paketverlust erhöht im Betrieb | Störung durch Fremdanlage, während des laufenden Betriebs | Abstand zu Fremdgeräten vergrößern | Hinweis |
| F246 | Paketverlust erhöht nach Aktualisierung | Störung durch Fremdanlage, erstmals nach einer Firmwareaktualisierung | Abstand zu Fremdgeräten vergrößern | Warnung |
| F247 | Paketverlust erhöht nach Stromausfall | Störung durch Fremdanlage, nach einer Unterbrechung der Versorgung | Abstand zu Fremdgeräten vergrößern | Störung |
| F248 | Paketverlust erhöht wiederholt | Störung durch Fremdanlage, mehrfach innerhalb einer Stunde | Abstand zu Fremdgeräten vergrößern | Kritisch |
| F249 | Paketverlust erhöht sporadisch | Störung durch Fremdanlage, unregelmäßig und ohne erkennbaren Auslöser | Abstand zu Fremdgeräten vergrößern | Hinweis |
| F250 | Kapazitätsgrenze erreicht | 64 Geräte je Hub überschritten | Zweiten Hub einsetzen | Kritisch |
| F251 | Kapazitätsgrenze erreicht beim Start | 64 Geräte je Hub überschritten, unmittelbar nach dem Einschalten | Zweiten Hub einsetzen | Hinweis |
| F252 | Kapazitätsgrenze erreicht im Betrieb | 64 Geräte je Hub überschritten, während des laufenden Betriebs | Zweiten Hub einsetzen | Warnung |
| F253 | Kapazitätsgrenze erreicht nach Aktualisierung | 64 Geräte je Hub überschritten, erstmals nach einer Firmwareaktualisierung | Zweiten Hub einsetzen | Störung |
| F254 | Kapazitätsgrenze erreicht nach Stromausfall | 64 Geräte je Hub überschritten, nach einer Unterbrechung der Versorgung | Zweiten Hub einsetzen | Kritisch |
| F255 | Kapazitätsgrenze erreicht wiederholt | 64 Geräte je Hub überschritten, mehrfach innerhalb einer Stunde | Zweiten Hub einsetzen | Hinweis |
| F256 | Kapazitätsgrenze erreicht sporadisch | 64 Geräte je Hub überschritten, unregelmäßig und ohne erkennbaren Auslöser | Zweiten Hub einsetzen | Warnung |
| F257 | Endknoten meldet verspätet | Batteriespannung niedrig | Batterie wechseln | Hinweis |
| F258 | Endknoten meldet verspätet beim Start | Batteriespannung niedrig, unmittelbar nach dem Einschalten | Batterie wechseln | Warnung |
| F259 | Endknoten meldet verspätet im Betrieb | Batteriespannung niedrig, während des laufenden Betriebs | Batterie wechseln | Störung |
| F260 | Endknoten meldet verspätet nach Aktualisierung | Batteriespannung niedrig, erstmals nach einer Firmwareaktualisierung | Batterie wechseln | Kritisch |
| F261 | Endknoten meldet verspätet nach Stromausfall | Batteriespannung niedrig, nach einer Unterbrechung der Versorgung | Batterie wechseln | Hinweis |
| F262 | Endknoten meldet verspätet wiederholt | Batteriespannung niedrig, mehrfach innerhalb einer Stunde | Batterie wechseln | Warnung |
| F263 | Endknoten meldet verspätet sporadisch | Batteriespannung niedrig, unregelmäßig und ohne erkennbaren Auslöser | Batterie wechseln | Störung |
| F264 | Firmware des Geräts zu alt | Aktualisierung ausstehend | Aktualisierung abwarten | Warnung |
| F265 | Firmware des Geräts zu alt beim Start | Aktualisierung ausstehend, unmittelbar nach dem Einschalten | Aktualisierung abwarten | Störung |
| F266 | Firmware des Geräts zu alt im Betrieb | Aktualisierung ausstehend, während des laufenden Betriebs | Aktualisierung abwarten | Kritisch |
| F267 | Firmware des Geräts zu alt nach Aktualisierung | Aktualisierung ausstehend, erstmals nach einer Firmwareaktualisierung | Aktualisierung abwarten | Hinweis |
| F268 | Firmware des Geräts zu alt nach Stromausfall | Aktualisierung ausstehend, nach einer Unterbrechung der Versorgung | Aktualisierung abwarten | Warnung |
| F269 | Firmware des Geräts zu alt wiederholt | Aktualisierung ausstehend, mehrfach innerhalb einer Stunde | Aktualisierung abwarten | Störung |
| F270 | Firmware des Geräts zu alt sporadisch | Aktualisierung ausstehend, unregelmäßig und ohne erkennbaren Auslöser | Aktualisierung abwarten | Kritisch |

# 3xx — Heizungsansteuerung

Fehler bei der Ansteuerung des Wärmeerzeugers oder der Ventile.

| Code | Meldung | Ursache | Massnahme | Schweregrad |
| --- | --- | --- | --- | --- |
| H301 | Kein Heizbedarf trotz Sollwert | Mindestzykluszeit aktiv | Zykluszeit prüfen | Hinweis |
| H302 | Kein Heizbedarf trotz Sollwert beim Start | Mindestzykluszeit aktiv, unmittelbar nach dem Einschalten | Zykluszeit prüfen | Warnung |
| H303 | Kein Heizbedarf trotz Sollwert im Betrieb | Mindestzykluszeit aktiv, während des laufenden Betriebs | Zykluszeit prüfen | Störung |
| H304 | Kein Heizbedarf trotz Sollwert nach Aktualisierung | Mindestzykluszeit aktiv, erstmals nach einer Firmwareaktualisierung | Zykluszeit prüfen | Kritisch |
| H305 | Kein Heizbedarf trotz Sollwert nach Stromausfall | Mindestzykluszeit aktiv, nach einer Unterbrechung der Versorgung | Zykluszeit prüfen | Hinweis |
| H306 | Kein Heizbedarf trotz Sollwert wiederholt | Mindestzykluszeit aktiv, mehrfach innerhalb einer Stunde | Zykluszeit prüfen | Warnung |
| H307 | Kein Heizbedarf trotz Sollwert sporadisch | Mindestzykluszeit aktiv, unregelmäßig und ohne erkennbaren Auslöser | Zykluszeit prüfen | Störung |
| H308 | Relais schaltet nicht | Kontakt verschlissen | Gerät tauschen | Warnung |
| H309 | Relais schaltet nicht beim Start | Kontakt verschlissen, unmittelbar nach dem Einschalten | Gerät tauschen | Störung |
| H310 | Relais schaltet nicht im Betrieb | Kontakt verschlissen, während des laufenden Betriebs | Gerät tauschen | Kritisch |
| H311 | Relais schaltet nicht nach Aktualisierung | Kontakt verschlissen, erstmals nach einer Firmwareaktualisierung | Gerät tauschen | Hinweis |
| H312 | Relais schaltet nicht nach Stromausfall | Kontakt verschlissen, nach einer Unterbrechung der Versorgung | Gerät tauschen | Warnung |
| H313 | Relais schaltet nicht wiederholt | Kontakt verschlissen, mehrfach innerhalb einer Stunde | Gerät tauschen | Störung |
| H314 | Relais schaltet nicht sporadisch | Kontakt verschlissen, unregelmäßig und ohne erkennbaren Auslöser | Gerät tauschen | Kritisch |
| H315 | OpenTherm-Antwort ungültig | Gerät unterstützt Modulation nicht | Auf Ein-Aus-Betrieb umstellen | Störung |
| H316 | OpenTherm-Antwort ungültig beim Start | Gerät unterstützt Modulation nicht, unmittelbar nach dem Einschalten | Auf Ein-Aus-Betrieb umstellen | Kritisch |
| H317 | OpenTherm-Antwort ungültig im Betrieb | Gerät unterstützt Modulation nicht, während des laufenden Betriebs | Auf Ein-Aus-Betrieb umstellen | Hinweis |
| H318 | OpenTherm-Antwort ungültig nach Aktualisierung | Gerät unterstützt Modulation nicht, erstmals nach einer Firmwareaktualisierung | Auf Ein-Aus-Betrieb umstellen | Warnung |
| H319 | OpenTherm-Antwort ungültig nach Stromausfall | Gerät unterstützt Modulation nicht, nach einer Unterbrechung der Versorgung | Auf Ein-Aus-Betrieb umstellen | Störung |
| H320 | OpenTherm-Antwort ungültig wiederholt | Gerät unterstützt Modulation nicht, mehrfach innerhalb einer Stunde | Auf Ein-Aus-Betrieb umstellen | Kritisch |
| H321 | OpenTherm-Antwort ungültig sporadisch | Gerät unterstützt Modulation nicht, unregelmäßig und ohne erkennbaren Auslöser | Auf Ein-Aus-Betrieb umstellen | Hinweis |
| H322 | Ventil meldet keine Rückmeldung | Aktor nicht verbunden | Verdrahtung des Aktors prüfen | Kritisch |
| H323 | Ventil meldet keine Rückmeldung beim Start | Aktor nicht verbunden, unmittelbar nach dem Einschalten | Verdrahtung des Aktors prüfen | Hinweis |
| H324 | Ventil meldet keine Rückmeldung im Betrieb | Aktor nicht verbunden, während des laufenden Betriebs | Verdrahtung des Aktors prüfen | Warnung |
| H325 | Ventil meldet keine Rückmeldung nach Aktualisierung | Aktor nicht verbunden, erstmals nach einer Firmwareaktualisierung | Verdrahtung des Aktors prüfen | Störung |
| H326 | Ventil meldet keine Rückmeldung nach Stromausfall | Aktor nicht verbunden, nach einer Unterbrechung der Versorgung | Verdrahtung des Aktors prüfen | Kritisch |
| H327 | Ventil meldet keine Rückmeldung wiederholt | Aktor nicht verbunden, mehrfach innerhalb einer Stunde | Verdrahtung des Aktors prüfen | Hinweis |
| H328 | Ventil meldet keine Rückmeldung sporadisch | Aktor nicht verbunden, unregelmäßig und ohne erkennbaren Auslöser | Verdrahtung des Aktors prüfen | Warnung |
| H329 | Schnittstellenmodul nicht erkannt | AH-IM1 nicht versorgt | Versorgung des Moduls prüfen | Hinweis |
| H330 | Schnittstellenmodul nicht erkannt beim Start | AH-IM1 nicht versorgt, unmittelbar nach dem Einschalten | Versorgung des Moduls prüfen | Warnung |
| H331 | Schnittstellenmodul nicht erkannt im Betrieb | AH-IM1 nicht versorgt, während des laufenden Betriebs | Versorgung des Moduls prüfen | Störung |
| H332 | Schnittstellenmodul nicht erkannt nach Aktualisierung | AH-IM1 nicht versorgt, erstmals nach einer Firmwareaktualisierung | Versorgung des Moduls prüfen | Kritisch |
| H333 | Schnittstellenmodul nicht erkannt nach Stromausfall | AH-IM1 nicht versorgt, nach einer Unterbrechung der Versorgung | Versorgung des Moduls prüfen | Hinweis |
| H334 | Schnittstellenmodul nicht erkannt wiederholt | AH-IM1 nicht versorgt, mehrfach innerhalb einer Stunde | Versorgung des Moduls prüfen | Warnung |
| H335 | Schnittstellenmodul nicht erkannt sporadisch | AH-IM1 nicht versorgt, unregelmäßig und ohne erkennbaren Auslöser | Versorgung des Moduls prüfen | Störung |
| H336 | Sicherheitsverriegelung offen | Interlock des Kessels aktiv | Kesselstörung beheben | Warnung |
| H337 | Sicherheitsverriegelung offen beim Start | Interlock des Kessels aktiv, unmittelbar nach dem Einschalten | Kesselstörung beheben | Störung |
| H338 | Sicherheitsverriegelung offen im Betrieb | Interlock des Kessels aktiv, während des laufenden Betriebs | Kesselstörung beheben | Kritisch |
| H339 | Sicherheitsverriegelung offen nach Aktualisierung | Interlock des Kessels aktiv, erstmals nach einer Firmwareaktualisierung | Kesselstörung beheben | Hinweis |
| H340 | Sicherheitsverriegelung offen nach Stromausfall | Interlock des Kessels aktiv, nach einer Unterbrechung der Versorgung | Kesselstörung beheben | Warnung |
| H341 | Sicherheitsverriegelung offen wiederholt | Interlock des Kessels aktiv, mehrfach innerhalb einer Stunde | Kesselstörung beheben | Störung |
| H342 | Sicherheitsverriegelung offen sporadisch | Interlock des Kessels aktiv, unregelmäßig und ohne erkennbaren Auslöser | Kesselstörung beheben | Kritisch |
| H343 | Vorlauftemperatur nicht plausibel | Fühler falsch platziert | Fühlerposition korrigieren | Störung |
| H344 | Vorlauftemperatur nicht plausibel beim Start | Fühler falsch platziert, unmittelbar nach dem Einschalten | Fühlerposition korrigieren | Kritisch |
| H345 | Vorlauftemperatur nicht plausibel im Betrieb | Fühler falsch platziert, während des laufenden Betriebs | Fühlerposition korrigieren | Hinweis |
| H346 | Vorlauftemperatur nicht plausibel nach Aktualisierung | Fühler falsch platziert, erstmals nach einer Firmwareaktualisierung | Fühlerposition korrigieren | Warnung |
| H347 | Vorlauftemperatur nicht plausibel nach Stromausfall | Fühler falsch platziert, nach einer Unterbrechung der Versorgung | Fühlerposition korrigieren | Störung |
| H348 | Vorlauftemperatur nicht plausibel wiederholt | Fühler falsch platziert, mehrfach innerhalb einer Stunde | Fühlerposition korrigieren | Kritisch |
| H349 | Vorlauftemperatur nicht plausibel sporadisch | Fühler falsch platziert, unregelmäßig und ohne erkennbaren Auslöser | Fühlerposition korrigieren | Hinweis |
| H350 | 0–10 V ausserhalb des Bereichs | Stellbereich falsch konfiguriert | Stellbereich in der App setzen | Kritisch |
| H351 | 0–10 V ausserhalb des Bereichs beim Start | Stellbereich falsch konfiguriert, unmittelbar nach dem Einschalten | Stellbereich in der App setzen | Hinweis |
| H352 | 0–10 V ausserhalb des Bereichs im Betrieb | Stellbereich falsch konfiguriert, während des laufenden Betriebs | Stellbereich in der App setzen | Warnung |
| H353 | 0–10 V ausserhalb des Bereichs nach Aktualisierung | Stellbereich falsch konfiguriert, erstmals nach einer Firmwareaktualisierung | Stellbereich in der App setzen | Störung |
| H354 | 0–10 V ausserhalb des Bereichs nach Stromausfall | Stellbereich falsch konfiguriert, nach einer Unterbrechung der Versorgung | Stellbereich in der App setzen | Kritisch |
| H355 | 0–10 V ausserhalb des Bereichs wiederholt | Stellbereich falsch konfiguriert, mehrfach innerhalb einer Stunde | Stellbereich in der App setzen | Hinweis |
| H356 | 0–10 V ausserhalb des Bereichs sporadisch | Stellbereich falsch konfiguriert, unregelmäßig und ohne erkennbaren Auslöser | Stellbereich in der App setzen | Warnung |
| H357 | Pumpe läuft nach | Nachlauf des Kessels | Kein Eingriff erforderlich | Hinweis |
| H358 | Pumpe läuft nach beim Start | Nachlauf des Kessels, unmittelbar nach dem Einschalten | Kein Eingriff erforderlich | Warnung |
| H359 | Pumpe läuft nach im Betrieb | Nachlauf des Kessels, während des laufenden Betriebs | Kein Eingriff erforderlich | Störung |
| H360 | Pumpe läuft nach nach Aktualisierung | Nachlauf des Kessels, erstmals nach einer Firmwareaktualisierung | Kein Eingriff erforderlich | Kritisch |
| H361 | Pumpe läuft nach nach Stromausfall | Nachlauf des Kessels, nach einer Unterbrechung der Versorgung | Kein Eingriff erforderlich | Hinweis |
| H362 | Pumpe läuft nach wiederholt | Nachlauf des Kessels, mehrfach innerhalb einer Stunde | Kein Eingriff erforderlich | Warnung |
| H363 | Pumpe läuft nach sporadisch | Nachlauf des Kessels, unregelmäßig und ohne erkennbaren Auslöser | Kein Eingriff erforderlich | Störung |
| H364 | Zone reagiert nicht auf Zonentest | Ventil sitzt fest | Ventil mechanisch gängig machen | Warnung |
| H365 | Zone reagiert nicht auf Zonentest beim Start | Ventil sitzt fest, unmittelbar nach dem Einschalten | Ventil mechanisch gängig machen | Störung |
| H366 | Zone reagiert nicht auf Zonentest im Betrieb | Ventil sitzt fest, während des laufenden Betriebs | Ventil mechanisch gängig machen | Kritisch |
| H367 | Zone reagiert nicht auf Zonentest nach Aktualisierung | Ventil sitzt fest, erstmals nach einer Firmwareaktualisierung | Ventil mechanisch gängig machen | Hinweis |
| H368 | Zone reagiert nicht auf Zonentest nach Stromausfall | Ventil sitzt fest, nach einer Unterbrechung der Versorgung | Ventil mechanisch gängig machen | Warnung |
| H369 | Zone reagiert nicht auf Zonentest wiederholt | Ventil sitzt fest, mehrfach innerhalb einer Stunde | Ventil mechanisch gängig machen | Störung |
| H370 | Zone reagiert nicht auf Zonentest sporadisch | Ventil sitzt fest, unregelmäßig und ohne erkennbaren Auslöser | Ventil mechanisch gängig machen | Kritisch |

# 4xx — Sensorik

Fehler der Messwerterfassung an Thermostat und Sensor.

| Code | Meldung | Ursache | Massnahme | Schweregrad |
| --- | --- | --- | --- | --- |
| S401 | Messwert unplausibel | Fremdwärme am Montageort | Montageort ändern | Hinweis |
| S402 | Messwert unplausibel beim Start | Fremdwärme am Montageort, unmittelbar nach dem Einschalten | Montageort ändern | Warnung |
| S403 | Messwert unplausibel im Betrieb | Fremdwärme am Montageort, während des laufenden Betriebs | Montageort ändern | Störung |
| S404 | Messwert unplausibel nach Aktualisierung | Fremdwärme am Montageort, erstmals nach einer Firmwareaktualisierung | Montageort ändern | Kritisch |
| S405 | Messwert unplausibel nach Stromausfall | Fremdwärme am Montageort, nach einer Unterbrechung der Versorgung | Montageort ändern | Hinweis |
| S406 | Messwert unplausibel wiederholt | Fremdwärme am Montageort, mehrfach innerhalb einer Stunde | Montageort ändern | Warnung |
| S407 | Messwert unplausibel sporadisch | Fremdwärme am Montageort, unregelmäßig und ohne erkennbaren Auslöser | Montageort ändern | Störung |
| S408 | Kein Messwert empfangen | Sensor offline | Batterie und Funkstrecke prüfen | Warnung |
| S409 | Kein Messwert empfangen beim Start | Sensor offline, unmittelbar nach dem Einschalten | Batterie und Funkstrecke prüfen | Störung |
| S410 | Kein Messwert empfangen im Betrieb | Sensor offline, während des laufenden Betriebs | Batterie und Funkstrecke prüfen | Kritisch |
| S411 | Kein Messwert empfangen nach Aktualisierung | Sensor offline, erstmals nach einer Firmwareaktualisierung | Batterie und Funkstrecke prüfen | Hinweis |
| S412 | Kein Messwert empfangen nach Stromausfall | Sensor offline, nach einer Unterbrechung der Versorgung | Batterie und Funkstrecke prüfen | Warnung |
| S413 | Kein Messwert empfangen wiederholt | Sensor offline, mehrfach innerhalb einer Stunde | Batterie und Funkstrecke prüfen | Störung |
| S414 | Kein Messwert empfangen sporadisch | Sensor offline, unregelmäßig und ohne erkennbaren Auslöser | Batterie und Funkstrecke prüfen | Kritisch |
| S415 | Kontakt meldet dauerhaft offen | Magnetabstand zu groß | Magnet näher setzen | Störung |
| S416 | Kontakt meldet dauerhaft offen beim Start | Magnetabstand zu groß, unmittelbar nach dem Einschalten | Magnet näher setzen | Kritisch |
| S417 | Kontakt meldet dauerhaft offen im Betrieb | Magnetabstand zu groß, während des laufenden Betriebs | Magnet näher setzen | Hinweis |
| S418 | Kontakt meldet dauerhaft offen nach Aktualisierung | Magnetabstand zu groß, erstmals nach einer Firmwareaktualisierung | Magnet näher setzen | Warnung |
| S419 | Kontakt meldet dauerhaft offen nach Stromausfall | Magnetabstand zu groß, nach einer Unterbrechung der Versorgung | Magnet näher setzen | Störung |
| S420 | Kontakt meldet dauerhaft offen wiederholt | Magnetabstand zu groß, mehrfach innerhalb einer Stunde | Magnet näher setzen | Kritisch |
| S421 | Kontakt meldet dauerhaft offen sporadisch | Magnetabstand zu groß, unregelmäßig und ohne erkennbaren Auslöser | Magnet näher setzen | Hinweis |
| S422 | Temperaturabweichung dauerhaft | Kalibrierung erforderlich | Korrekturwert hinterlegen | Kritisch |
| S423 | Temperaturabweichung dauerhaft beim Start | Kalibrierung erforderlich, unmittelbar nach dem Einschalten | Korrekturwert hinterlegen | Hinweis |
| S424 | Temperaturabweichung dauerhaft im Betrieb | Kalibrierung erforderlich, während des laufenden Betriebs | Korrekturwert hinterlegen | Warnung |
| S425 | Temperaturabweichung dauerhaft nach Aktualisierung | Kalibrierung erforderlich, erstmals nach einer Firmwareaktualisierung | Korrekturwert hinterlegen | Störung |
| S426 | Temperaturabweichung dauerhaft nach Stromausfall | Kalibrierung erforderlich, nach einer Unterbrechung der Versorgung | Korrekturwert hinterlegen | Kritisch |
| S427 | Temperaturabweichung dauerhaft wiederholt | Kalibrierung erforderlich, mehrfach innerhalb einer Stunde | Korrekturwert hinterlegen | Hinweis |
| S428 | Temperaturabweichung dauerhaft sporadisch | Kalibrierung erforderlich, unregelmäßig und ohne erkennbaren Auslöser | Korrekturwert hinterlegen | Warnung |
| S429 | Batteriespannung unter Schwelle | Zelle erschöpft | CR2450 ersetzen | Hinweis |
| S430 | Batteriespannung unter Schwelle beim Start | Zelle erschöpft, unmittelbar nach dem Einschalten | CR2450 ersetzen | Warnung |
| S431 | Batteriespannung unter Schwelle im Betrieb | Zelle erschöpft, während des laufenden Betriebs | CR2450 ersetzen | Störung |
| S432 | Batteriespannung unter Schwelle nach Aktualisierung | Zelle erschöpft, erstmals nach einer Firmwareaktualisierung | CR2450 ersetzen | Kritisch |
| S433 | Batteriespannung unter Schwelle nach Stromausfall | Zelle erschöpft, nach einer Unterbrechung der Versorgung | CR2450 ersetzen | Hinweis |
| S434 | Batteriespannung unter Schwelle wiederholt | Zelle erschöpft, mehrfach innerhalb einer Stunde | CR2450 ersetzen | Warnung |
| S435 | Batteriespannung unter Schwelle sporadisch | Zelle erschöpft, unregelmäßig und ohne erkennbaren Auslöser | CR2450 ersetzen | Störung |
| S436 | Batterieanzeige springt | Kälteeinfluss auf die Zelle | Nach Erwärmung erneut prüfen | Warnung |
| S437 | Batterieanzeige springt beim Start | Kälteeinfluss auf die Zelle, unmittelbar nach dem Einschalten | Nach Erwärmung erneut prüfen | Störung |
| S438 | Batterieanzeige springt im Betrieb | Kälteeinfluss auf die Zelle, während des laufenden Betriebs | Nach Erwärmung erneut prüfen | Kritisch |
| S439 | Batterieanzeige springt nach Aktualisierung | Kälteeinfluss auf die Zelle, erstmals nach einer Firmwareaktualisierung | Nach Erwärmung erneut prüfen | Hinweis |
| S440 | Batterieanzeige springt nach Stromausfall | Kälteeinfluss auf die Zelle, nach einer Unterbrechung der Versorgung | Nach Erwärmung erneut prüfen | Warnung |
| S441 | Batterieanzeige springt wiederholt | Kälteeinfluss auf die Zelle, mehrfach innerhalb einer Stunde | Nach Erwärmung erneut prüfen | Störung |
| S442 | Batterieanzeige springt sporadisch | Kälteeinfluss auf die Zelle, unregelmäßig und ohne erkennbaren Auslöser | Nach Erwärmung erneut prüfen | Kritisch |
| S443 | Meldeintervall überschritten | Funkstrecke ausgelastet | Repeater ergänzen | Störung |
| S444 | Meldeintervall überschritten beim Start | Funkstrecke ausgelastet, unmittelbar nach dem Einschalten | Repeater ergänzen | Kritisch |
| S445 | Meldeintervall überschritten im Betrieb | Funkstrecke ausgelastet, während des laufenden Betriebs | Repeater ergänzen | Hinweis |
| S446 | Meldeintervall überschritten nach Aktualisierung | Funkstrecke ausgelastet, erstmals nach einer Firmwareaktualisierung | Repeater ergänzen | Warnung |
| S447 | Meldeintervall überschritten nach Stromausfall | Funkstrecke ausgelastet, nach einer Unterbrechung der Versorgung | Repeater ergänzen | Störung |
| S448 | Meldeintervall überschritten wiederholt | Funkstrecke ausgelastet, mehrfach innerhalb einer Stunde | Repeater ergänzen | Kritisch |
| S449 | Meldeintervall überschritten sporadisch | Funkstrecke ausgelastet, unregelmäßig und ohne erkennbaren Auslöser | Repeater ergänzen | Hinweis |
| S450 | Sensor nach Batteriewechsel unbekannt | Kopplung verloren | Sensor neu koppeln | Kritisch |
| S451 | Sensor nach Batteriewechsel unbekannt beim Start | Kopplung verloren, unmittelbar nach dem Einschalten | Sensor neu koppeln | Hinweis |
| S452 | Sensor nach Batteriewechsel unbekannt im Betrieb | Kopplung verloren, während des laufenden Betriebs | Sensor neu koppeln | Warnung |
| S453 | Sensor nach Batteriewechsel unbekannt nach Aktualisierung | Kopplung verloren, erstmals nach einer Firmwareaktualisierung | Sensor neu koppeln | Störung |
| S454 | Sensor nach Batteriewechsel unbekannt nach Stromausfall | Kopplung verloren, nach einer Unterbrechung der Versorgung | Sensor neu koppeln | Kritisch |
| S455 | Sensor nach Batteriewechsel unbekannt wiederholt | Kopplung verloren, mehrfach innerhalb einer Stunde | Sensor neu koppeln | Hinweis |
| S456 | Sensor nach Batteriewechsel unbekannt sporadisch | Kopplung verloren, unregelmäßig und ohne erkennbaren Auslöser | Sensor neu koppeln | Warnung |
| S457 | Feuchtewert nicht verfügbar | Gerätevariante ohne Feuchtefühler | Kein Eingriff möglich | Hinweis |
| S458 | Feuchtewert nicht verfügbar beim Start | Gerätevariante ohne Feuchtefühler, unmittelbar nach dem Einschalten | Kein Eingriff möglich | Warnung |
| S459 | Feuchtewert nicht verfügbar im Betrieb | Gerätevariante ohne Feuchtefühler, während des laufenden Betriebs | Kein Eingriff möglich | Störung |
| S460 | Feuchtewert nicht verfügbar nach Aktualisierung | Gerätevariante ohne Feuchtefühler, erstmals nach einer Firmwareaktualisierung | Kein Eingriff möglich | Kritisch |
| S461 | Feuchtewert nicht verfügbar nach Stromausfall | Gerätevariante ohne Feuchtefühler, nach einer Unterbrechung der Versorgung | Kein Eingriff möglich | Hinweis |
| S462 | Feuchtewert nicht verfügbar wiederholt | Gerätevariante ohne Feuchtefühler, mehrfach innerhalb einer Stunde | Kein Eingriff möglich | Warnung |
| S463 | Feuchtewert nicht verfügbar sporadisch | Gerätevariante ohne Feuchtefühler, unregelmäßig und ohne erkennbaren Auslöser | Kein Eingriff möglich | Störung |
| S464 | Zwei Sensoren melden widersprüchlich | Mittelung über die Zone aktiv | Leitsensor festlegen | Warnung |
| S465 | Zwei Sensoren melden widersprüchlich beim Start | Mittelung über die Zone aktiv, unmittelbar nach dem Einschalten | Leitsensor festlegen | Störung |
| S466 | Zwei Sensoren melden widersprüchlich im Betrieb | Mittelung über die Zone aktiv, während des laufenden Betriebs | Leitsensor festlegen | Kritisch |
| S467 | Zwei Sensoren melden widersprüchlich nach Aktualisierung | Mittelung über die Zone aktiv, erstmals nach einer Firmwareaktualisierung | Leitsensor festlegen | Hinweis |
| S468 | Zwei Sensoren melden widersprüchlich nach Stromausfall | Mittelung über die Zone aktiv, nach einer Unterbrechung der Versorgung | Leitsensor festlegen | Warnung |
| S469 | Zwei Sensoren melden widersprüchlich wiederholt | Mittelung über die Zone aktiv, mehrfach innerhalb einer Stunde | Leitsensor festlegen | Störung |
| S470 | Zwei Sensoren melden widersprüchlich sporadisch | Mittelung über die Zone aktiv, unregelmäßig und ohne erkennbaren Auslöser | Leitsensor festlegen | Kritisch |

# 5xx — System und Konto

Fehler der Kontoverwaltung, der Zeitpläne und der Aktualisierung.

| Code | Meldung | Ursache | Massnahme | Schweregrad |
| --- | --- | --- | --- | --- |
| K501 | Zeitplan nicht ausgeführt | Urlaubsmodus überschreibt den Plan | Urlaubsmodus beenden | Hinweis |
| K502 | Zeitplan nicht ausgeführt beim Start | Urlaubsmodus überschreibt den Plan, unmittelbar nach dem Einschalten | Urlaubsmodus beenden | Warnung |
| K503 | Zeitplan nicht ausgeführt im Betrieb | Urlaubsmodus überschreibt den Plan, während des laufenden Betriebs | Urlaubsmodus beenden | Störung |
| K504 | Zeitplan nicht ausgeführt nach Aktualisierung | Urlaubsmodus überschreibt den Plan, erstmals nach einer Firmwareaktualisierung | Urlaubsmodus beenden | Kritisch |
| K505 | Zeitplan nicht ausgeführt nach Stromausfall | Urlaubsmodus überschreibt den Plan, nach einer Unterbrechung der Versorgung | Urlaubsmodus beenden | Hinweis |
| K506 | Zeitplan nicht ausgeführt wiederholt | Urlaubsmodus überschreibt den Plan, mehrfach innerhalb einer Stunde | Urlaubsmodus beenden | Warnung |
| K507 | Zeitplan nicht ausgeführt sporadisch | Urlaubsmodus überschreibt den Plan, unregelmäßig und ohne erkennbaren Auslöser | Urlaubsmodus beenden | Störung |
| K508 | Automatisierung ohne Wirkung | Gerät nach Anlage umbenannt | Automatisierung neu anlegen | Warnung |
| K509 | Automatisierung ohne Wirkung beim Start | Gerät nach Anlage umbenannt, unmittelbar nach dem Einschalten | Automatisierung neu anlegen | Störung |
| K510 | Automatisierung ohne Wirkung im Betrieb | Gerät nach Anlage umbenannt, während des laufenden Betriebs | Automatisierung neu anlegen | Kritisch |
| K511 | Automatisierung ohne Wirkung nach Aktualisierung | Gerät nach Anlage umbenannt, erstmals nach einer Firmwareaktualisierung | Automatisierung neu anlegen | Hinweis |
| K512 | Automatisierung ohne Wirkung nach Stromausfall | Gerät nach Anlage umbenannt, nach einer Unterbrechung der Versorgung | Automatisierung neu anlegen | Warnung |
| K513 | Automatisierung ohne Wirkung wiederholt | Gerät nach Anlage umbenannt, mehrfach innerhalb einer Stunde | Automatisierung neu anlegen | Störung |
| K514 | Automatisierung ohne Wirkung sporadisch | Gerät nach Anlage umbenannt, unregelmäßig und ohne erkennbaren Auslöser | Automatisierung neu anlegen | Kritisch |
| K515 | Aktualisierung abgebrochen | Uplink während der Verteilung verloren | Aktualisierung erneut anstoßen | Störung |
| K516 | Aktualisierung abgebrochen beim Start | Uplink während der Verteilung verloren, unmittelbar nach dem Einschalten | Aktualisierung erneut anstoßen | Kritisch |
| K517 | Aktualisierung abgebrochen im Betrieb | Uplink während der Verteilung verloren, während des laufenden Betriebs | Aktualisierung erneut anstoßen | Hinweis |
| K518 | Aktualisierung abgebrochen nach Aktualisierung | Uplink während der Verteilung verloren, erstmals nach einer Firmwareaktualisierung | Aktualisierung erneut anstoßen | Warnung |
| K519 | Aktualisierung abgebrochen nach Stromausfall | Uplink während der Verteilung verloren, nach einer Unterbrechung der Versorgung | Aktualisierung erneut anstoßen | Störung |
| K520 | Aktualisierung abgebrochen wiederholt | Uplink während der Verteilung verloren, mehrfach innerhalb einer Stunde | Aktualisierung erneut anstoßen | Kritisch |
| K521 | Aktualisierung abgebrochen sporadisch | Uplink während der Verteilung verloren, unregelmäßig und ohne erkennbaren Auslöser | Aktualisierung erneut anstoßen | Hinweis |
| K522 | Zurücksetzen nicht möglich | Gerät noch gekoppelt | Zuerst entkoppeln | Kritisch |
| K523 | Zurücksetzen nicht möglich beim Start | Gerät noch gekoppelt, unmittelbar nach dem Einschalten | Zuerst entkoppeln | Hinweis |
| K524 | Zurücksetzen nicht möglich im Betrieb | Gerät noch gekoppelt, während des laufenden Betriebs | Zuerst entkoppeln | Warnung |
| K525 | Zurücksetzen nicht möglich nach Aktualisierung | Gerät noch gekoppelt, erstmals nach einer Firmwareaktualisierung | Zuerst entkoppeln | Störung |
| K526 | Zurücksetzen nicht möglich nach Stromausfall | Gerät noch gekoppelt, nach einer Unterbrechung der Versorgung | Zuerst entkoppeln | Kritisch |
| K527 | Zurücksetzen nicht möglich wiederholt | Gerät noch gekoppelt, mehrfach innerhalb einer Stunde | Zuerst entkoppeln | Hinweis |
| K528 | Zurücksetzen nicht möglich sporadisch | Gerät noch gekoppelt, unregelmäßig und ohne erkennbaren Auslöser | Zuerst entkoppeln | Warnung |
| K529 | Freigabe fehlgeschlagen | Empfängerkonto nicht bestätigt | Einladung erneut senden | Hinweis |
| K530 | Freigabe fehlgeschlagen beim Start | Empfängerkonto nicht bestätigt, unmittelbar nach dem Einschalten | Einladung erneut senden | Warnung |
| K531 | Freigabe fehlgeschlagen im Betrieb | Empfängerkonto nicht bestätigt, während des laufenden Betriebs | Einladung erneut senden | Störung |
| K532 | Freigabe fehlgeschlagen nach Aktualisierung | Empfängerkonto nicht bestätigt, erstmals nach einer Firmwareaktualisierung | Einladung erneut senden | Kritisch |
| K533 | Freigabe fehlgeschlagen nach Stromausfall | Empfängerkonto nicht bestätigt, nach einer Unterbrechung der Versorgung | Einladung erneut senden | Hinweis |
| K534 | Freigabe fehlgeschlagen wiederholt | Empfängerkonto nicht bestätigt, mehrfach innerhalb einer Stunde | Einladung erneut senden | Warnung |
| K535 | Freigabe fehlgeschlagen sporadisch | Empfängerkonto nicht bestätigt, unregelmäßig und ohne erkennbaren Auslöser | Einladung erneut senden | Störung |
| K536 | Objekt nicht auffindbar | Konto ohne Zuordnung | Objekt in der App wählen | Warnung |
| K537 | Objekt nicht auffindbar beim Start | Konto ohne Zuordnung, unmittelbar nach dem Einschalten | Objekt in der App wählen | Störung |
| K538 | Objekt nicht auffindbar im Betrieb | Konto ohne Zuordnung, während des laufenden Betriebs | Objekt in der App wählen | Kritisch |
| K539 | Objekt nicht auffindbar nach Aktualisierung | Konto ohne Zuordnung, erstmals nach einer Firmwareaktualisierung | Objekt in der App wählen | Hinweis |
| K540 | Objekt nicht auffindbar nach Stromausfall | Konto ohne Zuordnung, nach einer Unterbrechung der Versorgung | Objekt in der App wählen | Warnung |
| K541 | Objekt nicht auffindbar wiederholt | Konto ohne Zuordnung, mehrfach innerhalb einer Stunde | Objekt in der App wählen | Störung |
| K542 | Objekt nicht auffindbar sporadisch | Konto ohne Zuordnung, unregelmäßig und ohne erkennbaren Auslöser | Objekt in der App wählen | Kritisch |
| K543 | Export unvollständig | Zeitraum ohne Daten | Zeitraum anpassen | Störung |
| K544 | Export unvollständig beim Start | Zeitraum ohne Daten, unmittelbar nach dem Einschalten | Zeitraum anpassen | Kritisch |
| K545 | Export unvollständig im Betrieb | Zeitraum ohne Daten, während des laufenden Betriebs | Zeitraum anpassen | Hinweis |
| K546 | Export unvollständig nach Aktualisierung | Zeitraum ohne Daten, erstmals nach einer Firmwareaktualisierung | Zeitraum anpassen | Warnung |
| K547 | Export unvollständig nach Stromausfall | Zeitraum ohne Daten, nach einer Unterbrechung der Versorgung | Zeitraum anpassen | Störung |
| K548 | Export unvollständig wiederholt | Zeitraum ohne Daten, mehrfach innerhalb einer Stunde | Zeitraum anpassen | Kritisch |
| K549 | Export unvollständig sporadisch | Zeitraum ohne Daten, unregelmäßig und ohne erkennbaren Auslöser | Zeitraum anpassen | Hinweis |
| K550 | Anmeldung abgelehnt | Zugangsdaten abgelaufen | Neu anmelden | Kritisch |
| K551 | Anmeldung abgelehnt beim Start | Zugangsdaten abgelaufen, unmittelbar nach dem Einschalten | Neu anmelden | Hinweis |
| K552 | Anmeldung abgelehnt im Betrieb | Zugangsdaten abgelaufen, während des laufenden Betriebs | Neu anmelden | Warnung |
| K553 | Anmeldung abgelehnt nach Aktualisierung | Zugangsdaten abgelaufen, erstmals nach einer Firmwareaktualisierung | Neu anmelden | Störung |
| K554 | Anmeldung abgelehnt nach Stromausfall | Zugangsdaten abgelaufen, nach einer Unterbrechung der Versorgung | Neu anmelden | Kritisch |
| K555 | Anmeldung abgelehnt wiederholt | Zugangsdaten abgelaufen, mehrfach innerhalb einer Stunde | Neu anmelden | Hinweis |
| K556 | Anmeldung abgelehnt sporadisch | Zugangsdaten abgelaufen, unregelmäßig und ohne erkennbaren Auslöser | Neu anmelden | Warnung |
| K557 | Übergabe nicht abgeschlossen | Installateurkonto weiterhin verknüpft | Übergabe im Portal abschliessen | Hinweis |
| K558 | Übergabe nicht abgeschlossen beim Start | Installateurkonto weiterhin verknüpft, unmittelbar nach dem Einschalten | Übergabe im Portal abschliessen | Warnung |
| K559 | Übergabe nicht abgeschlossen im Betrieb | Installateurkonto weiterhin verknüpft, während des laufenden Betriebs | Übergabe im Portal abschliessen | Störung |
| K560 | Übergabe nicht abgeschlossen nach Aktualisierung | Installateurkonto weiterhin verknüpft, erstmals nach einer Firmwareaktualisierung | Übergabe im Portal abschliessen | Kritisch |
| K561 | Übergabe nicht abgeschlossen nach Stromausfall | Installateurkonto weiterhin verknüpft, nach einer Unterbrechung der Versorgung | Übergabe im Portal abschliessen | Hinweis |
| K562 | Übergabe nicht abgeschlossen wiederholt | Installateurkonto weiterhin verknüpft, mehrfach innerhalb einer Stunde | Übergabe im Portal abschliessen | Warnung |
| K563 | Übergabe nicht abgeschlossen sporadisch | Installateurkonto weiterhin verknüpft, unregelmäßig und ohne erkennbaren Auslöser | Übergabe im Portal abschliessen | Störung |
| K564 | Konto gelöscht, Daten vorhanden | Löschfrist von 30 Tagen läuft | Frist abwarten | Warnung |
| K565 | Konto gelöscht, Daten vorhanden beim Start | Löschfrist von 30 Tagen läuft, unmittelbar nach dem Einschalten | Frist abwarten | Störung |
| K566 | Konto gelöscht, Daten vorhanden im Betrieb | Löschfrist von 30 Tagen läuft, während des laufenden Betriebs | Frist abwarten | Kritisch |
| K567 | Konto gelöscht, Daten vorhanden nach Aktualisierung | Löschfrist von 30 Tagen läuft, erstmals nach einer Firmwareaktualisierung | Frist abwarten | Hinweis |
| K568 | Konto gelöscht, Daten vorhanden nach Stromausfall | Löschfrist von 30 Tagen läuft, nach einer Unterbrechung der Versorgung | Frist abwarten | Warnung |
| K569 | Konto gelöscht, Daten vorhanden wiederholt | Löschfrist von 30 Tagen läuft, mehrfach innerhalb einer Stunde | Frist abwarten | Störung |
| K570 | Konto gelöscht, Daten vorhanden sporadisch | Löschfrist von 30 Tagen läuft, unregelmäßig und ohne erkennbaren Auslöser | Frist abwarten | Kritisch |

# Umgang mit unbekannten Codes

Codes, die hier nicht aufgeführt sind, stammen aus einer neueren Firmware als dieser Dokumentstand. Melden Sie den Code zusammen mit der Kennung des Hubs an den Support; erfinden Sie keine Massnahme auf Verdacht, insbesondere nicht bei Codes der Familie 3xx, die die Heizungsansteuerung betreffen.

