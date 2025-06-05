# Dexa GT7 Logger 🏁

Ein moderner, modularer Telemetrie-Logger für **Gran Turismo 7** – entwickelt zur präzisen Aufzeichnung und Analyse von Renndaten über das UDP-Protokoll.  
Erfasst u.a. **Rundenzeiten**, **Spritverbrauch**, **Geschwindigkeiten**, **Fahrzeugpositionen** und ermöglicht einfache Erweiterung für weitere Daten.

---

## 🚀 Funktionen

- 📦 Liest UDP-Datenpakete live von GT7 über Port `33740`
- ⛽ Berechnet zuverlässig den **Spritverbrauch**, inkl. Boxenrunden-Handling
- 🏁 Speichert Rundenzeiten, Position, Speed-Daten u.v.m.
- 📉 Ausgabe in Textformat oder zur Weiterverarbeitung in Tools wie Streamlit oder Excel
- 📂 Unterstützung für strukturiertes Log-File-Format
- ✅ Unterstützt `fuel_start_of_lap`, `fuel_used`, `best_lap`, `total_time` und weitere Telemetriedaten

---

## 📦 Voraussetzungen

- Python 3.10 oder höher
- Empfohlene Bibliotheken:

```
pip install -r requirements.txt
```
⚙️ Verwendung
Starte GT7 auf der PS5 mit aktiviertem UDP-Telemetrieausgang

Stelle sicher, dass dein PC im selben Netzwerk ist

Starte das Skript:
```
python logger_gt7_dexa.py  IP-Adresse der Playstation 
```
Die Daten werden in /logs/ als .txt gespeichert

🧪 Beispielausgabe
```
Lap  Pos  Laptime   Fuel_Used  Max_Speed  Min_Speed
1    3    01:37.532    3.41        216        94
2    3    01:38.008    1.02        220        91  
3    3    01:37.104    3.48        222        93
```




📸 Vorschau / Screenshots
Hier könnte ein Screenshot oder eine Textgrafik hin (ggf. verlinkt über Imgur)

❓ Fragen oder Ideen?
Ich bin immer offen für Tipps, wie man weitere oder andere Daten aus GT7 extrahieren kann – sei es über versteckte Pakete, kreative Umwege oder eigene Tools.
→ Issues oder direkt über einen PR! 😄

📄 Lizenz
MIT License – siehe LICENSE

🙏 Credits
Nenkai für das Verständnis der GT7-Paketstruktur

Gran Turismo™ – Polyphony Digital

