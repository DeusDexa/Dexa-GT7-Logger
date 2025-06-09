# nur für mich zum merken: .venv\Scripts\activate    py ./logger_gt7_dexa-work.py 
# Fuel per Lap muss errechnet werden 
# Max Speed pro Lap musserrechnet werden 
# Min Speed pro Lap muss errechnet werden 
# {my_pos:02}/{num_cars:02}  stehen im startbildschirm zu beginn eines rennens auf 65535 
# {lap:>2} steht am Ende eines Rennes auf 65535   
# hb schleife anders machen auch im warte fall hb senden ok  
# RaceID festlegen aus einem timestamp 
# v15 - es funktioniert alles auch der Spritverbrauch wird in der Box korrekt berechnet 
import socket
import sys
import struct
import os
#import datetime
import subprocess
import traceback

from salsa20 import Salsa20_xor
from collections import deque
from typing import List
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.patches import Rectangle 
from matplotlib.font_manager import FontProperties
from random import randint, uniform
from datetime import datetime

# Konfiguration
MATPLOTLIB_STYLE = 'ggplot'
dejavu_font = FontProperties(family="DejaVu Sans")

GGPLOT_THEME = {
    "lap_color": "#FFA500",
    "fuel_color": "#2ca02c",
    "bestlap_color": "#FFD700",
    "max_speed_color": "#1f77b4",
    "min_speed_color": "#d62728",
    "text_color": "black"
}


def global_exception_handler(exc_type, exc_value, exc_traceback):
    print("🚨 Unbehandelter Fehler:")
    traceback.print_exception(exc_type, exc_value, exc_traceback)

sys.excepthook = global_exception_handler

current_lap_max_speed = 0
current_lap_min_speed = 333 
lap_history = []
fuel_start_of_lap = None 
fuel_avg = 0
fuel_used = 0.00
fuel_used = round(fuel_used, 2)
fuel_used_cur = 0 
tanken = False
tanken_first_pkt = False
fuel_prev = None
fuel_before_box = 0
in_race = False
paket1_lap1_done = False
lastLap = None
fout = None
lapTime = 0
startTime = None
current_laptime = 0 
race_start_menu = False
main_menu = False
start_pos:int = 0
race_id = f"Race_ID_{datetime.now():%Y%m%d%H%M%S}"
current_lap_speeds: List[int] = []

SendDelaySeconds = 10
ReceivePort = 33740
SendPort = 33739
port = ReceivePort
pknt = 0
#DUMP_PACKET_NR = 112 # zu testzwecken paket 112 dumpen 

# wenn eine ip-adresse übergeben wurde dann diese nehmen
# falls keine übergeben wurde prüfen ob meine PS5 da ist
# Sonst abbruch     
# Standardwerte
ip = "192.168.178.27"
enable_graphics = True

# Parameter auswerten
if len(sys.argv) >= 2:
    ip = sys.argv[1]

if len(sys.argv) >= 3 and sys.argv[2].lower() == "nogfx":
    enable_graphics = False

print(f"Using IP: {ip}")

# IP-Konnektivität prüfen (Ping)
try:
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "1000", ip],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    if result.returncode != 0:
        print(f"ERROR: IP {ip} is unreachable.")
        exit(1)
except Exception as e:
    print(f"Ping failed: {e}")
    exit(1)

# Initialisierung eines Ringpuffers
log_lines = deque(maxlen=10)  # hält maximal 10 Einträge

def save_race_summary(logpath: str, lap_history: list, start_pos:int, race_id):
    """
    Speichert am Ende des Rennens alle geloggten Runden (lap_history) 
    in einer Datei summary.txt in logpath. 
    Jede Zeile entspricht einer Runde, mit Lap-Nr, Laptime, FuelUsed, Max-Speed, Min-Speed.
    Falls finish_pos angegeben, wird am Ende die finale Position angehängt.
    """
    if not lap_history:
        # nichts zu speichern
        return

    summary_file = os.path.join(logpath, "summary.txt")
    with open(summary_file, "w", encoding="utf-8") as f:
        # Header
        #f.write("Pos     Lap     Laptime         Fuel    Max     Min     Avg\n")
        f.write("Pos\tLap\tLaptime\t\tFuel\tMax\tMin\tAvg\n")
        # Jede Runde
        for entry in lap_history:
            f.write(
                f"{entry['pos']:02d}\t"
                f"{entry['lap']:03d}\t"
                f"{entry['laptime']}\t"
                f"{entry['fuel_used']:.2f}\t"
                f"{entry['max_speed']}\t"
                f"{entry['min_speed']}\t"
                f"{entry['avg_speed']:.0f}\n"
            )
        # Die lap_history enthält dicts mit keys "laptime", "max_speed", "min_speed" etc.
        if lap_history:
            # 1) max aller max_speed
            overall_max = max(e["max_speed"] for e in lap_history)
            # 2) min aller min_speed
            overall_min = min(e["min_speed"] for e in lap_history)
            # 3) Summe aller Laptimes
            total_ms = sum(timestr_to_ms(e["laptime"]) for e in lap_history if isinstance(e["laptime"], str))
            # formatiere Gesamt-Dauer zurück in hh:mm:ss,mmm
            total_time_str = ms_to_timestr(total_ms)
            # Bestlap 
            best_lap = min(e["laptime"] for e in lap_history)
            #finish 
            if len(lap_history) >= 2:
                pos_finish = lap_history[-2]["pos"]
            else:
                pos_finish = lap_history[-1]["pos"]  # fallback

            # Alle fuel_used-Werte sammeln (nur Zahlen)
            fuel_values = [
                entry["fuel_used"]
                for entry in lap_history
                if isinstance(entry["fuel_used"], (int, float))
            ]
            # Durchschnitt berechnen (falls Liste nicht leer)
            if fuel_values:
                avg_fuel = sum(fuel_values) / len(fuel_values)
            else:
                avg_fuel = 0.0  # oder None, je nachdem wie du's handhaben willst
           
            # avg_speed berechnen 
            # Alle avg_speed-Werte aus lap_history sammeln (nur Zahlen)
            avg_speeds: List[float] = [
                entry["avg_speed"]
                for entry in lap_history
                if isinstance(entry.get("avg_speed"), (int, float))
            ]

            # Durchschnitt berechnen (falls die Liste nicht leer ist)
            if avg_speeds:
                overall_avg_speed: float = sum(avg_speeds) / len(avg_speeds)
            else:
                overall_avg_speed: float = 0.0

            # Best Lap ermitteln - alle gültigen Laptimes in ms
            lap_times_ms = [
                timestr_to_ms(e["laptime"])
                for e in lap_history
                if e["laptime"] not in ("---", None)
            ]
            if lap_times_ms:
                fastest_ms = min(lap_times_ms)
                # zurück in das Anzeige-Format:
                best_lap = ms_to_timestr(fastest_ms)
                
            f.write(" \n") 
            f.write("Race_ID                 Dauer           BestLap         min     max     avg     PS      PF   fuelavg\n")    
            race_daten = f"{race_id}  00:{total_time_str}	00:{best_lap} 	{overall_min} 	{overall_max}	{overall_avg_speed:.0f}	{start_pos:02}	{pos_finish:02}   {avg_fuel:.2f}"
            f.write(f"{race_daten}\n")
    if enable_graphics:
        generate_graphics(logpath, lap_history, GGPLOT_THEME, race_id)


# Chart (s) anlegen 
def generate_graphics(logpath: str, lap_history: list, theme: dict, race_id, chunk_size: int = 12):
    if not lap_history:
        return
    os.makedirs(logpath, exist_ok=True)

    timestamp_str = race_id.split("_")[-1] # Zeitstempel extrahieren (nach dem letzten Unterstrich) 
    dt = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S") # In datetime-Objekt umwandeln 
    race_date_str = dt.strftime("%d.%m.%Y %H.%M")  # Formatieren in "tt.mm.jjjj hh.mm"

    for i in range(0, len(lap_history), chunk_size):
        chunk = lap_history[i:i + chunk_size]
        suffix = f"{chunk[0]['lap']:02d}-{chunk[-1]['lap']:02d}"
        chunk_logpath = os.path.join(logpath, f"lap_fuel_ggplot_{suffix}.png")
        print(f"Saving chunk: {chunk_logpath}")
        _render_graphic(chunk_logpath, chunk, theme, race_date_str)

def _render_graphic(filename: str, lap_history: list, theme: dict, race_date_str: str):
    plt.style.use(MATPLOTLIB_STYLE)
    plt.rcParams['axes.grid'] = False

    lap_nums = [entry["lap"] for entry in lap_history]
    lap_times_ms = [timestr_to_ms(entry["laptime"]) for entry in lap_history]
    fuel_used = [entry["fuel_used"] for entry in lap_history]

    fig, ax1 = plt.subplots(figsize=(12, 6))

    bar_width_lap = 0.6
    bar_width_fuel = 0.3
    bar_offset = bar_width_fuel / 2

    bar_lap = ax1.bar(
        [x - bar_offset for x in lap_nums],
        lap_times_ms,
        width=bar_width_lap,
        color=theme["lap_color"],
        edgecolor="black",
        linewidth=0.5,
        zorder=3
    )

    ax1.yaxis.set_major_formatter(FuncFormatter(lambda y, _: ms_to_timestr(int(y))))
    ax1.set_ylabel("Lap Time (mm:ss,ms)", color=theme["text_color"])
    ax1.set_xlabel("Lap", color=theme["text_color"])

    ax2 = ax1.twinx()
    bar_fuel = ax2.bar(
        [x + bar_offset for x in lap_nums],
        fuel_used,
        width=bar_width_fuel,
        color=theme["fuel_color"],
        edgecolor="black",
        linewidth=0.5,
        zorder=3
    )

    ax2.set_ylabel("Fuel Used (L)", color=theme["text_color"])

    ax1.set_xticks(lap_nums)
    ax1.tick_params(colors=theme["text_color"])
    ax2.tick_params(colors=theme["text_color"])

    fig.suptitle(f"Lap Time and Fuel Usage - {race_date_str}", fontsize=14, color=theme["text_color"])

    best_lap_time = min(lap_times_ms)
    for bar, entry, lap_time in zip(bar_lap, lap_history, lap_times_ms):
        x = bar.get_x() + bar.get_width() / 2
        y = bar.get_height()
        ax1.text(x, y + 500, f"▲ {entry['max_speed']} km/h", ha='center', va='bottom', fontsize=7, color=theme["max_speed_color"], zorder=4)
        ax1.text(x, y - 1500, f"▼ {entry['min_speed']} km/h", ha='center', va='top', fontsize=7, color=theme["min_speed_color"], zorder=4)
        if lap_time == best_lap_time:
            ax1.text(x, y + 2500, "★ Best", ha='center', va='bottom', fontsize=10, color=theme["bestlap_color"], fontproperties=dejavu_font, zorder=4)

    fig.text(0.4, 0.07, "Lap Time", ha="center", va="center", fontsize=10,
             bbox=dict(facecolor=theme["lap_color"], edgecolor="black", boxstyle="round,pad=0.4"))
    fig.text(0.6, 0.07, "Fuel Used", ha="center", va="center", fontsize=10,
             bbox=dict(facecolor=theme["fuel_color"], edgecolor="black", boxstyle="round,pad=0.4"))

    plt.tight_layout(rect=[0.05, 0.08, 0.95, 0.95])
    plt.subplots_adjust(bottom=0.18)

    fig.patches.append(
        Rectangle((0, 0), 1, 1, transform=fig.transFigure,
                  facecolor='none', edgecolor='gray', linewidth=1)
    )

    plt.savefig(filename, dpi=300)
    plt.close()
    


def clear():
    # Bildschirm säubern vor der Ausgabe 
    os.system('cls' if os.name == 'nt' else 'clear')

def ms_to_timestr(ms: int) -> str:
    # Wandelt Millisekunden in ein Format hh:mm:ss,mmm oder mm:ss,mmm um. 
    ms = int(ms)
    if ms is None or ms < 0:
        return "---"

    seconds_total = ms // 1000
    milliseconds = ms % 1000
    minutes = (seconds_total // 60) % 60
    hours = seconds_total // 3600
    seconds = seconds_total % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    else:
        return f"{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def timestr_to_ms(s: str) -> int:
# Hilfsfunktion, um einen aus ms_to_timestr stammenden String wieder in Millisekunden zu parsen
    # s = "hh:mm:ss,mmm" oder "mm:ss,mmm"
    parts = s.split(':')
    if len(parts) == 3:
        h, m, sm = parts
    else:
        h = 0
        m, sm = parts
    ssec, ms = sm.split(',')
    total_ms = (int(h) * 3600 + int(m) * 60 + int(ssec)) * 1000 + int(ms)
    return total_ms

def create_log_dir(base_path="log\gt7"):
    # Erstellt ein neues Log-Verzeichnis mit Zeitstempel und gibt den Pfad zurück.
    timestamp = datetime.now().replace(microsecond=0).isoformat().replace('-', '').replace(':', '')
    logpath = os.path.join(base_path, timestamp)
    os.makedirs(logpath, exist_ok=True)
    log_lines.append(f"📂 Neues Logverzeichnis erstellt: {logpath}")
    return logpath

logpath = create_log_dir() # Erstes Verzeichnisanlegen
logdir_initialized = True

data_type_spec = {
    'FLOAT':{'struct_decrypt':'f', 'bytes':4},
    'BYTE':{'struct_decrypt':'B', 'bytes':1},
    'INT':{'struct_decrypt':'i','bytes':4},
    'INT32':{'struct_decrypt':'i','bytes':4},
    'SHORT':{'struct_decrypt':'H','bytes':2}
}

packet_data_struct = [
    (0x04,3,"FLOAT","POSITION"),
    (0x10,3,"FLOAT","VELOCITY"),
    (0x3C,1,"FLOAT","RPM"),
    (0x44,1,"FLOAT","FUEL_LEVEL"),  #0-?100	Fuel Level	amount of of fuel left, starts at Fuel Capacity at start of race, TDB for EVs
    (0x48,1,"FLOAT","FUEL_CAPA"),   # 5,100?	Fuel Capacity	amount of fuel that fits into the tank, usually 100 for fossil fuel cars. 
    (0x4C,1,"FLOAT","SPEED"),
    (0x60,4,"FLOAT","TYRES_TEMP"),
    (0x74,2,"SHORT","LAPS"),
    (0x76,2,"SHORT","TOTALLAPS"), # How many laps the race has 
    (0x7C,1,"INT","LAST_LAPTIME"),
    (0x78,1,"INT","BEST_LAPTIME"),
    (0x84,2,"SHORT","RACE_POSITION"), # 01 von 16 2/16
    (0x90,1,"BYTE", "GEAR"),
    (0x91,1,"BYTE", "THROTTLE"),
    (0x92,1,"BYTE", "BRAKE"),
    # Erweiterung, nur fürs Logging
    #(0x0020, 1, "FLOAT", "SpeedMPS"),
    #(0x0108, 1, "FLOAT", "Throttle2"),
    #(0x010C, 1, "FLOAT", "Brake2"),
    #(0x0114, 1, "BYTE",  "Gear2"),
    #(0x0124, 3, "FLOAT", "Velocity2"),
    (0x0148, 1, "FLOAT", "Fuel"),
    (0x014C, 1, "FLOAT", "FuelCapacity"),
    (0x0150, 1, "FLOAT", "FuelPerLap"),
    (0x01B0, 4, "FLOAT", "TireWear"),
    (0x0204, 1, "INT32", "LapCount"),
    (0x0208, 1, "INT32", "CurrentLap"),
    # (0x020C, 1, "FLOAT", "LapTimeCurrent"),
    (0x0210, 1, "FLOAT", "LapTimePrevious"),
    #(0x0214, 1, "FLOAT", "LapTimeBest"),
    (0x0218, 1, "INT32", "RacePosition2"),
    (0x0220, 1, "INT32", "CarID"),
    (0x0224, 1, "INT32", "TrackID"),
    #(0x0228, 1, "FLOAT", "TotalTime"),
    #(0x022C, 1, "INT32", "BestLapCarIndex"),
    #(0x0244, 1, "INT32", "CarDamage"),
    #(0x0264, 1, "FLOAT", "BrakeBalance"),
    #(0x026C, 1, "FLOAT", "FuelMixture"),
    #(0x0270, 1, "FLOAT", "EngineMap"),
    #(0x0274, 1, "FLOAT", "TractionControlLevel")
]
# Initialisiert das UDP-Socket und bindet es an Port 33740; fängt Fehler ab, wenn der Port bereits in Benutzung ist 
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('0.0.0.0', port)
    s.bind(server_address)
except OSError as e:
    if e.errno == 10048:
        print(f"❌ Port {port} ist bereits belegt. Bitte sicherstellen, dass kein anderes Programm läuft.")
    else:
        print(f"❌ Socket-Fehler: {e}")
    exit(1)

s.settimeout(10)  # bezieht sich auf das UDP Datenpaket - Abbruch wenn 10 Sekunden nichts kommt 

# Entschlüsselt ein GT7-UDP-Datenpaket mit Salsa20 und prüft, ob das Paket gültig ist (Magic-Header "G7S0").
def salsa20_dec(dat):
    KEY = b'Simulator Interface Packet GT7 ver 0.0'
    oiv = dat[0x40:0x44]
    iv1 = int.from_bytes(oiv, byteorder='little')
    iv2 = iv1 ^ 0xDEADBEAF
    IV = bytearray()
    IV.extend(iv2.to_bytes(4, 'little'))
    IV.extend(iv1.to_bytes(4, 'little'))
    ddata = Salsa20_xor(dat, bytes(IV), KEY[0:32])
    magic = int.from_bytes(ddata[0:4], byteorder='little')
    if magic != 0x47375330:
        return bytearray(b'')
    return ddata

# Sendet einen regelmäßigen Heartbeat ("A") an die PS5, um die UDP-Übertragung der Telemetriedaten aktiv zu halten.
def send_hb(s):
    send_data = 'A'
    s.sendto(send_data.encode('utf-8'), (ip, SendPort))

send_hb(s)
# Main Loop 
try:
    while True:
        try:
            data, address = s.recvfrom(4096)
            pknt += 1
            ddata = salsa20_dec(data)
            # Alle 100 Pakete einen heartbeat senden 
            if pknt > 100:
                send_hb(s)
                pknt = 0
                
            # Wenn Daten im paket waren gehts hier weiter 
            if len(ddata) > 0:
                packet_data = {}
                for start, size, type, name in packet_data_struct:
                    end = start + size * (data_type_spec[type]['bytes'])
                    if len(ddata) >= end:
                        unpacker = data_type_spec[type]['struct_decrypt'] * size
                        data_decrypted = struct.unpack(unpacker, ddata[start:end])
                        packet_data[name] = data_decrypted
                # 
                # Ab hier Variablen parsen 
                car_id = packet_data.get("CarID", [None])[0]
                track_id = packet_data.get("TrackID", [None])[0]
                speed = int(round(float(packet_data["SPEED"][0]) * 3.6))
                current_lap_speeds.append(speed) #wird für den Durchschnitt gebraucht 
                rpm = packet_data["RPM"][0]
                lap = packet_data["LAPS"][0]
                ll = packet_data.get("LAST_LAPTIME", [None])[0] 
                lastLaptime = ms_to_timestr(ll)
                bl = packet_data.get("BEST_LAPTIME", [None])[0]
                bestLaptime = ms_to_timestr(bl)
                cl = packet_data.get("LapTimeCurrent", [None])[0] 
                # current_laptime = ms_to_timestr(cl) 
                my_pos          = packet_data.get("RACE_POSITION", [None, None])[0]
                num_cars        = packet_data.get("RACE_POSITION", [None, None])[1]  
                gas             = packet_data["THROTTLE"][0]
                brake           = packet_data["BRAKE"][0]
                gear            = packet_data["GEAR"][0] & 0x0f
                temps           = packet_data["TYRES_TEMP"]
                fuel            = packet_data.get("FUEL_LEVEL", [None])[0]
                fuel            = round(fuel, 2) if fuel is not None else None
                fuel_capacity   = packet_data.get("FUEL_CAPA", [None])[0]

                                            
                #Daten für das Runden Array sammeln 
                if speed > current_lap_max_speed:
                    current_lap_max_speed = speed
                if speed < current_lap_min_speed:
                    current_lap_min_speed = speed
                # DATEN PARSING ENDE #####################################
                
                # Im hauptmenü sind alle drei 65535 
                main_menu = (lap == 65535 and my_pos == 65535 and num_cars == 65535)
                
                if lap == 65535 or my_pos == 65535 or num_cars == 65535 or lap == 0: 
                # an 65535 kann man erkennen das kein Rennen läuft 
                    if in_race: # aber es lief schon eines 
                        log_lines.append("🛑 Rennen wurde beendet")
                        in_race = False
                        
                        # Letzte Logdatei schließen
                        if fout:
                            #Summary der vorherigen Runde in den aktuellen Pfad schreiben 
                            save_race_summary(logpath, lap_history, start_pos, race_id)
                            fout.flush()
                            fout.close()
                            fout = None 

                        # Hier ggf. Datei der Auslaufrunde löschen 
                        if lap_history:                      # erst prüfen, ob die Liste nicht leer ist
                            last_real_lap = lap_history[-1]["lap"]
                            # log_lines.append(f"Letzte Runde in lap_history : {last_real_lap}")
                            auslauf_lap = last_real_lap + 1 
                            logdatei = f"lap-{auslauf_lap}.txt"
                            datei = os.path.join(logpath, logdatei)
                            if os.path.exists(datei):
                                os.remove(datei)
                               
                else:
                    if not in_race and lap != 0:  
                        log_lines.append("🚦 Rennen beginnt oder Wiederholung läuft. ")
                        in_race = True
                
                # im startmenü eines rennens läuft im Hintegrund eine wiederholung und lap zählt hoch 
                # Prüfen ob das Spiel in einem Menü ist 
                race_start_menu = (
                    (lap != 65535 and my_pos == 65535 and num_cars == 65535)
                    or
                    (lap == 0     and my_pos == "---" and num_cars == "---")
                )

                
                # 
                # Prüfen ob das Auto an der Box ist und nachtankt
                #
                if speed > 0 and tanken: # tanken endet erstes Paket bei wiederanfahrt 
                        fuel_start_of_lap = fuel # neuer fuellstand 
                        log_lines.append(f"⛽🛑 Tanken beendet fuel ist gestiegen auf {fuel} | used: {fuel_used:.2f}")
                        tanken = False
                if (fuel_prev is not None and fuel > fuel_prev and speed == 0 and in_race) or tanken:
                    # ==> Fuel ist gestiegen: gerade wird wohl getankt
                    # Hier tanken regeln  
                    tanken = True 
                    if tanken_first_pkt == True: 
                        log_lines.append(f"⛽🟢 Tanken begonnen! fuel gestiegen von {fuel_prev} auf {fuel} | used: {fuel_used:.2f}")
                        fuel_before_box = fuel # Am Anfang in der Box den Füllstand merken 
                        tanken_first_pkt = False
                                               
                else: 
                # normales paket ohne tanken
                    #if fuel is not None and fuel_start_of_lap is not None:
                    tanken_first_pkt = True # Flag zurücksetzen 

            
                # --- Zum Schluss: speichere aktuellen Fuel in `fuel_prev` 
                # ab um zu nächstes Paket zu vergleichen ob der Tankinhalt steigt---
                if fuel_prev is not None and fuel < fuel_prev:
                    fuel_used += round(fuel_prev - fuel, 2)
                fuel_prev = fuel
                
                
                #
                # Prüfen ob ein Rennen beendet wurde  
                #
                if (lastLap is not None and lastLap > lap) or not in_race:
                    paket1_lap1_done = False # bedeutet der nächste Satz mit lap == 1 ist der erste 
                # 
                # Wenn eine Wiederholung oder der Rennstart beginnt
                # NEUES RENNEN 
                #
                if lap == 1 and not paket1_lap1_done and not race_start_menu:
                     # nur beim ersten Datensatz lap == 1 ausführen zu Beginn eines Rennens
                    race_id = f"Race_ID_{datetime.now():%Y%m%d%H%M%S}"
                    start_pos:int = my_pos # Startposition merken 
                    #fuel_start_of_lap = None  ###????????? müsste =fuel sein  
                    fuel_start_of_lap = fuel 
                    current_lap_max_speed = 0
                    current_lap_min_speed = 333
                    lap_history.clear()  # altes rennen löschen 
                    lastLap = None  # wichtig, sonst wird keine neue Runde erkannt
                    # continue  # springe zurück zum Anfang der Schleife
                    logpath = create_log_dir()
                    # logdir_initialized = False
                    log_lines.append(f"🏁🟢 Neues Rennen beginnt")
                    paket1_lap1_done = True  

                
                # 
                # NEUE RUNDE 
                #
                if lastLap != lap and in_race:
                    log_lines.append(f"🚦 Neue Runde erkannt {lap}")
                    if lastLap is not None:
                        # Durchschnitts-Speed ermitteln
                        if current_lap_speeds:
                            avg_speed = sum(current_lap_speeds) / len(current_lap_speeds)
                        else:
                            avg_speed = 0
                        
                        lap_record = {
                        "pos": my_pos, 
                        "lap": lastLap,
                        "laptime": lastLaptime,
                        "max_speed": current_lap_max_speed,
                        "min_speed": current_lap_min_speed,
                        "fuel_used": round(fuel_used,2),
                        "avg_speed": round(avg_speed, 2)
                        }
                        lap_history.append(lap_record) # Statistikarray schreiben 
                        
                        # Durschnittsverbrauch pro Runde ermitteln 
                        valid_fuel_values = [entry["fuel_used"] for entry in lap_history if isinstance(entry["fuel_used"], float)]
                        if valid_fuel_values:
                            fuel_avg = round(sum(valid_fuel_values) / len(valid_fuel_values), 2)
                        else:
                            fuel_avg = "---"
                
                    # Wenn eine neue Runde beginnt: alte Log-Datei schließen, neue Datei mit passendem Namen erstellen und Header schreiben
                    if fout:
                        fout.flush() # Aus Buffer auf Platte schreiben 
                        fout.close()
                    #if in_race:
                    fout = open(os.path.join(logpath, f'lap-{lap}.txt'), "w")
                    #header = ['speed', 'gas', 'brake', 'gear', 'tyre_FL', 'tyre_FR', 'tyre_RL', 'tyre_RR'] + [k for k in packet_data if k not in ['SPEED', 'THROTTLE', 'BRAKE', 'GEAR', 'TYRES_TEMP']]
                    header = ["LAP", "POS", "SPD", "GEAR", "RPM", "GAS", "BRK","MAX", "MIN", "TYRES           ", "FUEL", "USED", "LLAP     ", "BESTLAP"]
                    fout.write("\t".join(header) + "\n")
                    #Lap Variablen resetten
                    fuel_start_of_lap = fuel  # Startwert merken
                    current_lap_max_speed = 0
                    current_lap_min_speed = 333 
                    current_lap_speeds = []
                    fuel_prev = None
                    fuel_used = 0.00 
                    lastLap = lap  # NEUE RUNDE GESETZT ! 

                # Nächste zeile für das Log, schreibt einfach die nächste zeile in die offene Datei      
                if fout and in_race:
                    tyre_str = "|".join(f"{t:.1f}" for t in temps)
                    line = [
                        f"{lap:>2}",
                        f"{my_pos:02}/{num_cars:02}",
                        f"{speed:>3}",
                        str(gear),
                        f"{rpm:.0f}",
                        str(gas),
                        str(brake),
                        f"{current_lap_max_speed:.0f}",
                        f"{current_lap_min_speed:.0f}",
                        tyre_str,
                        f"{fuel:.2f}" if fuel is not None else "---",
                        f"{fuel_used:.2f}" if fuel_used is not None else "---",
                        lastLaptime,
                        bestLaptime
                    ]
                    #if in_race: 
                    fout.write("\t".join(line) + "\n")  # Nächste Zeile ins Log schreiben 
                    fout.flush()  # Aus Buffer auf Platte schreiben  

            # nach jedem 40. Datenpaket die Variablen ausgeben        
            if pknt % 20 == 0:  # ca 1 Sekunden ~20 Pakete -  Infos in der Konsole ausgeben
                clear() 
                # print(f"LAP: {lap:>2} POS: {my_pos} von {num_cars} | SPEED: {speed:6.2f} GAS: {gas:>3} BRAKE: {brake:>3} GEAR: {gear:>1} TYRES: {[round(t,1) for t in temps]} | FUEL: {fuel:.2f} / {fuel_capacity:.1f} l | PER LAP: {fuel_per_lap:.2f}", end='\r')
                # print(f"LAP: {lap:>2} SPEED: {speed:6.2f} GAS: {gas:>3} BRAKE: {brake:>3} GEAR: {gear:>1} TYRES: {[round(t,1) for t in temps]} | WEAR: {wear_display} | FUEL: {fuel} / {fuel_capacity} l | PER LAP: {fuel_per_lap}", end='\r')
                print("Dexa GT7 Logger - Thanks to the inspiration from Nenkai")
                print("Every millisecond tells a story. I just write it down.")
                print(f"LAP: {lap:>2} Lastlab {lastLap} POS: {my_pos:02}/{num_cars:02} | LastLap: {lastLaptime} | Bestlap: {bestLaptime}")
                print(f"SPEED: {speed:6.2f} GEAR: {gear:>1} RPM: {rpm:5.0f} GAS: {gas:>3} BRAKE: {brake:>3} | Max: {current_lap_max_speed:6.2f}  Min {current_lap_min_speed:6.2f} ")
                print(f"TYRES: {[round(t,1) for t in temps]}")
                print(f"FUEL: {fuel} l / {fuel_capacity} l | Used this Lap: {fuel_used:.2f} l | AVG: {fuel_avg} l")
                # print(f"Car_ID: {car_id} | Track_ID: {track_id}")
                # print(f"PAKETE {pknt}") 
                emoji = ["🛑", "🟢"]
                in_race_str      = emoji[in_race]
                paket1_lap1_done_str = emoji[paket1_lap1_done]
                race_start_menu_str = emoji[race_start_menu]
                main_menu_str = emoji[main_menu]
                tanken_str = emoji[tanken]
                print(f"in_race {in_race_str}  |  Rennen gestartet: {paket1_lap1_done_str} | RaceMenu: {race_start_menu_str} | HauptMenu: {main_menu_str} | tanken: {tanken_str}") 
                print(f"Ctrl+C to exit the program")
                for line in log_lines:
                    print(line) 
                        
  
        # Error Handling 
        except Exception:
            import traceback
            print("\n❌ Fehler im Hauptloop:")
            traceback.print_exc()
            try:
                send_hb(s)
            except:
                print("⚠️ Heartbeat konnte nicht gesendet werden.")
            pknt = 0
            try:
                if fout:
                    fout.close()
            except:
                print("⚠️ Fehler beim Schließen der Log-Datei.")
            exit(1)  # Skript sauber beenden
except KeyboardInterrupt:
    for lap_data in lap_history:
        print(f"Lap {lap_data['lap']:>2}: {lap_data['laptime']} | Max: {lap_data['max_speed']} | Min: {lap_data['min_speed']} | Fuel: {lap_data['fuel_used']} l ")
    print("\n❌ Abbruch mit Ctrl+C")

finally:
    print("\n📊 Letzte Rundenübersicht:")
    for lap_data in lap_history:
        print(f"Lap {lap_data['lap']:>2}: {lap_data['laptime']} | Max: {lap_data['max_speed']} | Min: {lap_data['min_speed']} | Fuel: {lap_data['fuel_used']} l ")