# Dexa GT7 Logger 🏎️
 *"Every millisecond tells a story. I just write it down."*

A modern, modular telemetry logger for **Gran Turismo 7** – built to precisely capture and analyze race data via the UDP protocol.
It records key data like **lap times**, **fuel usage**, **speed**, **vehicle position**, and is designed to be easily extended.
"This is my logger. There are many like it, but this one is mine." 

---

## 🚀 Features

* 📦 Reads live UDP packets from GT7 on port `33740`
* ⛽ Reliably calculates **fuel consumption**, including pit stop handling
* 🏎️ Logs lap times, speed data, fuel consumption and more
* 📉 Outputs as plain text or for further analysis in tools like Streamlit or Excel
* 📂 Supports structured log file format
* ✅ Tracks values like `fuel_start_of_lap`, `fuel_used`, `best_lap`, `total_time`, and other telemetry fields

---

## 📦 Requirements

* Python 3.10 or higher
* Recommended libraries:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Usage

Start GT7 on your PS5 with UDP telemetry output enabled.

Ensure your PC is on the same network.

Run the script:

```bash
python logger_gt7_dexa.py <IP address of your PlayStation> [nogfx]
```

Data will be saved as `.txt` files in the `/logs/` folder.

"Debugger? I log and pray."

---

## 🧪 Sample Output

```
Lap  Pos  Laptime   Fuel_Used  Max_Speed  Min_Speed
1    3    01:37.532    3.41        216        94
2    3    01:38.008    1.02        220        91  
3    3    01:37.104    3.48        222        93
```

---

## 📸 Preview / Screenshots

A few screenshots to illustrate what’s going on.

![Laptimes & fuel](https://i.imgur.com/oXZ4QUi.png)

![laptime / Fuel](https://github.com/DeusDexa/Dexa-GT7-Logger/blob/main/images/lap_fuel_overlay.png)

---

## ❓ Questions or Ideas?

Always open to tips on how to extract **more or different data from GT7** – whether it's hidden packet content, creative workarounds, or your own tools.
→ Open an Issue or send a PR! 😄

---

## 📄 License

MIT License – see `LICENSE`

---

## 🙏 Credits

This project is based on the excellent [raw-sim-telemetry](https://github.com/GeekyDeaks/raw-sim-telemetry) by [@GeekyDeaks](https://github.com/GeekyDeaks).  
Many thanks for the original structure and for sharing the code openly!


* [Nenkai](https://github.com/Nenkai) for insights into GT7 packet structures
* Gran Turismo™ – Polyphony Digital
